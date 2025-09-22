# BMAD Wrapper Pattern Implementation Guidelines

## Overview
This document provides specific implementation guidelines for applying the Phase 2 wrapper pattern to all subsequent BMAD phases.

## Implementation Template

### 1. Core Wrapper Class
```python
class BMADComponentWrapper:
    """Wrapper for BMAD-Method component with Cerebral extensions"""
    
    def __init__(self, bmad_root: Path = None):
        self.bmad_root = bmad_root or Path('vendor/bmad')
        self.component_path = self.bmad_root / 'bmad-core' / 'components'
        self.discovered_components: Dict[str, Any] = {}
        self.cerebral_extensions: Dict[str, Any] = {}
    
    async def discover_bmad_components(self) -> Dict[str, Any]:
        """Discover BMAD-Method components from vendor/bmad"""
        # Implementation follows bmad_persona_wrapper.py pattern
        pass
    
    async def wrap_component(self, component_id: str) -> Dict[str, Any]:
        """Wrap BMAD-Method component with Cerebral extensions"""
        # Implementation follows established wrapper pattern
        pass
```

### 2. MCP Handler Integration
```python
class BMADComponentHandlers:
    """MCP handlers for BMAD component wrapper"""
    
    def __init__(self):
        self.wrapper = BMADComponentWrapper()
    
    async def bmad_component_discover(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Discover BMAD components via MCP"""
        # Implementation follows bmad_persona_handlers.py pattern
        pass
```

### 3. Tool Registry Integration
```python
# In tool_registry.py
tools += [
    tool("bmad_component_discover", "Discover BMAD components"),
    tool("bmad_component_wrap", "Wrap BMAD component"),
    # ... other component tools
]
```

### 4. Direct Client Routing
```python
# In direct_client.py
elif tool_name == "bmad_component_discover":
    from ..handlers.bmad_component_handlers import bmad_component_handlers
    return await bmad_component_handlers.bmad_component_discover(kwargs or {})
```

## Phase-Specific Implementation

### Phase 3: Tool Consolidation
- Wrap vendor/bmad tools
- Consolidate existing tool patterns
- Maintain BMAD-Method compatibility

### Phase 4: Testing & Validation
- Wrap vendor/bmad testing components
- Extend with Cerebral testing features
- Maintain BMAD-Method test compatibility

### Phase 5: Advanced Features
- Wrap vendor/bmad expansion packs
- Extend with Cerebral features
- Maintain BMAD-Method compatibility

### Phase 6: Final Cleanup
- Validate all wrappers
- Ensure BMAD-Method compatibility
- Complete Cerebral integration

## Testing Requirements

### Unit Tests
- Test wrapper functionality
- Test BMAD-Method integration
- Test Cerebral extensions
- Test MCP integration

### Integration Tests
- Test end-to-end wrapper flow
- Test BMAD-Method compatibility
- Test MCP tool execution
- Test context preservation

## Documentation Requirements

### Architecture Documentation
- Document wrapper pattern implementation
- Document BMAD-Method integration
- Document Cerebral extensions
- Document MCP integration

### Implementation Documentation
- Document component discovery
- Document wrapper creation
- Document extension mechanisms
- Document testing approach

## Quality Assurance

### Code Review Checklist
- [ ] Follows wrapper pattern
- [ ] Integrates with vendor/bmad
- [ ] Provides MCP interfaces
- [ ] Maintains compatibility
- [ ] Includes Cerebral extensions
- [ ] Has comprehensive tests
- [ ] Has proper documentation

### Validation Checklist
- [ ] All components wrapped (not rebuilt)
- [ ] BMAD-Method compatibility maintained
- [ ] MCP integration working
- [ ] Context preservation working
- [ ] Session management working
- [ ] Dynamic discovery working
