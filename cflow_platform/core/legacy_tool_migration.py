"""
Legacy Tool Migration with Performance Validation

This module provides comprehensive migration from legacy individual tools
to master tools with performance validation and backward compatibility.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics

from .master_tool_base import MasterToolManager, OperationResult
from .performance_testing import PerformanceRegressionTester, LoadTester, CompatibilityTester

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Migration status for legacy tools"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"
    ROLLED_BACK = "rolled_back"


@dataclass
class LegacyToolMapping:
    """Mapping from legacy tool to master tool operation"""
    legacy_tool_name: str
    master_tool_name: str
    master_operation_name: str
    argument_mapping: Dict[str, str]  # legacy_arg -> master_arg
    validation_tests: List[str] = field(default_factory=list)
    performance_threshold: float = 500.0  # ms
    status: MigrationStatus = MigrationStatus.PENDING
    migration_date: Optional[str] = None
    validation_results: Optional[Dict[str, Any]] = None


@dataclass
class MigrationResult:
    """Result of migration operation"""
    legacy_tool_name: str
    master_tool_name: str
    master_operation_name: str
    success: bool
    execution_time: float
    performance_improvement: float
    validation_passed: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class LegacyToolMigrationManager:
    """Manages migration from legacy tools to master tools"""
    
    def __init__(self, master_tool_manager: MasterToolManager):
        self.master_tool_manager = master_tool_manager
        self.migration_mappings: Dict[str, LegacyToolMapping] = {}
        self.migration_stats = {
            "total_migrations": 0,
            "successful_migrations": 0,
            "failed_migrations": 0,
            "validated_migrations": 0,
            "average_performance_improvement": 0.0
        }
        
        # Performance testing components
        self.performance_tester = PerformanceRegressionTester()
        self.load_tester = LoadTester()
        self.compatibility_tester = CompatibilityTester()
        
        # Initialize migration mappings
        self._initialize_migration_mappings()
    
    def _initialize_migration_mappings(self):
        """Initialize mappings from legacy tools to master tools"""
        
        # BMAD Core Tools Migration
        self._add_migration_mapping(
            "bmad_prd_create", "bmad_doc", "create",
            {"title": "title", "content": "content", "document_type": "document_type"},
            ["test_doc_creation", "test_doc_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_prd_update", "bmad_doc", "update",
            {"document_id": "document_id", "title": "title", "content": "content"},
            ["test_doc_update", "test_doc_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_prd_get", "bmad_doc", "get",
            {"document_id": "document_id"},
            ["test_doc_retrieval"]
        )
        
        self._add_migration_mapping(
            "bmad_arch_create", "bmad_doc", "create",
            {"title": "title", "content": "content", "document_type": "document_type"},
            ["test_arch_creation", "test_arch_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_arch_update", "bmad_doc", "update",
            {"document_id": "document_id", "title": "title", "content": "content"},
            ["test_arch_update", "test_arch_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_arch_get", "bmad_doc", "get",
            {"document_id": "document_id"},
            ["test_arch_retrieval"]
        )
        
        self._add_migration_mapping(
            "bmad_story_create", "bmad_task", "create",
            {"title": "title", "description": "description", "priority": "priority"},
            ["test_task_creation", "test_task_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_story_update", "bmad_task", "update",
            {"task_id": "task_id", "title": "title", "description": "description", "status": "status"},
            ["test_task_update", "test_task_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_story_get", "bmad_task", "get",
            {"task_id": "task_id"},
            ["test_task_retrieval"]
        )
        
        # BMAD Planning Tools Migration
        self._add_migration_mapping(
            "bmad_epic_create", "bmad_plan", "create",
            {"name": "name", "description": "description", "project_type": "project_type"},
            ["test_plan_creation", "test_plan_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_epic_update", "bmad_plan", "update",
            {"plan_id": "plan_id", "name": "name", "description": "description"},
            ["test_plan_update", "test_plan_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_epic_get", "bmad_plan", "get",
            {"plan_id": "plan_id"},
            ["test_plan_retrieval"]
        )
        
        self._add_migration_mapping(
            "bmad_epic_list", "bmad_plan", "list",
            {"project_type": "project_type", "status": "status"},
            ["test_plan_listing"]
        )
        
        # BMAD Workflow Tools Migration
        self._add_migration_mapping(
            "bmad_workflow_start", "bmad_workflow", "create",
            {"name": "name", "description": "description", "steps": "steps"},
            ["test_workflow_creation", "test_workflow_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_workflow_execute", "bmad_workflow", "execute",
            {"workflow_id": "workflow_id", "parameters": "parameters"},
            ["test_workflow_execution"]
        )
        
        self._add_migration_mapping(
            "bmad_workflow_get", "bmad_workflow", "status",
            {"execution_id": "execution_id"},
            ["test_workflow_status"]
        )
        
        self._add_migration_mapping(
            "bmad_workflow_list", "bmad_workflow", "list",
            {"project_type": "project_type", "status": "status"},
            ["test_workflow_listing"]
        )
        
        # BMAD HIL Tools Migration
        self._add_migration_mapping(
            "bmad_hil_start_session", "bmad_hil", "request",
            {"request_type": "request_type", "context": "context", "urgency": "urgency"},
            ["test_hil_request", "test_hil_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_hil_continue_session", "bmad_hil", "status",
            {"request_id": "request_id"},
            ["test_hil_status"]
        )
        
        self._add_migration_mapping(
            "bmad_hil_end_session", "bmad_hil", "approve",
            {"request_id": "request_id", "approver": "approver"},
            ["test_hil_approval"]
        )
        
        self._add_migration_mapping(
            "bmad_hil_session_status", "bmad_hil", "status",
            {"request_id": "request_id"},
            ["test_hil_status"]
        )
        
        # BMAD Git Tools Migration
        self._add_migration_mapping(
            "bmad_git_commit_changes", "bmad_git", "commit",
            {"message": "message", "files": "files", "branch": "branch"},
            ["test_git_commit", "test_git_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_git_push_changes", "bmad_git", "push",
            {"branch": "branch", "remote": "remote"},
            ["test_git_push"]
        )
        
        self._add_migration_mapping(
            "bmad_git_validate_changes", "bmad_git", "status",
            {"branch": "branch"},
            ["test_git_status"]
        )
        
        self._add_migration_mapping(
            "bmad_git_get_history", "bmad_git", "status",
            {"branch": "branch"},
            ["test_git_history"]
        )
        
        # BMAD Expansion Pack Tools Migration
        self._add_migration_mapping(
            "bmad_expansion_packs_list", "bmad_expansion", "list",
            {"status": "status", "category": "category"},
            ["test_expansion_listing"]
        )
        
        self._add_migration_mapping(
            "bmad_expansion_packs_install", "bmad_expansion", "install",
            {"pack_name": "pack_name", "version": "version"},
            ["test_expansion_install", "test_expansion_validation"]
        )
        
        self._add_migration_mapping(
            "bmad_expansion_packs_enable", "bmad_expansion", "update",
            {"pack_name": "pack_name", "version": "version"},
            ["test_expansion_enable"]
        )
        
        logger.info(f"Initialized {len(self.migration_mappings)} legacy tool migration mappings")
    
    def _add_migration_mapping(self, legacy_tool: str, master_tool: str, master_operation: str,
                              argument_mapping: Dict[str, str], validation_tests: List[str] = None):
        """Add a migration mapping"""
        self.migration_mappings[legacy_tool] = LegacyToolMapping(
            legacy_tool_name=legacy_tool,
            master_tool_name=master_tool,
            master_operation_name=master_operation,
            argument_mapping=argument_mapping,
            validation_tests=validation_tests or [],
            status=MigrationStatus.PENDING
        )
    
    async def migrate_legacy_tool(self, legacy_tool_name: str, arguments: Dict[str, Any]) -> MigrationResult:
        """Migrate a legacy tool request to master tool"""
        start_time = time.time()
        
        try:
            # Get migration mapping
            mapping = self.migration_mappings.get(legacy_tool_name)
            if not mapping:
                raise ValueError(f"No migration mapping found for legacy tool: {legacy_tool_name}")
            
            # Update status
            mapping.status = MigrationStatus.IN_PROGRESS
            
            # Map arguments
            mapped_arguments = self._map_arguments(arguments, mapping.argument_mapping)
            
            # Execute master tool operation
            result = await self.master_tool_manager.execute_operation(
                mapping.master_tool_name,
                mapping.master_operation_name,
                mapped_arguments,
                request_id=f"migration_{legacy_tool_name}_{int(time.time() * 1000)}"
            )
            
            execution_time = time.time() - start_time
            
            # Validate performance
            performance_valid = execution_time <= mapping.performance_threshold
            
            # Update migration stats
            self.migration_stats["total_migrations"] += 1
            if result.success:
                self.migration_stats["successful_migrations"] += 1
                mapping.status = MigrationStatus.COMPLETED
            else:
                self.migration_stats["failed_migrations"] += 1
                mapping.status = MigrationStatus.FAILED
            
            # Calculate performance improvement (simplified)
            performance_improvement = max(0, (mapping.performance_threshold - execution_time) / mapping.performance_threshold * 100)
            
            migration_result = MigrationResult(
                legacy_tool_name=legacy_tool_name,
                master_tool_name=mapping.master_tool_name,
                master_operation_name=mapping.master_operation_name,
                success=result.success,
                execution_time=execution_time,
                performance_improvement=performance_improvement,
                validation_passed=performance_valid,
                metadata={
                    "mapped_arguments": mapped_arguments,
                    "original_arguments": arguments,
                    "performance_threshold": mapping.performance_threshold
                }
            )
            
            # Update mapping
            mapping.migration_date = time.strftime("%Y-%m-%d %H:%M:%S")
            mapping.validation_results = {
                "performance_valid": performance_valid,
                "execution_time": execution_time,
                "performance_improvement": performance_improvement
            }
            
            logger.info(f"Migrated legacy tool {legacy_tool_name} -> {mapping.master_tool_name}.{mapping.master_operation_name}")
            return migration_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Migration failed for {legacy_tool_name}: {e}")
            
            # Update stats
            self.migration_stats["total_migrations"] += 1
            self.migration_stats["failed_migrations"] += 1
            
            if legacy_tool_name in self.migration_mappings:
                self.migration_mappings[legacy_tool_name].status = MigrationStatus.FAILED
            
            return MigrationResult(
                legacy_tool_name=legacy_tool_name,
                master_tool_name="unknown",
                master_operation_name="unknown",
                success=False,
                execution_time=execution_time,
                performance_improvement=0.0,
                validation_passed=False,
                error=str(e)
            )
    
    def _map_arguments(self, legacy_arguments: Dict[str, Any], argument_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Map legacy tool arguments to master tool arguments"""
        mapped_arguments = {}
        
        for legacy_arg, master_arg in argument_mapping.items():
            if legacy_arg in legacy_arguments:
                mapped_arguments[master_arg] = legacy_arguments[legacy_arg]
        
        return mapped_arguments
    
    async def validate_migration_performance(self, legacy_tool_name: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate migration performance with test cases"""
        try:
            mapping = self.migration_mappings.get(legacy_tool_name)
            if not mapping:
                raise ValueError(f"No migration mapping found for: {legacy_tool_name}")
            
            # Run performance tests
            performance_results = []
            for test_case in test_cases:
                result = await self.migrate_legacy_tool(legacy_tool_name, test_case["arguments"])
                performance_results.append({
                    "test_case": test_case["name"],
                    "execution_time": result.execution_time,
                    "success": result.success,
                    "performance_improvement": result.performance_improvement
                })
            
            # Calculate statistics
            execution_times = [r["execution_time"] for r in performance_results if r["success"]]
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0
            max_execution_time = max(execution_times) if execution_times else 0
            min_execution_time = min(execution_times) if execution_times else 0
            
            success_rate = sum(1 for r in performance_results if r["success"]) / len(performance_results) * 100
            
            validation_result = {
                "legacy_tool": legacy_tool_name,
                "master_tool": mapping.master_tool_name,
                "master_operation": mapping.master_operation_name,
                "test_cases_count": len(test_cases),
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time,
                "max_execution_time": max_execution_time,
                "min_execution_time": min_execution_time,
                "performance_threshold": mapping.performance_threshold,
                "performance_valid": avg_execution_time <= mapping.performance_threshold,
                "test_results": performance_results,
                "validated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Update mapping status
            if validation_result["performance_valid"]:
                mapping.status = MigrationStatus.VALIDATED
                self.migration_stats["validated_migrations"] += 1
            
            logger.info(f"Validated migration performance for {legacy_tool_name}: {validation_result['performance_valid']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Performance validation failed for {legacy_tool_name}: {e}")
            return {
                "legacy_tool": legacy_tool_name,
                "validation_success": False,
                "error": str(e),
                "validated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    async def batch_migrate_legacy_tools(self, legacy_tool_names: List[str], 
                                       arguments_list: List[Dict[str, Any]]) -> List[MigrationResult]:
        """Batch migrate multiple legacy tools"""
        results = []
        
        for i, legacy_tool_name in enumerate(legacy_tool_names):
            arguments = arguments_list[i] if i < len(arguments_list) else {}
            result = await self.migrate_legacy_tool(legacy_tool_name, arguments)
            results.append(result)
        
        return results
    
    def get_migration_status(self, legacy_tool_name: str) -> Optional[Dict[str, Any]]:
        """Get migration status for a legacy tool"""
        mapping = self.migration_mappings.get(legacy_tool_name)
        if not mapping:
            return None
        
        return {
            "legacy_tool": mapping.legacy_tool_name,
            "master_tool": mapping.master_tool_name,
            "master_operation": mapping.master_operation_name,
            "status": mapping.status.value,
            "migration_date": mapping.migration_date,
            "validation_results": mapping.validation_results,
            "performance_threshold": mapping.performance_threshold
        }
    
    def get_all_migration_status(self) -> Dict[str, Any]:
        """Get migration status for all legacy tools"""
        status_summary = {}
        
        for legacy_tool, mapping in self.migration_mappings.items():
            status_summary[legacy_tool] = {
                "master_tool": mapping.master_tool_name,
                "master_operation": mapping.master_operation_name,
                "status": mapping.status.value,
                "migration_date": mapping.migration_date,
                "performance_threshold": mapping.performance_threshold
            }
        
        return {
            "total_legacy_tools": len(self.migration_mappings),
            "migration_summary": status_summary,
            "migration_stats": self.migration_stats.copy()
        }
    
    def get_migration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive migration statistics"""
        total_migrations = self.migration_stats["total_migrations"]
        success_rate = (self.migration_stats["successful_migrations"] / 
                      total_migrations * 100) if total_migrations > 0 else 0
        
        validation_rate = (self.migration_stats["validated_migrations"] / 
                          len(self.migration_mappings) * 100) if self.migration_mappings else 0
        
        return {
            **self.migration_stats,
            "success_rate_percent": success_rate,
            "validation_rate_percent": validation_rate,
            "total_legacy_tools": len(self.migration_mappings),
            "pending_migrations": sum(1 for m in self.migration_mappings.values() 
                                    if m.status == MigrationStatus.PENDING),
            "completed_migrations": sum(1 for m in self.migration_mappings.values() 
                                      if m.status == MigrationStatus.COMPLETED),
            "failed_migrations": sum(1 for m in self.migration_mappings.values() 
                                   if m.status == MigrationStatus.FAILED),
            "validated_migrations": sum(1 for m in self.migration_mappings.values() 
                                       if m.status == MigrationStatus.VALIDATED)
        }
    
    async def rollback_migration(self, legacy_tool_name: str) -> bool:
        """Rollback a migration (mark as rolled back)"""
        mapping = self.migration_mappings.get(legacy_tool_name)
        if not mapping:
            return False
        
        mapping.status = MigrationStatus.ROLLED_BACK
        logger.info(f"Rolled back migration for legacy tool: {legacy_tool_name}")
        return True
    
    def get_legacy_tools_ready_for_removal(self) -> List[str]:
        """Get list of legacy tools that are ready for removal (migrated and validated)"""
        ready_for_removal = []
        
        for legacy_tool, mapping in self.migration_mappings.items():
            if mapping.status in [MigrationStatus.VALIDATED, MigrationStatus.COMPLETED]:
                ready_for_removal.append(legacy_tool)
        
        return ready_for_removal
