#!/usr/bin/env python3
"""
Task Manager - Manages and tracks tasks extracted from PRDs.

This module provides functionality to:
- Load tasks from parsed PRDs
- Track task status and progress
- Handle task dependencies
- Generate progress reports
- Query and filter tasks
"""

import json
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from prd_parser import PRDParser, Task, Phase, TaskStatus, Priority


class TaskManager:
    """Manages tasks extracted from PRD files."""

    def __init__(self, tasks_file: Optional[str] = None):
        """
        Initialize the task manager.

        Args:
            tasks_file: Optional path to tasks JSON/YAML file
        """
        self.tasks: List[Dict[str, Any]] = []
        self.phases: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.tasks_file = tasks_file

        if tasks_file and Path(tasks_file).exists():
            self.load_tasks(tasks_file)

    def load_from_prd(self, prd_file: str) -> None:
        """
        Load tasks directly from a PRD file.

        Args:
            prd_file: Path to PRD markdown file
        """
        parser = PRDParser(prd_file)
        data = parser.parse()

        self.metadata = data['metadata']
        self.phases = data['phases']
        self.tasks = data['tasks']

        print(f"Loaded {len(self.tasks)} tasks from PRD: {self.metadata.get('title', 'Unknown')}")

    def load_tasks(self, tasks_file: str) -> None:
        """
        Load tasks from JSON or YAML file.

        Args:
            tasks_file: Path to tasks file
        """
        file_path = Path(tasks_file)

        if file_path.suffix == '.json':
            with open(tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif file_path.suffix in ['.yaml', '.yml']:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        self.metadata = data.get('metadata', {})
        self.phases = data.get('phases', [])
        self.tasks = data.get('tasks', [])

        print(f"Loaded {len(self.tasks)} tasks from file: {tasks_file}")

    def save_tasks(self, output_file: str, format: str = 'json') -> None:
        """
        Save tasks to file.

        Args:
            output_file: Path to output file
            format: Output format ('json' or 'yaml')
        """
        data = {
            'metadata': self.metadata,
            'phases': self.phases,
            'tasks': self.tasks,
            'last_updated': datetime.now().isoformat()
        }

        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif format in ['yaml', 'yml']:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        print(f"Tasks saved to: {output_file}")

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task dictionary or None if not found
        """
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None

    def get_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get tasks with optional filtering.

        Args:
            filters: Optional dictionary with filter criteria:
                - status: Filter by status
                - phase: Filter by phase
                - priority: Filter by priority
                - section: Filter by section

        Returns:
            List of matching tasks
        """
        if not filters:
            return self.tasks

        filtered_tasks = self.tasks

        if 'status' in filters:
            filtered_tasks = [t for t in filtered_tasks if t['status'] == filters['status']]

        if 'phase' in filters:
            filtered_tasks = [t for t in filtered_tasks if t['phase'] == filters['phase']]

        if 'priority' in filters:
            filtered_tasks = [t for t in filtered_tasks if t['priority'] == filters['priority']]

        if 'section' in filters:
            filtered_tasks = [t for t in filtered_tasks if t['section'] == filters['section']]

        return filtered_tasks

    def update_task_status(self, task_id: str, status: str, message: Optional[str] = None) -> bool:
        """
        Update the status of a task.

        Args:
            task_id: Task identifier
            status: New status (pending/in_progress/completed/failed/blocked)
            message: Optional status message

        Returns:
            True if successful, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            print(f"Task not found: {task_id}")
            return False

        # Validate status
        valid_statuses = [s.value for s in TaskStatus]
        if status not in valid_statuses:
            print(f"Invalid status: {status}. Must be one of: {valid_statuses}")
            return False

        task['status'] = status

        # Add status history
        if 'status_history' not in task:
            task['status_history'] = []

        task['status_history'].append({
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'message': message
        })

        print(f"Updated task {task_id} to status: {status}")
        return True

    def get_task_dependencies(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all dependencies for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of dependency tasks
        """
        task = self.get_task(task_id)
        if not task:
            return []

        dependencies = []
        for dep_id in task.get('dependencies', []):
            dep_task = self.get_task(dep_id)
            if dep_task:
                dependencies.append(dep_task)

        return dependencies

    def can_start_task(self, task_id: str) -> bool:
        """
        Check if a task can be started (all dependencies completed).

        Args:
            task_id: Task identifier

        Returns:
            True if task can be started, False otherwise
        """
        dependencies = self.get_task_dependencies(task_id)

        for dep in dependencies:
            if dep['status'] != TaskStatus.COMPLETED.value:
                return False

        return True

    def get_next_tasks(self) -> List[Dict[str, Any]]:
        """
        Get list of tasks that can be started next.

        Returns:
            List of tasks with pending status and all dependencies met
        """
        next_tasks = []

        for task in self.tasks:
            if task['status'] == TaskStatus.PENDING.value and self.can_start_task(task['id']):
                next_tasks.append(task)

        return next_tasks

    def get_progress_report(self) -> Dict[str, Any]:
        """
        Generate a progress report.

        Returns:
            Dictionary with progress statistics
        """
        total = len(self.tasks)
        pending = len([t for t in self.tasks if t['status'] == TaskStatus.PENDING.value])
        in_progress = len([t for t in self.tasks if t['status'] == TaskStatus.IN_PROGRESS.value])
        completed = len([t for t in self.tasks if t['status'] == TaskStatus.COMPLETED.value])
        failed = len([t for t in self.tasks if t['status'] == TaskStatus.FAILED.value])
        blocked = len([t for t in self.tasks if t['status'] == TaskStatus.BLOCKED.value])

        progress_pct = (completed / total * 100) if total > 0 else 0

        # Phase progress
        phase_progress = []
        for phase in self.phases:
            phase_tasks = phase.get('tasks', [])
            if not phase_tasks:
                continue

            phase_completed = len([t for t in phase_tasks if t['status'] == TaskStatus.COMPLETED.value])
            phase_total = len(phase_tasks)
            phase_pct = (phase_completed / phase_total * 100) if phase_total > 0 else 0

            phase_progress.append({
                'phase': phase['name'],
                'priority': phase['priority'],
                'completed': phase_completed,
                'total': phase_total,
                'progress': round(phase_pct, 1)
            })

        return {
            'total_tasks': total,
            'pending': pending,
            'in_progress': in_progress,
            'completed': completed,
            'failed': failed,
            'blocked': blocked,
            'progress_percentage': round(progress_pct, 1),
            'phase_progress': phase_progress
        }

    def print_progress_report(self) -> None:
        """Print a formatted progress report."""
        report = self.get_progress_report()

        print("\n" + "=" * 60)
        print(f"PROJECT: {self.metadata.get('title', 'Unknown')}")
        print("=" * 60)

        print(f"\nOVERALL PROGRESS: {report['progress_percentage']}%")
        print(f"  Total Tasks: {report['total_tasks']}")
        print(f"  Completed: {report['completed']}")
        print(f"  In Progress: {report['in_progress']}")
        print(f"  Pending: {report['pending']}")
        print(f"  Failed: {report['failed']}")
        print(f"  Blocked: {report['blocked']}")

        print(f"\nPHASE PROGRESS:")
        for phase in report['phase_progress']:
            print(f"  {phase['phase']} ({phase['priority']}): "
                  f"{phase['completed']}/{phase['total']} ({phase['progress']}%)")

        next_tasks = self.get_next_tasks()
        if next_tasks:
            print(f"\nNEXT AVAILABLE TASKS ({len(next_tasks)}):")
            for i, task in enumerate(next_tasks[:5], 1):
                print(f"  {i}. [{task['priority']}] {task['title']}")
            if len(next_tasks) > 5:
                print(f"  ... and {len(next_tasks) - 5} more")

        print("=" * 60 + "\n")

    def print_tasks(self, filters: Optional[Dict[str, Any]] = None) -> None:
        """
        Print tasks with optional filtering.

        Args:
            filters: Optional filter criteria
        """
        tasks = self.get_tasks(filters)

        if not tasks:
            print("No tasks found matching the criteria.")
            return

        print(f"\nFound {len(tasks)} task(s):\n")

        for task in tasks:
            status_symbol = {
                TaskStatus.PENDING.value: "[ ]",
                TaskStatus.IN_PROGRESS.value: "[~]",
                TaskStatus.COMPLETED.value: "[✓]",
                TaskStatus.FAILED.value: "[✗]",
                TaskStatus.BLOCKED.value: "[!]"
            }.get(task['status'], "[?]")

            print(f"{status_symbol} {task['id']}: {task['title']}")
            print(f"    Phase: {task['phase']} | Priority: {task['priority']} | Status: {task['status']}")
            if task.get('dependencies'):
                print(f"    Dependencies: {', '.join(task['dependencies'])}")
            print()


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description='Task Manager for PRD-based project management')
    parser.add_argument('--prd', help='Load tasks from PRD file')
    parser.add_argument('--tasks', help='Load tasks from JSON/YAML file')
    parser.add_argument('--save', help='Save tasks to file')
    parser.add_argument('--format', choices=['json', 'yaml'], default='json', help='Output format')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--status', help='Filter by status')
    list_parser.add_argument('--phase', help='Filter by phase')
    list_parser.add_argument('--priority', help='Filter by priority')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update task status')
    update_parser.add_argument('task_id', help='Task ID')
    update_parser.add_argument('status', help='New status')
    update_parser.add_argument('--message', help='Status message')

    # Progress command
    subparsers.add_parser('progress', help='Show progress report')

    # Next command
    subparsers.add_parser('next', help='Show next available tasks')

    args = parser.parse_args()

    # Initialize task manager
    tm = TaskManager()

    # Load tasks
    if args.prd:
        tm.load_from_prd(args.prd)
    elif args.tasks:
        tm.load_tasks(args.tasks)
    else:
        print("Please specify --prd or --tasks to load tasks")
        return

    # Execute command
    if args.command == 'list':
        filters = {}
        if args.status:
            filters['status'] = args.status
        if args.phase:
            filters['phase'] = args.phase
        if args.priority:
            filters['priority'] = args.priority
        tm.print_tasks(filters)

    elif args.command == 'update':
        tm.update_task_status(args.task_id, args.status, args.message)
        if args.save:
            tm.save_tasks(args.save, args.format)

    elif args.command == 'progress':
        tm.print_progress_report()

    elif args.command == 'next':
        next_tasks = tm.get_next_tasks()
        print(f"\nNext available tasks ({len(next_tasks)}):\n")
        for task in next_tasks:
            print(f"  [{task['priority']}] {task['id']}: {task['title']}")
            print(f"      Phase: {task['phase']}\n")

    else:
        # Default: show progress
        tm.print_progress_report()

    # Save if requested
    if args.save and args.command != 'update':
        tm.save_tasks(args.save, args.format)


if __name__ == '__main__':
    main()
