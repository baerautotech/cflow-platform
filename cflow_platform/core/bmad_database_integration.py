"""
BMAD Database Integration Module

This module provides integration between BMAD artifacts and the cerebral database schema,
handling document storage, versioning, RAG/KG integration, and task generation.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)


class BMADDatabaseIntegration:
    """Handles integration between BMAD artifacts and cerebral database schema."""
    
    def __init__(self, supabase_url: str, supabase_key: str, tenant_id: str):
        """
        Initialize BMAD database integration.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            tenant_id: Tenant identifier
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.tenant_id = tenant_id
        self.client = httpx.AsyncClient(
            base_url=supabase_url,
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    # ============================================================================
    # DOCUMENT MANAGEMENT
    # ============================================================================
    
    async def create_bmad_document(
        self,
        project_id: str,
        doc_type: str,
        title: str,
        content: str,
        metadata: Dict[str, Any] = None,
        artifacts: Dict[str, Any] = None,
        bmad_template: str = None,
        bmad_workflow: str = None,
        authored_by: str = None
    ) -> str:
        """
        Create a new BMAD document in the database.
        
        Args:
            project_id: Project identifier
            doc_type: Document type ('PRD', 'ARCH', 'STORY', 'EPIC', 'TASK')
            title: Document title
            content: Document content
            metadata: Additional metadata
            artifacts: BMAD-specific artifacts
            bmad_template: BMAD template used
            bmad_workflow: BMAD workflow used
            authored_by: Author user ID
            
        Returns:
            Document ID
        """
        try:
            # Validate document type
            valid_types = ['PRD', 'ARCH', 'STORY', 'EPIC', 'TASK']
            if doc_type not in valid_types:
                raise ValueError(f"Invalid document type: {doc_type}. Must be one of: {valid_types}")
            
            # Prepare document data
            doc_data = {
                "tenant_id": self.tenant_id,
                "project_id": project_id,
                "type": doc_type,
                "title": title,
                "content": content,
                "metadata": metadata or {},
                "artifacts": artifacts or {},
                "bmad_template": bmad_template,
                "bmad_workflow": bmad_workflow,
                "authored_by": authored_by,
                "status": "draft"
            }
            
            # Call Supabase function
            response = await self.client.post(
                "/rest/v1/rpc/create_bmad_document",
                json={
                    "p_tenant_id": self.tenant_id,
                    "p_project_id": project_id,
                    "p_type": doc_type,
                    "p_title": title,
                    "p_content": content,
                    "p_metadata": doc_data["metadata"],
                    "p_artifacts": doc_data["artifacts"],
                    "p_bmad_template": bmad_template,
                    "p_bmad_workflow": bmad_workflow,
                    "p_authored_by": authored_by
                }
            )
            
            response.raise_for_status()
            doc_id = response.text.strip('"')
            
            logger.info(f"Created BMAD document: {doc_id} ({doc_type})")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to create BMAD document: {e}")
            raise
    
    async def update_document_status(
        self,
        doc_id: str,
        status: str,
        actor: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Update document status.
        
        Args:
            doc_id: Document ID
            status: New status
            actor: User performing the action
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            valid_statuses = ['draft', 'review', 'approved', 'archived', 'rejected']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status: {status}. Must be one of: {valid_statuses}")
            
            response = await self.client.post(
                "/rest/v1/rpc/update_document_status",
                json={
                    "p_doc_id": doc_id,
                    "p_status": status,
                    "p_actor": actor,
                    "p_metadata": metadata or {}
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Updated document status: {doc_id} -> {status}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            response = await self.client.get(
                f"/rest/v1/cerebral_documents?doc_id=eq.{doc_id}&tenant_id=eq.{self.tenant_id}",
                headers={"Prefer": "return=representation"}
            )
            
            response.raise_for_status()
            documents = response.json()
            
            return documents[0] if documents else None
            
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    async def list_documents(
        self,
        project_id: str = None,
        doc_type: str = None,
        status: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List documents with optional filters.
        
        Args:
            project_id: Filter by project
            doc_type: Filter by document type
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of documents
        """
        try:
            query_params = [f"tenant_id=eq.{self.tenant_id}"]
            
            if project_id:
                query_params.append(f"project_id=eq.{project_id}")
            if doc_type:
                query_params.append(f"type=eq.{doc_type}")
            if status:
                query_params.append(f"status=eq.{status}")
            
            query_string = "&".join(query_params)
            
            response = await self.client.get(
                f"/rest/v1/cerebral_documents?{query_string}&order=created_at.desc&limit={limit}",
                headers={"Prefer": "return=representation"}
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    # ============================================================================
    # TASK MANAGEMENT
    # ============================================================================
    
    async def create_tasks_from_story(self, story_doc_id: str, actor: str) -> int:
        """
        Create tasks from an approved story document.
        
        Args:
            story_doc_id: Story document ID
            actor: User performing the action
            
        Returns:
            Number of tasks created
        """
        try:
            response = await self.client.post(
                "/rest/v1/rpc/create_tasks_from_story",
                json={
                    "p_story_doc_id": story_doc_id,
                    "p_actor": actor
                }
            )
            
            response.raise_for_status()
            tasks_created = response.json()
            
            logger.info(f"Created {tasks_created} tasks from story: {story_doc_id}")
            return tasks_created
            
        except Exception as e:
            logger.error(f"Failed to create tasks from story: {e}")
            raise
    
    async def get_tasks(
        self,
        project_id: str = None,
        status: str = None,
        assigned_to: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filters.
        
        Args:
            project_id: Filter by project
            status: Filter by status
            assigned_to: Filter by assigned user
            limit: Maximum number of results
            
        Returns:
            List of tasks
        """
        try:
            query_params = [f"tenant_id=eq.{self.tenant_id}"]
            
            if project_id:
                query_params.append(f"project_id=eq.{project_id}")
            if status:
                query_params.append(f"status=eq.{status}")
            if assigned_to:
                query_params.append(f"assigned_to=eq.{assigned_to}")
            
            query_string = "&".join(query_params)
            
            response = await self.client.get(
                f"/rest/v1/cerebral_tasks?{query_string}&order=created_at.desc&limit={limit}",
                headers={"Prefer": "return=representation"}
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []
    
    # ============================================================================
    # RAG/KG INTEGRATION
    # ============================================================================
    
    async def index_document_for_rag(
        self,
        doc_id: str,
        content: str,
        doc_type: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Index document content for RAG retrieval.
        
        Args:
            doc_id: Document ID
            content: Document content to index
            doc_type: Document type
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            # Chunk the content for embedding
            chunks = self._chunk_content(content, doc_type)
            
            # Create knowledge items and embeddings
            for i, chunk in enumerate(chunks):
                # Create knowledge item
                knowledge_item_data = {
                    "tenant_id": self.tenant_id,
                    "title": f"{doc_type} Document Chunk {i+1}",
                    "content": chunk["content"],
                    "metadata": {
                        **metadata or {},
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "chunk_type": chunk["type"],
                        "section_id": chunk.get("section_id"),
                        "section_title": chunk.get("section_title")
                    },
                    "doc_id": doc_id,
                    "content_type": doc_type
                }
                
                # Insert knowledge item
                response = await self.client.post(
                    "/rest/v1/knowledge_items",
                    json=knowledge_item_data,
                    headers={"Prefer": "return=representation"}
                )
                
                response.raise_for_status()
                knowledge_item = response.json()[0]
                
                # Generate embedding (this would typically call an embedding service)
                embedding = await self._generate_embedding(chunk["content"])
                
                # Create embedding record
                embedding_data = {
                    "knowledge_item_id": knowledge_item["id"],
                    "tenant_id": self.tenant_id,
                    "content_chunk": chunk["content"],
                    "embedding": embedding,
                    "chunk_index": i,
                    "content_type": doc_type,
                    "metadata": chunk["metadata"],
                    "doc_id": doc_id,
                    "chunk_type": chunk["type"]
                }
                
                # Insert embedding
                await self.client.post(
                    "/rest/v1/knowledge_embeddings",
                    json=embedding_data
                )
            
            logger.info(f"Indexed document for RAG: {doc_id} ({len(chunks)} chunks)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index document for RAG: {e}")
            return False
    
    async def search_documents(
        self,
        query: str,
        doc_type: str = None,
        match_count: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Search documents using semantic search.
        
        Args:
            query: Search query
            doc_type: Filter by document type
            match_count: Maximum number of results
            
        Returns:
            List of matching documents
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Search using the database function
            response = await self.client.post(
                "/rest/v1/rpc/search_bmad_documents",
                json={
                    "query_embedding": query_embedding,
                    "match_count": match_count,
                    "tenant_filter": self.tenant_id,
                    "doc_type_filter": doc_type
                }
            )
            
            response.raise_for_status()
            results = response.json()
            
            logger.info(f"Found {len(results)} documents for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    # ============================================================================
    # PROJECT MANAGEMENT
    # ============================================================================
    
    async def create_project(
        self,
        name: str,
        description: str = None,
        project_type: str = "greenfield",
        bmad_config: Dict[str, Any] = None,
        expansion_packs: List[str] = None
    ) -> str:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Project description
            project_type: Project type ('greenfield' or 'brownfield')
            bmad_config: BMAD configuration
            expansion_packs: List of expansion packs
            
        Returns:
            Project ID
        """
        try:
            project_data = {
                "tenant_id": self.tenant_id,
                "name": name,
                "description": description,
                "project_type": project_type,
                "bmad_config": bmad_config or {},
                "expansion_packs": expansion_packs or [],
                "status": "active"
            }
            
            response = await self.client.post(
                "/rest/v1/cerebral_projects",
                json=project_data,
                headers={"Prefer": "return=representation"}
            )
            
            response.raise_for_status()
            project = response.json()[0]
            
            logger.info(f"Created project: {project['project_id']} ({name})")
            return project["project_id"]
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project data or None if not found
        """
        try:
            response = await self.client.get(
                f"/rest/v1/cerebral_projects?project_id=eq.{project_id}&tenant_id=eq.{self.tenant_id}",
                headers={"Prefer": "return=representation"}
            )
            
            response.raise_for_status()
            projects = response.json()
            
            return projects[0] if projects else None
            
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return None
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _chunk_content(self, content: str, doc_type: str) -> List[Dict[str, Any]]:
        """
        Chunk content for embedding based on document type.
        
        Args:
            content: Content to chunk
            doc_type: Document type
            
        Returns:
            List of content chunks
        """
        chunks = []
        
        if doc_type == "PRD":
            chunks = self._chunk_prd_content(content)
        elif doc_type == "ARCH":
            chunks = self._chunk_arch_content(content)
        elif doc_type == "STORY":
            chunks = self._chunk_story_content(content)
        else:
            # Generic chunking
            chunks = self._chunk_generic_content(content)
        
        return chunks
    
    def _chunk_prd_content(self, content: str) -> List[Dict[str, Any]]:
        """Chunk PRD content by sections."""
        chunks = []
        sections = [
            "goals-context", "user-research", "requirements", "non-functional",
            "success-metrics", "risks-assumptions", "timeline", "appendices"
        ]
        
        for section in sections:
            # Simple section extraction (in real implementation, use proper parsing)
            if section in content.lower():
                chunk_content = f"PRD Section: {section}\n\n{content}"
                chunks.append({
                    "content": chunk_content,
                    "type": "section",
                    "section_id": section,
                    "section_title": section.replace("-", " ").title(),
                    "metadata": {"section": section, "doc_type": "PRD"}
                })
        
        if not chunks:
            chunks.append({
                "content": content,
                "type": "general",
                "metadata": {"doc_type": "PRD"}
            })
        
        return chunks
    
    def _chunk_arch_content(self, content: str) -> List[Dict[str, Any]]:
        """Chunk Architecture content by sections."""
        chunks = []
        sections = [
            "introduction", "tech-stack", "system-architecture", "data-architecture",
            "security-architecture", "deployment-architecture", "integration-patterns",
            "performance-considerations"
        ]
        
        for section in sections:
            if section in content.lower():
                chunk_content = f"Architecture Section: {section}\n\n{content}"
                chunks.append({
                    "content": chunk_content,
                    "type": "section",
                    "section_id": section,
                    "section_title": section.replace("-", " ").title(),
                    "metadata": {"section": section, "doc_type": "ARCH"}
                })
        
        if not chunks:
            chunks.append({
                "content": content,
                "type": "general",
                "metadata": {"doc_type": "ARCH"}
            })
        
        return chunks
    
    def _chunk_story_content(self, content: str) -> List[Dict[str, Any]]:
        """Chunk Story content by user stories."""
        chunks = []
        
        # Extract user stories (simple regex-based extraction)
        import re
        story_pattern = r"As a\s+(.+?),\s+I want\s+(.+?),\s+so that\s+(.+?)(?=\n\n|\nAs a|$)"
        stories = re.findall(story_pattern, content, re.DOTALL)
        
        for i, story in enumerate(stories):
            story_content = f"As a {story[0]}, I want {story[1]}, so that {story[2]}"
            chunks.append({
                "content": story_content,
                "type": "story",
                "section_id": f"story_{i+1}",
                "section_title": f"User Story {i+1}",
                "metadata": {"story_index": i, "doc_type": "STORY"}
            })
        
        if not chunks:
            chunks.append({
                "content": content,
                "type": "general",
                "metadata": {"doc_type": "STORY"}
            })
        
        return chunks
    
    def _chunk_generic_content(self, content: str) -> List[Dict[str, Any]]:
        """Generic content chunking."""
        # Simple chunking by paragraphs
        paragraphs = content.split('\n\n')
        chunks = []
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                chunks.append({
                    "content": paragraph.strip(),
                    "type": "general",
                    "section_id": f"chunk_{i+1}",
                    "section_title": f"Chunk {i+1}",
                    "metadata": {"chunk_index": i}
                })
        
        return chunks if chunks else [{
            "content": content,
            "type": "general",
            "metadata": {}
        }]
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # This is a placeholder implementation
        # In a real implementation, you would call an embedding service
        # like OpenAI, Hugging Face, or a local embedding model
        
        # For now, return a dummy embedding
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert hash to a 1536-dimensional vector (OpenAI embedding size)
        embedding = []
        for i in range(1536):
            embedding.append((hash_bytes[i % len(hash_bytes)] / 255.0) * 2 - 1)
        
        return embedding


# ============================================================================
# BMAD API INTEGRATION WRAPPER
# ============================================================================

class BMADAPIIntegration:
    """High-level integration between BMAD API and database."""
    
    def __init__(self, bmad_db: BMADDatabaseIntegration):
        """
        Initialize BMAD API integration.
        
        Args:
            bmad_db: BMAD database integration instance
        """
        self.db = bmad_db
    
    async def process_bmad_workflow_result(
        self,
        workflow_result: Dict[str, Any],
        project_id: str,
        workflow_type: str,
        actor: str
    ) -> Dict[str, Any]:
        """
        Process BMAD workflow result and store in database.
        
        Args:
            workflow_result: Result from BMAD workflow
            project_id: Project ID
            workflow_type: Type of workflow executed
            actor: User who executed the workflow
            
        Returns:
            Processing result with document IDs
        """
        try:
            result = {
                "documents_created": [],
                "tasks_created": 0,
                "indexed_for_rag": False,
                "errors": []
            }
            
            # Process different types of workflow results
            if workflow_type == "prd":
                doc_id = await self._process_prd_result(workflow_result, project_id, actor)
                result["documents_created"].append(doc_id)
                
            elif workflow_type == "architecture":
                doc_id = await self._process_arch_result(workflow_result, project_id, actor)
                result["documents_created"].append(doc_id)
                
            elif workflow_type == "story":
                doc_id = await self._process_story_result(workflow_result, project_id, actor)
                result["documents_created"].append(doc_id)
                
                # If story is approved, create tasks
                if workflow_result.get("status") == "approved":
                    tasks_created = await self.db.create_tasks_from_story(doc_id, actor)
                    result["tasks_created"] = tasks_created
            
            # Index documents for RAG
            for doc_id in result["documents_created"]:
                doc = await self.db.get_document(doc_id)
                if doc:
                    indexed = await self.db.index_document_for_rag(
                        doc_id, doc["content"], doc["type"], doc["metadata"]
                    )
                    if indexed:
                        result["indexed_for_rag"] = True
            
            logger.info(f"Processed BMAD workflow result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process BMAD workflow result: {e}")
            raise
    
    async def _process_prd_result(
        self,
        prd_result: Dict[str, Any],
        project_id: str,
        actor: str
    ) -> str:
        """Process PRD workflow result."""
        return await self.db.create_bmad_document(
            project_id=project_id,
            doc_type="PRD",
            title=prd_result.get("title", "Product Requirements Document"),
            content=prd_result.get("content", ""),
            metadata=prd_result.get("metadata", {}),
            artifacts=prd_result.get("artifacts", {}),
            bmad_template="prd-tmpl.yaml",
            bmad_workflow="greenfield-service.yaml",
            authored_by=actor
        )
    
    async def _process_arch_result(
        self,
        arch_result: Dict[str, Any],
        project_id: str,
        actor: str
    ) -> str:
        """Process Architecture workflow result."""
        return await self.db.create_bmad_document(
            project_id=project_id,
            doc_type="ARCH",
            title=arch_result.get("title", "Architecture Document"),
            content=arch_result.get("content", ""),
            metadata=arch_result.get("metadata", {}),
            artifacts=arch_result.get("artifacts", {}),
            bmad_template="architecture-tmpl.yaml",
            bmad_workflow="greenfield-service.yaml",
            authored_by=actor
        )
    
    async def _process_story_result(
        self,
        story_result: Dict[str, Any],
        project_id: str,
        actor: str
    ) -> str:
        """Process Story workflow result."""
        return await self.db.create_bmad_document(
            project_id=project_id,
            doc_type="STORY",
            title=story_result.get("title", "User Stories"),
            content=story_result.get("content", ""),
            metadata=story_result.get("metadata", {}),
            artifacts=story_result.get("artifacts", {}),
            bmad_template="story-tmpl.yaml",
            bmad_workflow="greenfield-service.yaml",
            authored_by=actor
        )
