"""
BMAD Plan Conflict Detection and Resolution System

This module provides comprehensive plan conflict detection, analysis, and resolution
recommendations for the BMAD Master system. It integrates with HIL (Human-in-the-Loop)
for decision support and ensures plan consistency across the Cerebral platform.
"""

from __future__ import annotations

import os
import re
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ConflictType(Enum):
    """Types of plan conflicts that can be detected."""
    REQUIREMENT_OVERLAP = "requirement_overlap"
    IMPLEMENTATION_CONFLICT = "implementation_conflict"
    TIMELINE_CONFLICT = "timeline_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    ARCHITECTURE_CONFLICT = "architecture_conflict"
    SCOPE_CONFLICT = "scope_conflict"


class ResolutionStrategy(Enum):
    """Recommended resolution strategies for conflicts."""
    MERGE = "merge"
    REPLACE = "replace"
    VERSION = "version"
    SPLIT = "split"
    HIL_DECISION = "hil_decision"


@dataclass
class PlanConflict:
    """Represents a detected conflict between plans."""
    conflict_id: str
    conflict_type: ConflictType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    affected_plans: List[str]
    conflicting_elements: List[str]
    resolution_strategy: ResolutionStrategy
    resolution_rationale: str
    detected_at: datetime
    requires_hil: bool = False


@dataclass
class PlanElement:
    """Represents an element within a plan."""
    element_id: str
    element_type: str  # task, requirement, milestone, resource, etc.
    content: str
    metadata: Dict[str, Any]
    dependencies: List[str]
    completion_status: str


class PlanConflictDetector:
    """
    Detects and analyzes conflicts between BMAD implementation plans.
    
    This class provides comprehensive conflict detection capabilities including:
    - Requirement overlap analysis
    - Implementation conflict detection
    - Timeline and resource conflict analysis
    - Architecture consistency checking
    - Scope boundary validation
    """
    
    def __init__(self):
        self.conflicts: List[PlanConflict] = []
        self.plans: Dict[str, Dict[str, Any]] = {}
        self.elements: Dict[str, PlanElement] = {}
        
    def load_plan(self, plan_path: str) -> bool:
        """
        Load a plan file for analysis.
        
        Args:
            plan_path: Path to the plan file
            
        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            with open(plan_path, 'r') as f:
                content = f.read()
                
            plan_name = os.path.basename(plan_path)
            
            # Parse plan metadata
            metadata = self._extract_plan_metadata(content)
            
            # Extract plan elements
            elements = self._extract_plan_elements(content, plan_name)
            
            # Store plan information
            self.plans[plan_name] = {
                'path': plan_path,
                'content': content,
                'metadata': metadata,
                'elements': elements,
                'loaded_at': datetime.now()
            }
            
            # Store elements for cross-plan analysis
            for element in elements:
                self.elements[element.element_id] = element
                
            return True
            
        except Exception as e:
            print(f"Error loading plan {plan_path}: {e}")
            return False
    
    def _extract_plan_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from plan content."""
        metadata = {}
        
        # Extract version
        version_match = re.search(r'Version:\s*([^\n]+)', content)
        if version_match:
            metadata['version'] = version_match.group(1).strip()
            
        # Extract date
        date_match = re.search(r'Date:\s*([^\n]+)', content)
        if date_match:
            metadata['date'] = date_match.group(1).strip()
            
        # Extract status
        status_match = re.search(r'Status:\s*([^\n]+)', content)
        if status_match:
            metadata['status'] = status_match.group(1).strip()
            
        # Extract priority
        priority_match = re.search(r'Priority:\s*([^\n]+)', content)
        if priority_match:
            metadata['priority'] = priority_match.group(1).strip()
            
        return metadata
    
    def _extract_plan_elements(self, content: str, plan_name: str) -> List[PlanElement]:
        """Extract structured elements from plan content."""
        elements = []
        
        # Extract tasks (various formats)
        task_patterns = [
            r'^\s*-\s*\[([^\]]*)\]\s*(.+)$',  # Markdown checkboxes
            r'^\s*\d+\.\s*(.+)$',  # Numbered lists
            r'^\s*\*\s*(.+)$',  # Bullet points
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern in task_patterns:
                match = re.match(pattern, line)
                if match:
                    element_id = f"{plan_name}_task_{i}"
                    
                    if len(match.groups()) == 2:  # Checkbox format
                        completion = "completed" if match.group(1).strip() == "x" else "pending"
                        content_text = match.group(2).strip()
                    else:  # Other formats
                        completion = "pending"
                        content_text = match.group(1).strip()
                    
                    element = PlanElement(
                        element_id=element_id,
                        element_type="task",
                        content=content_text,
                        metadata={
                            'line_number': i,
                            'plan_name': plan_name,
                            'pattern_type': pattern
                        },
                        dependencies=[],
                        completion_status=completion
                    )
                    elements.append(element)
                    break
        
        return elements
    
    def detect_conflicts(self) -> List[PlanConflict]:
        """
        Detect all conflicts between loaded plans.
        
        Returns:
            List of detected conflicts
        """
        self.conflicts = []
        
        if len(self.plans) < 2:
            return self.conflicts
        
        plan_names = list(self.plans.keys())
        
        # Check for conflicts between all plan pairs
        for i in range(len(plan_names)):
            for j in range(i + 1, len(plan_names)):
                plan1 = plan_names[i]
                plan2 = plan_names[j]
                
                # Detect different types of conflicts
                self._detect_requirement_overlaps(plan1, plan2)
                self._detect_implementation_conflicts(plan1, plan2)
                self._detect_timeline_conflicts(plan1, plan2)
                self._detect_architecture_conflicts(plan1, plan2)
                self._detect_scope_conflicts(plan1, plan2)
        
        return self.conflicts
    
    def _detect_requirement_overlaps(self, plan1: str, plan2: str) -> None:
        """Detect overlapping requirements between plans."""
        elements1 = self.plans[plan1]['elements']
        elements2 = self.plans[plan2]['elements']
        
        overlaps = []
        
        for elem1 in elements1:
            for elem2 in elements2:
                # Simple content similarity check (can be enhanced with NLP)
                similarity = self._calculate_content_similarity(
                    elem1.content, elem2.content
                )
                
                if similarity > 0.7:  # 70% similarity threshold
                    overlaps.append((elem1, elem2, similarity))
        
        if overlaps:
            conflict = PlanConflict(
                conflict_id=f"req_overlap_{plan1}_{plan2}",
                conflict_type=ConflictType.REQUIREMENT_OVERLAP,
                severity="MEDIUM",
                description=f"Overlapping requirements between {plan1} and {plan2}",
                affected_plans=[plan1, plan2],
                conflicting_elements=[f"{e1.element_id} <-> {e2.element_id}" for e1, e2, _ in overlaps],
                resolution_strategy=ResolutionStrategy.HIL_DECISION,
                resolution_rationale="Similar requirements detected - HIL decision required for merge/replace strategy",
                detected_at=datetime.now(),
                requires_hil=True
            )
            self.conflicts.append(conflict)
    
    def _detect_implementation_conflicts(self, plan1: str, plan2: str) -> None:
        """Detect conflicting implementation approaches."""
        # Check for conflicting technical approaches
        tech_keywords = [
            'architecture', 'framework', 'technology', 'implementation',
            'design pattern', 'approach', 'methodology'
        ]
        
        conflicts = []
        
        for keyword in tech_keywords:
            plan1_mentions = [e for e in self.plans[plan1]['elements'] 
                            if keyword.lower() in e.content.lower()]
            plan2_mentions = [e for e in self.plans[plan2]['elements'] 
                            if keyword.lower() in e.content.lower()]
            
            if plan1_mentions and plan2_mentions:
                # Check for conflicting approaches
                for e1 in plan1_mentions:
                    for e2 in plan2_mentions:
                        if self._has_conflicting_approaches(e1.content, e2.content):
                            conflicts.append((e1, e2))
        
        if conflicts:
            conflict = PlanConflict(
                conflict_id=f"impl_conflict_{plan1}_{plan2}",
                conflict_type=ConflictType.IMPLEMENTATION_CONFLICT,
                severity="HIGH",
                description=f"Conflicting implementation approaches between {plan1} and {plan2}",
                affected_plans=[plan1, plan2],
                conflicting_elements=[f"{e1.element_id} <-> {e2.element_id}" for e1, e2 in conflicts],
                resolution_strategy=ResolutionStrategy.HIL_DECISION,
                resolution_rationale="Conflicting technical approaches detected - HIL decision required",
                detected_at=datetime.now(),
                requires_hil=True
            )
            self.conflicts.append(conflict)
    
    def _detect_timeline_conflicts(self, plan1: str, plan2: str) -> None:
        """Detect timeline conflicts between plans."""
        # Extract timeline information from plans
        timeline1 = self._extract_timeline_info(plan1)
        timeline2 = self._extract_timeline_info(plan2)
        
        if timeline1 and timeline2:
            # Check for overlapping timelines with conflicting priorities
            conflicts = []
            
            for t1 in timeline1:
                for t2 in timeline2:
                    if self._timelines_overlap(t1, t2) and t1.get('priority') == t2.get('priority'):
                        conflicts.append((t1, t2))
            
            if conflicts:
                conflict = PlanConflict(
                    conflict_id=f"timeline_conflict_{plan1}_{plan2}",
                    conflict_type=ConflictType.TIMELINE_CONFLICT,
                    severity="HIGH",
                    description=f"Timeline conflicts between {plan1} and {plan2}",
                    affected_plans=[plan1, plan2],
                    conflicting_elements=[f"{t1.get('task', 'unknown')} <-> {t2.get('task', 'unknown')}" for t1, t2 in conflicts],
                    resolution_strategy=ResolutionStrategy.HIL_DECISION,
                    resolution_rationale="Timeline conflicts with same priority detected - HIL decision required",
                    detected_at=datetime.now(),
                    requires_hil=True
                )
                self.conflicts.append(conflict)
    
    def _detect_architecture_conflicts(self, plan1: str, plan2: str) -> None:
        """Detect architectural conflicts between plans."""
        # Look for conflicting architectural decisions
        arch_keywords = ['architecture', 'design', 'pattern', 'framework', 'system']
        
        conflicts = []
        
        for keyword in arch_keywords:
            plan1_elements = [e for e in self.plans[plan1]['elements'] 
                            if keyword.lower() in e.content.lower()]
            plan2_elements = [e for e in self.plans[plan2]['elements'] 
                            if keyword.lower() in e.content.lower()]
            
            for e1 in plan1_elements:
                for e2 in plan2_elements:
                    if self._has_architectural_conflict(e1.content, e2.content):
                        conflicts.append((e1, e2))
        
        if conflicts:
            conflict = PlanConflict(
                conflict_id=f"arch_conflict_{plan1}_{plan2}",
                conflict_type=ConflictType.ARCHITECTURE_CONFLICT,
                severity="CRITICAL",
                description=f"Architectural conflicts between {plan1} and {plan2}",
                affected_plans=[plan1, plan2],
                conflicting_elements=[f"{e1.element_id} <-> {e2.element_id}" for e1, e2 in conflicts],
                resolution_strategy=ResolutionStrategy.HIL_DECISION,
                resolution_rationale="Critical architectural conflicts detected - HIL decision required",
                detected_at=datetime.now(),
                requires_hil=True
            )
            self.conflicts.append(conflict)
    
    def _detect_scope_conflicts(self, plan1: str, plan2: str) -> None:
        """Detect scope boundary conflicts between plans."""
        # Check for overlapping scope definitions
        scope_keywords = ['scope', 'boundary', 'responsibility', 'component', 'module']
        
        conflicts = []
        
        for keyword in scope_keywords:
            plan1_elements = [e for e in self.plans[plan1]['elements'] 
                            if keyword.lower() in e.content.lower()]
            plan2_elements = [e for e in self.plans[plan2]['elements'] 
                            if keyword.lower() in e.content.lower()]
            
            for e1 in plan1_elements:
                for e2 in plan2_elements:
                    if self._has_scope_conflict(e1.content, e2.content):
                        conflicts.append((e1, e2))
        
        if conflicts:
            conflict = PlanConflict(
                conflict_id=f"scope_conflict_{plan1}_{plan2}",
                conflict_type=ConflictType.SCOPE_CONFLICT,
                severity="MEDIUM",
                description=f"Scope conflicts between {plan1} and {plan2}",
                affected_plans=[plan1, plan2],
                conflicting_elements=[f"{e1.element_id} <-> {e2.element_id}" for e1, e2 in conflicts],
                resolution_strategy=ResolutionStrategy.HIL_DECISION,
                resolution_rationale="Scope boundary conflicts detected - HIL decision required",
                detected_at=datetime.now(),
                requires_hil=True
            )
            self.conflicts.append(conflict)
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings."""
        # Simple word-based similarity (can be enhanced with more sophisticated NLP)
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _has_conflicting_approaches(self, content1: str, content2: str) -> bool:
        """Check if two content pieces have conflicting technical approaches."""
        # Define conflicting approach patterns
        conflicts = [
            ('microservices', 'monolith'),
            ('rest', 'graphql'),
            ('sql', 'nosql'),
            ('react', 'vue'),
            ('python', 'javascript'),
            ('docker', 'kubernetes'),
            ('aws', 'azure')
        ]
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        for approach1, approach2 in conflicts:
            if (approach1 in content1_lower and approach2 in content2_lower) or \
               (approach2 in content1_lower and approach1 in content2_lower):
                return True
        
        return False
    
    def _extract_timeline_info(self, plan_name: str) -> List[Dict[str, Any]]:
        """Extract timeline information from a plan."""
        # This is a simplified implementation
        # In practice, this would parse more sophisticated timeline formats
        timeline_info = []
        
        # Look for timeline patterns in the plan
        content = self.plans[plan_name]['content']
        
        # Extract week/day patterns
        week_pattern = r'Week\s+(\d+).*?(?=Week|\Z)'
        week_matches = re.findall(week_pattern, content, re.DOTALL)
        
        for week in week_matches:
            timeline_info.append({
                'week': int(week),
                'plan': plan_name,
                'priority': 'MEDIUM'  # Default priority
            })
        
        return timeline_info
    
    def _timelines_overlap(self, timeline1: Dict[str, Any], timeline2: Dict[str, Any]) -> bool:
        """Check if two timelines overlap."""
        # Simplified overlap detection
        return timeline1.get('week') == timeline2.get('week')
    
    def _has_architectural_conflict(self, content1: str, content2: str) -> bool:
        """Check if two content pieces have architectural conflicts."""
        # Define architectural conflict patterns
        arch_conflicts = [
            ('centralized', 'distributed'),
            ('synchronous', 'asynchronous'),
            ('stateful', 'stateless'),
            ('tightly coupled', 'loosely coupled'),
            ('client-server', 'peer-to-peer')
        ]
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        for arch1, arch2 in arch_conflicts:
            if (arch1 in content1_lower and arch2 in content2_lower) or \
               (arch2 in content1_lower and arch1 in content2_lower):
                return True
        
        return False
    
    def _has_scope_conflict(self, content1: str, content2: str) -> bool:
        """Check if two content pieces have scope conflicts."""
        # Look for overlapping responsibilities
        scope_keywords = ['responsible for', 'handles', 'manages', 'controls', 'owns']
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        # Check for overlapping responsibilities
        for keyword in scope_keywords:
            if keyword in content1_lower and keyword in content2_lower:
                # Check if they're talking about the same domain
                if self._calculate_content_similarity(content1, content2) > 0.5:
                    return True
        
        return False
    
    def generate_resolution_recommendations(self) -> Dict[str, Any]:
        """
        Generate resolution recommendations for detected conflicts.
        
        Returns:
            Dictionary containing resolution recommendations
        """
        recommendations = {
            'total_conflicts': len(self.conflicts),
            'critical_conflicts': len([c for c in self.conflicts if c.severity == 'CRITICAL']),
            'high_conflicts': len([c for c in self.conflicts if c.severity == 'HIGH']),
            'medium_conflicts': len([c for c in self.conflicts if c.severity == 'MEDIUM']),
            'low_conflicts': len([c for c in self.conflicts if c.severity == 'LOW']),
            'hil_required': len([c for c in self.conflicts if c.requires_hil]),
            'recommendations': []
        }
        
        for conflict in self.conflicts:
            recommendation = {
                'conflict_id': conflict.conflict_id,
                'severity': conflict.severity,
                'strategy': conflict.resolution_strategy.value,
                'rationale': conflict.resolution_rationale,
                'requires_hil': conflict.requires_hil,
                'affected_plans': conflict.affected_plans,
                'suggested_actions': self._get_suggested_actions(conflict)
            }
            recommendations['recommendations'].append(recommendation)
        
        return recommendations
    
    def _get_suggested_actions(self, conflict: PlanConflict) -> List[str]:
        """Get suggested actions for resolving a conflict."""
        actions = []
        
        if conflict.conflict_type == ConflictType.REQUIREMENT_OVERLAP:
            actions.extend([
                "Review overlapping requirements for duplication",
                "Determine if requirements can be merged",
                "Consider requirement prioritization",
                "Document decision rationale"
            ])
        elif conflict.conflict_type == ConflictType.IMPLEMENTATION_CONFLICT:
            actions.extend([
                "Evaluate technical approaches",
                "Consider hybrid implementation",
                "Document architectural decision record",
                "Update implementation guidelines"
            ])
        elif conflict.conflict_type == ConflictType.TIMELINE_CONFLICT:
            actions.extend([
                "Adjust timeline priorities",
                "Consider parallel development",
                "Review resource allocation",
                "Update project milestones"
            ])
        elif conflict.conflict_type == ConflictType.ARCHITECTURE_CONFLICT:
            actions.extend([
                "CRITICAL: Resolve architectural conflicts immediately",
                "Conduct architecture review",
                "Document architectural decisions",
                "Update system design"
            ])
        elif conflict.conflict_type == ConflictType.SCOPE_CONFLICT:
            actions.extend([
                "Clarify scope boundaries",
                "Update responsibility matrix",
                "Document scope decisions",
                "Communicate changes to team"
            ])
        
        return actions
    
    def export_conflict_report(self, output_path: str) -> bool:
        """
        Export conflict analysis report to file.
        
        Args:
            output_path: Path to save the report
            
        Returns:
            True if successfully exported, False otherwise
        """
        try:
            report = {
                'analysis_date': datetime.now().isoformat(),
                'plans_analyzed': list(self.plans.keys()),
                'conflicts': [
                    {
                        'conflict_id': c.conflict_id,
                        'type': c.conflict_type.value,
                        'severity': c.severity,
                        'description': c.description,
                        'affected_plans': c.affected_plans,
                        'conflicting_elements': c.conflicting_elements,
                        'resolution_strategy': c.resolution_strategy.value,
                        'resolution_rationale': c.resolution_rationale,
                        'requires_hil': c.requires_hil,
                        'detected_at': c.detected_at.isoformat()
                    }
                    for c in self.conflicts
                ],
                'recommendations': self.generate_resolution_recommendations()
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting conflict report: {e}")
            return False


def main():
    """Example usage of the PlanConflictDetector."""
    detector = PlanConflictDetector()
    
    # Load plans from archived directory
    archived_dir = "docs/plans/archived"
    if os.path.exists(archived_dir):
        for filename in os.listdir(archived_dir):
            if filename.endswith('.md'):
                plan_path = os.path.join(archived_dir, filename)
                detector.load_plan(plan_path)
    
    # Detect conflicts
    conflicts = detector.detect_conflicts()
    
    print(f"Detected {len(conflicts)} conflicts")
    for conflict in conflicts:
        print(f"- {conflict.conflict_type.value}: {conflict.description}")
    
    # Generate recommendations
    recommendations = detector.generate_resolution_recommendations()
    print(f"\nRecommendations: {recommendations['total_conflicts']} total conflicts")
    print(f"HIL required for: {recommendations['hil_required']} conflicts")
    
    # Export report
    detector.export_conflict_report("docs/plans/conflict_analysis_report.json")


if __name__ == "__main__":
    main()

