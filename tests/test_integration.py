"""
Integration tests for the task management system.
"""

import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
from task_manager import TaskManager
from prd_parser import PRDParser
from task_master import TaskMaster


class TestTaskManagementIntegration:
    """Integration tests for the complete task management system."""
    
    def test_prd_to_task_manager_integration(self, temp_prd_file):
        """Test integration between PRD parser and task manager."""
        # Parse PRD
        parser = PRDParser(temp_prd_file)
        parsed_data = parser.parse()
        
        # Load into task manager
        task_manager = TaskManager()
        task_manager.metadata = parsed_data['metadata']
        task_manager.phases = parsed_data['phases']
        task_manager.tasks = parsed_data['tasks']
        
        # Verify integration
        assert len(task_manager.tasks) > 0
        assert len(task_manager.phases) > 0
        assert task_manager.metadata['title'] == "Test Product Requirements Document"
        
        # Test task operations
        task = task_manager.get_task(task_manager.tasks[0]['id'])
        assert task is not None
        assert task['id'] == task_manager.tasks[0]['id']
        
        # Test filtering
        critical_tasks = task_manager.get_tasks({"priority": "critical"})
        assert len(critical_tasks) > 0
        
        # Test status updates
        success = task_manager.update_task_status(task['id'], "in_progress", "Testing integration")
        assert success is True
        
        updated_task = task_manager.get_task(task['id'])
        assert updated_task['status'] == "in_progress"
        assert len(updated_task['status_history']) == 1
    
    def test_task_manager_to_task_master_integration(self, temp_prd_file):
        """Test integration between task manager and task master."""
        # Set up task manager
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Set up task master
        context = {
            "terraform_dir": "/tmp/terraform",
            "namespace": "test-namespace",
            "argocd_server": "localhost:8080"
        }
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        # Verify integration
        assert task_master.task_manager == task_manager
        assert task_master.context == context
        assert len(task_master.task_manager.tasks) > 0
        
        # Test task execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
            
            task_id = task_manager.tasks[0]['id']
            result = task_master.execute_task(task_id)
            
            assert result.success is True
            assert result.output == "Success"
            
            # Verify task status was updated
            task = task_manager.get_task(task_id)
            assert task['status'] == "completed"
    
    def test_end_to_end_task_lifecycle(self, temp_prd_file):
        """Test complete task lifecycle from PRD to execution."""
        # Step 1: Parse PRD
        parser = PRDParser(temp_prd_file)
        parsed_data = parser.parse()
        
        # Step 2: Load into task manager
        task_manager = TaskManager()
        task_manager.metadata = parsed_data['metadata']
        task_manager.phases = parsed_data['phases']
        task_manager.tasks = parsed_data['tasks']
        
        # Step 3: Set up task master
        task_master = TaskMaster(task_manager=task_manager)
        
        # Step 4: Execute tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Command executed", stderr="")
            
            # Execute first few tasks
            for i, task in enumerate(task_manager.tasks[:3]):
                result = task_master.execute_task(task['id'])
                assert result.success is True
                
                # Verify task status
                updated_task = task_manager.get_task(task['id'])
                assert updated_task['status'] == "completed"
        
        # Step 5: Generate progress report
        report = task_manager.get_progress_report()
        assert report['completed'] >= 3
        assert report['progress_percentage'] > 0
        
        # Step 6: Get execution log
        logs = task_master.get_execution_log()
        assert len(logs) >= 3
        
        # Step 7: Save execution log
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            task_master.save_execution_log(temp_file.name)
            
            with open(temp_file.name, 'r') as f:
                saved_logs = json.load(f)
            
            assert len(saved_logs) >= 3
            os.unlink(temp_file.name)
    
    def test_phase_execution_integration(self, temp_prd_file):
        """Test complete phase execution integration."""
        # Set up system
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        # Execute a phase
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Phase task executed", stderr="")
            
            phase_result = task_master.execute_phase("Infrastructure Setup")
            
            assert phase_result.success is True
            assert phase_result.tasks_completed > 0
            assert phase_result.tasks_failed == 0
            assert len(phase_result.results) > 0
            assert phase_result.duration > 0
        
        # Verify all tasks in phase are completed
        phase_tasks = task_manager.get_tasks({"phase": "Infrastructure Setup"})
        for task in phase_tasks:
            assert task['status'] == "completed"
    
    def test_task_dependencies_integration(self, temp_prd_file):
        """Test task dependencies integration."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Add dependencies to tasks
        if len(task_manager.tasks) >= 2:
            task_manager.tasks[1]['dependencies'] = [task_manager.tasks[0]['id']]
            
            # Test dependency checking
            can_start = task_manager.can_start_task(task_manager.tasks[1]['id'])
            assert can_start is False  # Dependency not completed
            
            # Complete dependency
            task_manager.update_task_status(task_manager.tasks[0]['id'], "completed")
            
            # Now should be able to start
            can_start = task_manager.can_start_task(task_manager.tasks[1]['id'])
            assert can_start is True
            
            # Test next tasks
            next_tasks = task_manager.get_next_tasks()
            task_ids = [task['id'] for task in next_tasks]
            assert task_manager.tasks[1]['id'] in task_ids
    
    def test_error_handling_integration(self, temp_prd_file):
        """Test error handling across the system."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        # Test task execution failure
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="Command failed")
            
            task_id = task_manager.tasks[0]['id']
            result = task_master.execute_task(task_id)
            
            assert result.success is False
            assert "Command failed" in result.error
            
            # Verify task status
            task = task_manager.get_task(task_id)
            assert task['status'] == "failed"
    
    def test_data_persistence_integration(self, temp_prd_file):
        """Test data persistence across the system."""
        # Parse and load PRD
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Update some task statuses
        task_manager.update_task_status(task_manager.tasks[0]['id'], "completed", "Test completed")
        task_manager.update_task_status(task_manager.tasks[1]['id'], "in_progress", "Test in progress")
        
        # Save to file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            task_manager.save_tasks(temp_file.name, 'json')
            
            # Load from file
            new_task_manager = TaskManager(temp_file.name)
            
            # Verify data persistence
            assert len(new_task_manager.tasks) == len(task_manager.tasks)
            assert new_task_manager.metadata['title'] == task_manager.metadata['title']
            
            # Check task statuses
            task1 = new_task_manager.get_task(task_manager.tasks[0]['id'])
            task2 = new_task_manager.get_task(task_manager.tasks[1]['id'])
            
            assert task1['status'] == "completed"
            assert task2['status'] == "in_progress"
            
            # Check status history
            assert len(task1['status_history']) == 1
            assert task1['status_history'][0]['message'] == "Test completed"
            
            os.unlink(temp_file.name)
    
    def test_concurrent_task_execution_simulation(self, temp_prd_file):
        """Test simulation of concurrent task execution."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        # Simulate concurrent execution by executing multiple tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Concurrent execution", stderr="")
            
            # Execute multiple tasks
            results = []
            for task in task_manager.tasks[:3]:
                result = task_master.execute_task(task['id'])
                results.append(result)
            
            # All should succeed
            for result in results:
                assert result.success is True
            
            # Check final state
            completed_tasks = task_manager.get_tasks({"status": "completed"})
            assert len(completed_tasks) >= 3
    
    def test_system_resilience(self, temp_prd_file):
        """Test system resilience to various error conditions."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        # Test with invalid context
        invalid_context = {"invalid_key": "invalid_value"}
        
        # Mock command execution to avoid real command execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Generic task executed", stderr="")
            
            result = task_master.execute_task(task_manager.tasks[0]['id'], invalid_context)
            
            # Should still work (generic task execution)
            assert result.success is True
        
        # Test with missing task manager
        task_master_no_tm = TaskMaster()
        result = task_master_no_tm.execute_task("nonexistent")
        assert result.success is False
        assert "No task manager available" in result.error
        
        # Test with empty task list
        empty_task_manager = TaskManager()
        task_master_empty = TaskMaster(task_manager=empty_task_manager)
        result = task_master_empty.execute_phase("Empty Phase")
        assert result.success is False
        assert result.tasks_completed == 0
    
    def test_performance_characteristics(self, temp_prd_file):
        """Test performance characteristics of the system."""
        import time
        
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        # Test task execution performance
        start_time = time.time()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Fast execution", stderr="")
            
            # Execute multiple tasks
            for task in task_manager.tasks[:5]:
                result = task_master.execute_task(task['id'])
                assert result.success is True
        
        execution_time = time.time() - start_time
        
        # Should complete quickly (under 1 second for mocked commands)
        assert execution_time < 1.0
        
        # Test progress report generation performance
        start_time = time.time()
        report = task_manager.get_progress_report()
        report_time = time.time() - start_time
        
        # Should generate report quickly
        assert report_time < 0.1
        assert report['total_tasks'] > 0
    
    def test_system_scalability(self, temp_prd_file):
        """Test system scalability with larger datasets."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Simulate larger dataset by duplicating tasks
        original_tasks = task_manager.tasks.copy()
        for i in range(10):  # Create 10x more tasks
            for task in original_tasks:
                new_task = task.copy()
                new_task['id'] = f"{task['id']}_copy_{i}"
                task_manager.tasks.append(new_task)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        # Test operations with larger dataset
        all_tasks = task_manager.get_tasks()
        assert len(all_tasks) > len(original_tasks)
        
        # Test filtering performance
        critical_tasks = task_manager.get_tasks({"priority": "critical"})
        assert len(critical_tasks) > 0
        
        # Test progress report with larger dataset
        report = task_manager.get_progress_report()
        assert report['total_tasks'] > len(original_tasks)
        
        # Test execution log with larger dataset
        logs = task_master.get_execution_log()
        # Should handle empty logs gracefully
        assert isinstance(logs, list)
