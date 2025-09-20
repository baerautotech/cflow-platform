# BMAD Master Tool Pattern Implementation PRD

**Document Version**: 1.0  
**Date**: 2025-01-09  
**Project Type**: Brownfield Enhancement  
**BMAD Phase**: Phase 1.4 - Tool Management System Enhancement

## 🎯 **Executive Summary**

This PRD defines the implementation of a master tool pattern for BMAD WebMCP server, consolidating individual tools into master tools with operation switches. This enhancement reduces tool count by ~44% while improving scalability, maintainability, and Cursor IDE compliance.

## 📋 **Problem Statement**

### **Current Issues**
1. **Tool Count Explosion**: 94 individual tools exceed Cursor's 50-tool limit
2. **Poor Scalability**: Adding new operations requires new tools
3. **Expansion Pack Complexity**: Each pack adds multiple tools
4. **Maintenance Overhead**: Managing individual tools is complex
5. **Client Filtering Complexity**: Difficult to expose relevant tool subsets

### **Business Impact**
- **Cursor Compliance**: Cannot deploy to Cursor IDE due to tool limits
- **Development Velocity**: Slower feature development due to tool management overhead
- **User Experience**: Cluttered tool interfaces with too many similar tools
- **Expansion Pack Adoption**: Complex tool management discourages pack usage

## 🎯 **Solution Overview**

### **Master Tool Pattern**
Consolidate related operations into single master tools with operation switches:

**Before**: `task_add`, `task_get`, `task_list`, `task_update`, `task_delete` (5 tools)
**After**: `bmad_task` with operations: `add`, `get`, `list`, `update`, `delete` (1 tool)

### **Key Benefits**
1. **Tool Count Reduction**: 94 tools → 51 tools (44% reduction)
2. **Cursor Compliance**: All clients stay under tool limits
3. **Scalability**: Easy to add new operations to existing tools
4. **Expansion Pack Integration**: 1 master tool per expansion pack
5. **Better UX**: Logical grouping of related operations

## 🏗️ **Technical Architecture**

### **Master Tool Structure**
```json
{
  "name": "bmad_task",
  "description": "BMAD task management operations",
  "inputSchema": {
    "type": "object",
    "properties": {
      "operation": {
        "type": "string",
        "enum": ["add", "get", "list", "update", "delete", "search"]
      },
      "task_id": {"type": "string"},
      "task_data": {"type": "object"},
      "filters": {"type": "object"}
    },
    "required": ["operation"]
  }
}
```

### **Tool Categories**

#### **Core BMAD Master Tools (8 tools)**
1. `bmad_task` - Task management operations
2. `bmad_plan` - Planning operations  
3. `bmad_doc` - Document management operations
4. `bmad_workflow` - Workflow operations
5. `bmad_hil` - Human-in-the-Loop operations
6. `bmad_git` - Git integration operations
7. `bmad_orchestrator` - Orchestration operations
8. `bmad_expansion` - Expansion pack management

#### **Platform Tools (40 tools)**
- Code analysis: `code.*`, `lint_*`, `enh_*`
- Testing: `test_*`
- Memory: `memory_*`
- Research: `research`, `internet_search`, `doc_*`
- System: `sys_*`, `desktop.notify`, `sandbox.*`

#### **Expansion Pack Master Tools (3 tools)**
1. `bmad_game_dev` - Game development operations
2. `bmad_devops` - DevOps operations
3. `bmad_creative` - Creative writing operations

## 📊 **Impact Analysis**

### **Tool Count Reduction**

| Category | Current | Master Tools | Reduction |
|----------|---------|--------------|-----------|
| Task Management | 11 tools | 1 tool | 91% |
| Planning | 3 tools | 1 tool | 67% |
| BMAD Core | 37 tools | 8 tools | 78% |
| Expansion Packs | 3 tools | 3 tools | 0% |
| Platform Tools | 40 tools | 40 tools | 0% |
| **Total** | **94 tools** | **51 tools** | **44%** |

### **Client Tool Limit Compliance**

| Client Type | Current Tools | Master Tools | Compliance |
|-------------|---------------|--------------|------------|
| **Cursor IDE** | 46 tools | 12 tools | ✅ Under 50 |
| **Mobile App** | 12 tools | 8 tools | ✅ Under 30 |
| **Web Client** | 72 tools | 51 tools | ✅ Under 100 |
| **IDE Integration** | 60 tools | 45 tools | ✅ Under 75 |
| **CLI** | 27 tools | 10 tools | ✅ Under 40 |

### **Expansion Pack Integration**

| Expansion Pack | Current Tools | Master Tool | Operations |
|----------------|---------------|-------------|------------|
| **Game Dev** | 3 tools | `bmad_game_dev` | create_character, design_level, balance_gameplay |
| **DevOps** | 3 tools | `bmad_devops` | deploy, monitor, scale, backup |
| **Creative Writing** | 3 tools | `bmad_creative` | write_story, edit_content, review_grammar |

## 🔄 **Migration Strategy**

### **Phase 1: Core Master Tools**
1. Implement `bmad_task` master tool
2. Implement `bmad_plan` master tool
3. Implement `bmad_doc` master tool
4. Update tool registry and management system

### **Phase 2: Workflow Master Tools**
1. Implement `bmad_workflow` master tool
2. Implement `bmad_hil` master tool
3. Implement `bmad_git` master tool
4. Implement `bmad_orchestrator` master tool

### **Phase 3: Expansion Pack Master Tools**
1. Implement `bmad_expansion` master tool
2. Implement expansion pack master tools
3. Update client configurations
4. Test and validate

### **Phase 4: Cleanup and Optimization**
1. Remove individual tools
2. Update documentation
3. Performance optimization
4. Final testing and validation

## 🎯 **Success Criteria**

### **Functional Requirements**
- [ ] Tool count reduced from 94 to 51 tools
- [ ] All clients comply with tool limits
- [ ] Master tools support all required operations
- [ ] Expansion packs integrate seamlessly
- [ ] Backward compatibility maintained during migration

### **Performance Requirements**
- [ ] Tool execution time < 100ms for simple operations
- [ ] Tool execution time < 500ms for complex operations
- [ ] Memory usage reduced by 20%
- [ ] API response time improved by 15%

### **Quality Requirements**
- [ ] 100% test coverage for master tools
- [ ] All existing functionality preserved
- [ ] Documentation updated and comprehensive
- [ ] No breaking changes for existing clients

## 🚀 **Implementation Timeline**

### **Week 1-2: Core Master Tools**
- Implement `bmad_task`, `bmad_plan`, `bmad_doc`
- Update tool registry
- Basic testing

### **Week 3-4: Workflow Master Tools**
- Implement `bmad_workflow`, `bmad_hil`, `bmad_git`, `bmad_orchestrator`
- Update tool management system
- Integration testing

### **Week 5-6: Expansion Pack Master Tools**
- Implement expansion pack master tools
- Update client configurations
- End-to-end testing

### **Week 7-8: Cleanup and Optimization**
- Remove individual tools
- Performance optimization
- Final validation and deployment

## 📚 **Dependencies**

### **Technical Dependencies**
- Tool management system (Phase 1.3)
- WebMCP server (Phase 1.4)
- BMAD core agents (Phase 1.2)
- Expansion pack system (Phase 2.3)

### **Resource Dependencies**
- Development team: 2 developers
- Testing team: 1 QA engineer
- Documentation: 1 technical writer
- Timeline: 8 weeks

## 🔍 **Risks and Mitigation**

### **Technical Risks**
1. **Breaking Changes**: Risk of breaking existing clients
   - **Mitigation**: Maintain backward compatibility during migration
2. **Performance Impact**: Risk of slower tool execution
   - **Mitigation**: Implement caching and optimization
3. **Complexity**: Risk of over-engineering master tools
   - **Mitigation**: Keep master tools simple and focused

### **Business Risks**
1. **User Adoption**: Risk of user confusion with new tool structure
   - **Mitigation**: Comprehensive documentation and training
2. **Timeline**: Risk of delays in implementation
   - **Mitigation**: Phased approach with regular milestones

## 📈 **Success Metrics**

### **Quantitative Metrics**
- Tool count reduction: 44% (94 → 51 tools)
- Client compliance: 100% (all clients under limits)
- Performance improvement: 15% faster API responses
- Memory usage reduction: 20%

### **Qualitative Metrics**
- Developer satisfaction: Improved tool management
- User experience: Cleaner, more organized tool interface
- Maintainability: Easier to add new operations
- Scalability: Better expansion pack integration

---

**This PRD provides the foundation for implementing the master tool pattern, ensuring BMAD WebMCP server compliance with client tool limits while improving scalability and maintainability.**
