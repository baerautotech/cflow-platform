"""
Enhanced YAML-based Task Template System for BMAD Integration

This module provides YAML-based task templates that integrate with BMAD
documentation generation and codegen agent needs.
"""

import yaml
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class YAMLTaskTemplate:
    """
    YAML-based task template system for BMAD integration.
    
    Templates define structured tasks that can be instantiated
    with specific parameters for BMAD workflows.
    """
    
    def __init__(self, template_path: str):
        """Initialize with YAML template file."""
        self.template_path = Path(template_path)
        self.template_data = self._load_template()
    
    def _load_template(self) -> Dict[str, Any]:
        """Load YAML template file."""
        try:
            with open(self.template_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load template {self.template_path}: {e}")
            return {}
    
    def instantiate_task(self, 
                        project_id: str,
                        tenant_id: str,
                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Instantiate a task from this template.
        
        Args:
            project_id: Project identifier
            tenant_id: Tenant identifier
            parameters: Template parameters for substitution
            
        Returns:
            Task data ready for Supabase insertion
        """
        template = self.template_data.get('template', {})
        workflow = self.template_data.get('workflow', {})
        sections = self.template_data.get('sections', [])
        
        # Generate task ID
        task_id = f"T{int(datetime.utcnow().timestamp()*1000)}"
        
        # Build task metadata
        metadata = {
            'template_id': template.get('id'),
            'template_version': template.get('version'),
            'project_id': project_id,
            'tenant_id': tenant_id,
            'bmad_workflow_type': template.get('bmad_type', 'GENERIC'),
            'workflow_mode': workflow.get('mode', 'interactive'),
            'sections_count': len(sections),
            'parameters': parameters,
            'created_by': 'bmad_api'
        }
        
        # Generate title and description
        title = self._substitute_variables(template.get('title', 'BMAD Task'), parameters)
        description = self._substitute_variables(template.get('description', ''), parameters)
        
        # Build section data
        section_data = []
        for section in sections:
            section_info = {
                'id': section.get('id'),
                'title': section.get('title'),
                'instruction': section.get('instruction'),
                'type': section.get('type'),
                'elicit': section.get('elicit', False),
                'repeatable': section.get('repeatable', False),
                'condition': section.get('condition')
            }
            section_data.append(section_info)
        
        metadata['sections'] = section_data
        
        return {
            'task_id': task_id,
            'title': title,
            'description': description,
            'status': 'pending',
            'priority': template.get('priority', 'medium'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': metadata
        }
    
    def _substitute_variables(self, text: str, parameters: Dict[str, Any]) -> str:
        """Substitute template variables with actual values."""
        if not text:
            return text
        
        result = text
        for key, value in parameters.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        
        return result
    
    def get_template_info(self) -> Dict[str, Any]:
        """Get template metadata."""
        template = self.template_data.get('template', {})
        return {
            'id': template.get('id'),
            'name': template.get('name'),
            'version': template.get('version'),
            'bmad_type': template.get('bmad_type'),
            'priority': template.get('priority'),
            'sections_count': len(self.template_data.get('sections', []))
        }


class BMADTaskTemplateManager:
    """
    Manager for BMAD-specific task templates.
    
    Provides templates for PRD, Architecture, Story, and Codegen tasks.
    """
    
    def __init__(self, templates_dir: str = "bmad_api_service/templates"):
        """Initialize with templates directory."""
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self._ensure_default_templates()
    
    def _ensure_default_templates(self):
        """Ensure default BMAD templates exist."""
        default_templates = {
            'prd-template.yaml': {
                'template': {
                    'id': 'prd-template',
                    'name': 'Product Requirements Document',
                    'version': '1.0',
                    'bmad_type': 'PRD',
                    'priority': 'high',
                    'title': 'Create PRD for {{project_name}}',
                    'description': 'Generate comprehensive Product Requirements Document using BMAD methodology'
                },
                'workflow': {
                    'mode': 'interactive',
                    'elicitation': 'advanced-elicitation'
                },
                'sections': [
                    {
                        'id': 'project-overview',
                        'title': 'Project Overview',
                        'instruction': 'Define the project scope, objectives, and success criteria',
                        'type': 'overview',
                        'elicit': True
                    },
                    {
                        'id': 'user-personas',
                        'title': 'User Personas',
                        'instruction': 'Identify and describe key user personas',
                        'type': 'personas',
                        'elicit': True,
                        'repeatable': True
                    },
                    {
                        'id': 'functional-requirements',
                        'title': 'Functional Requirements',
                        'instruction': 'Define detailed functional requirements',
                        'type': 'requirements',
                        'elicit': True,
                        'repeatable': True
                    },
                    {
                        'id': 'non-functional-requirements',
                        'title': 'Non-Functional Requirements',
                        'instruction': 'Define performance, security, and scalability requirements',
                        'type': 'requirements',
                        'elicit': True
                    }
                ]
            },
            'architecture-template.yaml': {
                'template': {
                    'id': 'architecture-template',
                    'name': 'System Architecture',
                    'version': '1.0',
                    'bmad_type': 'ARCH',
                    'priority': 'high',
                    'title': 'Create Architecture for {{project_name}}',
                    'description': 'Design comprehensive system architecture using BMAD methodology'
                },
                'workflow': {
                    'mode': 'interactive',
                    'elicitation': 'advanced-elicitation'
                },
                'sections': [
                    {
                        'id': 'system-overview',
                        'title': 'System Overview',
                        'instruction': 'Define high-level system architecture and components',
                        'type': 'overview',
                        'elicit': True
                    },
                    {
                        'id': 'component-diagram',
                        'title': 'Component Diagram',
                        'instruction': 'Create detailed component interaction diagrams',
                        'type': 'diagram',
                        'elicit': True
                    },
                    {
                        'id': 'data-flow',
                        'title': 'Data Flow',
                        'instruction': 'Define data flow patterns and storage requirements',
                        'type': 'data',
                        'elicit': True
                    },
                    {
                        'id': 'deployment-architecture',
                        'title': 'Deployment Architecture',
                        'instruction': 'Design deployment and infrastructure requirements',
                        'type': 'deployment',
                        'elicit': True
                    }
                ]
            },
            'story-template.yaml': {
                'template': {
                    'id': 'story-template',
                    'name': 'User Story',
                    'version': '1.0',
                    'bmad_type': 'STORY',
                    'priority': 'medium',
                    'title': 'Create User Story: {{story_title}}',
                    'description': 'Generate detailed user story with acceptance criteria'
                },
                'workflow': {
                    'mode': 'interactive',
                    'elicitation': 'advanced-elicitation'
                },
                'sections': [
                    {
                        'id': 'story-description',
                        'title': 'Story Description',
                        'instruction': 'Write clear, concise user story description',
                        'type': 'description',
                        'elicit': True
                    },
                    {
                        'id': 'acceptance-criteria',
                        'title': 'Acceptance Criteria',
                        'instruction': 'Define detailed acceptance criteria',
                        'type': 'criteria',
                        'elicit': True,
                        'repeatable': True
                    },
                    {
                        'id': 'technical-notes',
                        'title': 'Technical Notes',
                        'instruction': 'Add technical implementation notes',
                        'type': 'technical',
                        'elicit': False
                    }
                ]
            },
            'codegen-template.yaml': {
                'template': {
                    'id': 'codegen-template',
                    'name': 'Code Generation Task',
                    'version': '1.0',
                    'bmad_type': 'CODEGEN',
                    'priority': 'medium',
                    'title': 'Generate Code: {{component_name}}',
                    'description': 'Generate implementation code for specified component'
                },
                'workflow': {
                    'mode': 'yolo',
                    'elicitation': 'minimal'
                },
                'sections': [
                    {
                        'id': 'code-generation',
                        'title': 'Code Generation',
                        'instruction': 'Generate clean, production-ready code',
                        'type': 'code',
                        'elicit': False
                    },
                    {
                        'id': 'testing',
                        'title': 'Testing',
                        'instruction': 'Generate comprehensive tests',
                        'type': 'testing',
                        'elicit': False
                    },
                    {
                        'id': 'documentation',
                        'title': 'Documentation',
                        'instruction': 'Generate inline documentation',
                        'type': 'documentation',
                        'elicit': False
                    }
                ]
            }
        }
        
        for filename, template_data in default_templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                with open(template_path, 'w') as f:
                    yaml.dump(template_data, f, default_flow_style=False)
                logger.info(f"Created default template: {filename}")
    
    def get_template(self, template_id: str) -> Optional[YAMLTaskTemplate]:
        """Get a specific template by ID."""
        template_files = {
            'prd-template': 'prd-template.yaml',
            'architecture-template': 'architecture-template.yaml',
            'story-template': 'story-template.yaml',
            'codegen-template': 'codegen-template.yaml'
        }
        
        filename = template_files.get(template_id)
        if not filename:
            return None
        
        template_path = self.templates_dir / filename
        if not template_path.exists():
            return None
        
        return YAMLTaskTemplate(str(template_path))
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        templates = []
        for template_file in self.templates_dir.glob('*.yaml'):
            try:
                template = YAMLTaskTemplate(str(template_file))
                templates.append(template.get_template_info())
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")
        
        return templates
    
    def create_task_from_template(self,
                                 template_id: str,
                                 project_id: str,
                                 tenant_id: str,
                                 parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a task from a template."""
        template = self.get_template(template_id)
        if not template:
            logger.error(f"Template not found: {template_id}")
            return None
        
        return template.instantiate_task(project_id, tenant_id, parameters)


# Global template manager instance
bmad_template_manager = BMADTaskTemplateManager()
