"""
BMAD-Supabase Task Management Integration

This module integrates BMAD workflows with the existing Supabase task management system,
replacing the old SQLite/ChromaDB approach with direct Supabase integration.
"""

from .yaml_task_templates import bmad_template_manager

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)


class BMADSupabaseTaskManager:
    """
    BMAD integration with Supabase task management system.
    
    This class provides BMAD-specific task management that integrates
    with the existing cerebraflow_tasks table in Supabase.
    """
    
    def __init__(self):
        """Initialize the BMAD Supabase task manager."""
        self.supabase_client = None
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase client."""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase SDK not available - using mock mode")
            return
        
        url = os.getenv("SUPABASE_URL", "").strip()
        key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
               os.getenv("SUPABASE_ANON_KEY") or "").strip()
        
        if not url or not key:
            # PRODUCTION GATE: Hard fail instead of mock mode fallback
            if os.getenv("BMAD_PRODUCTION_MODE", "false").lower() == "true":
                raise RuntimeError("PRODUCTION GATE VIOLATION: Supabase credentials not found in production mode. Mock mode is UNACCEPTABLE!")
            logger.warning("Supabase credentials not found - using mock mode")
            return
        
        try:
            self.supabase_client = create_client(url, key)
            logger.info("BMAD Supabase task manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase_client = None
    
    async def create_bmad_task_from_template(self,
                                            template_id: str,
                                            project_id: str,
                                            tenant_id: str,
                                            parameters: Dict[str, Any]) -> Optional[str]:
        """
        Create a BMAD task from a YAML template.
        
        Args:
            template_id: Template identifier (prd-template, architecture-template, etc.)
            project_id: Project identifier
            tenant_id: Tenant identifier
            parameters: Template parameters
            
        Returns:
            Task ID if successful, None otherwise
        """
        if not self.supabase_client:
            logger.warning("Supabase not available - task not created")
            return None
        
        try:
            # Get template and instantiate task
            task_data = bmad_template_manager.create_task_from_template(
                template_id=template_id,
                project_id=project_id,
                tenant_id=tenant_id,
                parameters=parameters
            )
            
            if not task_data:
                logger.error(f"Failed to create task from template: {template_id}")
                return None
            
            response = self.supabase_client.table("cerebraflow_tasks").insert(task_data).execute()
            
            if response.data:
                task_id = response.data[0].get("id")
                logger.info(f"Created BMAD task from template {template_id}: {task_id}")
                return str(task_id)
            else:
                logger.error("Failed to create BMAD task - no data returned")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create BMAD task from template: {e}")
            return None
                
    async def create_bmad_task(self, 
                              title: str, 
                              description: str, 
                              workflow_type: str,
                              project_id: str,
                              tenant_id: str,
                              priority: str = "medium",
                              metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a BMAD-specific task in Supabase.
        
        Args:
            title: Task title
            description: Task description
            workflow_type: Type of BMAD workflow (PRD, ARCH, STORY, etc.)
            project_id: Project identifier
            tenant_id: Tenant identifier
            priority: Task priority
            metadata: Additional metadata
            
        Returns:
            Task ID if successful, None otherwise
        """
        if not self.supabase_client:
            logger.warning("Supabase not available - task not created")
            return None
        
        try:
            task_data = {
                "title": title,
                "description": description,
                "status": "pending",
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "bmad_workflow_type": workflow_type,
                    "project_id": project_id,
                    "tenant_id": tenant_id,
                    "source": "bmad_api",
                    **(metadata or {})
                }
            }
            
            response = self.supabase_client.table("cerebraflow_tasks").insert(task_data).execute()
            
            if response.data:
                task_id = response.data[0].get("id")
                logger.info(f"Created BMAD task: {task_id} - {title}")
                return str(task_id)
            else:
                logger.error("Failed to create BMAD task - no data returned")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create BMAD task: {e}")
            return None
    
    async def update_bmad_task_status(self, 
                                    task_id: str, 
                                    status: str,
                                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update BMAD task status in Supabase.
        
        Args:
            task_id: Task identifier
            status: New status
            metadata: Additional metadata to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.supabase_client:
            logger.warning("Supabase not available - task not updated")
            return False
        
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if metadata:
                # Merge with existing metadata
                existing = await self.get_bmad_task(task_id)
                if existing and existing.get("metadata"):
                    existing_metadata = existing["metadata"]
                    if isinstance(existing_metadata, dict):
                        update_data["metadata"] = {**existing_metadata, **metadata}
                    else:
                        update_data["metadata"] = metadata
                else:
                    update_data["metadata"] = metadata
            
            response = self.supabase_client.table("cerebraflow_tasks").update(update_data).eq("id", task_id).execute()
            
            if response.data:
                logger.info(f"Updated BMAD task {task_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update BMAD task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update BMAD task {task_id}: {e}")
            return False
    
    async def get_bmad_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get BMAD task from Supabase.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task data if found, None otherwise
        """
        if not self.supabase_client:
            logger.warning("Supabase not available - task not retrieved")
            return None
        
        try:
            response = self.supabase_client.table("cerebraflow_tasks").select("*").eq("id", task_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                logger.warning(f"BMAD task {task_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get BMAD task {task_id}: {e}")
            return None
    
    async def list_bmad_tasks(self, 
                            project_id: Optional[str] = None,
                            tenant_id: Optional[str] = None,
                            status: Optional[str] = None,
                            workflow_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List BMAD tasks from Supabase.
        
        Args:
            project_id: Filter by project ID
            tenant_id: Filter by tenant ID
            status: Filter by status
            workflow_type: Filter by workflow type
            
        Returns:
            List of task data
        """
        if not self.supabase_client:
            logger.warning("Supabase not available - tasks not retrieved")
            return []
        
        try:
            query = self.supabase_client.table("cerebraflow_tasks").select("*")
            
            # Apply filters
            if project_id:
                query = query.eq("metadata->project_id", project_id)
            if tenant_id:
                query = query.eq("metadata->tenant_id", tenant_id)
            if status:
                query = query.eq("status", status)
            if workflow_type:
                query = query.eq("metadata->bmad_workflow_type", workflow_type)
            
            # Only get BMAD tasks
            query = query.eq("metadata->source", "bmad_api")
            
            response = query.execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} BMAD tasks")
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to list BMAD tasks: {e}")
            return []
    
    async def create_bmad_workflow_tasks(self, 
                                       workflow_id: str,
                                       workflow_type: str,
                                       project_id: str,
                                       tenant_id: str,
                                       workflow_steps: List[Dict[str, Any]]) -> List[str]:
        """
        Create multiple BMAD workflow tasks.
        
        Args:
            workflow_id: Workflow identifier
            workflow_type: Type of workflow
            project_id: Project identifier
            tenant_id: Tenant identifier
            workflow_steps: List of workflow steps
            
        Returns:
            List of created task IDs
        """
        task_ids = []
        
        for i, step in enumerate(workflow_steps):
            title = step.get("title", f"{workflow_type} Step {i+1}")
            description = step.get("description", f"Execute {workflow_type} workflow step {i+1}")
            priority = step.get("priority", "medium")
            
            metadata = {
                "workflow_id": workflow_id,
                "workflow_step": i,
                "workflow_steps_total": len(workflow_steps),
                "step_metadata": step.get("metadata", {})
            }
            
            task_id = await self.create_bmad_task(
                title=title,
                description=description,
                workflow_type=workflow_type,
                project_id=project_id,
                tenant_id=tenant_id,
                priority=priority,
                metadata=metadata
            )
            
            if task_id:
                task_ids.append(task_id)
        
        logger.info(f"Created {len(task_ids)} BMAD workflow tasks for {workflow_id}")
        return task_ids
    
    async def track_bmad_workflow_progress(self, 
                                        workflow_id: str,
                                        current_step: int,
                                        total_steps: int,
                                        status: str = "in_progress") -> bool:
        """
        Track BMAD workflow progress by updating related tasks.
        
        Args:
            workflow_id: Workflow identifier
            current_step: Current step number
            total_steps: Total number of steps
            status: Current status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all tasks for this workflow
            tasks = await self.list_bmad_tasks()
            workflow_tasks = [
                task for task in tasks 
                if task.get("metadata", {}).get("workflow_id") == workflow_id
            ]
            
            if not workflow_tasks:
                logger.warning(f"No tasks found for workflow {workflow_id}")
                return False
            
            # Update task statuses based on progress
            for task in workflow_tasks:
                task_step = task.get("metadata", {}).get("workflow_step", 0)
                
                if task_step < current_step:
                    # Completed steps
                    await self.update_bmad_task_status(
                        task["id"], 
                        "completed",
                        {"completed_at": datetime.utcnow().isoformat()}
                    )
                elif task_step == current_step:
                    # Current step
                    await self.update_bmad_task_status(
                        task["id"], 
                        status,
                        {"current_step": current_step, "total_steps": total_steps}
                    )
                else:
                    # Future steps
                    await self.update_bmad_task_status(
                        task["id"], 
                        "pending",
                        {"current_step": current_step, "total_steps": total_steps}
                    )
            
            logger.info(f"Updated workflow {workflow_id} progress: {current_step}/{total_steps}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track workflow progress: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get BMAD task management statistics."""
        return {
            "supabase_available": self.supabase_client is not None,
            "supabase_sdk_available": SUPABASE_AVAILABLE,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global BMAD Supabase task manager instance
bmad_supabase_task_manager = BMADSupabaseTaskManager()


# Convenience functions for BMAD workflow integration
async def create_bmad_prd_task(project_id: str, tenant_id: str, prd_data: Dict[str, Any]) -> Optional[str]:
    """Create a BMAD PRD task."""
    return await bmad_supabase_task_manager.create_bmad_task(
        title=f"Create PRD for {project_id}",
        description=f"Generate Product Requirements Document using BMAD",
        workflow_type="PRD",
        project_id=project_id,
        tenant_id=tenant_id,
        priority="high",
        metadata={"prd_data": prd_data}
    )


async def create_bmad_architecture_task(project_id: str, tenant_id: str, arch_data: Dict[str, Any]) -> Optional[str]:
    """Create a BMAD Architecture task."""
    return await bmad_supabase_task_manager.create_bmad_task(
        title=f"Create Architecture for {project_id}",
        description=f"Generate System Architecture using BMAD",
        workflow_type="ARCH",
        project_id=project_id,
        tenant_id=tenant_id,
        priority="high",
        metadata={"arch_data": arch_data}
    )


async def create_bmad_story_task(project_id: str, tenant_id: str, story_data: Dict[str, Any]) -> Optional[str]:
    """Create a BMAD Story task."""
    return await bmad_supabase_task_manager.create_bmad_task(
        title=f"Create User Stories for {project_id}",
        description=f"Generate User Stories using BMAD",
        workflow_type="STORY",
        project_id=project_id,
        tenant_id=tenant_id,
        priority="medium",
        metadata={"story_data": story_data}
    )


async def track_bmad_workflow_execution(workflow_id: str, step: int, total_steps: int, status: str = "in_progress"):
    """Track BMAD workflow execution progress."""
    return await bmad_supabase_task_manager.track_bmad_workflow_progress(
        workflow_id=workflow_id,
        current_step=step,
        total_steps=total_steps,
        status=status
    )
