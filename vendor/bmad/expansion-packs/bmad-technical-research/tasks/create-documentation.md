# Create Documentation Task

## Task Overview
Create technical documentation using YAML templates for standardized, customizable document generation.

## Prerequisites
- User has selected a document type
- User has provided necessary information for the document
- Template system is available

## Steps

### Step 1: Document Type Selection
**elicit: true**
**format: numbered_list**

Please select the type of documentation you want to create:

1. **TDD (Test-Driven Development)** - Test-driven development document
2. **API Documentation** - REST API documentation
3. **User Guide** - End-user documentation
4. **Technical Specification** - Technical requirements and design
5. **README** - Project overview and setup instructions
6. **Architecture Document** - System architecture documentation
7. **Deployment Guide** - Deployment and infrastructure documentation
8. **Troubleshooting Guide** - Common issues and solutions
9. **Changelog** - Version history and changes
10. **Custom Template** - Use a custom template

**User Input Required**: Select a number (1-10) or specify custom template name.

### Step 2: Template Selection
**elicit: true**
**format: numbered_list**

Based on your selection, choose the specific template:

{{#if document_type == "TDD"}}
1. **Standard TDD Template** - Complete TDD document with all sections
2. **Minimal TDD Template** - Simplified TDD document
3. **API TDD Template** - TDD focused on API development
4. **Frontend TDD Template** - TDD focused on frontend development
{{/if}}

{{#if document_type == "API_DOCS"}}
1. **REST API Template** - Standard REST API documentation
2. **GraphQL API Template** - GraphQL API documentation
3. **WebSocket API Template** - WebSocket API documentation
4. **Microservice API Template** - Microservice API documentation
{{/if}}

{{#if document_type == "USER_GUIDE"}}
1. **Getting Started Guide** - Basic user onboarding
2. **Feature Guide** - Specific feature documentation
3. **Administrator Guide** - Admin user documentation
4. **Developer Guide** - Developer-focused documentation
{{/if}}

**User Input Required**: Select a number or specify custom template.

### Step 3: Document Information Collection
**elicit: true**
**format: form**

Please provide the following information for your document:

**Required Fields:**
- **Document Title**: {{document_title}}
- **Project Name**: {{project_name}}
- **Author**: {{author}}
- **Version**: {{version}}
- **Description**: {{description}}

**Optional Fields:**
- **Tags**: {{tags}}
- **Related Documents**: {{related_documents}}
- **Stakeholders**: {{stakeholders}}

**User Input Required**: Fill in all required fields and any optional fields.

### Step 4: Template-Specific Information
**elicit: true**
**format: dynamic_form**

Based on the selected template, collect template-specific information:

{{#if template_id == "tdd-tmpl"}}
**TDD Template Fields:**
- **Feature Name**: {{feature_name}}
- **Feature Description**: {{feature_description}}
- **Business Value**: {{business_value}}
- **Acceptance Criteria**: {{acceptance_criteria}}
- **Test Scenarios**: {{test_scenarios}}
- **Implementation Plan**: {{implementation_plan}}
- **Technical Requirements**: {{technical_requirements}}
- **Deliverables**: {{deliverables}}
{{/if}}

{{#if template_id == "api-docs-tmpl"}}
**API Documentation Template Fields:**
- **API Name**: {{api_name}}
- **API Version**: {{api_version}}
- **API Description**: {{api_description}}
- **Base URL**: {{base_url}}
- **Authentication Method**: {{authentication_method}}
- **Endpoints**: {{endpoints}}
- **Data Models**: {{data_models}}
- **Error Handling**: {{error_handling}}
- **Examples**: {{examples}}
{{/if}}

**User Input Required**: Fill in all template-specific fields.

### Step 5: Document Generation
**elicit: false**

Generate the document using the selected template and provided information:

1. **Load Template**: Load the selected YAML template
2. **Validate Data**: Validate all provided information against template requirements
3. **Generate Content**: Generate document content using template structure
4. **Format Output**: Format output in requested format (Markdown, YAML, JSON)
5. **Save Document**: Save document to appropriate location

### Step 6: Quality Check
**elicit: false**

Perform quality checks on the generated document:

1. **Template Compliance**: Verify document follows template structure
2. **Content Validation**: Check all required fields are present
3. **Format Validation**: Ensure output format is correct
4. **Link Validation**: Verify all links and references are valid

### Step 7: Downstream Processing
**elicit: true**
**format: numbered_list**

The document has been created successfully. Would you like to trigger downstream processing?

1. **Create Tasks** - Generate tasks from document analysis
2. **Create Stories** - Generate user stories from document
3. **Create Epics** - Generate epics from document
4. **Skip Downstream Processing** - Just save the document
5. **Custom Processing** - Specify custom downstream processing

**User Input Required**: Select a number (1-5) or specify custom processing.

### Step 8: Task Creation (if selected)
**elicit: false**

If task creation was selected:

1. **Load Task Creation Template**: Load task-creation-tmpl.yaml
2. **Map Document Fields**: Map document fields to task fields
3. **Generate Tasks**: Create tasks based on document analysis
4. **Validate Tasks**: Ensure tasks are properly formatted
5. **Save Tasks**: Save tasks to task management system

### Step 9: Completion
**elicit: false**

Document creation process completed:

- **Document Created**: {{document_path}}
- **Tasks Created**: {{task_count}} tasks
- **Stories Created**: {{story_count}} stories
- **Epics Created**: {{epic_count}} epics
- **Processing Time**: {{processing_time}}

## Output Format

The task will output:
- **Document**: Generated document in requested format
- **Tasks**: Generated tasks (if requested)
- **Stories**: Generated stories (if requested)
- **Epics**: Generated epics (if requested)
- **Metadata**: Processing metadata and statistics

## Error Handling

- **Template Not Found**: Provide list of available templates
- **Validation Errors**: Show specific validation errors and allow correction
- **Generation Errors**: Provide error details and retry options
- **Save Errors**: Handle file system and database errors gracefully

## Success Criteria

- Document is generated using correct template
- All required fields are populated
- Document passes quality checks
- Downstream processing (if requested) completes successfully
- Document is saved to appropriate location
