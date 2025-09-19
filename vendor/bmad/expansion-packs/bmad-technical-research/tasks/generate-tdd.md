# Generate TDD Task

## Task Overview
Generate a Test-Driven Development (TDD) document using the standardized TDD template for consistent, actionable test-driven development documentation.

## Prerequisites
- User has a feature or functionality to develop
- User understands TDD methodology
- TDD template is available

## Steps

### Step 1: Feature Information Collection
**elicit: true**
**format: form**

Please provide the following information about the feature to be developed:

**Required Fields:**
- **Feature Name**: {{feature_name}}
- **Feature Description**: {{feature_description}}
- **Business Value**: {{business_value}}
- **Acceptance Criteria**: {{acceptance_criteria}}

**User Input Required**: Fill in all required fields with detailed information.

### Step 2: Test Scenario Definition
**elicit: true**
**format: structured_input**

Define the test scenarios for this feature:

**Happy Path Tests:**
{{happy_path_tests}}

**Edge Cases:**
{{edge_case_tests}}

**Error Handling Tests:**
{{error_handling_tests}}

**Integration Tests:**
{{integration_tests}}

**User Input Required**: Provide detailed test scenarios for each category.

### Step 3: Implementation Plan
**elicit: true**
**format: structured_input**

Define the implementation plan:

**Phase 1: Test Setup**
{{test_setup_steps}}

**Phase 2: Implementation**
{{implementation_steps}}

**Phase 3: Refactoring**
{{refactoring_steps}}

**Phase 4: Integration**
{{integration_steps}}

**User Input Required**: Provide detailed steps for each phase.

### Step 4: Technical Requirements
**elicit: true**
**format: structured_input**

Define technical requirements:

**Dependencies:**
{{dependencies}}

**Technical Constraints:**
{{technical_constraints}}

**Performance Requirements:**
{{performance_requirements}}

**Security Considerations:**
{{security_considerations}}

**User Input Required**: Provide detailed technical requirements.

### Step 5: Deliverables Definition
**elicit: true**
**format: structured_input**

Define deliverables:

**Code Deliverables:**
{{code_deliverables}}

**Test Deliverables:**
{{test_deliverables}}

**Documentation Deliverables:**
{{documentation_deliverables}}

**Deployment Requirements:**
{{deployment_requirements}}

**User Input Required**: Provide detailed deliverables for each category.

### Step 6: TDD Document Generation
**elicit: false**

Generate the TDD document:

1. **Load TDD Template**: Load tdd-tmpl.yaml
2. **Validate Data**: Validate all provided information
3. **Generate Content**: Create TDD document using template
4. **Format Output**: Format in requested format (Markdown, YAML, JSON)
5. **Save Document**: Save to appropriate location

### Step 7: Quality Validation
**elicit: false**

Validate the generated TDD document:

1. **Template Compliance**: Verify document follows TDD template structure
2. **Content Completeness**: Check all required sections are present
3. **Test Coverage**: Ensure comprehensive test scenarios
4. **Implementation Clarity**: Verify implementation steps are clear
5. **Deliverable Specificity**: Check deliverables are specific and measurable

### Step 8: Downstream Processing Options
**elicit: true**
**format: numbered_list**

The TDD document has been generated successfully. Would you like to trigger downstream processing?

1. **Create Development Tasks** - Generate tasks from TDD analysis
2. **Create User Stories** - Generate user stories from TDD
3. **Create Epics** - Generate epics from TDD
4. **Create Test Cases** - Generate specific test cases
5. **Create Implementation Plan** - Generate detailed implementation plan
6. **Skip Downstream Processing** - Just save the TDD document
7. **Custom Processing** - Specify custom downstream processing

**User Input Required**: Select a number (1-7) or specify custom processing.

### Step 9: Task Creation (if selected)
**elicit: false**

If task creation was selected:

1. **Load Task Creation Template**: Load task-creation-tmpl.yaml
2. **Map TDD Fields**: Map TDD fields to task fields
3. **Generate Tasks**: Create tasks for each implementation phase
4. **Validate Tasks**: Ensure tasks are properly formatted
5. **Save Tasks**: Save tasks to task management system

### Step 10: Story Creation (if selected)
**elicit: false**

If story creation was selected:

1. **Load Story Generation Template**: Load story-generation-tmpl.yaml
2. **Map TDD Fields**: Map TDD fields to story fields
3. **Generate Stories**: Create user stories from TDD
4. **Validate Stories**: Ensure stories follow proper format
5. **Save Stories**: Save stories to story management system

### Step 11: Epic Creation (if selected)
**elicit: false**

If epic creation was selected:

1. **Load Epic Planning Template**: Load epic-planning-tmpl.yaml
2. **Map TDD Fields**: Map TDD fields to epic fields
3. **Generate Epics**: Create epics from TDD
4. **Validate Epics**: Ensure epics are properly structured
5. **Save Epics**: Save epics to epic management system

### Step 12: Completion
**elicit: false**

TDD generation process completed:

- **TDD Document Created**: {{tdd_document_path}}
- **Tasks Created**: {{task_count}} tasks
- **Stories Created**: {{story_count}} stories
- **Epics Created**: {{epic_count}} epics
- **Test Cases Created**: {{test_case_count}} test cases
- **Processing Time**: {{processing_time}}

## Output Format

The task will output:
- **TDD Document**: Generated TDD document in requested format
- **Tasks**: Generated development tasks (if requested)
- **Stories**: Generated user stories (if requested)
- **Epics**: Generated epics (if requested)
- **Test Cases**: Generated test cases (if requested)
- **Metadata**: Processing metadata and statistics

## Error Handling

- **Template Not Found**: Provide list of available TDD templates
- **Validation Errors**: Show specific validation errors and allow correction
- **Generation Errors**: Provide error details and retry options
- **Save Errors**: Handle file system and database errors gracefully

## Success Criteria

- TDD document is generated using correct template
- All required fields are populated with detailed information
- Test scenarios are comprehensive and actionable
- Implementation plan is clear and step-by-step
- Technical requirements are specific and measurable
- Deliverables are clearly defined
- Document passes quality validation
- Downstream processing (if requested) completes successfully
- Document is saved to appropriate location

## Template Integration

This task integrates with:
- **TDD Template**: tdd-tmpl.yaml for document structure
- **Task Creation Template**: task-creation-tmpl.yaml for task generation
- **Story Generation Template**: story-generation-tmpl.yaml for story creation
- **Epic Planning Template**: epic-planning-tmpl.yaml for epic generation
