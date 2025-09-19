# CFlow Platform BMAD Implementation Project Brief

## Project Overview
**Project Name**: CFlow Platform BMAD Integration  
**Project Type**: Brownfield Full-Stack Development  
**Domain**: AI Platform Development  
**Complexity**: High  

## Project Description
Integration of BMAD-METHOD (MIT) as the authoritative planning/PM/story core of the Cerebral platform, replacing existing planning systems with BMAD's agentic planning and context-engineered development methodology.

## Key Documents
- **Main Implementation Plan**: `docs/BMAD_CORE_PLATFORM_INTEGRATION_PLAN.md`
- **Implementation Tasks**: `docs/BMAD_CORE_PLATFORM_INTEGRATION_TASKS.md`
- **Comprehensive Plan**: `docs/BMAD_COMPREHENSIVE_IMPLEMENTATION_PLAN.md`

## Technical Architecture
- **Backend**: Python FastAPI
- **Frontend**: React Native Web
- **Database**: Supabase (PostgreSQL)
- **Storage**: MinIO S3
- **AI/ML**: GPU-agnostic acceleration
- **Package Management**: UV (Python 3.11)

## Current Status
- ✅ BMAD Core Platform Integration Plan completed
- ✅ BMAD Technical Research Expansion Pack created
- ✅ Multi-user cluster compatibility fixes implemented
- ✅ HIL (Human-in-the-Loop) system implemented
- ✅ Cursor integration with BMAD agents completed
- ✅ BMAD-CFlow bridge agent created

## Implementation Goals
1. **Make BMAD-METHOD the authoritative planning core**
2. **Keep CAEF as orchestrator for multi-agent code/test/validation**
3. **Use hosted LLM APIs for agent reasoning**
4. **Replace BMAD's web UI with Cerebral Web/mobile/wearable UIs**
5. **Vendor BMAD into our stack with proper attribution**

## Key Features Implemented
- **28+ BMAD MCP Tools**: Database-integrated planning tools
- **Real HIL Integration**: Interactive sessions with workflow pausing
- **Multi-User Cluster**: Supabase integration for team collaboration
- **Expansion Packs**: Technical research, healthcare, business, legal, finance
- **Bridge Agent**: Connects standard BMAD with custom cflow platform

## Next Steps
1. **Run BMAD PRD Agent** on implementation plan
2. **Run BMAD Architecture Agent** on technical architecture
3. **Run BMAD Epic Agent** to create development epics
4. **Run BMAD Story Agent** to create user stories
5. **Execute development workflow** with CAEF multi-agent codegen

## Available BMAD Agents
- `@bmad-master`: Universal executor of all BMAD capabilities
- `@bmad-cflow-bridge`: Bridge between standard BMAD and custom cflow platform
- `@analyst`: Market research and project brief creation
- `@pm`: Product management and planning
- `@architect`: Technical architecture design
- `@po`: Product owner and story management
- `@sm`: Scrum master and process management
- `@dev`: Development and implementation
- `@qa`: Quality assurance and testing
- `@ux-expert`: User experience design

## Usage Instructions
1. **Activate BMAD Master**: Type `@bmad-master` in Cursor chat
2. **Reference Documents**: Point to implementation plan docs
3. **Execute Workflow**: Follow BMAD methodology for planning
4. **Use Bridge Agent**: Type `@bmad-cflow-bridge` for custom platform tools

This project represents a comprehensive integration of BMAD methodology with our custom cflow platform, providing both standard BMAD capabilities and enhanced multi-user cluster functionality.
