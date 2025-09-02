#!/usr/bin/env python3
"""
CAEF Task Database Manager - ChromaDB Primary
============================================
Date: August 1, 2025
Authority: AEMI - Atomic Enterprise Methodology Implementation

Real database integration for CAEF task management using ChromaDB as primary.
ChromaDB → Supabase sync handled by existing sync service.
NO MOCKS - This actually stores and retrieves tasks from ChromaDB.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import uuid
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib

# Load environment from .env
from dotenv import load_dotenv
load_dotenv()

# Import ChromaDB
import chromadb
from chromadb.config import Settings

# Import existing services
import sys
sys.path.append('/Users/bbaer/Development/Cerebral/backend-python')
sys.path.append('/Users/bbaer/Development/Cerebral/.cerebraflow')

try:
    from core.storage.unified_database_manager import UnifiedDatabaseManager
    HAS_UNIFIED_DB = True
except ImportError:
    HAS_UNIFIED_DB = False
    logger.warning("UnifiedDatabaseManager not available")

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CAEFTask:
    """CAEF Task data model"""
    task_id: str
    title: str
    description: str
    task_type: str  # cleanup, feature, bug, refactor, etc.
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    assigned_agent: Optional[str] = None
    parent_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    effort_hours: float = 0.0
    actual_hours: Optional[float] = None
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    acceptance_criteria: List[str] = None
    dependencies: List[str] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    tenant_id: str = "00000000-0000-0000-0000-000000000100"  # Default tenant
    
    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.metadata is None:
            self.metadata = {}
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
        if self.dependencies is None:
            self.dependencies = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        # Convert datetime objects to strings
        for field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
            if data.get(field) and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()
        # Convert enums to strings
        if hasattr(self.status, 'value'):
            data['status'] = self.status.value
        else:
            data['status'] = self.status
        if hasattr(self.priority, 'value'):
            data['priority'] = self.priority.value
        else:
            data['priority'] = self.priority
        return data


class CAEFTaskDatabaseManagerChromaDB:
    """
    Real database manager for CAEF tasks using ChromaDB as primary
    Integrates with Cerebral's existing ChromaDB → Supabase sync architecture
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ChromaDB-based database manager"""
        self.config = config or self._default_config()
        
        # Set up paths
        self.project_root = Path("/Users/bbaer/Development/Cerebral")
        self.chromadb_path = self.project_root / ".cerebraflow" / "core" / "storage" / "chromadb"
        
        # Tenant ID (default development tenant)
        self.tenant_id = self.config.get("tenant_id", "00000000-0000-0000-0000-000000000100")
        
        # ChromaDB client
        self.chroma_client = None
        self.collection = None
        
        # Local cache for performance
        self.task_cache: Dict[str, CAEFTask] = {}
        self.cache_ttl = timedelta(minutes=5)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Metrics
        self.metrics = {
            "tasks_created": 0,
            "tasks_updated": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "db_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Initialize ChromaDB connection
        self._initialize_chromadb()
        
        logger.info("CAEFTaskDatabaseManagerChromaDB initialized - using ChromaDB as primary")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "collection_name": "cerebral_tasks",  # Maps to cerebraflow_tasks in Supabase
            "enable_cache": True,
            "batch_size": 100,
            "retry_attempts": 3,
            "retry_delay": 1,
            "tenant_id": "00000000-0000-0000-0000-000000000100"
        }
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB connection and ensure collection exists"""
        try:
            # Create ChromaDB client with persistent storage
            self.chromadb_path.mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.chromadb_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            
            # Get or create the tasks collection
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.config["collection_name"]
                )
                logger.info(f"Connected to existing ChromaDB collection: {self.config['collection_name']}")
            except:
                # Create collection with metadata
                self.collection = self.chroma_client.create_collection(
                    name=self.config["collection_name"],
                    metadata={
                        "description": "CAEF task management",
                        "created_at": datetime.now().isoformat(),
                        "tenant_aware": True,
                        "sync_to_supabase": True
                    }
                )
                logger.info(f"Created new ChromaDB collection: {self.config['collection_name']}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _generate_enterprise_task_sequence(self, category: str) -> str:
        """
        Generate enterprise-grade task sequence number with ChromaDB validation
        
        Args:
            category: Task category (e.g., 'CORE', 'TASK', etc.)
            
        Returns:
            9-digit sequence number with leading zeros
        """
        try:
            # Query ChromaDB for existing tasks in this category
            result = self.collection.get(
                where={"category": category},
                include=["metadatas"]
            )
            
            # Extract sequence numbers from existing task IDs
            sequences = []
            for metadata in result.get("metadatas", []):
                task_id = metadata.get("task_id", "")
                if task_id.startswith(f"{category}-"):
                    try:
                        sequence_part = task_id.split("-")[-1]
                        sequences.append(int(sequence_part))
                    except (ValueError, IndexError):
                        continue
            
            # Generate next sequence number
            next_sequence = max(sequences) + 1 if sequences else 1
            
            # Format as 9-digit sequence with leading zeros
            return f"{next_sequence:09d}"
            
        except Exception as e:
            logger.warning(f"Error generating enterprise task sequence: {e}")
            # Fallback to timestamp-based sequence
            import time
            return f"{int(time.time()):09d}"
    
    async def create_task(self, task_data: Dict[str, Any]) -> CAEFTask:
        """
        Create a new task in ChromaDB
        
        Args:
            task_data: Task information
            
        Returns:
            Created task object
        """
        try:
            # Generate task ID if not provided
            if "task_id" not in task_data:
                # Generate CEREBRAL_397 compliant task ID
                category = task_data.get("category", "TASK").upper()
                # Enterprise-grade task ID generation with ChromaDB validation
                sequence = self._generate_enterprise_task_sequence(category)
                task_data["task_id"] = f"{category}-{sequence}"
            
            # Set timestamps
            now = datetime.now()
            task_data["created_at"] = now
            task_data["updated_at"] = now
            
            # Set defaults
            task_data.setdefault("description", "")
            task_data.setdefault("status", TaskStatus.PENDING)
            task_data.setdefault("priority", TaskPriority.MEDIUM)
            task_data.setdefault("retry_count", 0)
            task_data.setdefault("metadata", {})
            task_data.setdefault("acceptance_criteria", [])
            task_data.setdefault("dependencies", [])
            task_data.setdefault("tenant_id", self.tenant_id)
            
            # Create task object
            task = CAEFTask(**task_data)
            
            # Store in ChromaDB
            await self._store_task_chromadb(task)
            
            # Update cache
            if self.config["enable_cache"]:
                self.task_cache[task.task_id] = task
                self.cache_timestamps[task.task_id] = now
            
            # Update metrics
            self.metrics["tasks_created"] += 1
            self.metrics["db_operations"] += 1
            
            logger.info(f"Created task {task.task_id}: {task.title}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    async def _store_task_chromadb(self, task: CAEFTask):
        """Store task in ChromaDB"""
        task_dict = task.to_dict()
        
        # Create document for ChromaDB
        # Use title + description as the document content for embeddings
        document = f"{task.title}\n{task.description}"
        
        # Create metadata (ChromaDB doesn't support complex types in metadata)
        metadata = {
            "task_id": task.task_id,
            "title": task.title,
            "task_type": task.task_type,
            "status": task_dict["status"],
            "priority": task_dict["priority"],
            "tenant_id": task.tenant_id,
            "created_at": task_dict["created_at"],
            "updated_at": task_dict["updated_at"],
            "assigned_agent": task.assigned_agent or "",
            "parent_task_id": task.parent_task_id or "",
            "effort_hours": str(task.effort_hours),
            "file_path": task.file_path or ""
        }
        
        # Add other fields as JSON in metadata
        metadata["full_data"] = json.dumps({
            "acceptance_criteria": task.acceptance_criteria,
            "dependencies": task.dependencies,
            "metadata": task.metadata,
            "results": task_dict.get("results"),
            "error_message": task.error_message,
            "retry_count": task.retry_count,
            "started_at": task_dict.get("started_at"),
            "completed_at": task_dict.get("completed_at"),
            "actual_hours": task_dict.get("actual_hours")
        })
        
        # Add to ChromaDB
        self.collection.add(
            ids=[task.task_id],
            documents=[document],
            metadatas=[metadata]
        )
    
    async def get_task(self, task_id: str) -> Optional[CAEFTask]:
        """
        Retrieve a task by ID from ChromaDB
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task object or None if not found
        """
        try:
            # Check cache first
            if self.config["enable_cache"] and task_id in self.task_cache:
                cache_time = self.cache_timestamps.get(task_id)
                if cache_time and datetime.now() - cache_time < self.cache_ttl:
                    self.metrics["cache_hits"] += 1
                    return self.task_cache[task_id]
            
            self.metrics["cache_misses"] += 1
            
            # Fetch from ChromaDB
            task = await self._fetch_task_chromadb(task_id)
            
            if task and self.config["enable_cache"]:
                self.task_cache[task_id] = task
                self.cache_timestamps[task_id] = datetime.now()
            
            self.metrics["db_operations"] += 1
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def _fetch_task_chromadb(self, task_id: str) -> Optional[CAEFTask]:
        """Fetch task from ChromaDB"""
        try:
            # Get from ChromaDB by ID
            result = self.collection.get(
                ids=[task_id],
                include=["metadatas", "documents"]
            )
            
            if not result["ids"]:
                return None
            
            # Reconstruct task from metadata
            metadata = result["metadatas"][0]
            
            # Parse full_data JSON
            full_data = json.loads(metadata.get("full_data", "{}"))
            
            # Build task data
            task_data = {
                "task_id": metadata["task_id"],
                "title": metadata["title"],
                "description": result["documents"][0].split("\n", 1)[1] if "\n" in result["documents"][0] else "",
                "task_type": metadata["task_type"],
                "status": TaskStatus(metadata["status"]),
                "priority": TaskPriority(metadata["priority"]),
                "tenant_id": metadata["tenant_id"],
                "created_at": datetime.fromisoformat(metadata["created_at"]),
                "updated_at": datetime.fromisoformat(metadata["updated_at"]),
                "assigned_agent": metadata.get("assigned_agent") or None,
                "parent_task_id": metadata.get("parent_task_id") or None,
                "effort_hours": float(metadata.get("effort_hours", 0)),
                "file_path": metadata.get("file_path") or None,
                "acceptance_criteria": full_data.get("acceptance_criteria", []),
                "dependencies": full_data.get("dependencies", []),
                "metadata": full_data.get("metadata", {}),
                "results": full_data.get("results"),
                "error_message": full_data.get("error_message"),
                "retry_count": full_data.get("retry_count", 0)
            }
            
            # Parse optional datetime fields
            if full_data.get("started_at"):
                task_data["started_at"] = datetime.fromisoformat(full_data["started_at"])
            if full_data.get("completed_at"):
                task_data["completed_at"] = datetime.fromisoformat(full_data["completed_at"])
            if full_data.get("actual_hours") is not None:
                task_data["actual_hours"] = full_data["actual_hours"]
            
            return CAEFTask(**task_data)
            
        except Exception as e:
            logger.error(f"Error fetching task from ChromaDB: {e}")
            return None
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[CAEFTask]:
        """
        Update a task in ChromaDB
        
        Args:
            task_id: Task identifier
            updates: Fields to update
            
        Returns:
            Updated task object
        """
        try:
            # Get existing task
            task = await self.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found for update")
                return None
            
            # Apply updates
            task_dict = task.to_dict()
            task_dict.update(updates)
            task_dict["updated_at"] = datetime.now()
            
            # Convert string status/priority back to enums if needed
            if "status" in task_dict and isinstance(task_dict["status"], str):
                task_dict["status"] = TaskStatus(task_dict["status"])
            if "priority" in task_dict and isinstance(task_dict["priority"], str):
                task_dict["priority"] = TaskPriority(task_dict["priority"])
            
            # Handle status transitions
            if "status" in updates:
                old_status = task.status
                new_status = TaskStatus(updates["status"])
                
                # Set timestamps based on status
                if new_status == TaskStatus.IN_PROGRESS and old_status == TaskStatus.PENDING:
                    task_dict["started_at"] = datetime.now()
                elif new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    task_dict["completed_at"] = datetime.now()
                    if task.started_at:
                        task_dict["actual_hours"] = (
                            task_dict["completed_at"] - task.started_at
                        ).total_seconds() / 3600
            
            # Filter out any invalid fields before creating task object
            valid_fields = {
                'task_id', 'title', 'description', 'task_type', 'status', 'priority',
                'created_at', 'updated_at', 'assigned_agent', 'parent_task_id',
                'started_at', 'completed_at', 'effort_hours', 'actual_hours',
                'file_path', 'metadata', 'acceptance_criteria', 'dependencies',
                'results', 'error_message', 'retry_count', 'tenant_id'
            }
            filtered_dict = {k: v for k, v in task_dict.items() if k in valid_fields}
            
            # Create updated task object
            updated_task = CAEFTask(**filtered_dict)
            
            # Update in ChromaDB (delete and re-add)
            self.collection.delete(ids=[task_id])
            await self._store_task_chromadb(updated_task)
            
            # Update cache
            if self.config["enable_cache"]:
                self.task_cache[task_id] = updated_task
                self.cache_timestamps[task_id] = datetime.now()
            
            # Update metrics
            self.metrics["tasks_updated"] += 1
            self.metrics["db_operations"] += 1
            
            if updated_task.status == TaskStatus.COMPLETED:
                self.metrics["tasks_completed"] += 1
            elif updated_task.status == TaskStatus.FAILED:
                self.metrics["tasks_failed"] += 1
            
            logger.info(f"Updated task {task_id}: {updates}")
            return updated_task
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise
    
    async def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[CAEFTask]:
        """
        List tasks with optional filters using ChromaDB query
        
        Args:
            filters: Query filters (status, priority, assigned_agent, etc.)
            
        Returns:
            List of matching tasks
        """
        try:
            # ChromaDB where clause requires operators for multiple conditions
            # We'll use $and operator to combine conditions
            where_conditions = [{"tenant_id": {"$eq": self.tenant_id}}]
            
            if filters:
                if "status" in filters:
                    where_conditions.append({"status": {"$eq": filters["status"]}})
                if "priority" in filters:
                    where_conditions.append({"priority": {"$eq": filters["priority"]}})
                if "assigned_agent" in filters:
                    where_conditions.append({"assigned_agent": {"$eq": filters["assigned_agent"]}})
                if "parent_task_id" in filters:
                    where_conditions.append({"parent_task_id": {"$eq": filters["parent_task_id"]}})
                if "task_type" in filters:
                    where_conditions.append({"task_type": {"$eq": filters["task_type"]}})
            
            # Build where clause
            where = {"$and": where_conditions} if len(where_conditions) > 1 else where_conditions[0]
            
            # Query ChromaDB
            result = self.collection.get(
                where=where,
                limit=self.config["batch_size"],
                include=["metadatas", "documents"]
            )
            
            tasks = []
            for i, task_id in enumerate(result["ids"]):
                # Reconstruct task from metadata
                metadata = result["metadatas"][i]
                full_data = json.loads(metadata.get("full_data", "{}"))
                
                task_data = {
                    "task_id": metadata["task_id"],
                    "title": metadata["title"],
                    "description": result["documents"][i].split("\n", 1)[1] if "\n" in result["documents"][i] else "",
                    "task_type": metadata["task_type"],
                    "status": TaskStatus(metadata["status"]),
                    "priority": TaskPriority(metadata["priority"]),
                    "tenant_id": metadata["tenant_id"],
                    "created_at": datetime.fromisoformat(metadata["created_at"]),
                    "updated_at": datetime.fromisoformat(metadata["updated_at"]),
                    "assigned_agent": metadata.get("assigned_agent") or None,
                    "parent_task_id": metadata.get("parent_task_id") or None,
                    "effort_hours": float(metadata.get("effort_hours", 0)),
                    "file_path": metadata.get("file_path") or None,
                    "acceptance_criteria": full_data.get("acceptance_criteria", []),
                    "dependencies": full_data.get("dependencies", []),
                    "metadata": full_data.get("metadata", {}),
                    "results": full_data.get("results"),
                    "error_message": full_data.get("error_message"),
                    "retry_count": full_data.get("retry_count", 0)
                }
                
                # Parse optional datetime fields
                if full_data.get("started_at"):
                    task_data["started_at"] = datetime.fromisoformat(full_data["started_at"])
                if full_data.get("completed_at"):
                    task_data["completed_at"] = datetime.fromisoformat(full_data["completed_at"])
                if full_data.get("actual_hours") is not None:
                    task_data["actual_hours"] = full_data["actual_hours"]
                
                tasks.append(CAEFTask(**task_data))
            
            # Sort by priority and created date
            tasks.sort(key=lambda t: (
                {"critical": 0, "high": 1, "medium": 2, "low": 3}[t.priority.value],
                t.created_at
            ))
            
            self.metrics["db_operations"] += 1
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []
    
    async def search_tasks(self, query: str, n_results: int = 10) -> List[CAEFTask]:
        """
        Search tasks using ChromaDB's vector search capabilities
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of matching tasks
        """
        try:
            # Search ChromaDB using embeddings
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"tenant_id": self.tenant_id},
                include=["metadatas", "documents", "distances"]
            )
            
            tasks = []
            if results["ids"] and results["ids"][0]:
                for i, task_id in enumerate(results["ids"][0]):
                    # Reconstruct task
                    metadata = results["metadatas"][0][i]
                    full_data = json.loads(metadata.get("full_data", "{}"))
                    
                    task_data = {
                        "task_id": metadata["task_id"],
                        "title": metadata["title"],
                        "description": results["documents"][0][i].split("\n", 1)[1] if "\n" in results["documents"][0][i] else "",
                        "task_type": metadata["task_type"],
                        "status": TaskStatus(metadata["status"]),
                        "priority": TaskPriority(metadata["priority"]),
                        "tenant_id": metadata["tenant_id"],
                        "created_at": datetime.fromisoformat(metadata["created_at"]),
                        "updated_at": datetime.fromisoformat(metadata["updated_at"]),
                        "assigned_agent": metadata.get("assigned_agent") or None,
                        "parent_task_id": metadata.get("parent_task_id") or None,
                        "effort_hours": float(metadata.get("effort_hours", 0)),
                        "file_path": metadata.get("file_path") or None,
                        "acceptance_criteria": full_data.get("acceptance_criteria", []),
                        "dependencies": full_data.get("dependencies", []),
                        "metadata": full_data.get("metadata", {}),
                        "results": full_data.get("results"),
                        "error_message": full_data.get("error_message"),
                        "retry_count": full_data.get("retry_count", 0)
                    }
                    
                    # Parse optional datetime fields
                    if full_data.get("started_at"):
                        task_data["started_at"] = datetime.fromisoformat(full_data["started_at"])
                    if full_data.get("completed_at"):
                        task_data["completed_at"] = datetime.fromisoformat(full_data["completed_at"])
                    if full_data.get("actual_hours") is not None:
                        task_data["actual_hours"] = full_data["actual_hours"]
                    
                    tasks.append(CAEFTask(**task_data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to search tasks: {e}")
            return []
    
    async def get_task_metrics(self) -> Dict[str, Any]:
        """
        Get task execution metrics
        
        Returns:
            Comprehensive metrics about task execution
        """
        try:
            # Note: Since we have existing tasks in the collection, we'll query a subset
            # to avoid processing thousands of documents
            
            # Get a sample of tasks for metrics
            sample_result = self.collection.get(
                where={"tenant_id": {"$eq": self.tenant_id}},
                limit=100,  # Sample size
                include=["metadatas"]
            )
            
            # Count tasks by status from sample
            status_counts = {status.value: 0 for status in TaskStatus}
            
            for metadata in sample_result.get("metadatas", []):
                status = metadata.get("status", "pending")
                if status in status_counts:
                    status_counts[status] += 1
            
            # Since collection has thousands of existing tasks, estimate totals
            collection_stats = self.collection.count()
            sample_size = len(sample_result.get("ids", []))
            
            if sample_size > 0:
                # Extrapolate from sample
                for status in status_counts:
                    status_counts[status] = int(status_counts[status] * collection_stats / sample_size)
            
            metrics = {
                "status_distribution": status_counts,
                "total_tasks": collection_stats,  # Use actual collection count
                "average_execution_hours": 0,  # Would need to process all tasks
                "estimation_accuracy": 0,  # Would need to process all tasks
                "database_metrics": self.metrics,
                "chromadb_stats": {
                    "total_documents": collection_stats,
                    "collection": self.config["collection_name"]
                },
                "cache_hit_rate": (
                    self.metrics["cache_hits"] / 
                    (self.metrics["cache_hits"] + self.metrics["cache_misses"])
                    if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0
                    else 0
                )
            }
            
            # Increment operation count
            self.metrics["db_operations"] += 1
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get task metrics: {e}")
            return {}
    
    async def get_task_dependencies(self, task_id: str) -> List[CAEFTask]:
        """
        Get all tasks that this task depends on
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of dependency tasks
        """
        task = await self.get_task(task_id)
        if not task or not task.dependencies:
            return []
        
        dependency_tasks = []
        for dep_id in task.dependencies:
            dep_task = await self.get_task(dep_id)
            if dep_task:
                dependency_tasks.append(dep_task)
        
        return dependency_tasks
    
    async def get_child_tasks(self, parent_task_id: str) -> List[CAEFTask]:
        """
        Get all child tasks of a parent task
        
        Args:
            parent_task_id: Parent task identifier
            
        Returns:
            List of child tasks
        """
        return await self.list_tasks({"parent_task_id": parent_task_id})
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get current database connection status"""
        collection_count = 0
        try:
            collection_count = self.collection.count()
        except:
            pass
            
        return {
            "connected": self.collection is not None,
            "database_type": "chromadb",
            "collection_name": self.config["collection_name"],
            "collection_path": str(self.chromadb_path),
            "document_count": collection_count,
            "cache_enabled": self.config["enable_cache"],
            "tenant_id": self.tenant_id,
            "metrics": self.metrics,
            "sync_notes": "ChromaDB → Supabase sync handled by chromadb_supabase_sync_service.py"
        }


# Example usage
async def example_usage():
    """Example of using the ChromaDB task database manager"""
    manager = CAEFTaskDatabaseManagerChromaDB()
    
    # Create a new task
    task = await manager.create_task({
        "title": "Implement ChromaDB integration for CAEF",
        "description": "Update CAEF to use ChromaDB as primary database with Supabase sync",
        "task_type": "feature",
        "priority": TaskPriority.HIGH,
        "effort_hours": 4,
        "acceptance_criteria": [
            "ChromaDB used as primary storage",
            "Existing sync service integration maintained",
            "All tests passing",
            "No mock implementations"
        ],
        "metadata": {
            "component": "database",
            "aemi_compliant": True
        }
    })
    
    print(f"Created task: {task.task_id}")
    
    # Search for tasks
    search_results = await manager.search_tasks("ChromaDB integration")
    print(f"Found {len(search_results)} matching tasks")
    
    # Get database status
    status = manager.get_database_status()
    print(f"Database status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    # This would actually run if executed directly
    # Use asyncio.get_event_loop().run_until_complete() for enterprise compliance
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(example_usage())
    finally:
        loop.close()