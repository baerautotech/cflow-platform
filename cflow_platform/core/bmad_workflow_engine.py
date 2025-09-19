"""
BMAD Workflow Engine

This module implements the BMAD workflow engine to replace the CAEF orchestrator.
It integrates BMAD's workflow definitions with the cflow platform infrastructure.
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

try:
    import yaml
except ImportError:
    yaml = None

from dataclasses import dataclass

from .bmad_hil_integration import BMADHILIntegration
from .public_api import get_direct_client_executor
from .telemetry import log_event, telemetry_enabled
from .test_runner import run_tests
from .profiles import InstructionProfile, resolve_profile
from .git_ops import attempt_auto_commit
from .post_run_updates import update_cursor_artifacts
from .memory.checkpointer import checkpoint_iteration, latest_checkpoint_index


@dataclass
class BMADWorkflowStep:
    """Represents a single step in a BMAD workflow."""
    agent: Optional[str] = None
    action: Optional[str] = None
    creates: Optional[str] = None
    requires: Optional[List[str]] = None
    condition: Optional[str] = None
    optional: bool = False
    repeats: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class BMADWorkflow:
    """Represents a complete BMAD workflow definition."""
    id: str
    name: str
    description: str
    type: str
    project_types: List[str]
    sequence: List[BMADWorkflowStep]
    flow_diagram: Optional[str] = None
    decision_guidance: Optional[Dict[str, Any]] = None
    handoff_prompts: Optional[Dict[str, str]] = None


class BMADWorkflowEngine:
    """
    BMAD Workflow Engine that replaces the CAEF orchestrator.
    
    This engine executes BMAD workflows using BMAD's agent definitions,
    templates, and HIL integration patterns.
    """
    
    def __init__(self):
        self.bmad_root = Path(__file__).parent.parent.parent / "vendor" / "bmad"
        self.hil_integration = BMADHILIntegration()
        self.executor = get_direct_client_executor()
        self.workflows: Dict[str, BMADWorkflow] = {}
        self._load_workflows()
    
    def _load_workflows(self) -> None:
        """Load BMAD workflow definitions from vendor/bmad/workflows/."""
        workflows_dir = self.bmad_root / "bmad-core" / "workflows"
        
        if not workflows_dir.exists():
            print(f"Warning: BMAD workflows directory not found: {workflows_dir}")
            return
        
        for workflow_file in workflows_dir.glob("*.yaml"):
            try:
                with open(workflow_file, 'r') as f:
                    workflow_data = yaml.safe_load(f)
                
                workflow = self._parse_workflow(workflow_data)
                self.workflows[workflow.id] = workflow
                
            except Exception as e:
                print(f"Warning: Failed to load workflow {workflow_file}: {e}")
    
    def _parse_workflow(self, data: Dict[str, Any]) -> BMADWorkflow:
        """Parse workflow YAML data into BMADWorkflow object."""
        workflow_data = data.get("workflow", {})
        
        # Parse sequence steps
        sequence = []
        for step_data in workflow_data.get("sequence", []):
            if isinstance(step_data, dict):
                step = BMADWorkflowStep(
                    agent=step_data.get("agent"),
                    action=step_data.get("action"),
                    creates=step_data.get("creates"),
                    requires=step_data.get("requires"),
                    condition=step_data.get("condition"),
                    optional=step_data.get("optional", False),
                    repeats=step_data.get("repeats"),
                    notes=step_data.get("notes")
                )
                sequence.append(step)
        
        return BMADWorkflow(
            id=workflow_data.get("id", ""),
            name=workflow_data.get("name", ""),
            description=workflow_data.get("description", ""),
            type=workflow_data.get("type", ""),
            project_types=workflow_data.get("project_types", []),
            sequence=sequence,
            flow_diagram=workflow_data.get("flow_diagram"),
            decision_guidance=workflow_data.get("decision_guidance"),
            handoff_prompts=workflow_data.get("handoff_prompts")
        )
    
    async def execute_workflow(
        self,
        workflow_id: str,
        project_context: Dict[str, Any],
        profile: InstructionProfile,
        max_iterations: int = 1,
        wallclock_limit_sec: Optional[int] = None,
        step_budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a BMAD workflow.
        
        This replaces the CAEF agent loop with BMAD workflow execution.
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {
                "status": "error",
                "message": f"Workflow {workflow_id} not found"
            }
        
        # Telemetry: workflow start
        log_event(
            "bmad_workflow.start",
            {
                "workflow_id": workflow_id,
                "workflow_name": workflow.name,
                "profile": profile.name if profile else None,
                "max_iterations": int(max_iterations),
            },
        )
        
        history: List[Dict[str, Any]] = []
        start_time = time.time()
        steps_used = 0
        stop_info: Optional[Dict[str, Any]] = None
        
        # Resume support: continue from the next iteration after the latest checkpoint
        start_index_offset = 0
        try:
            if os.getenv("CFLOW_RESUME", "").strip().lower() in {"1", "true", "yes"}:
                last_idx = latest_checkpoint_index()
                if last_idx > 0:
                    start_index_offset = last_idx
        except Exception:
            start_index_offset = 0
        
        for i in range(max_iterations):
            iteration_number = start_index_offset + i + 1
            log_event("bmad_workflow.iteration.begin", {"iteration": iteration_number})
            
            # Pre-iteration budget checks
            if wallclock_limit_sec is not None:
                elapsed = time.time() - start_time
                if elapsed >= wallclock_limit_sec:
                    stop_info = {
                        "reason": "budget_exhausted",
                        "budget_kind": "wallclock",
                        "elapsed_sec": int(elapsed),
                        "limit_sec": int(wallclock_limit_sec),
                    }
                    break
            
            if step_budget is not None and steps_used >= step_budget:
                stop_info = {
                    "reason": "budget_exhausted",
                    "budget_kind": "steps",
                    "steps_used": int(steps_used),
                    "step_budget": int(step_budget),
                }
                break
            
            # Execute workflow iteration
            iteration_result = await self._execute_workflow_iteration(
                workflow, project_context, profile, iteration_number
            )
            
            history.append({
                "iteration": iteration_number,
                **iteration_result
            })
            
            # Count steps (each workflow step counts as 1)
            steps_used += len(workflow.sequence)
            
            # Persist checkpoint
            try:
                checkpoint_iteration(
                    iteration_index=iteration_number,
                    plan={"workflow": workflow_id, "steps": len(workflow.sequence)},
                    verify=iteration_result,
                    run_id=os.getenv("CFLOW_RUN_ID", "bmad-workflow-run"),
                    task_id=os.getenv("CFLOW_TASK_ID", ""),
                    extra_metadata={
                        "profile": profile.name,
                        "workflow_id": workflow_id,
                        "workflow_name": workflow.name
                    },
                )
            except Exception:
                pass
            
            if iteration_result.get("status") == "success":
                log_event("bmad_workflow.iteration.success", {"iteration": iteration_number})
                
                # Update Cursor artifacts after successful runs
                try:
                    update_cursor_artifacts({
                        "task_id": os.getenv("CFLOW_TASK_ID", ""),
                        "profile": profile.name,
                        "iterations": iteration_number,
                        "status": "success",
                        "workflow": workflow_id,
                        "workflow_name": workflow.name,
                    })
                except Exception:
                    pass
                
                # Optional auto-commit when workflow completes successfully
                try:
                    if os.getenv("CFLOW_AUTOCOMMIT", "").strip().lower() in {"1", "true", "yes"}:
                        task_id = os.getenv("CFLOW_TASK_ID", "")
                        msg_parts = []
                        if task_id:
                            msg_parts.append(f"Task {task_id}")
                        msg_parts.append(f"workflow:{workflow_id}")
                        msg_parts.append("bmad:success")
                        commit_msg = "cflow:bmad-workflow - " + " ".join(msg_parts)
                        commit_res = attempt_auto_commit(message=commit_msg)
                        
                        # Attach commit info to checkpoint
                        try:
                            checkpoint_iteration(
                                iteration_index=iteration_number,
                                plan={"workflow": workflow_id, "steps": len(workflow.sequence)},
                                verify={**iteration_result, "auto_commit": commit_res},
                                run_id=os.getenv("CFLOW_RUN_ID", "bmad-workflow-run"),
                                task_id=task_id,
                                extra_metadata={
                                    "profile": profile.name,
                                    "workflow_id": workflow_id,
                                    "workflow_name": workflow.name
                                },
                            )
                        except Exception:
                            pass
                except Exception:
                    pass
                
                break
            
            # Post-iteration budget check
            if step_budget is not None and steps_used >= step_budget:
                stop_info = {
                    "reason": "budget_exhausted",
                    "budget_kind": "steps",
                    "steps_used": int(steps_used),
                    "step_budget": int(step_budget),
                }
                break
        
        final_status = history[-1].get("status", "error") if history else "error"
        result: Dict[str, Any] = {
            "status": final_status,
            "iterations": len(history),
            "history": history,
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
        }
        
        # Attach structured stop info and budgets when applicable
        if stop_info is not None:
            result["stop"] = stop_info
        
        budgets: Dict[str, Any] = {}
        if wallclock_limit_sec is not None:
            budgets["wallclock_limit_sec"] = int(wallclock_limit_sec)
        if step_budget is not None:
            budgets["step_budget"] = int(step_budget)
        if budgets:
            result["budgets"] = budgets
        
        log_event(
            "bmad_workflow.end",
            {
                "status": result.get("status"),
                "iterations": int(result.get("iterations", 0)),
                "workflow_id": workflow_id,
                "budgets": result.get("budgets"),
                "stop": result.get("stop"),
            },
        )
        
        return result
    
    async def _execute_workflow_iteration(
        self,
        workflow: BMADWorkflow,
        project_context: Dict[str, Any],
        profile: InstructionProfile,
        iteration_number: int
    ) -> Dict[str, Any]:
        """Execute a single iteration of the BMAD workflow."""
        try:
            # Check if workflow is paused for HIL interaction
            hil_status = await self.hil_integration.check_workflow_status(
                project_context.get("project_id", "")
            )
            
            if hil_status.get("workflow_paused", False):
                return {
                    "status": "paused",
                    "hil_session_active": True,
                    "session_id": hil_status.get("session_id"),
                    "doc_type": hil_status.get("doc_type"),
                    "message": hil_status.get("message", "Workflow paused for HIL interaction")
                }
            
            # Execute workflow steps
            step_results = []
            for step in workflow.sequence:
                step_result = await self._execute_workflow_step(
                    step, project_context, profile, iteration_number
                )
                step_results.append(step_result)
                
                # If step fails and is not optional, stop workflow
                if step_result.get("status") == "error" and not step.optional:
                    return {
                        "status": "error",
                        "message": f"Workflow step failed: {step.agent}:{step.action}",
                        "step_results": step_results
                    }
            
            # All steps completed successfully
            return {
                "status": "success",
                "message": f"BMAD workflow {workflow.name} completed successfully",
                "step_results": step_results,
                "workflow_completed": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Workflow execution failed: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_workflow_step(
        self,
        step: BMADWorkflowStep,
        project_context: Dict[str, Any],
        profile: InstructionProfile,
        iteration_number: int
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            if step.agent:
                # Execute agent step
                return await self._execute_agent_step(step, project_context, profile)
            elif step.action:
                # Execute action step
                return await self._execute_action_step(step, project_context, profile)
            else:
                return {
                    "status": "skipped",
                    "message": "No agent or action specified for step"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Step execution failed: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_agent_step(
        self,
        step: BMADWorkflowStep,
        project_context: Dict[str, Any],
        profile: InstructionProfile
    ) -> Dict[str, Any]:
        """Execute an agent step using BMAD agent definitions."""
        try:
            # Load BMAD agent definition
            agent_file = self.bmad_root / "bmad-core" / "agents" / f"{step.agent}.md"
            
            if not agent_file.exists():
                return {
                    "status": "error",
                    "message": f"BMAD agent {step.agent} not found"
                }
            
            agent_content = agent_file.read_text()
            
            # Execute agent using direct client
            args = {
                "agent": step.agent,
                "action": step.action,
                "creates": step.creates,
                "requires": step.requires,
                "project_context": project_context,
                "agent_content": agent_content,
                "notes": step.notes
            }
            
            result = await self.executor("bmad_agent_execute", **args)
            
            # Check if this step triggers HIL interaction
            if result.get("hil_required", False):
                hil_result = await self.hil_integration.trigger_hil_session(
                    doc_id=result.get("doc_id", ""),
                    doc_type=result.get("doc_type", ""),
                    workflow_context=project_context
                )
                
                if hil_result.get("success", False):
                    return {
                        "status": "paused",
                        "hil_session_active": True,
                        "session_id": hil_result.get("session_id"),
                        "message": hil_result.get("message"),
                        "agent_result": result
                    }
            
            return {
                "status": "success",
                "agent": step.agent,
                "action": step.action,
                "result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Agent step execution failed: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_action_step(
        self,
        step: BMADWorkflowStep,
        project_context: Dict[str, Any],
        profile: InstructionProfile
    ) -> Dict[str, Any]:
        """Execute an action step."""
        try:
            # Map BMAD actions to cflow platform actions
            action_mapping = {
                "guide_project_structure": "project_setup_guidance",
                "guide_development_sequence": "development_order_guidance",
                "continue_for_all_stories": "repeat_development_cycle",
                "project_complete": "workflow_end"
            }
            
            cflow_action = action_mapping.get(step.action, step.action)
            
            # Execute action using direct client
            args = {
                "action": cflow_action,
                "project_context": project_context,
                "notes": step.notes
            }
            
            result = await self.executor("bmad_action_execute", **args)
            
            return {
                "status": "success",
                "action": step.action,
                "result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Action step execution failed: {str(e)}",
                "error": str(e)
            }
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available BMAD workflows."""
        return [
            {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "type": workflow.type,
                "project_types": workflow.project_types
            }
            for workflow in self.workflows.values()
        ]
    
    def get_workflow(self, workflow_id: str) -> Optional[BMADWorkflow]:
        """Get a specific workflow by ID."""
        return self.workflows.get(workflow_id)


# Global workflow engine instance
_workflow_engine: Optional[BMADWorkflowEngine] = None


def get_workflow_engine() -> BMADWorkflowEngine:
    """Get the global BMAD workflow engine instance."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = BMADWorkflowEngine()
    return _workflow_engine


async def run_bmad_workflow(
    workflow_id: str,
    project_context: Dict[str, Any],
    profile_name: str = "quick",
    max_iterations: int = 1,
    wallclock_limit_sec: Optional[int] = None,
    step_budget: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a BMAD workflow.
    
    This is the main entry point that replaces the CAEF agent loop.
    """
    profile = resolve_profile(profile_name)
    if not profile:
        return {"status": "error", "message": f"Unknown profile {profile_name}"}
    
    engine = get_workflow_engine()
    return await engine.execute_workflow(
        workflow_id=workflow_id,
        project_context=project_context,
        profile=profile,
        max_iterations=max_iterations,
        wallclock_limit_sec=wallclock_limit_sec,
        step_budget=step_budget
    )


def cli() -> int:
    """CLI interface for BMAD workflow engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BMAD Workflow Engine CLI")
    parser.add_argument("--workflow", required=True, help="BMAD workflow ID")
    parser.add_argument("--profile", default="quick", help="Instruction profile name")
    parser.add_argument("--max-iter", type=int, default=1, help="Maximum loop iterations")
    parser.add_argument("--wallclock-sec", type=int, default=None, help="Wall-clock budget in seconds")
    parser.add_argument("--step-budget", type=int, default=None, help="Maximum number of steps")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result")
    parser.add_argument("--list-workflows", action="store_true", help="List available workflows")
    
    args = parser.parse_args()
    
    if args.list_workflows:
        engine = get_workflow_engine()
        workflows = engine.get_available_workflows()
        if args.json:
            print(json.dumps(workflows, indent=2))
        else:
            print("Available BMAD Workflows:")
            for workflow in workflows:
                print(f"  {workflow['id']}: {workflow['name']}")
                print(f"    Type: {workflow['type']}")
                print(f"    Project Types: {', '.join(workflow['project_types'])}")
                print(f"    Description: {workflow['description']}")
                print()
        return 0
    
    # Default project context
    project_context = {
        "project_id": os.getenv("CFLOW_TASK_ID", "default-project"),
        "project_type": "web-app",
        "workspace_path": os.getcwd()
    }
    
    result = asyncio.run(run_bmad_workflow(
        workflow_id=args.workflow,
        project_context=project_context,
        profile_name=args.profile,
        max_iterations=args.max_iter,
        wallclock_limit_sec=args.wallclock_sec,
        step_budget=args.step_budget
    ))
    
    if args.json:
        print(json.dumps(result))
    else:
        status = result.get("status")
        workflow_name = result.get("workflow_name", args.workflow)
        print(f"BMAD workflow '{workflow_name}' finished with status={status} after {result.get('iterations')} iteration(s)")
    
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(cli())
