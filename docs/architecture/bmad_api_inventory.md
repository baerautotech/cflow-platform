# BMAD API Inventory

Document version: 1.0  
Date: 2025-09-17  
Source: BMAD-METHOD vendored in `vendor/bmad/`

## Overview

This document catalogs the BMAD agent entrypoints and interfaces for API facade design. BMAD agents operate as specialized personas with defined workflows, tasks, and templates.

## Agent Roles & Capabilities

### 1. BMad Orchestrator (`bmad-orchestrator`)
- **Role**: Master Orchestrator & BMad Method Expert
- **Purpose**: Workflow coordination, multi-agent tasks, role switching guidance
- **Key Commands**: `*help`, `*agent`, `*workflow-guidance`
- **API Endpoint**: `/bmad/orchestrator/coordinate`

### 2. Analyst (`analyst`)
- **Role**: Business Analyst & Requirements Expert
- **Purpose**: PRD creation, requirements gathering, stakeholder analysis
- **Key Commands**: `*analyze`, `*requirements`, `*stakeholder`
- **API Endpoint**: `/bmad/planning/prd`

### 3. Architect (`architect`)
- **Role**: Solution Architect & Technical Design Expert
- **Purpose**: Architecture design, technical specifications, system design
- **Key Commands**: `*design`, `*architecture`, `*specifications`
- **API Endpoint**: `/bmad/planning/architecture`

### 4. Product Manager (`pm`)
- **Role**: Product Management & Strategy Expert
- **Purpose**: Product strategy, roadmap planning, feature prioritization
- **Key Commands**: `*strategy`, `*roadmap`, `*prioritize`
- **API Endpoint**: `/bmad/planning/strategy`

### 5. Product Owner (`po`)
- **Role**: Product Owner & Story Management Expert
- **Purpose**: Story creation, backlog management, acceptance criteria
- **Key Commands**: `*story`, `*backlog`, `*acceptance`
- **API Endpoint**: `/bmad/planning/story`

### 6. Developer (`dev`)
- **Role**: Software Developer & Implementation Expert
- **Purpose**: Code implementation, technical solutions, development guidance
- **Key Commands**: `*implement`, `*code`, `*solution`
- **API Endpoint**: `/bmad/implementation/guidance`

### 7. QA Engineer (`qa`)
- **Role**: Quality Assurance & Testing Expert
- **Purpose**: Test planning, quality assurance, validation strategies
- **Key Commands**: `*test`, `*quality`, `*validation`
- **API Endpoint**: `/bmad/testing/strategy`

### 8. Scrum Master (`sm`)
- **Role**: Agile Coach & Process Expert
- **Purpose**: Process optimization, team coordination, agile practices
- **Key Commands**: `*process`, `*coordinate`, `*agile`
- **API Endpoint**: `/bmad/process/coordination`

### 9. UX Expert (`ux-expert`)
- **Role**: User Experience & Design Expert
- **Purpose**: User research, interface design, usability optimization
- **Key Commands**: `*ux`, `*design`, `*usability`
- **API Endpoint**: `/bmad/ux/design`

## Core Workflows

### Planning Workflow
1. **PRD Creation**: Analyst → Requirements → PRD Document
2. **Architecture Design**: Architect → Technical Specs → Architecture Document
3. **Story Generation**: Product Owner → User Stories → Story Document
4. **Gate Approval**: Orchestrator → Review → Planning Gate Token

### Implementation Workflow
1. **Development Guidance**: Developer → Technical Solutions → Implementation Plan
2. **Testing Strategy**: QA Engineer → Test Plans → Quality Assurance
3. **Process Coordination**: Scrum Master → Agile Practices → Process Optimization

## API Contract Design

### Input/Output Schema

#### PRD Creation
```json
{
  "input": {
    "project_context": "string",
    "stakeholders": ["string"],
    "business_objectives": "string",
    "constraints": "string"
  },
  "output": {
    "prd_document": "string",
    "requirements": ["string"],
    "acceptance_criteria": ["string"],
    "status": "draft|review|approved"
  }
}
```

#### Architecture Design
```json
{
  "input": {
    "prd_reference": "string",
    "technical_constraints": "string",
    "performance_requirements": "string",
    "integration_points": ["string"]
  },
  "output": {
    "architecture_document": "string",
    "technical_specifications": "string",
    "system_design": "string",
    "status": "draft|review|approved"
  }
}
```

#### Story Generation
```json
{
  "input": {
    "architecture_reference": "string",
    "user_personas": ["string"],
    "business_value": "string",
    "acceptance_criteria": ["string"]
  },
  "output": {
    "story_document": "string",
    "user_stories": ["string"],
    "acceptance_criteria": ["string"],
    "status": "draft|review|approved"
  }
}
```

## Integration Points

### Cerebral Platform Integration
- **Database**: `cerebral_documents` table for artifact storage
- **RAG/KG**: Index artifacts for context retrieval
- **CAEF**: Trigger code/test/validation after planning gate approval
- **WebMCP**: Expose BMAD agents as MCP tools

### Security & Compliance
- **Tenant Isolation**: All artifacts scoped to tenant_id
- **Audit Logging**: All agent interactions logged
- **Access Control**: Role-based permissions for agent access
- **Data Governance**: PII detection and redaction

## Next Steps

1. **API Facade Implementation**: Create HTTP endpoints for each agent
2. **Database Schema**: Design tables for artifact storage
3. **Integration Testing**: Test agent workflows end-to-end
4. **Documentation**: Create API documentation and examples
