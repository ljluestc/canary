"""
Unit tests for Task Manager functionality.
"""

import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from task_manager import TaskManager
from prd_parser import TaskStatus, Priority


class TestTaskManager:
    """Test TaskManager functionality."""
    
    def test_initialization_empty(self):
        """Test initialization without tasks file."""
        tm = TaskManager()
        
        assert tm.tasks == []
        assert tm.phases == []
        assert tm.metadata == {}
        assert tm.tasks_file is None
    
    def test_initialization_with_file(self, temp_tasks_file):
        """Test initialization with existing tasks file."""
        tm = TaskManager(temp_tasks_file)
        
        assert len(tm.tasks) > 0
        assert len(tm.phases) > 0
        assert tm.metadata["title"] == "Test Project"
        assert tm.tasks_file == temp_tasks_file
    
    def test_load_from_prd(self, temp_prd_file):
        """Test loading tasks from PRD file."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        assert len(tm.tasks) > 0
        assert len(tm.phases) > 0
        assert tm.metadata["title"] == "Test Product Requirements Document"
        
        # Check that tasks are properly loaded
        for task in tm.tasks:
            assert "id" in task
            assert "title" in task
            assert "phase" in task
            assert "priority" in task
            assert "status" in task
    
    def test_load_tasks_json(self, temp_tasks_file):
        """Test loading tasks from JSON file."""
        tm = TaskManager()
        tm.load_tasks(temp_tasks_file)
        
        assert len(tm.tasks) > 0
        assert tm.metadata["title"] == "Test Project"
        
        # Verify task structure
        task = tm.tasks[0]
        assert task["id"] == "phase_1_task_1"
        assert task["title"] == "Create Terraform configurations for kind cluster"
        assert task["phase"] == "Infrastructure Setup"
        assert task["priority"] == "critical"
    
    def test_load_tasks_yaml(self, temp_tasks_yaml_file):
        """Test loading tasks from YAML file."""
        tm = TaskManager()
        tm.load_tasks(temp_tasks_yaml_file)
        
        assert len(tm.tasks) > 0
        assert tm.metadata["title"] == "Test Project"
    
    def test_load_tasks_invalid_format(self):
        """Test loading tasks from invalid file format."""
        tm = TaskManager()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Invalid format")
            temp_file.flush()
            
            with pytest.raises(ValueError, match="Unsupported file format"):
                tm.load_tasks(temp_file.name)
            
            os.unlink(temp_file.name)
    
    def test_save_tasks_json(self, temp_tasks_file):
        """Test saving tasks to JSON file."""
        tm = TaskManager(temp_tasks_file)
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            tm.save_tasks(temp_file.name, 'json')
            
            assert os.path.exists(temp_file.name)
            
            with open(temp_file.name, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["metadata"]["title"] == "Test Project"
            assert len(saved_data["tasks"]) == len(tm.tasks)
            assert "last_updated" in saved_data
            
            os.unlink(temp_file.name)
    
    def test_save_tasks_yaml(self, temp_tasks_file):
        """Test saving tasks to YAML file."""
        tm = TaskManager(temp_tasks_file)
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp_file:
            tm.save_tasks(temp_file.name, 'yaml')
            
            assert os.path.exists(temp_file.name)
            
            with open(temp_file.name, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data["metadata"]["title"] == "Test Project"
            assert len(saved_data["tasks"]) == len(tm.tasks)
            
            os.unlink(temp_file.name)
    
    def test_save_tasks_invalid_format(self, temp_tasks_file):
        """Test saving tasks with invalid format."""
        tm = TaskManager(temp_tasks_file)
        
        with pytest.raises(ValueError, match="Unsupported format"):
            tm.save_tasks("test.xml", "xml")
    
    def test_get_task_existing(self, temp_tasks_file):
        """Test getting an existing task."""
        tm = TaskManager(temp_tasks_file)
        
        task = tm.get_task("phase_1_task_1")
        
        assert task is not None
        assert task["id"] == "phase_1_task_1"
        assert task["title"] == "Create Terraform configurations for kind cluster"
    
    def test_get_task_nonexistent(self, temp_tasks_file):
        """Test getting a non-existent task."""
        tm = TaskManager(temp_tasks_file)
        
        task = tm.get_task("nonexistent_task")
        
        assert task is None
    
    def test_get_tasks_no_filters(self, temp_tasks_file):
        """Test getting all tasks without filters."""
        tm = TaskManager(temp_tasks_file)
        
        tasks = tm.get_tasks()
        
        assert len(tasks) == len(tm.tasks)
        assert tasks == tm.tasks
    
    def test_get_tasks_filter_by_status(self, temp_tasks_file):
        """Test filtering tasks by status."""
        tm = TaskManager(temp_tasks_file)
        
        # Update a task status first
        tm.update_task_status("phase_1_task_1", "completed")
        
        # Filter by completed status
        completed_tasks = tm.get_tasks({"status": "completed"})
        assert len(completed_tasks) == 1
        assert completed_tasks[0]["id"] == "phase_1_task_1"
        
        # Filter by pending status
        pending_tasks = tm.get_tasks({"status": "pending"})
        assert len(pending_tasks) == 0  # All tasks should be completed or not pending
    
    def test_get_tasks_filter_by_phase(self, temp_prd_file):
        """Test filtering tasks by phase."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        infrastructure_tasks = tm.get_tasks({"phase": "Infrastructure Setup"})
        assert len(infrastructure_tasks) > 0
        
        for task in infrastructure_tasks:
            assert task["phase"] == "Infrastructure Setup"
    
    def test_get_tasks_filter_by_priority(self, temp_prd_file):
        """Test filtering tasks by priority."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        critical_tasks = tm.get_tasks({"priority": "critical"})
        assert len(critical_tasks) > 0
        
        for task in critical_tasks:
            assert task["priority"] == "critical"
    
    def test_get_tasks_multiple_filters(self, temp_prd_file):
        """Test filtering tasks with multiple criteria."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        # Filter by phase and priority
        filtered_tasks = tm.get_tasks({
            "phase": "Infrastructure Setup",
            "priority": "critical"
        })
        
        for task in filtered_tasks:
            assert task["phase"] == "Infrastructure Setup"
            assert task["priority"] == "critical"
    
    def test_update_task_status_valid(self, temp_tasks_file):
        """Test updating task status with valid status."""
        tm = TaskManager(temp_tasks_file)
        
        result = tm.update_task_status("phase_1_task_1", "in_progress", "Starting work")
        
        assert result is True
        
        task = tm.get_task("phase_1_task_1")
        assert task["status"] == "in_progress"
        
        # Check status history
        assert "status_history" in task
        assert len(task["status_history"]) == 1
        assert task["status_history"][0]["status"] == "in_progress"
        assert task["status_history"][0]["message"] == "Starting work"
    
    def test_update_task_status_invalid(self, temp_tasks_file):
        """Test updating task status with invalid status."""
        tm = TaskManager(temp_tasks_file)
        
        result = tm.update_task_status("phase_1_task_1", "invalid_status")
        
        assert result is False
        
        task = tm.get_task("phase_1_task_1")
        assert task["status"] == "pending"  # Should remain unchanged
    
    def test_update_task_status_nonexistent(self, temp_tasks_file):
        """Test updating status of non-existent task."""
        tm = TaskManager(temp_tasks_file)
        
        result = tm.update_task_status("nonexistent_task", "completed")
        
        assert result is False
    
    def test_get_task_dependencies(self, temp_prd_file):
        """Test getting task dependencies."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        # Add a dependency to a task
        task_id = tm.tasks[0]["id"]
        tm.tasks[0]["dependencies"] = [tm.tasks[1]["id"]]
        
        dependencies = tm.get_task_dependencies(task_id)
        
        assert len(dependencies) == 1
        assert dependencies[0]["id"] == tm.tasks[1]["id"]
    
    def test_get_task_dependencies_nonexistent(self, temp_tasks_file):
        """Test getting dependencies for non-existent task."""
        tm = TaskManager(temp_tasks_file)
        
        dependencies = tm.get_task_dependencies("nonexistent_task")
        
        assert dependencies == []
    
    def test_can_start_task_no_dependencies(self, temp_tasks_file):
        """Test checking if task can start when it has no dependencies."""
        tm = TaskManager(temp_tasks_file)
        
        can_start = tm.can_start_task("phase_1_task_1")
        
        assert can_start is True
    
    def test_can_start_task_with_completed_dependencies(self, temp_prd_file):
        """Test checking if task can start when dependencies are completed."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        # Add a dependency and complete it
        task_id = tm.tasks[0]["id"]
        dep_id = tm.tasks[1]["id"]
        tm.tasks[0]["dependencies"] = [dep_id]
        tm.update_task_status(dep_id, "completed")
        
        can_start = tm.can_start_task(task_id)
        
        assert can_start is True
    
    def test_can_start_task_with_pending_dependencies(self, temp_prd_file):
        """Test checking if task cannot start when dependencies are pending."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        # Add a dependency that remains pending
        task_id = tm.tasks[0]["id"]
        dep_id = tm.tasks[1]["id"]
        tm.tasks[0]["dependencies"] = [dep_id]
        
        can_start = tm.can_start_task(task_id)
        
        assert can_start is False
    
    def test_get_next_tasks(self, temp_prd_file):
        """Test getting next available tasks."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        next_tasks = tm.get_next_tasks()
        
        # All tasks should be pending and have no dependencies
        for task in next_tasks:
            assert task["status"] == TaskStatus.PENDING.value
            assert tm.can_start_task(task["id"]) is True
    
    def test_get_progress_report(self, temp_prd_file):
        """Test generating progress report."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        # Update some task statuses
        tm.update_task_status(tm.tasks[0]["id"], "completed")
        tm.update_task_status(tm.tasks[1]["id"], "in_progress")
        tm.update_task_status(tm.tasks[2]["id"], "failed")
        
        report = tm.get_progress_report()
        
        assert "total_tasks" in report
        assert "pending" in report
        assert "in_progress" in report
        assert "completed" in report
        assert "failed" in report
        assert "blocked" in report
        assert "progress_percentage" in report
        assert "phase_progress" in report
        
        # Verify counts
        total = len(tm.tasks)
        assert report["total_tasks"] == total
        assert report["completed"] >= 1
        assert report["in_progress"] >= 1
        assert report["failed"] >= 1
        assert report["progress_percentage"] >= 0
        assert report["progress_percentage"] <= 100
    
    def test_print_progress_report(self, temp_prd_file, capsys):
        """Test printing progress report."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        tm.print_progress_report()
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "PROJECT:" in output
        assert "OVERALL PROGRESS:" in output
        assert "Total Tasks:" in output
        assert "Completed:" in output
        assert "In Progress:" in output
        assert "Pending:" in output
        assert "PHASE PROGRESS:" in output
    
    def test_print_tasks_no_filters(self, temp_prd_file, capsys):
        """Test printing all tasks."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        tm.print_tasks()
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Found" in output
        assert "task(s):" in output
        
        # Check that task information is displayed
        for task in tm.tasks[:3]:  # Check first few tasks
            assert task["id"] in output
            assert task["title"] in output
    
    def test_print_tasks_with_filters(self, temp_prd_file, capsys):
        """Test printing tasks with filters."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        tm.print_tasks({"priority": "critical"})
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Found" in output
        assert "task(s):" in output
    
    def test_print_tasks_no_matches(self, temp_prd_file, capsys):
        """Test printing tasks when no matches found."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        tm.print_tasks({"priority": "nonexistent"})
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "No tasks found matching the criteria." in output
    
    def test_status_history_tracking(self, temp_tasks_file):
        """Test that status history is properly tracked."""
        tm = TaskManager(temp_tasks_file)
        
        task_id = "phase_1_task_1"
        
        # Update status multiple times
        tm.update_task_status(task_id, "in_progress", "Started work")
        tm.update_task_status(task_id, "completed", "Finished work")
        
        task = tm.get_task(task_id)
        
        assert len(task["status_history"]) == 2
        assert task["status_history"][0]["status"] == "in_progress"
        assert task["status_history"][0]["message"] == "Started work"
        assert task["status_history"][1]["status"] == "completed"
        assert task["status_history"][1]["message"] == "Finished work"
    
    def test_task_status_validation(self, temp_tasks_file):
        """Test validation of task status values."""
        tm = TaskManager(temp_tasks_file)
        
        # Test all valid statuses
        valid_statuses = [status.value for status in TaskStatus]
        
        for status in valid_statuses:
            result = tm.update_task_status("phase_1_task_1", status)
            assert result is True
        
        # Test invalid status
        result = tm.update_task_status("phase_1_task_1", "invalid")
        assert result is False
    
    def test_phase_progress_calculation(self, temp_prd_file):
        """Test phase progress calculation."""
        tm = TaskManager()
        tm.load_from_prd(temp_prd_file)
        
        # Complete some tasks in the first phase
        first_phase_tasks = [task for task in tm.tasks if task["phase"] == "Infrastructure Setup"]
        if len(first_phase_tasks) >= 2:
            tm.update_task_status(first_phase_tasks[0]["id"], "completed")
            tm.update_task_status(first_phase_tasks[1]["id"], "completed")
        
        report = tm.get_progress_report()
        
        # Check phase progress
        phase_progress = report["phase_progress"]
        assert len(phase_progress) > 0
        
        for phase in phase_progress:
            assert "phase" in phase
            assert "priority" in phase
            assert "completed" in phase
            assert "total" in phase
            assert "progress" in phase
            assert phase["progress"] >= 0
            assert phase["progress"] <= 100
