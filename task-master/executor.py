#!/usr/bin/env python3
"""
Task Executor - Core execution engine for deployment tasks.

This module provides the core execution engine that handles:
- Command execution with proper error handling
- Retry logic with exponential backoff
- Context variable substitution
- Execution logging and monitoring
"""

import subprocess
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import threading
import queue
import signal
import sys


@dataclass
class ExecutionContext:
    """Context for task execution."""
    variables: Dict[str, Any]
    working_directory: Optional[str] = None
    environment: Dict[str, str] = None
    timeout: Optional[int] = None

    def __post_init__(self):
        if self.environment is None:
            self.environment = {}


class CommandExecutor:
    """Executes shell commands with advanced features."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the command executor.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.execution_history: List[Dict[str, Any]] = []
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.shutdown_event = threading.Event()

    def execute(self, command: str, context: ExecutionContext = None) -> Dict[str, Any]:
        """
        Execute a shell command.

        Args:
            command: Command to execute
            context: Execution context

        Returns:
            Dictionary with execution results
        """
        if context is None:
            context = ExecutionContext(variables={})

        # Substitute variables
        substituted_command = self._substitute_variables(command, context.variables)
        
        # Prepare environment
        env = dict(os.environ)
        env.update(context.environment)

        # Prepare working directory
        cwd = context.working_directory
        if cwd:
            cwd = Path(cwd).resolve()

        execution_id = f"exec_{int(time.time() * 1000)}"
        
        self.logger.info(f"Executing command [{execution_id}]: {substituted_command}")
        if cwd:
            self.logger.info(f"Working directory: {cwd}")

        start_time = time.time()
        
        try:
            # Execute command
            process = subprocess.Popen(
                substituted_command,
                shell=True,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Store active process
            self.active_processes[execution_id] = process

            # Wait for completion with timeout
            timeout = context.timeout or 300
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(
                    process.args, timeout, output=stdout, stderr=stderr
                )

            duration = time.time() - start_time
            success = process.returncode == 0

            result = {
                'execution_id': execution_id,
                'command': substituted_command,
                'success': success,
                'exit_code': process.returncode,
                'stdout': stdout,
                'stderr': stderr,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'working_directory': str(cwd) if cwd else None
            }

            if success:
                self.logger.info(f"Command succeeded [{execution_id}] in {duration:.2f}s")
            else:
                self.logger.error(f"Command failed [{execution_id}] with exit code {process.returncode}")
                self.logger.error(f"Error output: {stderr}")

            # Clean up
            del self.active_processes[execution_id]
            self.execution_history.append(result)
            
            return result

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            self.logger.error(f"Command timed out [{execution_id}] after {duration:.2f}s")
            
            # Clean up
            if execution_id in self.active_processes:
                del self.active_processes[execution_id]
            
            result = {
                'execution_id': execution_id,
                'command': substituted_command,
                'success': False,
                'exit_code': -1,
                'stdout': e.stdout or '',
                'stderr': f"Command timed out after {duration:.2f}s",
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'working_directory': str(cwd) if cwd else None
            }
            
            self.execution_history.append(result)
            return result

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Command execution failed [{execution_id}]: {str(e)}")
            
            # Clean up
            if execution_id in self.active_processes:
                del self.active_processes[execution_id]
            
            result = {
                'execution_id': execution_id,
                'command': substituted_command,
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'working_directory': str(cwd) if cwd else None
            }
            
            self.execution_history.append(result)
            return result

    def _substitute_variables(self, command: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in command string."""
        substituted = command
        
        for key, value in variables.items():
            # Support both ${VAR} and $VAR syntax
            placeholder1 = f"${{{key}}}"
            placeholder2 = f"${key}"
            substituted = substituted.replace(placeholder1, str(value))
            substituted = substituted.replace(placeholder2, str(value))
        
        return substituted

    def execute_with_retry(self, command: str, context: ExecutionContext = None,
                          max_attempts: int = 3, delay: float = 5.0,
                          backoff_factor: float = 2.0) -> Dict[str, Any]:
        """
        Execute command with retry logic.

        Args:
            command: Command to execute
            context: Execution context
            max_attempts: Maximum number of attempts
            delay: Initial delay between attempts
            backoff_factor: Backoff multiplier for delays

        Returns:
            Dictionary with execution results
        """
        last_result = None
        current_delay = delay

        for attempt in range(max_attempts):
            self.logger.info(f"Attempt {attempt + 1}/{max_attempts} for command: {command}")
            
            result = self.execute(command, context)
            last_result = result
            
            if result['success']:
                self.logger.info(f"Command succeeded on attempt {attempt + 1}")
                return result
            
            if attempt < max_attempts - 1:
                self.logger.info(f"Waiting {current_delay} seconds before retry...")
                time.sleep(current_delay)
                current_delay *= backoff_factor

        self.logger.error(f"Command failed after {max_attempts} attempts")
        return last_result

    def execute_async(self, command: str, context: ExecutionContext = None,
                      callback: Optional[Callable] = None) -> str:
        """
        Execute command asynchronously.

        Args:
            command: Command to execute
            context: Execution context
            callback: Optional callback function for results

        Returns:
            Execution ID for tracking
        """
        execution_id = f"async_{int(time.time() * 1000)}"
        
        def _async_executor():
            try:
                result = self.execute(command, context)
                if callback:
                    callback(result)
            except Exception as e:
                self.logger.error(f"Async execution failed [{execution_id}]: {str(e)}")
                if callback:
                    callback({
                        'execution_id': execution_id,
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })

        thread = threading.Thread(target=_async_executor, name=f"executor-{execution_id}")
        thread.daemon = True
        thread.start()
        
        return execution_id

    def kill_all_processes(self) -> None:
        """Kill all active processes."""
        for execution_id, process in list(self.active_processes.items()):
            try:
                process.kill()
                self.logger.info(f"Killed process [{execution_id}]")
            except Exception as e:
                self.logger.error(f"Failed to kill process [{execution_id}]: {str(e)}")
        
        self.active_processes.clear()

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history."""
        return self.execution_history.copy()

    def clear_history(self) -> None:
        """Clear execution history."""
        self.execution_history.clear()

    def shutdown(self) -> None:
        """Shutdown the executor."""
        self.shutdown_event.set()
        self.kill_all_processes()


class TaskExecutor:
    """High-level task executor with workflow support."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the task executor.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.command_executor = CommandExecutor(logger)
        self.task_registry: Dict[str, Callable] = {}
        self.workflow_registry: Dict[str, List[str]] = {}

    def register_task(self, task_id: str, task_function: Callable) -> None:
        """
        Register a task function.

        Args:
            task_id: Task identifier
            task_function: Function to execute for the task
        """
        self.task_registry[task_id] = task_function
        self.logger.info(f"Registered task: {task_id}")

    def register_workflow(self, workflow_id: str, task_sequence: List[str]) -> None:
        """
        Register a workflow (sequence of tasks).

        Args:
            workflow_id: Workflow identifier
            task_sequence: List of task IDs in execution order
        """
        self.workflow_registry[workflow_id] = task_sequence
        self.logger.info(f"Registered workflow: {workflow_id} with {len(task_sequence)} tasks")

    def execute_task(self, task_id: str, context: ExecutionContext = None) -> Dict[str, Any]:
        """
        Execute a registered task.

        Args:
            task_id: Task identifier
            context: Execution context

        Returns:
            Dictionary with execution results
        """
        if task_id not in self.task_registry:
            error_msg = f"Unknown task: {task_id}"
            self.logger.error(error_msg)
            return {
                'task_id': task_id,
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }

        self.logger.info(f"Executing task: {task_id}")
        
        try:
            task_function = self.task_registry[task_id]
            result = task_function(self.command_executor, context or ExecutionContext(variables={}))
            
            if isinstance(result, dict):
                result['task_id'] = task_id
                result['timestamp'] = datetime.now().isoformat()
            else:
                result = {
                    'task_id': task_id,
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            error_msg = f"Task execution failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'task_id': task_id,
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }

    def execute_workflow(self, workflow_id: str, context: ExecutionContext = None) -> Dict[str, Any]:
        """
        Execute a registered workflow.

        Args:
            workflow_id: Workflow identifier
            context: Execution context

        Returns:
            Dictionary with workflow execution results
        """
        if workflow_id not in self.workflow_registry:
            error_msg = f"Unknown workflow: {workflow_id}"
            self.logger.error(error_msg)
            return {
                'workflow_id': workflow_id,
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }

        self.logger.info(f"Executing workflow: {workflow_id}")
        
        task_sequence = self.workflow_registry[workflow_id]
        results = []
        start_time = time.time()
        
        for task_id in task_sequence:
            result = self.execute_task(task_id, context)
            results.append(result)
            
            if not result.get('success', False):
                self.logger.error(f"Workflow {workflow_id} failed at task {task_id}")
                break
        
        duration = time.time() - start_time
        success = all(result.get('success', False) for result in results)
        
        return {
            'workflow_id': workflow_id,
            'success': success,
            'tasks_executed': len(results),
            'tasks_succeeded': sum(1 for r in results if r.get('success', False)),
            'tasks_failed': sum(1 for r in results if not r.get('success', False)),
            'duration': duration,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    def get_task_list(self) -> List[str]:
        """Get list of registered task IDs."""
        return list(self.task_registry.keys())

    def get_workflow_list(self) -> List[str]:
        """Get list of registered workflow IDs."""
        return list(self.workflow_registry.keys())

    def shutdown(self) -> None:
        """Shutdown the task executor."""
        self.command_executor.shutdown()


# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\nReceived signal {signum}, shutting down...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    executor = TaskExecutor()
    
    # Register a simple task
    def hello_task(cmd_executor, context):
        return cmd_executor.execute("echo 'Hello from task executor!'")
    
    executor.register_task('hello', hello_task)
    
    # Execute the task
    result = executor.execute_task('hello')
    print(f"Task result: {result}")
    
    executor.shutdown()
