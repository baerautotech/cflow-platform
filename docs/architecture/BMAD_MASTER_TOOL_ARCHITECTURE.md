# BMAD Master Tool Architecture

**Document Version**: 1.0  
**Date**: 2025-01-09  
**Purpose**: Technical architecture for BMAD master tool pattern implementation

## 🏗️ **Architecture Overview**

The master tool pattern consolidates related operations into single tools with operation switches, reducing tool count while improving scalability and maintainability.

### **Core Design Principles**

1. **Single Responsibility**: Each master tool handles one domain
2. **Operation Switches**: Multiple operations per tool via parameters
3. **Backward Compatibility**: Maintain existing functionality
4. **Scalability**: Easy to add new operations
5. **Client Compliance**: Stay under tool limits

## 🔧 **Master Tool Structure**

### **Base Master Tool Class**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

class Operation(Enum):
    """Base operation enum for master tools"""
    pass

class MasterTool(ABC):
    """Abstract base class for master tools"""
    
    def __init__(self, name: str, description: str, operations: List[Operation]):
        self.name = name
        self.description = description
        self.operations = operations
    
    @abstractmethod
    def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute the specified operation"""
        pass
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the tool schema for MCP"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [op.value for op in self.operations],
                        "description": "The operation to perform"
                    }
                },
                "required": ["operation"]
            }
        }
```

### **Concrete Master Tool Example**
```python
class TaskOperation(Operation):
    ADD = "add"
    GET = "get"
    LIST = "list"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"

class BMADTaskMasterTool(MasterTool):
    """BMAD Task Management Master Tool"""
    
    def __init__(self):
        super().__init__(
            name="bmad_task",
            description="BMAD task management operations",
            operations=list(TaskOperation)
        )
    
    def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute task operation"""
        if operation == TaskOperation.ADD.value:
            return self._add_task(**kwargs)
        elif operation == TaskOperation.GET.value:
            return self._get_task(**kwargs)
        elif operation == TaskOperation.LIST.value:
            return self._list_tasks(**kwargs)
        elif operation == TaskOperation.UPDATE.value:
            return self._update_task(**kwargs)
        elif operation == TaskOperation.DELETE.value:
            return self._delete_task(**kwargs)
        elif operation == TaskOperation.SEARCH.value:
            return self._search_tasks(**kwargs)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _add_task(self, **kwargs) -> Dict[str, Any]:
        """Add a new task"""
        # Implementation
        pass
    
    def _get_task(self, **kwargs) -> Dict[str, Any]:
        """Get a task by ID"""
        # Implementation
        pass
    
    # ... other operation methods
```

## 📋 **Master Tool Registry**

### **Tool Registry Structure**
```python
class MasterToolRegistry:
    """Registry for master tools"""
    
    def __init__(self):
        self.master_tools: Dict[str, MasterTool] = {}
        self.operation_mappings: Dict[str, str] = {}
    
    def register_master_tool(self, tool: MasterTool):
        """Register a master tool"""
        self.master_tools[tool.name] = tool
        
        # Create operation mappings for backward compatibility
        for operation in tool.operations:
            old_tool_name = f"{tool.name}_{operation.value}"
            self.operation_mappings[old_tool_name] = tool.name
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas"""
        return [tool.get_tool_schema() for tool in self.master_tools.values()]
    
    def execute_tool(self, tool_name: str, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool operation"""
        if tool_name in self.master_tools:
            return self.master_tools[tool_name].execute(operation, **kwargs)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
```

### **Master Tool Definitions**

#### **Core BMAD Master Tools**
```python
# Task Management
class BMADTaskMasterTool(MasterTool):
    operations = ["add", "get", "list", "update", "delete", "search"]

# Planning
class BMADPlanMasterTool(MasterTool):
    operations = ["create", "update", "get", "list", "validate", "execute"]

# Document Management
class BMADDocMasterTool(MasterTool):
    operations = ["create", "update", "get", "list", "approve", "reject"]

# Workflow Management
class BMADWorkflowMasterTool(MasterTool):
    operations = ["start", "next", "get", "list", "execute", "status"]

# Human-in-the-Loop
class BMADHILMasterTool(MasterTool):
    operations = ["start_session", "continue_session", "end_session", "status"]

# Git Integration
class BMADGitMasterTool(MasterTool):
    operations = ["commit_changes", "push_changes", "validate_changes", "get_history"]

# Orchestration
class BMADOrchestratorMasterTool(MasterTool):
    operations = ["status", "checklist"]

# Expansion Pack Management
class BMADExpansionMasterTool(MasterTool):
    operations = ["list", "install", "enable"]
```

#### **Expansion Pack Master Tools**
```python
# Game Development
class BMADGameDevMasterTool(MasterTool):
    operations = ["create_character", "design_level", "balance_gameplay", "test_mechanics"]

# DevOps
class BMADDevOpsMasterTool(MasterTool):
    operations = ["deploy", "monitor", "scale", "backup", "rollback"]

# Creative Writing
class BMADCreativeMasterTool(MasterTool):
    operations = ["write_story", "edit_content", "review_grammar", "generate_ideas"]
```

## 🔄 **Migration Architecture**

### **Backward Compatibility Layer**
```python
class ToolMigrationAdapter:
    """Adapter for backward compatibility during migration"""
    
    def __init__(self, master_tool_registry: MasterToolRegistry):
        self.master_tool_registry = master_tool_registry
        self.legacy_tool_mappings = self._build_legacy_mappings()
    
    def _build_legacy_mappings(self) -> Dict[str, Dict[str, str]]:
        """Build mappings from legacy tools to master tools"""
        mappings = {}
        
        # Task tools
        mappings["task_add"] = {"master_tool": "bmad_task", "operation": "add"}
        mappings["task_get"] = {"master_tool": "bmad_task", "operation": "get"}
        mappings["task_list"] = {"master_tool": "bmad_task", "operation": "list"}
        # ... etc
        
        return mappings
    
    def execute_legacy_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute legacy tool via master tool"""
        if tool_name in self.legacy_tool_mappings:
            mapping = self.legacy_tool_mappings[tool_name]
            return self.master_tool_registry.execute_tool(
                mapping["master_tool"],
                mapping["operation"],
                **kwargs
            )
        else:
            raise ValueError(f"Unknown legacy tool: {tool_name}")
```

### **Migration Phases**

#### **Phase 1: Parallel Implementation**
- Implement master tools alongside existing tools
- Use migration adapter for backward compatibility
- Test master tools with existing functionality

#### **Phase 2: Gradual Migration**
- Update clients to use master tools
- Maintain legacy tool support
- Monitor performance and functionality

#### **Phase 3: Legacy Cleanup**
- Remove legacy tools
- Remove migration adapter
- Update documentation

## 🎯 **Client Integration**

### **Tool Filtering for Master Tools**
```python
class MasterToolFilter:
    """Filter master tools based on client and project requirements"""
    
    def __init__(self, client_config: ClientToolConfig, project_filter: ProjectToolFilter):
        self.client_config = client_config
        self.project_filter = project_filter
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available master tools for client/project"""
        available_tools = []
        
        for tool_name, tool in self.master_tool_registry.master_tools.items():
            if self._is_tool_available(tool_name):
                available_tools.append(tool.get_tool_schema())
        
        return available_tools
    
    def _is_tool_available(self, tool_name: str) -> bool:
        """Check if tool is available for client/project"""
        # Check client configuration
        if tool_name not in self.client_config.enabled_tools:
            return False
        
        # Check project filter
        if tool_name in self.project_filter.disabled_tools:
            return False
        
        return True
```

### **Client-Specific Tool Exposure**

#### **Cursor IDE Configuration**
```json
{
  "client_type": "cursor",
  "max_tools": 50,
  "enabled_master_tools": [
    "bmad_task",
    "bmad_plan", 
    "bmad_doc",
    "bmad_workflow",
    "bmad_git"
  ],
  "enabled_platform_tools": [
    "code.search_functions",
    "lint_full",
    "test_analyze"
  ]
}
```

#### **Mobile App Configuration**
```json
{
  "client_type": "mobile",
  "max_tools": 30,
  "enabled_master_tools": [
    "bmad_task",
    "bmad_hil"
  ],
  "enabled_platform_tools": [
    "memory_add",
    "memory_search"
  ]
}
```

## 📊 **Performance Considerations**

### **Caching Strategy**
```python
class MasterToolCache:
    """Cache for master tool operations"""
    
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl
    
    def get_cached_result(self, tool_name: str, operation: str, params: str) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        key = f"{tool_name}:{operation}:{params}"
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
        return None
    
    def cache_result(self, tool_name: str, operation: str, params: str, result: Dict[str, Any]):
        """Cache result"""
        key = f"{tool_name}:{operation}:{params}"
        self.cache[key] = (result, time.time())
```

### **Operation Optimization**
```python
class OptimizedMasterTool(MasterTool):
    """Master tool with operation optimization"""
    
    def __init__(self, name: str, description: str, operations: List[Operation]):
        super().__init__(name, description, operations)
        self.cache = MasterToolCache()
        self.operation_handlers = self._build_operation_handlers()
    
    def _build_operation_handlers(self) -> Dict[str, callable]:
        """Build operation handlers for performance"""
        handlers = {}
        for operation in self.operations:
            handlers[operation.value] = getattr(self, f"_handle_{operation.value}")
        return handlers
    
    def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute operation with optimization"""
        # Check cache
        cache_key = f"{operation}:{hash(str(kwargs))}"
        cached_result = self.cache.get_cached_result(self.name, operation, cache_key)
        if cached_result:
            return cached_result
        
        # Execute operation
        if operation in self.operation_handlers:
            result = self.operation_handlers[operation](**kwargs)
            self.cache.cache_result(self.name, operation, cache_key, result)
            return result
        else:
            raise ValueError(f"Unknown operation: {operation}")
```

## 🔍 **Testing Architecture**

### **Master Tool Testing**
```python
class MasterToolTestSuite:
    """Test suite for master tools"""
    
    def test_all_operations(self, master_tool: MasterTool):
        """Test all operations of a master tool"""
        for operation in master_tool.operations:
            self._test_operation(master_tool, operation.value)
    
    def _test_operation(self, master_tool: MasterTool, operation: str):
        """Test specific operation"""
        # Test with valid parameters
        result = master_tool.execute(operation, **self._get_test_params(operation))
        self.assertIsInstance(result, dict)
        
        # Test with invalid parameters
        with self.assertRaises(ValueError):
            master_tool.execute(operation, invalid_param="test")
    
    def _get_test_params(self, operation: str) -> Dict[str, Any]:
        """Get test parameters for operation"""
        # Return appropriate test parameters based on operation
        pass
```

### **Migration Testing**
```python
class MigrationTestSuite:
    """Test suite for migration"""
    
    def test_backward_compatibility(self):
        """Test backward compatibility during migration"""
        # Test legacy tools still work
        legacy_result = self.legacy_tool_registry.execute_tool("task_add", **test_params)
        master_result = self.master_tool_registry.execute_tool("bmad_task", "add", **test_params)
        
        self.assertEqual(legacy_result, master_result)
    
    def test_performance_comparison(self):
        """Test performance comparison"""
        # Compare performance between legacy and master tools
        legacy_time = self._time_execution(self.legacy_tool_registry.execute_tool, "task_add", **test_params)
        master_time = self._time_execution(self.master_tool_registry.execute_tool, "bmad_task", "add", **test_params)
        
        self.assertLess(master_time, legacy_time * 1.1)  # Allow 10% overhead
```

## 📚 **Documentation Architecture**

### **Master Tool Documentation**
```python
class MasterToolDocumentation:
    """Documentation generator for master tools"""
    
    def generate_tool_docs(self, master_tool: MasterTool) -> str:
        """Generate documentation for master tool"""
        doc = f"""
# {master_tool.name}

{master_tool.description}

## Operations

"""
        for operation in master_tool.operations:
            doc += f"### {operation.value}\n"
            doc += f"Description: {self._get_operation_description(operation)}\n"
            doc += f"Parameters: {self._get_operation_params(operation)}\n"
            doc += f"Returns: {self._get_operation_returns(operation)}\n\n"
        
        return doc
```

---

**This architecture provides a comprehensive foundation for implementing the master tool pattern, ensuring scalability, maintainability, and client compliance while preserving existing functionality.**
