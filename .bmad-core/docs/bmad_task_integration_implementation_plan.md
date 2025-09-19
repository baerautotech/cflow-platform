# BMAD Task Integration Implementation Plan

**Date**: 2025-01-09  
**Status**: 📋 **IMPLEMENTATION PLAN**  
**Scope**: Complete BMAD integration with cflow task management and CAEF

## 🎯 **Implementation Overview**

This plan addresses the critical gaps in BMAD integration with cflow task management and CAEF orchestration, implementing the complete workflow from BMAD story approval to CAEF multi-agent execution.

## 🏗️ **Phase 1: Database Schema Implementation**

### **Task 1.1: Create cerebral_tasks Table**
```sql
-- Create cerebral_tasks table
CREATE TABLE IF NOT EXISTS cerebral_tasks (
  task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL DEFAULT '00000000-0000-0000-0000-000000000100',
  project_id uuid NOT NULL,
  derived_from_story uuid REFERENCES cerebral_documents(doc_id),
  status text NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')) DEFAULT 'pending',
  priority text NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
  title text NOT NULL,
  description text,
  acceptance_criteria text,
  dependencies jsonb DEFAULT '[]'::jsonb,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_tenant_project ON cerebral_tasks(tenant_id, project_id);
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_status_priority ON cerebral_tasks(status, priority);
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_derived_from_story ON cerebral_tasks(derived_from_story);
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_created_at ON cerebral_tasks(created_at);
```

### **Task 1.2: Create cerebral_activities Table**
```sql
-- Create cerebral_activities table
CREATE TABLE IF NOT EXISTS cerebral_activities (
  activity_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL DEFAULT '00000000-0000-0000-0000-000000000100',
  actor uuid NOT NULL,
  action text NOT NULL,
  resource_type text NOT NULL,
  resource_id uuid NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb,
  timestamp timestamptz NOT NULL DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_cerebral_activities_tenant_actor ON cerebral_activities(tenant_id, actor);
CREATE INDEX IF NOT EXISTS idx_cerebral_activities_resource ON cerebral_activities(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_cerebral_activities_timestamp ON cerebral_activities(timestamp);
```

### **Task 1.3: Extend Knowledge Graph Tables**
```sql
-- Extend knowledge_items table
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS doc_id uuid REFERENCES cerebral_documents(doc_id);
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS task_id uuid REFERENCES cerebral_tasks(task_id);
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS content_type text CHECK (content_type IN ('PRD', 'ARCH', 'STORY', 'TASK', 'GENERAL'));

-- Extend knowledge_embeddings table
ALTER TABLE knowledge_embeddings ADD COLUMN IF NOT EXISTS doc_id uuid REFERENCES cerebral_documents(doc_id);
ALTER TABLE knowledge_embeddings ADD COLUMN IF NOT EXISTS task_id uuid REFERENCES cerebral_tasks(task_id);
ALTER TABLE knowledge_embeddings ADD COLUMN IF NOT EXISTS chunk_type text CHECK (chunk_type IN ('section', 'requirement', 'story', 'task', 'general'));

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_items_doc_id ON knowledge_items(doc_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_task_id ON knowledge_items(task_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_content_type ON knowledge_items(content_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_doc_id ON knowledge_embeddings(doc_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_task_id ON knowledge_embeddings(task_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_chunk_type ON knowledge_embeddings(chunk_type);
```

## 🔧 **Phase 2: Task Management Implementation**

### **Task 2.1: Implement Task Handlers**
```python
# File: cflow_platform/handlers/task_handlers.py
class TaskHandlers:
    async def handle_list_tasks(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """List tasks with optional filters"""
        try:
            query = self.supabase_client.table("cerebral_tasks").select("*")
            
            if filters.get("status"):
                query = query.eq("status", filters["status"])
            if filters.get("priority"):
                query = query.eq("priority", filters["priority"])
            if filters.get("project_id"):
                query = query.eq("project_id", filters["project_id"])
            
            result = query.execute()
            return {"success": True, "tasks": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        try:
            result = self.supabase_client.table("cerebral_tasks").insert(task_data).execute()
            return {"success": True, "task": result.data[0]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def handle_update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            result = self.supabase_client.table("cerebral_tasks").update(updates).eq("task_id", task_id).execute()
            return {"success": True, "task": result.data[0]}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### **Task 2.2: Implement Story-to-Task Parser**
```python
# File: cflow_platform/handlers/bmad_handlers.py
class BMADHandlers:
    async def generate_tasks_from_story(self, story_doc_id: str) -> Dict[str, Any]:
        """Generate tasks from approved BMAD story"""
        try:
            # Get story document
            story_result = await self.bmad_story_get(doc_id=story_doc_id)
            if not story_result.get("success"):
                return {"success": False, "error": "Story not found"}
            
            story = story_result["data"]
            if story["status"] != "approved":
                return {"success": False, "error": "Story must be approved to generate tasks"}
            
            # Parse story content
            tasks = self._parse_story_to_tasks(story)
            
            # Create tasks
            created_tasks = []
            for task_data in tasks:
                task_data["derived_from_story"] = story_doc_id
                task_data["project_id"] = story["project_id"]
                task_data["tenant_id"] = story["tenant_id"]
                
                task_result = await self.task_handlers.handle_create_task(task_data)
                if task_result.get("success"):
                    created_tasks.append(task_result["task"])
            
            return {"success": True, "tasks": created_tasks, "count": len(created_tasks)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_story_to_tasks(self, story: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse BMAD story content into tasks"""
        tasks = []
        content = story["content"]
        
        # Extract user stories from content
        import re
        user_stories = re.findall(r'- As a (.+?), I want (.+?) so (.+?)', content)
        
        for i, (role, want, so) in enumerate(user_stories):
            task = {
                "title": f"Implement: {want}",
                "description": f"As a {role}, I want {want} so {so}",
                "acceptance_criteria": f"User story: As a {role}, I want {want} so {so}",
                "priority": "medium",
                "status": "pending",
                "metadata": {
                    "story_index": i,
                    "role": role,
                    "want": want,
                    "so": so
                }
            }
            tasks.append(task)
        
        return tasks
```

### **Task 2.3: Implement Task Generation Workflow**
```python
# File: cflow_platform/handlers/bmad_handlers.py
class BMADHandlers:
    async def bmad_story_approve(self, doc_id: str, approver: str) -> Dict[str, Any]:
        """Approve BMAD story and trigger task generation"""
        try:
            # Approve the story
            approve_result = await self.bmad_doc_approve(doc_id=doc_id, approver=approver)
            if not approve_result.get("success"):
                return approve_result
            
            # Generate tasks from approved story
            tasks_result = await self.generate_tasks_from_story(doc_id)
            if not tasks_result.get("success"):
                return {"success": False, "error": f"Story approved but task generation failed: {tasks_result['error']}"}
            
            # Log activity
            await self._log_activity(
                actor=approver,
                action="approve_story_and_generate_tasks",
                resource_type="story",
                resource_id=doc_id,
                metadata={"tasks_generated": tasks_result["count"]}
            )
            
            return {
                "success": True,
                "message": f"Story approved and {tasks_result['count']} tasks generated",
                "tasks": tasks_result["tasks"]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

## 🚀 **Phase 3: CAEF Integration Implementation**

### **Task 3.1: Implement Planning Gate Enforcement**
```python
# File: cflow_platform/handlers/caef_handlers.py
class CAEFHandlers:
    async def check_planning_gate(self, project_id: str) -> Dict[str, Any]:
        """Check if planning is complete before allowing codegen"""
        try:
            # Check for approved PRD
            prd_result = self.supabase_client.table("cerebral_documents").select("*").eq("project_id", project_id).eq("kind", "PRD").eq("status", "approved").execute()
            if not prd_result.data:
                return {"success": False, "gate_open": False, "reason": "No approved PRD found"}
            
            # Check for approved Architecture
            arch_result = self.supabase_client.table("cerebral_documents").select("*").eq("project_id", project_id).eq("kind", "ARCHITECTURE").eq("status", "approved").execute()
            if not arch_result.data:
                return {"success": False, "gate_open": False, "reason": "No approved Architecture found"}
            
            # Check for approved Story
            story_result = self.supabase_client.table("cerebral_documents").select("*").eq("project_id", project_id).eq("kind", "STORY").eq("status", "approved").execute()
            if not story_result.data:
                return {"success": False, "gate_open": False, "reason": "No approved Story found"}
            
            # Check for generated tasks
            tasks_result = self.supabase_client.table("cerebral_tasks").select("*").eq("project_id", project_id).execute()
            if not tasks_result.data:
                return {"success": False, "gate_open": False, "reason": "No tasks generated from stories"}
            
            return {
                "success": True,
                "gate_open": True,
                "message": "Planning gate is open - all requirements met",
                "prd_count": len(prd_result.data),
                "arch_count": len(arch_result.data),
                "story_count": len(story_result.data),
                "task_count": len(tasks_result.data)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### **Task 3.2: Implement CAEF Orchestration**
```python
# File: cflow_platform/handlers/caef_handlers.py
class CAEFHandlers:
    async def start_caef_execution(self, project_id: str) -> Dict[str, Any]:
        """Start CAEF multi-agent execution for approved project"""
        try:
            # Check planning gate
            gate_result = await self.check_planning_gate(project_id)
            if not gate_result.get("gate_open"):
                return {"success": False, "error": f"Planning gate closed: {gate_result.get('reason')}"}
            
            # Get tasks for execution
            tasks_result = self.supabase_client.table("cerebral_tasks").select("*").eq("project_id", project_id).eq("status", "pending").execute()
            if not tasks_result.data:
                return {"success": False, "error": "No pending tasks found"}
            
            # Start CAEF orchestration
            execution_id = str(uuid.uuid4())
            execution_data = {
                "execution_id": execution_id,
                "project_id": project_id,
                "status": "running",
                "tasks": tasks_result.data,
                "started_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "gate_check": gate_result,
                    "task_count": len(tasks_result.data)
                }
            }
            
            # Store execution record
            self.supabase_client.table("cerebral_executions").insert(execution_data).execute()
            
            # Start multi-agent execution (placeholder for now)
            await self._start_multi_agent_execution(execution_id, tasks_result.data)
            
            return {
                "success": True,
                "execution_id": execution_id,
                "message": f"CAEF execution started for {len(tasks_result.data)} tasks",
                "execution": execution_data
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _start_multi_agent_execution(self, execution_id: str, tasks: List[Dict[str, Any]]) -> None:
        """Start multi-agent execution for tasks"""
        # Placeholder implementation
        # This would integrate with the actual CAEF orchestrator
        for task in tasks:
            # Update task status to in_progress
            self.supabase_client.table("cerebral_tasks").update({"status": "in_progress"}).eq("task_id", task["task_id"]).execute()
            
            # Simulate agent execution
            await asyncio.sleep(1)  # Placeholder
            
            # Update task status to completed
            self.supabase_client.table("cerebral_tasks").update({"status": "completed"}).eq("task_id", task["task_id"]).execute()
        
        # Update execution status
        self.supabase_client.table("cerebral_executions").update({"status": "completed", "completed_at": datetime.utcnow().isoformat()}).eq("execution_id", execution_id).execute()
```

### **Task 3.3: Add CAEF Tools to Registry**
```python
# File: cflow_platform/core/tool_registry.py
class ToolRegistry:
    @staticmethod
    def get_tools_for_mcp() -> List[Dict[str, Any]]:
        tools = []
        
        # Add CAEF tools
        tools += [
            tool("caef_check_gate", "Check planning gate status", {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": ["project_id"]}),
            tool("caef_start_execution", "Start CAEF multi-agent execution", {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": ["project_id"]}),
            tool("caef_status", "Get CAEF execution status", {"type": "object", "properties": {"execution_id": {"type": "string"}}, "required": ["execution_id"]}),
        ]
        
        return tools
```

## 🔄 **Phase 4: Document Context Implementation**

### **Task 4.1: Implement Document Context Retrieval**
```python
# File: cflow_platform/handlers/bmad_handlers.py
class BMADHandlers:
    async def get_document_context(self, project_id: str) -> Dict[str, Any]:
        """Get PRD and Architecture context for Epic/Story creation"""
        try:
            # Get approved PRD
            prd_result = self.supabase_client.table("cerebral_documents").select("*").eq("project_id", project_id).eq("kind", "PRD").eq("status", "approved").order("created_at", desc=True).limit(1).execute()
            
            # Get approved Architecture
            arch_result = self.supabase_client.table("cerebral_documents").select("*").eq("project_id", project_id).eq("kind", "ARCHITECTURE").eq("status", "approved").order("created_at", desc=True).limit(1).execute()
            
            context = {
                "project_id": project_id,
                "prd": prd_result.data[0] if prd_result.data else None,
                "architecture": arch_result.data[0] if arch_result.data else None,
                "context_available": bool(prd_result.data and arch_result.data)
            }
            
            return {"success": True, "context": context}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def bmad_story_create_with_context(self, project_name: str, prd_id: str, arch_id: str, user_stories: List[str]) -> Dict[str, Any]:
        """Create story with full context from PRD and Architecture"""
        try:
            # Get document context
            context_result = await self.get_document_context(prd_id)
            if not context_result.get("success"):
                return context_result
            
            context = context_result["context"]
            
            # Create story with enhanced context
            story_content = self._create_story_with_context(
                project_name, user_stories, 
                context["prd"], context["architecture"]
            )
            
            # Create story document
            story_data = {
                "project_id": prd_id,
                "kind": "STORY",
                "title": f"{project_name} User Story Document",
                "content": story_content,
                "status": "draft",
                "metadata": {
                    "prd_id": prd_id,
                    "arch_id": arch_id,
                    "context_included": True
                }
            }
            
            result = self.supabase_client.table("cerebral_documents").insert(story_data).execute()
            
            if result.data:
                # Index to knowledge graph
                await self._index_to_knowledge_graph(
                    result.data[0]["id"],
                    result.data[0]["title"],
                    result.data[0]["content"],
                    "STORY",
                    result.data[0]["metadata"]
                )
                
                return {
                    "success": True,
                    "doc_id": result.data[0]["id"],
                    "message": "Story document created with full context",
                    "data": result.data[0]
                }
            else:
                return {"success": False, "error": "Failed to create story document"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
```

## 📋 **Implementation Timeline**

### **Week 1: Database Schema**
- [ ] Create `cerebral_tasks` table
- [ ] Create `cerebral_activities` table
- [ ] Extend knowledge graph tables
- [ ] Test database schema

### **Week 2: Task Management**
- [ ] Implement task handlers
- [ ] Implement story-to-task parser
- [ ] Implement task generation workflow
- [ ] Test task creation from stories

### **Week 3: CAEF Integration**
- [ ] Implement planning gate enforcement
- [ ] Implement CAEF orchestration
- [ ] Add CAEF tools to registry
- [ ] Test CAEF execution workflow

### **Week 4: Document Context**
- [ ] Implement document context retrieval
- [ ] Implement context sharing between agents
- [ ] Implement approval workflow automation
- [ ] Test complete workflow

## 🎯 **Success Criteria**

### **Phase 1 Complete When**
- [ ] Database schema created and tested
- [ ] All tables have proper indexes
- [ ] Foreign key relationships working

### **Phase 2 Complete When**
- [ ] Tasks can be created from approved stories
- [ ] Task management tools working
- [ ] Task-document linking functional

### **Phase 3 Complete When**
- [ ] Planning gate enforcement working
- [ ] CAEF orchestration triggered by story approval
- [ ] Multi-agent execution workflow functional

### **Phase 4 Complete When**
- [ ] Document context available to all agents
- [ ] Complete workflow from PRD → Architecture → Story → Tasks → CAEF
- [ ] All integration points working

## 🚀 **Expected Outcome**

After implementation, the complete workflow will be:

1. **BMAD PRD Created** → Stored + indexed for context
2. **BMAD Architecture Created** → Stored + linked to PRD
3. **BMAD Story Created** → Stored + linked to Architecture + context from PRD/Arch
4. **Story Approved** → **Automatically generates tasks**
5. **Tasks Generated** → Created in `cerebral_tasks` table
6. **Planning Gate Check** → Verifies all documents approved
7. **CAEF Triggered** → Multi-agent execution begins
8. **Results Stored** → Execution results linked to tasks

This will provide the complete BMAD → Task → CAEF integration that is currently missing.
