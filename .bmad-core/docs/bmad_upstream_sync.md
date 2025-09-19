# BMAD Upstream Sync Policy

Document version: 1.0  
Date: 2025-09-17  
Purpose: Establish monthly upstream sync procedure and contract tests for BMAD planning/story APIs

## Overview

This document defines the procedure for maintaining synchronization with the upstream BMAD-METHOD repository while ensuring API compatibility and preventing breaking changes.

## Sync Schedule

- **Frequency**: Monthly (first Monday of each month)
- **Responsible**: Platform Architecture Team
- **Notification**: 48 hours advance notice to all teams

## Sync Procedure

### 1. Pre-Sync Preparation
- [ ] Review upstream CHANGELOG.md for breaking changes
- [ ] Check GitHub issues/PRs for API modifications
- [ ] Run existing contract tests to establish baseline
- [ ] Create sync branch: `sync/bmad-upstream-YYYY-MM`

### 2. Upstream Integration
```bash
# Add upstream remote (if not exists)
git remote add bmad-upstream https://github.com/bmadcode/BMAD-METHOD.git

# Fetch latest changes
git fetch bmad-upstream main

# Create sync branch
git checkout -b sync/bmad-upstream-2025-09

# Merge upstream changes
git merge bmad-upstream/main --no-ff -m "sync: integrate BMAD upstream changes"
```

### 3. Contract Testing
- [ ] Run agent interface tests
- [ ] Validate API schema compatibility
- [ ] Test workflow execution
- [ ] Verify template compatibility

### 4. Integration Testing
- [ ] Test PRD creation workflow
- [ ] Test Architecture design workflow
- [ ] Test Story generation workflow
- [ ] Test Orchestrator coordination

### 5. Documentation Updates
- [ ] Update API inventory if interfaces changed
- [ ] Update integration documentation
- [ ] Update NOTICE file if needed
- [ ] Update vendor README

## Contract Tests

### Agent Interface Tests
```python
def test_analyst_prd_creation():
    """Test Analyst agent PRD creation interface"""
    # Test input/output schema compatibility
    # Test workflow execution
    # Test error handling

def test_architect_design_interface():
    """Test Architect agent design interface"""
    # Test architecture document generation
    # Test technical specification output
    # Test integration with PRD input

def test_po_story_generation():
    """Test Product Owner story generation"""
    # Test story document creation
    # Test user story format
    # Test acceptance criteria generation
```

### API Schema Tests
```python
def test_prd_api_schema():
    """Test PRD API input/output schema"""
    # Validate JSON schema
    # Test required fields
    # Test optional fields
    # Test data types

def test_architecture_api_schema():
    """Test Architecture API schema"""
    # Validate schema compatibility
    # Test nested object structures
    # Test array field validation

def test_story_api_schema():
    """Test Story API schema"""
    # Validate story format
    # Test user story structure
    # Test acceptance criteria format
```

### Workflow Integration Tests
```python
def test_planning_workflow():
    """Test complete planning workflow"""
    # PRD creation → Architecture design → Story generation
    # Test data flow between agents
    # Test artifact persistence
    # Test gate approval process

def test_orchestrator_coordination():
    """Test Orchestrator agent coordination"""
    # Test multi-agent coordination
    # Test workflow guidance
    # Test role switching
```

## Breaking Change Handling

### Detection
- Automated schema validation
- Contract test failures
- Workflow execution errors
- Documentation inconsistencies

### Response Process
1. **Immediate**: Revert to previous version
2. **Assessment**: Analyze impact and required changes
3. **Planning**: Create migration plan
4. **Implementation**: Update Cerebral platform code
5. **Testing**: Comprehensive integration testing
6. **Deployment**: Staged rollout with monitoring

### Migration Strategies
- **Schema Changes**: Version API endpoints
- **Workflow Changes**: Update integration code
- **Template Changes**: Update template mappings
- **Agent Changes**: Update agent configurations

## Monitoring & Alerts

### Automated Monitoring
- Contract test execution on every PR
- Schema validation in CI/CD pipeline
- Workflow execution monitoring
- API response time monitoring

### Alert Conditions
- Contract test failures
- Schema validation errors
- Workflow execution failures
- Performance degradation

## Rollback Procedure

### Emergency Rollback
```bash
# Revert to previous BMAD version
git checkout previous-bmad-version
git checkout -b hotfix/bmad-rollback-YYYY-MM-DD

# Update vendor directory
rm -rf vendor/bmad
git checkout previous-bmad-version -- vendor/bmad

# Run tests
python -m pytest tests/contract/bmad/
python -m pytest tests/integration/bmad/

# Deploy rollback
git commit -m "hotfix: rollback BMAD to previous version"
```

### Planned Rollback
- 24-hour advance notice
- Staged rollout with monitoring
- Automated rollback triggers
- Post-incident review

## Success Criteria

- [ ] All contract tests pass
- [ ] No breaking changes detected
- [ ] Integration tests successful
- [ ] Documentation updated
- [ ] Performance maintained
- [ ] Security validation passed

## Responsibilities

### Platform Architecture Team
- Execute monthly sync procedure
- Maintain contract tests
- Handle breaking changes
- Update documentation

### Development Teams
- Review sync notifications
- Test integration points
- Report compatibility issues
- Update dependent code

### QA Team
- Validate contract tests
- Execute integration testing
- Monitor performance impact
- Verify security compliance

## References

- [BMAD-METHOD Repository](https://github.com/bmadcode/BMAD-METHOD)
- [API Inventory Document](../architecture/bmad_api_inventory.md)
- [Integration Plan](../../plans/BMAD_CORE_PLATFORM_INTEGRATION_PLAN.md)
