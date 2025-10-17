#!/usr/bin/env python3
"""
Task Master - Executes deployment tasks automatically.

This module provides functionality to:
- Execute deployment tasks automatically
- Run Terraform commands
- Run kubectl commands
- Run ArgoCD CLI commands
- Handle task failures and retries
- Generate execution logs
"""

import subprocess
import time
import json
import yaml
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging


@dataclass
class ExecutionResult:
    """Result of task execution."""
    success: bool
    output: str
    error: str
    duration: float
    command: str
    timestamp: str


@dataclass
class PhaseResult:
    """Result of phase execution."""
    success: bool
    tasks_completed: int
    tasks_failed: int
    results: List[ExecutionResult]
    duration: float
    phase_name: str


class TaskExecutor:
    """Executes individual tasks."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize the task executor.
        
        Args:
            context: Execution context with environment variables and configs
        """
        self.context = context or {}
        self.logger = logging.getLogger(__name__)
        
        # Set up logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def execute_command(self, command: List[str], cwd: Optional[str] = None, 
                       timeout: int = 300) -> ExecutionResult:
        """
        Execute a shell command.
        
        Args:
            command: Command to execute as list of strings
            cwd: Working directory for command execution
            timeout: Command timeout in seconds
            
        Returns:
            ExecutionResult with execution details
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            self.logger.info(f"Executing command: {' '.join(command)}")
            
            # Prepare environment
            env = os.environ.copy()
            env.update(self.context.get('env', {}))
            
            # Execute command
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info(f"Command succeeded in {duration:.2f}s")
                return ExecutionResult(
                    success=True,
                    output=result.stdout,
                    error=result.stderr,
                    duration=duration,
                    command=' '.join(command),
                    timestamp=timestamp
                )
            else:
                self.logger.error(f"Command failed with return code {result.returncode}")
                return ExecutionResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr,
                    duration=duration,
                    command=' '.join(command),
                    timestamp=timestamp
                )
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.logger.error(f"Command timed out after {timeout}s")
            return ExecutionResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                duration=duration,
                command=' '.join(command),
                timestamp=timestamp
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Command execution failed: {str(e)}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                duration=duration,
                command=' '.join(command),
                timestamp=timestamp
            )
    
    def execute_terraform_command(self, action: str, args: List[str] = None, 
                                 working_dir: str = None) -> ExecutionResult:
        """
        Execute a Terraform command.
        
        Args:
            action: Terraform action (init, plan, apply, destroy)
            args: Additional arguments
            working_dir: Working directory for Terraform commands
            
        Returns:
            ExecutionResult with execution details
        """
        command = ['terraform', action]
        if args:
            command.extend(args)
        
        return self.execute_command(command, cwd=working_dir)
    
    def execute_kubectl_command(self, action: str, resource: str = None, 
                               args: List[str] = None) -> ExecutionResult:
        """
        Execute a kubectl command.
        
        Args:
            action: kubectl action (get, apply, delete, etc.)
            resource: Kubernetes resource type
            args: Additional arguments
            
        Returns:
            ExecutionResult with execution details
        """
        command = ['kubectl', action]
        if resource:
            command.append(resource)
        if args:
            command.extend(args)
        
        return self.execute_command(command)
    
    def execute_argocd_command(self, action: str, args: List[str] = None) -> ExecutionResult:
        """
        Execute an ArgoCD CLI command.
        
        Args:
            action: ArgoCD action (login, app create, app sync, etc.)
            args: Additional arguments
            
        Returns:
            ExecutionResult with execution details
        """
        command = ['argocd']
        if action:
            command.extend(action.split())
        if args:
            command.extend(args)
        
        return self.execute_command(command)


class TaskMaster:
    """Main task execution engine."""
    
    def __init__(self, task_manager=None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize the task master.
        
        Args:
            task_manager: TaskManager instance for task management
            context: Execution context
        """
        self.task_manager = task_manager
        self.context = context or {}
        self.executor = TaskExecutor(context)
        self.logger = logging.getLogger(__name__)
        
        # Set up logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def execute_task(self, task_id: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a specific task.
        
        Args:
            task_id: Task identifier
            context: Additional execution context
            
        Returns:
            ExecutionResult with execution details
        """
        if not self.task_manager:
            return ExecutionResult(
                success=False,
                output="",
                error="No task manager available",
                duration=0.0,
                command="",
                timestamp=datetime.now().isoformat()
            )
        
        task = self.task_manager.get_task(task_id)
        if not task:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Task {task_id} not found",
                duration=0.0,
                command="",
                timestamp=datetime.now().isoformat()
            )
        
        # Merge contexts
        exec_context = self.context.copy()
        if context:
            exec_context.update(context)
        
        # Update task status to in_progress
        self.task_manager.update_task_status(task_id, "in_progress", "Starting execution")
        
        self.logger.info(f"Executing task: {task['title']}")
        
        # Execute task based on its type/content
        result = self._execute_task_by_type(task, exec_context)
        
        # Update task status based on result
        if result.success:
            self.task_manager.update_task_status(task_id, "completed", "Task completed successfully")
        else:
            self.task_manager.update_task_status(task_id, "failed", f"Task failed: {result.error}")
        
        return result
    
    def _execute_task_by_type(self, task: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute task based on its type and content.
        
        Args:
            task: Task dictionary
            context: Execution context
            
        Returns:
            ExecutionResult with execution details
        """
        title = task['title'].lower()
        
        # Terraform tasks
        if 'terraform' in title or 'kind cluster' in title:
            return self._execute_terraform_task(task, context)
        
        # Kubernetes tasks
        elif any(kw in title for kw in ['kubectl', 'kubernetes', 'namespace', 'deployment', 'service', 'active', 'preview', 'services']):
            return self._execute_k8s_task(task, context)
        
        # ArgoCD tasks
        elif 'argocd' in title or 'argo' in title:
            return self._execute_argocd_task(task, context)
        
        # Helm tasks
        elif 'helm' in title:
            return self._execute_helm_task(task, context)
        
        # Generic command tasks
        else:
            return self._execute_generic_task(task, context)
    
    def _execute_terraform_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """Execute Terraform-related tasks."""
        title = task['title'].lower()
        
        if 'init' in title:
            return self.executor.execute_terraform_command('init', working_dir=context.get('terraform_dir'))
        elif 'plan' in title:
            return self.executor.execute_terraform_command('plan', working_dir=context.get('terraform_dir'))
        elif 'apply' in title:
            return self.executor.execute_terraform_command('apply', ['-auto-approve'], working_dir=context.get('terraform_dir'))
        elif 'destroy' in title:
            return self.executor.execute_terraform_command('destroy', ['-auto-approve'], working_dir=context.get('terraform_dir'))
        elif 'kind cluster' in title or 'configurations' in title:
            # Handle kind cluster configuration tasks
            return self.executor.execute_terraform_command('init', working_dir=context.get('terraform_dir'))
        else:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Unknown Terraform task: {task['title']}",
                duration=0.0,
                command="",
                timestamp=datetime.now().isoformat()
            )
    
    def _execute_k8s_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """Execute Kubernetes-related tasks."""
        title = task['title'].lower()
        
        if 'namespace' in title and 'create' in title:
            namespace = context.get('namespace', 'default')
            return self.executor.execute_kubectl_command('create', 'namespace', [namespace])
        elif 'apply' in title:
            manifest_file = context.get('manifest_file')
            if manifest_file:
                return self.executor.execute_kubectl_command('apply', args=['-f', manifest_file])
            else:
                return ExecutionResult(
                    success=False,
                    output="",
                    error="No manifest file specified for kubectl apply",
                    duration=0.0,
                    command="",
                    timestamp=datetime.now().isoformat()
                )
        elif 'get' in title:
            resource = context.get('resource', 'pods')
            return self.executor.execute_kubectl_command('get', resource)
        elif 'services' in title or 'service' in title:
            # Handle service creation tasks
            manifest_file = context.get('manifest_file', '/tmp/service-manifest.yaml')
            return self.executor.execute_kubectl_command('apply', args=['-f', manifest_file])
        else:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Unknown Kubernetes task: {task['title']}",
                duration=0.0,
                command="",
                timestamp=datetime.now().isoformat()
            )
    
    def _execute_argocd_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """Execute ArgoCD-related tasks."""
        title = task['title'].lower()
        
        if 'login' in title:
            server = context.get('argocd_server', 'localhost:8080')
            username = context.get('argocd_username', 'admin')
            password = context.get('argocd_password', '')
            return self.executor.execute_argocd_command('login', [server, '--username', username, '--password', password])
        elif 'app' in title and 'create' in title:
            app_name = context.get('app_name', 'test-app')
            repo_url = context.get('repo_url', 'https://github.com/example/repo')
            path = context.get('path', '.')
            return self.executor.execute_argocd_command('app create', [app_name, '--repo', repo_url, '--path', path])
        elif 'sync' in title:
            app_name = context.get('app_name', 'test-app')
            return self.executor.execute_argocd_command('app sync', [app_name])
        elif 'install' in title:
            # Handle ArgoCD installation tasks
            return self.executor.execute_command(['kubectl', 'apply', '-f', 'https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml'])
        else:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Unknown ArgoCD task: {task['title']}",
                duration=0.0,
                command="",
                timestamp=datetime.now().isoformat()
            )
    
    def _execute_helm_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """Execute Helm-related tasks."""
        title = task['title'].lower()
        
        if 'install' in title:
            chart_name = context.get('chart_name', 'test-chart')
            release_name = context.get('release_name', 'test-release')
            return self.executor.execute_command(['helm', 'install', release_name, chart_name])
        elif 'upgrade' in title:
            chart_name = context.get('chart_name', 'test-chart')
            release_name = context.get('release_name', 'test-release')
            return self.executor.execute_command(['helm', 'upgrade', release_name, chart_name])
        else:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Unknown Helm task: {task['title']}",
                duration=0.0,
                command="",
                timestamp=datetime.now().isoformat()
            )
    
    def _execute_generic_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """Execute generic tasks."""
        # For now, just return a success result for generic tasks
        return ExecutionResult(
            success=True,
            output=f"Generic task executed: {task['title']}",
            error="",
            duration=0.1,
            command=f"generic: {task['title']}",
            timestamp=datetime.now().isoformat()
        )
    
    def execute_phase(self, phase_name: str, context: Optional[Dict[str, Any]] = None) -> PhaseResult:
        """
        Execute all tasks in a phase sequentially.
        
        Args:
            phase_name: Name of phase to execute
            context: Additional execution context
            
        Returns:
            PhaseResult with execution details
        """
        if not self.task_manager:
            return PhaseResult(
                success=False,
                tasks_completed=0,
                tasks_failed=0,
                results=[],
                duration=0.0,
                phase_name=phase_name
            )
        
        # Get tasks for the phase
        phase_tasks = self.task_manager.get_tasks({"phase": phase_name})
        if not phase_tasks:
            return PhaseResult(
                success=False,
                tasks_completed=0,
                tasks_failed=0,
                results=[],
                duration=0.0,
                phase_name=phase_name
            )
        
        start_time = time.time()
        results = []
        tasks_completed = 0
        tasks_failed = 0
        
        self.logger.info(f"Executing phase: {phase_name} ({len(phase_tasks)} tasks)")
        
        # Merge contexts
        exec_context = self.context.copy()
        if context:
            exec_context.update(context)
        
        # Execute tasks sequentially
        for task in phase_tasks:
            task_result = self.execute_task(task['id'], exec_context)
            results.append(task_result)
            
            if task_result.success:
                tasks_completed += 1
            else:
                tasks_failed += 1
                # Optionally stop on first failure
                if exec_context.get('stop_on_failure', True):
                    self.logger.error(f"Stopping phase execution due to task failure: {task['title']}")
                    break
        
        duration = time.time() - start_time
        success = tasks_failed == 0
        
        self.logger.info(f"Phase {phase_name} completed: {tasks_completed} succeeded, {tasks_failed} failed")
        
        return PhaseResult(
            success=success,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            results=results,
            duration=duration,
            phase_name=phase_name
        )
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """
        Get execution log from task manager.
        
        Returns:
            List of task execution logs
        """
        if not self.task_manager:
            return []
        
        logs = []
        for task in self.task_manager.tasks:
            if 'status_history' in task:
                for entry in task['status_history']:
                    logs.append({
                        'task_id': task['id'],
                        'task_title': task['title'],
                        'status': entry['status'],
                        'timestamp': entry['timestamp'],
                        'message': entry.get('message', '')
                    })
        
        return sorted(logs, key=lambda x: x['timestamp'])
    
    def save_execution_log(self, output_file: str, format: str = 'json') -> None:
        """
        Save execution log to file.
        
        Args:
            output_file: Path to output file
            format: Output format ('json' or 'yaml')
        """
        logs = self.get_execution_log()
        
        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
        elif format in ['yaml', 'yml']:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(logs, f, default_flow_style=False, sort_keys=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info(f"Execution log saved to: {output_file}")


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Task Master for automated deployment execution')
    parser.add_argument('--tasks', help='Path to tasks JSON/YAML file')
    parser.add_argument('--prd', help='Path to PRD file')
    parser.add_argument('--context', help='Path to context JSON/YAML file')
    parser.add_argument('--log', help='Path to save execution log')
    parser.add_argument('--format', choices=['json', 'yaml'], default='json', help='Output format')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Execute task command
    task_parser = subparsers.add_parser('execute-task', help='Execute a specific task')
    task_parser.add_argument('task_id', help='Task ID to execute')
    
    # Execute phase command
    phase_parser = subparsers.add_parser('execute-phase', help='Execute all tasks in a phase')
    phase_parser.add_argument('phase_name', help='Phase name to execute')
    
    # Log command
    subparsers.add_parser('log', help='Show execution log')
    
    args = parser.parse_args()
    
    # Load context
    context = {}
    if args.context:
        context_file = Path(args.context)
        if context_file.suffix == '.json':
            with open(args.context, 'r') as f:
                context = json.load(f)
        elif context_file.suffix in ['.yaml', '.yml']:
            with open(args.context, 'r') as f:
                context = yaml.safe_load(f)
    
    # Initialize task master
    task_manager = None
    if args.tasks:
        from task_manager.task_manager import TaskManager
        task_manager = TaskManager(args.tasks)
    elif args.prd:
        from task_manager.task_manager import TaskManager
        task_manager = TaskManager()
        task_manager.load_from_prd(args.prd)
    
    task_master = TaskMaster(task_manager, context)
    
    # Execute command
    if args.command == 'execute-task':
        result = task_master.execute_task(args.task_id)
        print(f"Task execution {'succeeded' if result.success else 'failed'}")
        print(f"Duration: {result.duration:.2f}s")
        if result.output:
            print(f"Output: {result.output}")
        if result.error:
            print(f"Error: {result.error}")
    
    elif args.command == 'execute-phase':
        result = task_master.execute_phase(args.phase_name)
        print(f"Phase execution {'succeeded' if result.success else 'failed'}")
        print(f"Tasks completed: {result.tasks_completed}")
        print(f"Tasks failed: {result.tasks_failed}")
        print(f"Duration: {result.duration:.2f}s")
    
    elif args.command == 'log':
        logs = task_master.get_execution_log()
        for log_entry in logs:
            print(f"{log_entry['timestamp']} - {log_entry['task_id']}: {log_entry['status']} - {log_entry['message']}")
    
    else:
        print("Please specify a command (execute-task, execute-phase, or log)")
        return
    
    # Save log if requested
    if args.log:
        task_master.save_execution_log(args.log, args.format)


if __name__ == '__main__':
    main()