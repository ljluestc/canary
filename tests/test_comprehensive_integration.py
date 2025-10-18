"""
Comprehensive Integration Test Suite
Tests component interactions and system-wide functionality
"""

import unittest
import tempfile
import os
import json
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import time
import threading
import concurrent.futures
import gc
import psutil

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "task-manager"))
sys.path.insert(0, str(project_root / "task-master"))

from prd_parser import PRDParser, Task, Phase, TaskStatus, Priority, PRDMetadata
from task_manager import TaskManager
from task_master import TaskMaster, TaskExecutor

class TestSystemIntegration(unittest.TestCase):
    """Comprehensive system integration tests"""
    
    def setUp(self):
        self.parser = PRDParser()
        self.manager = TaskManager()
        self.executor = TaskExecutor()
        self.master = TaskMaster(self.executor)
        
        self.sample_prd_content = """# Canary Deployment System PRD

## 1. Executive Summary
This document outlines the requirements for a comprehensive canary deployment system.

## 2. System Architecture
- Blue-Green Deployment
- Canary Deployment
- GitOps Integration
- Monitoring and Alerting

## 3. Feature Requirements

### 3.1 Blue-Green Deployment
- [ ] Set up blue environment
- [ ] Set up green environment
- [ ] Implement traffic switching
- [ ] Add rollback capability

### 3.2 Canary Deployment
- [ ] Implement traffic splitting
- [ ] Add automated analysis
- [ ] Create rollback triggers
- [ ] Monitor canary metrics

### 3.3 GitOps Integration
- [ ] Install ArgoCD
- [ ] Configure Git repositories
- [ ] Set up automated sync
- [ ] Add approval workflows

## 4. Implementation Phases

### Phase 1: Infrastructure Setup
- [ ] Create Kubernetes cluster
- [ ] Install Terraform
- [ ] Configure monitoring
- [ ] Set up logging

### Phase 2: Blue-Green Implementation
- [ ] Deploy blue environment
- [ ] Deploy green environment
- [ ] Test traffic switching
- [ ] Validate rollback

### Phase 3: Canary Implementation
- [ ] Implement traffic splitting
- [ ] Add analysis engine
- [ ] Create monitoring dashboards
- [ ] Test rollback scenarios
"""
        
        # Create temporary PRD file
        self.temp_dir = tempfile.mkdtemp()
        self.prd_file = os.path.join(self.temp_dir, "test_prd.md")
        with open(self.prd_file, 'w') as f:
            f.write(self.sample_prd_content)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_prd_to_task_manager_integration(self):
        """Test PRD parser to Task Manager integration"""
        # Parse PRD
        prd_data = self.parser.parse_prd(self.prd_file)
        self.assertIsNotNone(prd_data)
        
        # Extract tasks
        tasks = self.parser.extract_tasks(self.sample_prd_content)
        self.assertGreater(len(tasks), 0)
        
        # Add tasks to manager
        for task in tasks:
            self.manager.add_task(task)
        
        # Verify integration
        self.assertEqual(len(self.manager.tasks), len(tasks))
        
        # Test task status updates
        for task in self.manager.tasks.values():
            self.manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)
        
        in_progress_tasks = self.manager.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        self.assertEqual(len(in_progress_tasks), len(tasks))
    
    def test_task_manager_to_task_master_integration(self):
        """Test Task Manager to Task Master integration"""
        # Create test tasks
        task1 = Task("int-1", "Terraform init", "Initialize Terraform", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("int-2", "Create namespace", "Create Kubernetes namespace", Priority.MEDIUM, TaskStatus.PENDING)
        task3 = Task("int-3", "Install ArgoCD", "Install ArgoCD", Priority.HIGH, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_task(task3)
        
        # Execute tasks through Task Master
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in self.manager.tasks.values():
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        completed_tasks = self.manager.get_tasks_by_status(TaskStatus.COMPLETED)
        self.assertEqual(len(completed_tasks), 3)
    
    def test_complete_workflow_integration(self):
        """Test complete workflow integration"""
        # Step 1: Parse PRD
        prd_data = self.parser.parse_prd(self.prd_file)
        self.assertIsNotNone(prd_data)
        
        # Step 2: Extract tasks and phases
        tasks = self.parser.extract_tasks(self.sample_prd_content)
        phases = self.parser.extract_phases(self.sample_prd_content)
        
        self.assertGreater(len(tasks), 0)
        self.assertGreater(len(phases), 0)
        
        # Step 3: Add tasks to manager
        for task in tasks:
            self.manager.add_task(task)
        
        # Step 4: Execute tasks through Task Master
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in self.manager.tasks.values():
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        # Step 5: Verify workflow completion
        progress = self.manager.get_progress_report()
        self.assertGreater(progress['total_tasks'], 0)
        self.assertGreater(progress['completed_tasks'], 0)
    
    def test_error_propagation_integration(self):
        """Test error propagation across components"""
        # Create failing task
        failing_task = Task("fail-1", "Failing task", "Task that will fail", Priority.HIGH, TaskStatus.PENDING)
        self.manager.add_task(failing_task)
        
        # Execute with failure
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout=b'', stderr=b'Error occurred')
            
            result = self.master.execute_task(failing_task, {})
            self.assertFalse(result.success)
            
            # Task status should remain PENDING
            self.assertEqual(self.manager.get_task("fail-1").status, TaskStatus.PENDING)
    
    def test_data_persistence_integration(self):
        """Test data persistence across components"""
        # Create tasks
        task1 = Task("persist-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("persist-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.IN_PROGRESS)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        
        # Save tasks
        tasks_file = os.path.join(self.temp_dir, "tasks.json")
        self.manager.save_tasks(tasks_file)
        
        # Create new manager and load tasks
        new_manager = TaskManager()
        new_manager.load_tasks(tasks_file)
        
        # Verify data persistence
        self.assertEqual(len(new_manager.tasks), 2)
        self.assertIn("persist-1", new_manager.tasks)
        self.assertIn("persist-2", new_manager.tasks)
        self.assertEqual(new_manager.get_task("persist-2").status, TaskStatus.IN_PROGRESS)
    
    def test_phase_execution_integration(self):
        """Test phase execution integration"""
        # Create phase with tasks
        task1 = Task("phase-1", "Phase Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("phase-2", "Phase Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        
        phase = Phase("phase-1", "Test Phase", "Test Phase Description", [task1, task2])
        
        # Execute phase
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.master.execute_phase(phase, {})
            self.assertTrue(result.success)
    
    def test_dependency_management_integration(self):
        """Test dependency management integration"""
        # Create tasks with dependencies
        task1 = Task("dep-1", "Dependency Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("dep-2", "Dependency Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        task3 = Task("dep-3", "Dependency Task 3", "Description 3", Priority.LOW, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_task(task3)
        
        # Add dependencies
        self.manager.add_dependency("dep-2", "dep-1")
        self.manager.add_dependency("dep-3", "dep-2")
        
        # Verify dependencies
        deps_2 = self.manager.get_task_dependencies("dep-2")
        deps_3 = self.manager.get_task_dependencies("dep-3")
        
        self.assertIn("dep-1", deps_2)
        self.assertIn("dep-2", deps_3)
        
        # Test dependency resolution
        dependents_1 = self.manager.get_dependents("dep-1")
        self.assertIn("dep-2", dependents_1)
    
    def test_concurrent_operations_integration(self):
        """Test concurrent operations integration"""
        def add_and_execute_task(task_id):
            task = Task(f"concurrent-{task_id}", f"Concurrent Task {task_id}", f"Description {task_id}", Priority.MEDIUM, TaskStatus.PENDING)
            self.manager.add_task(task)
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
                
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
            
            return result.success
        
        # Run concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_and_execute_task, i) for i in range(100)]
            results = [future.result() for future in futures]
        
        # Verify results
        self.assertEqual(len(results), 100)
        self.assertEqual(len(self.manager.tasks), 100)
        
        completed_tasks = self.manager.get_tasks_by_status(TaskStatus.COMPLETED)
        self.assertEqual(len(completed_tasks), 100)
    
    def test_memory_management_integration(self):
        """Test memory management integration"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many tasks and execute them
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for i in range(1000):
                task = Task(f"memory-{i}", f"Memory Task {i}", f"Description {i}", Priority.MEDIUM, TaskStatus.PENDING)
                self.manager.add_task(task)
                
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 100)  # Less than 100MB increase
        
        # Clean up
        del self.manager
        del self.master
        gc.collect()
    
    def test_performance_integration(self):
        """Test performance integration"""
        start_time = time.time()
        
        # Parse large PRD
        large_prd_content = self.sample_prd_content * 100
        prd_data = self.parser.parse_prd_content(large_prd_content)
        
        # Extract tasks
        tasks = self.parser.extract_tasks(large_prd_content)
        
        # Add tasks to manager
        for task in tasks:
            self.manager.add_task(task)
        
        # Execute tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in self.manager.tasks.values():
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance should be reasonable
        self.assertLess(execution_time, 10.0)  # Less than 10 seconds
    
    def test_error_recovery_integration(self):
        """Test error recovery integration"""
        # Create task that will fail
        failing_task = Task("recovery-1", "Recovery Task", "Task that will fail", Priority.HIGH, TaskStatus.PENDING)
        self.manager.add_task(failing_task)
        
        # Execute with failure
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout=b'', stderr=b'Error occurred')
            
            result = self.master.execute_task(failing_task, {})
            self.assertFalse(result.success)
        
        # Retry with success
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.master.execute_task(failing_task, {})
            self.assertTrue(result.success)
            
            if result.success:
                self.manager.update_task_status(failing_task.id, TaskStatus.COMPLETED)
        
        # Verify recovery
        self.assertEqual(self.manager.get_task("recovery-1").status, TaskStatus.COMPLETED)
    
    def test_context_propagation_integration(self):
        """Test context propagation integration"""
        # Set initial context
        initial_context = {"ENV": "production", "REGION": "us-west-2"}
        self.master.context = initial_context.copy()
        
        # Create task
        task = Task("context-1", "Context Task", "Task with context", Priority.HIGH, TaskStatus.PENDING)
        self.manager.add_task(task)
        
        # Execute task with additional context
        task_context = {"WORKING_DIR": "/tmp", "LOG_LEVEL": "debug"}
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.master.execute_task(task, task_context)
            self.assertTrue(result.success)
        
        # Verify context propagation
        self.assertEqual(self.master.context["ENV"], "production")
        self.assertEqual(self.master.context["REGION"], "us-west-2")
        self.assertEqual(self.master.context["WORKING_DIR"], "/tmp")
        self.assertEqual(self.master.context["LOG_LEVEL"], "debug")
    
    def test_logging_integration(self):
        """Test logging integration"""
        # Create task
        task = Task("log-1", "Logging Task", "Task for logging test", Priority.HIGH, TaskStatus.PENDING)
        self.manager.add_task(task)
        
        # Execute task with logging
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.master.execute_task(task, {})
            self.assertTrue(result.success)
        
        # Verify logging (this would require actual logging verification in a real implementation)
        self.assertTrue(result.success)
    
    def test_metrics_collection_integration(self):
        """Test metrics collection integration"""
        # Create tasks
        tasks = [
            Task(f"metrics-{i}", f"Metrics Task {i}", f"Description {i}", Priority.MEDIUM, TaskStatus.PENDING)
            for i in range(10)
        ]
        
        for task in tasks:
            self.manager.add_task(task)
        
        # Execute tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in tasks:
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        # Collect metrics
        progress = self.manager.get_progress_report()
        
        # Verify metrics
        self.assertEqual(progress['total_tasks'], 10)
        self.assertEqual(progress['completed_tasks'], 10)
        self.assertEqual(progress['pending_tasks'], 0)
        self.assertEqual(progress['in_progress_tasks'], 0)
    
    def test_system_resilience_integration(self):
        """Test system resilience integration"""
        # Create tasks
        tasks = [
            Task(f"resilience-{i}", f"Resilience Task {i}", f"Description {i}", Priority.MEDIUM, TaskStatus.PENDING)
            for i in range(100)
        ]
        
        for task in tasks:
            self.manager.add_task(task)
        
        # Execute tasks with some failures
        with patch('subprocess.run') as mock_run:
            def mock_run_side_effect(*args, **kwargs):
                # Simulate some failures
                if "resilience-50" in str(args):
                    return Mock(returncode=1, stdout=b'', stderr=b'Error')
                return Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            mock_run.side_effect = mock_run_side_effect
            
            for task in tasks:
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        # Verify resilience
        completed_tasks = self.manager.get_tasks_by_status(TaskStatus.COMPLETED)
        self.assertEqual(len(completed_tasks), 99)  # One task should have failed
        
        pending_tasks = self.manager.get_tasks_by_status(TaskStatus.PENDING)
        self.assertEqual(len(pending_tasks), 1)  # One task should remain pending


class TestComponentIntegration(unittest.TestCase):
    """Test individual component integrations"""
    
    def setUp(self):
        self.parser = PRDParser()
        self.manager = TaskManager()
        self.executor = TaskExecutor()
        self.master = TaskMaster(self.executor)
    
    def test_prd_parser_task_manager_integration(self):
        """Test PRD parser to Task Manager integration"""
        content = """# Test PRD
## Features
- [ ] Feature 1
- [x] Feature 2
"""
        
        # Parse PRD
        prd_data = self.parser.parse_prd_content(content)
        tasks = self.parser.extract_tasks(content)
        
        # Add to manager
        for task in tasks:
            self.manager.add_task(task)
        
        # Verify integration
        self.assertEqual(len(self.manager.tasks), 2)
        
        # Test task status updates
        for task in self.manager.tasks.values():
            if task.status == TaskStatus.PENDING:
                self.manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)
        
        in_progress_tasks = self.manager.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        self.assertEqual(len(in_progress_tasks), 1)
    
    def test_task_manager_task_master_integration(self):
        """Test Task Manager to Task Master integration"""
        # Create tasks
        task1 = Task("tm-1", "Terraform init", "Initialize Terraform", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("tm-2", "Create namespace", "Create Kubernetes namespace", Priority.MEDIUM, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        
        # Execute through Task Master
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in self.manager.tasks.values():
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        # Verify integration
        completed_tasks = self.manager.get_tasks_by_status(TaskStatus.COMPLETED)
        self.assertEqual(len(completed_tasks), 2)
    
    def test_task_executor_task_master_integration(self):
        """Test Task Executor to Task Master integration"""
        # Create task
        task = Task("te-1", "Test task", "Test description", Priority.HIGH, TaskStatus.PENDING)
        
        # Execute through Task Master
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.master.execute_task(task, {})
            self.assertTrue(result.success)
    
    def test_data_flow_integration(self):
        """Test data flow integration"""
        # Create PRD content
        content = """# Test PRD
## Phase 1
- [ ] Task 1.1
- [ ] Task 1.2
## Phase 2
- [ ] Task 2.1
- [x] Task 2.2
"""
        
        # Parse PRD
        prd_data = self.parser.parse_prd_content(content)
        tasks = self.parser.extract_tasks(content)
        phases = self.parser.extract_phases(content)
        
        # Add tasks to manager
        for task in tasks:
            self.manager.add_task(task)
        
        # Execute tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in self.manager.tasks.values():
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        # Verify data flow
        progress = self.manager.get_progress_report()
        self.assertEqual(progress['total_tasks'], 4)
        self.assertEqual(progress['completed_tasks'], 4)
    
    def test_error_handling_integration(self):
        """Test error handling integration"""
        # Create task
        task = Task("error-1", "Error task", "Task that will fail", Priority.HIGH, TaskStatus.PENDING)
        self.manager.add_task(task)
        
        # Execute with failure
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout=b'', stderr=b'Error occurred')
            
            result = self.master.execute_task(task, {})
            self.assertFalse(result.success)
        
        # Task should remain pending
        self.assertEqual(self.manager.get_task("error-1").status, TaskStatus.PENDING)
    
    def test_performance_integration(self):
        """Test performance integration"""
        start_time = time.time()
        
        # Create many tasks
        tasks = [
            Task(f"perf-{i}", f"Performance Task {i}", f"Description {i}", Priority.MEDIUM, TaskStatus.PENDING)
            for i in range(1000)
        ]
        
        # Add to manager
        for task in tasks:
            self.manager.add_task(task)
        
        # Execute tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in tasks:
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance should be reasonable
        self.assertLess(execution_time, 5.0)  # Less than 5 seconds


if __name__ == '__main__':
    # Run comprehensive integration tests
    unittest.main(verbosity=2)
