## Project Build Guide: Agentic Automated Code Generation

### Overview
To create an effective plan for agentic automated code generation, organize your documentation into a few clear sections and use consistent, skimmable formatting. The following structure improves clarity and collaboration.

## I. Base Project Description
A well-structured project description defines the problem, goals, and high-level scope.

- **Project Requirements Document (PRD)**: Outlines functional and non-functional requirements, including features, user stories, performance expectations, security considerations, and constraints.
- **Technical Stack Specification**: Specifies programming languages, frameworks, libraries, tools, and platforms to provide the technical context for generation.
- **High‑Level Architecture**: Illustrates modules, components, and interactions using C4 or UML diagrams for clarity.
- **Database Schema Design (if applicable)**: Presents tables, relationships, and data types with clear ERDs or schema diagrams.
- **Code Style Guidelines**: Establishes consistency and readability standards for generated and human-written code.

## II. Process Outline (Agentic Workflow)
Focus this documentation on how agents interact and execute the code generation process.

- **Agentic Workflow Definition**: Define the step sequence and decision points (e.g., YAML, LangGraph, or LangChain) to orchestrate multi-step workflows predictably.
- **Prompt Definitions and Templates**: Provide precise, context-rich prompts for each agent to ensure consistent, accurate outputs.
- **Tool Definitions**: Describe tools agents can use (web search, code analysis, external system calls), including input/output formats and concrete examples.
- **Context Management Strategy**: Explain how agents manage and utilize context (e.g., CLAUDE.md and shared artifacts) across iterations.
- **Feedback Loops and Reflection**: Detail how testing results, error reports, and human feedback refine subsequent generations.
- **Logging and Observability**: Specify logs for interactions, tool usage, outputs, errors, and timing to support debugging and optimization.
- **Test Case Design and Execution Plan**: Describe how tests are designed and executed (potentially by agents) to validate generated code.

## III. Recommended Formats

- **Markdown**: Ideal for developer-facing docs (CLAUDE.md, style guides, process outlines) due to simplicity, readability, and VCS compatibility.
- **YAML/JSON**: Suitable for declarative workflows, configuration, and structured data easily parsed by agents and tools.
- **Diagrams (UML, C4 models)**: Essential for high-level architecture, application flow, and agent interactions. Create with tools like draw.io or Miro and embed in docs.

Building an effective agentic code generation plan relies on meticulously documented requirements, clear workflow descriptions, and precise instructions for each agent. Following this structure creates a robust, adaptable framework for automated code generation.