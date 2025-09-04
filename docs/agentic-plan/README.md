## CerebraFlow Agentic Plan (ProjectBuildGuide-aligned)

### Overview
This folder organizes the CerebraFlow agent plan per `docs/ProjectBuildGuide.md` and consolidates all AEMI/VEG tasks into a single, sequential tracker.

### Index
- Base Project Description
  - PRD: `./PRD.md`
  - Technical Stack: `./TechnicalStack.md`
  - High‑Level Architecture: `./Architecture.md`
  - Database Schema: `./DatabaseSchema.md`
  - Code Style: `./CodeStyle.md`
- Process Outline (Agentic Workflow)
  - Agentic Workflow: `./AgenticWorkflow.md`
  - Prompt Definitions: `./Prompts.md`
  - Tool Definitions: `./Tools.md`
  - Context Management: `./ContextManagement.md`
  - Feedback & Reflection: `./FeedbackAndReflection.md`
  - Logging & Observability: `./LoggingAndObservability.md`
  - Test Plan: `./TestPlan.md`
- Tasking & Validation
  - AEMI + VEG Task Tracker: `./TaskTracker.md`
  - Validation Gates: `./ValidationGates.md`
- User-Facing Docs
  - Examples: `./Examples.md`
  - Governance: `./Governance.md`
- Domain‑specific Notes
  - Apple Silicon Accelerator: `./AppleSiliconAccelerator.md`
  - Memory & Supabase Sync: `./MemoryAndSync.md`
  - Next Steps (Sync, Vectors, Memory): `./NextSteps.md`

### Notes
- This structure supersedes the legacy `docs/plans/Fowler-aligned_implementation_plan.md`. That file now points here.

### Sources
- Primary inspiration and capability model: [Building your own CLI Coding Agent with Pydantic-AI](https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai)
- Runtime environment: Cerebral Server private cluster (documented in knowledgeRAG/GRAPH); AWS not required.

