# BMAD Rollback Plan

Document version: 1.0  
Date: 2025-01-09  
Purpose: Emergency rollback procedures to restore CAEF functionality if BMAD integration fails

## Overview

This document provides step-by-step procedures to rollback the BMAD integration and restore the original CAEF (Cursor Agent Execution Framework) functionality in case of critical failures.

## Rollback Triggers

Rollback should be initiated if:

1. **Critical System Failure**: BMAD integration causes system-wide failures
2. **Data Loss**: BMAD operations result in data corruption or loss
3. **Performance Degradation**: BMAD causes significant performance issues
4. **Security Vulnerabilities**: BMAD introduces security risks
5. **User Impact**: BMAD failures affect user workflows

## Pre-Rollback Checklist

Before initiating rollback:

- [ ] Document the specific failure or issue
- [ ] Backup current state and any BMAD-generated data
- [ ] Notify stakeholders of rollback decision
- [ ] Prepare rollback timeline and communication plan
- [ ] Ensure rollback team is available

## Rollback Procedures

### Phase 1: Immediate Stabilization (0-30 minutes)

#### 1.1 Stop BMAD Operations
```bash
# Kill any running BMAD processes
pkill -f "bmad"
pkill -f "bmad_workflow"

# Check for running processes
ps aux | grep -i bmad
```

#### 1.2 Disable BMAD Tools
```bash
# Comment out BMAD tools in tool registry
cd /path/to/cflow-platform
cp cflow_platform/core/tool_registry.py cflow_platform/core/tool_registry.py.backup

# Edit tool_registry.py to comment out BMAD tools
sed -i 's/^        # BMAD/# BMAD/g' cflow_platform/core/tool_registry.py
```

#### 1.3 Restore CAEF Components
```bash
# Restore CAEF orchestrator
git checkout HEAD~1 -- cflow_platform/core/orchestrator.py

# Restore CAEF agent loop
git checkout HEAD~1 -- cflow_platform/core/agent_loop.py

# Restore CAEF agents directory
git checkout HEAD~1 -- cflow_platform/core/agents/
```

### Phase 2: System Restoration (30-60 minutes)

#### 2.1 Restore Test Files
```bash
# Restore test files that import from agent_loop
git checkout HEAD~1 -- cflow_platform/tests/test_agent_loop_budgets_and_lint.py
git checkout HEAD~1 -- cflow_platform/tests/test_agent_loop_lint_gate.py
git checkout HEAD~1 -- cflow_platform/tests/test_e2e_seeded_fix.py
```

#### 2.2 Update Import Statements
```bash
# Update imports in test files
cd cflow_platform/tests/

# Restore agent_loop imports
sed -i 's/from cflow_platform.core.linting_handlers import run_lint_and_hooks/from cflow_platform.core.agent_loop import run_lint_and_hooks/g' test_agent_loop_*.py
```

#### 2.3 Remove BMAD Components
```bash
# Remove BMAD-specific files
rm -f cflow_platform/core/bmad_workflow_engine.py
rm -f cflow_platform/core/bmad_agents.py
rm -f cflow_platform/core/bmad_hil_integration.py
rm -f cflow_platform/core/bmad_git_workflow.py
rm -f cflow_platform/handlers/bmad_handlers.py
rm -f cflow_platform/tests/test_bmad_integration.py
```

### Phase 3: Database Cleanup (60-90 minutes)

#### 3.1 Backup BMAD Data
```sql
-- Create backup tables for BMAD data
CREATE TABLE cerebral_documents_bmad_backup AS 
SELECT * FROM cerebral_documents WHERE kind IN ('PRD', 'ARCH', 'STORY');

CREATE TABLE bmad_hil_sessions_backup AS 
SELECT * FROM bmad_hil_sessions;

CREATE TABLE bmad_commit_tracking_backup AS 
SELECT * FROM bmad_commit_tracking;

CREATE TABLE bmad_validation_results_backup AS 
SELECT * FROM bmad_validation_results;
```

#### 3.2 Clean BMAD Tables (Optional)
```sql
-- Only if BMAD data is corrupted
-- WARNING: This will permanently delete BMAD data
-- TRUNCATE TABLE cerebral_documents WHERE kind IN ('PRD', 'ARCH', 'STORY');
-- TRUNCATE TABLE bmad_hil_sessions;
-- TRUNCATE TABLE bmad_commit_tracking;
-- TRUNCATE TABLE bmad_validation_results;
```

### Phase 4: Verification and Testing (90-120 minutes)

#### 4.1 Test CAEF Functionality
```bash
# Test CAEF orchestrator
cd /path/to/cflow-platform
python3 -c "
from cflow_platform.core.orchestrator import run_iteration
print('CAEF orchestrator restored successfully')
"

# Test agent loop
python3 -c "
from cflow_platform.core.agent_loop import loop
print('CAEF agent loop restored successfully')
"
```

#### 4.2 Run Test Suite
```bash
# Run CAEF tests
python3 -m pytest cflow_platform/tests/test_agent_loop_*.py -v

# Run integration tests
python3 -m pytest cflow_platform/tests/test_e2e_seeded_fix.py -v
```

#### 4.3 Verify System Health
```bash
# Check system status
python3 -c "
from cflow_platform.core.direct_client import execute_mcp_tool
import asyncio

async def test():
    result = await execute_mcp_tool('sys_test')
    print(f'System test: {result}')

asyncio.run(test())
"
```

## Post-Rollback Actions

### Immediate Actions (0-24 hours)

1. **Monitor System**: Watch for any remaining issues
2. **User Communication**: Notify users of rollback completion
3. **Documentation**: Update system documentation
4. **Incident Report**: Document the failure and rollback process

### Short-term Actions (1-7 days)

1. **Root Cause Analysis**: Investigate what caused the BMAD failure
2. **Lessons Learned**: Document improvements for future integrations
3. **Recovery Planning**: Plan for future BMAD integration attempts
4. **Team Training**: Ensure team understands rollback procedures

### Long-term Actions (1-4 weeks)

1. **Process Improvement**: Update integration procedures
2. **Testing Enhancement**: Improve testing before deployment
3. **Monitoring**: Implement better monitoring for future integrations
4. **Documentation**: Update all relevant documentation

## Emergency Contacts

- **System Administrator**: [Contact Info]
- **Database Administrator**: [Contact Info]
- **Development Team Lead**: [Contact Info]
- **Product Manager**: [Contact Info]

## Rollback Checklist

### Pre-Rollback
- [ ] Document failure/issue
- [ ] Backup current state
- [ ] Notify stakeholders
- [ ] Prepare rollback team

### Phase 1: Stabilization
- [ ] Stop BMAD operations
- [ ] Disable BMAD tools
- [ ] Restore CAEF components

### Phase 2: Restoration
- [ ] Restore test files
- [ ] Update import statements
- [ ] Remove BMAD components

### Phase 3: Database Cleanup
- [ ] Backup BMAD data
- [ ] Clean BMAD tables (if needed)

### Phase 4: Verification
- [ ] Test CAEF functionality
- [ ] Run test suite
- [ ] Verify system health

### Post-Rollback
- [ ] Monitor system
- [ ] Communicate with users
- [ ] Document incident
- [ ] Plan recovery

## Recovery Planning

After successful rollback, plan for future BMAD integration:

1. **Identify Root Cause**: What specifically failed?
2. **Fix Issues**: Address the specific problems
3. **Improve Testing**: Add more comprehensive tests
4. **Gradual Rollout**: Consider phased deployment
5. **Monitoring**: Implement better monitoring

## Prevention Measures

To prevent future rollbacks:

1. **Comprehensive Testing**: Test all components thoroughly
2. **Staged Deployment**: Deploy in stages with rollback points
3. **Monitoring**: Implement real-time monitoring
4. **Documentation**: Keep all documentation up-to-date
5. **Team Training**: Ensure team understands all components

## References

- [CAEF Documentation](docs/architecture/caef_architecture.md)
- [BMAD Integration Plan](docs/plans/BMAD_CORE_PLATFORM_INTEGRATION_PLAN.md)
- [System Architecture](docs/architecture/system_architecture.md)
- [Emergency Procedures](docs/emergency_procedures.md)

