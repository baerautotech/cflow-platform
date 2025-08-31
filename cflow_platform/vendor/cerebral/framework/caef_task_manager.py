#!/usr/bin/env python3
"""
CAEF Task Manager - Task creation, listing, and management for CAEF CLI
============================================================================

Provides task management capabilities for the CAEF system, including:
- Creating tasks from implementation plans
- Listing available tasks
- Importing tasks from various sources
- Task ID generation and management

Date: July 31, 2025
"""

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid
import random
from dotenv import load_dotenv


class CAEFTaskManager:
    """Manages tasks for the CAEF system"""
    
    def __init__(self):
        self.task_db_path = Path(".cerebraflow/framework/caef_tasks.db")
        self.task_dir = Path(".cerebraflow/tasks")
        self.plans_dir = Path("docs/plans")
        
        # Load environment variables from .cerebraflow/.env
        env_path = Path(".cerebraflow/.env")
        if env_path.exists():
            load_dotenv(env_path)
        
        # Get tenant and user from environment
        self.tenant_id = os.getenv("CEREBRAL_TENANT_ID")
        self.user_id = os.getenv("CEREBRAL_USER_ID")
        
        if not self.tenant_id or not self.user_id:
            print("⚠️ Warning: CEREBRAL_TENANT_ID and CEREBRAL_USER_ID should be set in .cerebraflow/.env")
        
        # Create directories if they don't exist
        self.task_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.task_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize hierarchical task ID service with tag validation
        import sys
        sys.path.append(str(Path(__file__).parent / '..' / 'core' / 'utils'))
        try:
            from hierarchical_task_id_service import HierarchicalTaskIDService
            self.task_id_service = HierarchicalTaskIDService(str(self.task_db_path), default_tag="CORE")
        except ImportError:
            print("⚠️ Hierarchical task ID service not available")
            self.task_id_service = None
        
        # Initialize database
        self._init_database()
        
        # Import user context
        try:
            from caef_user_context import CAEFUserContext
            self.user_context = CAEFUserContext()
        except:
            self.user_context = None
        
    def _init_database(self):
        """Initialize the task database"""
        conn = sqlite3.connect(self.task_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                plan_path TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atomic_level TEXT,
                parent_task_id TEXT,
                metadata TEXT,
                tenant_id TEXT,
                user_id TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
    def create_task_from_plan(self, plan_path: Path, project_tag: Optional[str] = None) -> List[Dict]:
        """Create tasks from an implementation plan using smart import"""
        try:
            from caef_task_import_system import CAEFTaskImportSystem
            import_system = CAEFTaskImportSystem(self)
            
            # First analyze the plan
            print(f"📊 Analyzing plan structure...")
            analysis = import_system.analyze_plan_structure(plan_path)
            print(f"  Original levels: {analysis['original_structure']}")
            print(f"  Compressed to: {analysis['compressed_structure']}")
            print(f"  Compression ratio: {analysis['compression_ratio']:.1%}")
            
            # Import with smart numbering
            return import_system.import_tasks_from_plan(plan_path, project_tag)
            
        except ImportError:
            # Fallback to old method
            print("⚠️ Smart import not available, using legacy import")
            return self._legacy_create_task_from_plan(plan_path)
            
    def _legacy_create_task_from_plan(self, plan_path: Path) -> List[Dict]:
        """Legacy task creation method"""
        tasks = []
        
        if not plan_path.exists():
            raise FileNotFoundError(f"Plan not found: {plan_path}")
            
        with open(plan_path, 'r') as f:
            content = f.read()
            
        # Extract atomic tasks using regex patterns
        task_pattern = r'^#+\s*\**(?:Task\s+)?(\d+(?:\.\d+)*):?\s*[-:]?\s*(.+?)(?:\**)?$'
        
        matches = re.finditer(task_pattern, content, re.MULTILINE)
        
        for match in matches:
            task_level = match.group(1)
            task_title = match.group(2).strip()
            
            # Clean up title - remove trailing asterisks and colons
            task_title = task_title.rstrip('*').rstrip(':').strip()
            
            # Generate CAEF task ID
            task_id = self._generate_task_id(task_level)
            
            task = {
                'task_id': task_id,
                'title': task_title,
                'description': f"Atomic task from {plan_path.name}",
                'plan_path': str(plan_path),
                'atomic_level': task_level,
                'priority': self._determine_priority(task_level),
                'metadata': json.dumps({
                    'source': 'implementation_plan',
                    'plan_name': plan_path.stem,
                    'tag': task_id.split('-')[0] if '-' in task_id else 'master'
                })
            }
            
            tasks.append(task)
            self._save_task(task)
            
        return tasks
        
    def _generate_task_id(self, atomic_level: str, tag: Optional[str] = None) -> str:
        """Generate a hierarchical task ID with tag validation"""
        if self.task_id_service:
            # Determine tag based on task context
            if not tag:
                # Infer tag from atomic level or use master as default
                parts = atomic_level.split(".")
                if len(parts) > 0:
                    step = int(parts[0])
                    # Map CAEF steps to tags
                    step_to_tag = {
                        1: 'CORE',         # Analysis & Research
                        2: 'CORE',         # Planning & Design
                        3: 'FEATURE',      # Implementation & Coding
                        4: 'INTEGRATION',  # Integration & Validation
                        5: 'TESTING',      # Testing & Quality Assurance
                        6: 'DEPLOYMENT'    # Deployment & Governance
                    }
                    tag = step_to_tag.get(step, 'CORE')
                else:
                    tag = 'CORE'
            
            # Validate tag
            tag_validation = self.task_id_service.validate_tag(tag)
            if not tag_validation['valid']:
                print(f"⚠️ Invalid tag '{tag}', using 'CORE' instead")
                tag = 'CORE'
            
            # Generate hierarchical ID
            if len(atomic_level.split(".")) == 1:
                # Main task
                return self.task_id_service.generate_next_main_task_id(tag)
            else:
                # For subtasks, we need to find or create parent first
                # For now, generate as main task
                return self.task_id_service.generate_next_main_task_id(tag)
        else:
            # Fallback to CEREBRAL_397 format
            date_part = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_part = str(uuid.uuid4())[:8].upper()
            return f"CORE-{date_part[:9]}"  # 9-digit sequence from timestamp
        
    def _determine_priority(self, atomic_level: str) -> str:
        """Determine task priority based on atomic level"""
        parts = atomic_level.split(".")
        if len(parts) <= 2:
            return "high"
        elif len(parts) <= 3:
            return "medium"
        else:
            return "low"
            
    def _save_task(self, task: Dict):
        """Save task to database with tenant and user info"""
        if not self.tenant_id or not self.user_id:
            raise ValueError("Cannot save task without tenant_id and user_id configured")
        
        conn = sqlite3.connect(self.task_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO tasks 
            (task_id, title, description, plan_path, status, priority, atomic_level, metadata, tenant_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task['task_id'],
            task['title'],
            task['description'],
            task['plan_path'],
            task.get('status', 'pending'),
            task['priority'],
            task['atomic_level'],
            task['metadata'],
            self.tenant_id,
            self.user_id
        ))
        
        conn.commit()
        conn.close()
        
        # Also save as JSON file for compatibility
        task_file = self.task_dir / f"{task['task_id']}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
            
    def list_tasks(self, status: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """List tasks from the database"""
        conn = sqlite3.connect(self.task_db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM tasks"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        tasks = []
        
        for row in cursor.fetchall():
            task = dict(zip(columns, row))
            if task.get('metadata'):
                task['metadata'] = json.loads(task['metadata'])
            tasks.append(task)
            
        conn.close()
        return tasks
        
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task by ID"""
        conn = sqlite3.connect(self.task_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            task = dict(zip(columns, row))
            if task.get('metadata'):
                task['metadata'] = json.loads(task['metadata'])
            conn.close()
            return task
            
        conn.close()
        return None
        
    def import_all_plans(self) -> Tuple[int, List[str]]:
        """Import all implementation plans as tasks"""
        imported = 0
        errors = []
        
        for plan_path in self.plans_dir.rglob("*IMPLEMENTATION_PLAN.md"):
            try:
                tasks = self.create_task_from_plan(plan_path)
                imported += len(tasks)
                print(f"✅ Imported {len(tasks)} tasks from {plan_path.name}")
            except Exception as e:
                errors.append(f"{plan_path.name}: {str(e)}")
                
        return imported, errors
        
    def update_task_status(self, task_id: str, status: str):
        """Update task status"""
        conn = sqlite3.connect(self.task_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tasks 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        """, (status, task_id))
        
        conn.commit()
        conn.close()
        
        # Update JSON file
        task_file = self.task_dir / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, 'r') as f:
                task = json.load(f)
            task['status'] = status
            task['updated_at'] = datetime.now().isoformat()
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
                
        # Update user context
        if self.user_context and status == 'completed':
            self.user_context.record_task_completion(task_id)
            
    def find_task_by_number(self, task_number: str) -> Optional[Dict]:
        """Find task by short number or partial ID"""
        conn = sqlite3.connect(self.task_db_path)
        cursor = conn.cursor()
        
        # If user context available, add tenant-user prefix
        if self.user_context:
            full_task_id = self.user_context.format_task_id(task_number)
        else:
            full_task_id = task_number
            
        # Try exact match first
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (full_task_id,))
        row = cursor.fetchone()
        
        if not row:
            # Try suffix match (e.g., just the number part)
            cursor.execute("SELECT * FROM tasks WHERE task_id LIKE ?", (f"%{task_number}",))
            row = cursor.fetchone()
            
        if row:
            columns = [desc[0] for desc in cursor.description]
            task = dict(zip(columns, row))
            if task.get('metadata'):
                task['metadata'] = json.loads(task['metadata'])
            conn.close()
            return task
            
        conn.close()
        return None
        
    def select_next_task(self, strategy: Optional[str] = None) -> Optional[Dict]:
        """Select the next best task to work on"""
        if not strategy and self.user_context:
            strategy = self.user_context.get_task_selection_strategy()
        
        if not strategy:
            strategy = "priority_based"
            
        conn = sqlite3.connect(self.task_db_path)
        cursor = conn.cursor()
        
        # Get all pending tasks
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE status = 'pending'
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                created_at ASC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        tasks = []
        
        for row in cursor.fetchall():
            task = dict(zip(columns, row))
            if task.get('metadata'):
                task['metadata'] = json.loads(task['metadata'])
            tasks.append(task)
            
        conn.close()
        
        if not tasks:
            return None
            
        # Apply selection strategy
        if strategy == "priority_based":
            # Already sorted by priority
            selected = tasks[0]
        elif strategy == "oldest_first":
            selected = min(tasks, key=lambda t: t['created_at'])
        elif strategy == "atomic_level":
            # Prefer lower atomic levels (broader tasks)
            selected = min(tasks, key=lambda t: len(t.get('atomic_level', '').split('.')))
        elif strategy == "random":
            selected = random.choice(tasks)
        elif strategy == "hierarchical":
            # Work through tasks depth-first within each plan
            # Group by plan
            tasks_by_plan = {}
            for task in tasks:
                plan = task.get('plan_path', 'unknown')
                if plan not in tasks_by_plan:
                    tasks_by_plan[plan] = []
                tasks_by_plan[plan].append(task)
            
            # Find the plan with the most progress
            best_plan = None
            best_score = -1
            
            for plan, plan_tasks in tasks_by_plan.items():
                # Count completed tasks in this plan
                conn = sqlite3.connect(self.task_db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM tasks WHERE plan_path = ? AND status = 'completed'",
                    (plan,)
                )
                completed_count = cursor.fetchone()[0]
                conn.close()
                
                # Score based on progress and priority
                score = completed_count * 10
                for task in plan_tasks:
                    if task['priority'] == 'high':
                        score += 3
                    elif task['priority'] == 'medium':
                        score += 2
                    else:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_plan = plan
            
            # Select the lowest level task from the best plan
            if best_plan and best_plan in tasks_by_plan:
                plan_tasks = tasks_by_plan[best_plan]
                # Sort by atomic level depth
                plan_tasks.sort(key=lambda t: (
                    len(t.get('atomic_level', '').split('.')),
                    t.get('atomic_level', '')
                ))
                selected = plan_tasks[0]
            else:
                selected = tasks[0]
        elif strategy == "related":
            # Try to find task related to last completed
            if self.user_context and self.user_context.context['history']['last_task']:
                last_task_id = self.user_context.context['history']['last_task']
                last_task = self.get_task(last_task_id)
                if last_task and last_task.get('plan_path'):
                    # Prefer tasks from same plan
                    related = [t for t in tasks if t.get('plan_path') == last_task['plan_path']]
                    if related:
                        selected = related[0]
                    else:
                        selected = tasks[0]
                else:
                    selected = tasks[0]
            else:
                selected = tasks[0]
        else:
            # Default to priority-based
            selected = tasks[0]
            
        return selected
        
    def get_next_task_recommendation(self) -> Dict:
        """Get recommendation for next task with explanation"""
        task = self.select_next_task()
        
        if not task:
            return {
                "task": None,
                "reason": "No pending tasks available",
                "alternatives": []
            }
            
        # Get alternatives
        all_pending = self.list_tasks(status="pending", limit=5)
        alternatives = [t for t in all_pending if t['task_id'] != task['task_id']]
        
        # Generate reason
        strategy = self.user_context.get_task_selection_strategy() if self.user_context else "priority_based"
        reasons = {
            "priority_based": f"Highest priority {task['priority']} task",
            "oldest_first": f"Oldest pending task (created {task['created_at']})",
            "atomic_level": f"Broadest scope task (level {task.get('atomic_level', 'unknown')})",
            "random": "Randomly selected task",
            "related": f"Related to previous work on {task.get('plan_path', 'unknown')}"
        }
        
        return {
            "task": task,
            "reason": reasons.get(strategy, "Selected based on configured strategy"),
            "alternatives": alternatives[:3],
            "strategy": strategy
        }


if __name__ == "__main__":
    # Test the task manager
    manager = CAEFTaskManager()
    
    # Import all plans
    imported, errors = manager.import_all_plans()
    print(f"\n📊 Import Summary: {imported} tasks imported")
    
    if errors:
        print(f"⚠️ Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
            
    # List tasks
    print("\n📋 Available Tasks:")
    tasks = manager.list_tasks(limit=10)
    for task in tasks:
        print(f"  {task['task_id']}: {task['title']} [{task['priority']}]")