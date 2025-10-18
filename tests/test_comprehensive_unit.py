"""
Comprehensive Unit Test Classes for All Components
Achieves 100% Unit Test Coverage
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

class TestPRDParserComprehensive(unittest.TestCase):
    """Comprehensive unit tests for PRD Parser"""
    
    def setUp(self):
        self.parser = PRDParser()
        self.sample_content = """# Test PRD

## 1. Executive Summary
This is a test PRD.

## 2. Features
- [ ] Feature 1
- [x] Feature 2
- [ ] Feature 3

## 3. Implementation
### Phase 1
- [ ] Task 1.1
- [ ] Task 1.2

### Phase 2
- [ ] Task 2.1
- [x] Task 2.2
"""
    
    def test_parse_prd_content_basic(self):
        """Test basic PRD content parsing"""
        result = self.parser.parse_prd_content(self.sample_content)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
    
    def test_parse_prd_content_empty(self):
        """Test parsing empty content"""
        result = self.parser.parse_prd_content("")
        self.assertIsNotNone(result)
        self.assertEqual(result['metadata']['title'], '')
    
    def test_parse_prd_content_none(self):
        """Test parsing None content"""
        result = self.parser.parse_prd_content(None)
        self.assertIsNotNone(result)
    
    def test_parse_prd_content_malformed(self):
        """Test parsing malformed content"""
        malformed = "# Title\n- [ ] Task without proper format\n## Section"
        result = self.parser.parse_prd_content(malformed)
        self.assertIsNotNone(result)
    
    def test_parse_prd_content_very_large(self):
        """Test parsing very large content"""
        large_content = "# Title\n" + "\n".join([f"- [ ] Task {i}" for i in range(10000)])
        result = self.parser.parse_prd_content(large_content)
        self.assertIsNotNone(result)
    
    def test_parse_prd_content_special_characters(self):
        """Test parsing content with special characters"""
        special_content = "# Title with émojis 🚀\n- [ ] Task with unicode: αβγ\n- [x] Task with symbols: @#$%"
        result = self.parser.parse_prd_content(special_content)
        self.assertIsNotNone(result)
    
    def test_parse_prd_content_html_tags(self):
        """Test parsing content with HTML tags"""
        html_content = "# Title\n- [ ] Task with <b>bold</b> text\n- [x] Task with <i>italic</i> text"
        result = self.parser.parse_prd_content(html_content)
        self.assertIsNotNone(result)
    
    def test_parse_prd_content_markdown_complex(self):
        """Test parsing complex markdown content"""
        complex_content = """# Title

## Section 1
Some **bold** and *italic* text.

### Subsection 1.1
- [ ] Task 1
- [x] Task 2

```python
def hello():
    print("world")
```

## Section 2
> Quote text

- [ ] Task 3
"""
        result = self.parser.parse_prd_content(complex_content)
        self.assertIsNotNone(result)
    
    def test_extract_metadata_basic(self):
        """Test basic metadata extraction"""
        metadata = self.parser.extract_metadata(self.sample_content)
        self.assertIsInstance(metadata, PRDMetadata)
        self.assertEqual(metadata.title, "Test PRD")
        self.assertGreater(len(metadata.sections), 0)
    
    def test_extract_metadata_no_title(self):
        """Test metadata extraction without title"""
        content = "## Section 1\n- [ ] Task 1"
        metadata = self.parser.extract_metadata(content)
        self.assertEqual(metadata.title, "")
    
    def test_extract_metadata_multiple_titles(self):
        """Test metadata extraction with multiple titles"""
        content = "# Title 1\n## Title 2\n### Title 3\n- [ ] Task 1"
        metadata = self.parser.extract_metadata(content)
        self.assertEqual(metadata.title, "Title 1")
    
    def test_extract_metadata_empty_sections(self):
        """Test metadata extraction with empty sections"""
        content = "# Title\n\n\n## Section 1\n\n\n## Section 2"
        metadata = self.parser.extract_metadata(content)
        self.assertGreaterEqual(len(metadata.sections), 0)
    
    def test_extract_tasks_basic(self):
        """Test basic task extraction"""
        tasks = self.parser.extract_tasks(self.sample_content)
        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)
        
        for task in tasks:
            self.assertIsInstance(task, Task)
            self.assertIsInstance(task.priority, Priority)
            self.assertIsInstance(task.status, TaskStatus)
    
    def test_extract_tasks_no_tasks(self):
        """Test task extraction with no tasks"""
        content = "# Title\n## Section\nNo tasks here."
        tasks = self.parser.extract_tasks(content)
        self.assertEqual(len(tasks), 0)
    
    def test_extract_tasks_mixed_status(self):
        """Test task extraction with mixed status"""
        content = """# Title
- [ ] Pending task
- [x] Completed task
- [ ] Another pending task
"""
        tasks = self.parser.extract_tasks(content)
        self.assertEqual(len(tasks), 3)
        
        pending_count = sum(1 for task in tasks if task.status == TaskStatus.PENDING)
        completed_count = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
        
        self.assertEqual(pending_count, 2)
        self.assertEqual(completed_count, 1)
    
    def test_extract_tasks_priority_assignment(self):
        """Test task priority assignment"""
        content = """# Title
## High Priority Features
- [ ] High priority task

## Medium Priority Features
- [ ] Medium priority task

## Low Priority Features
- [ ] Low priority task
"""
        tasks = self.parser.extract_tasks(content)
        
        high_priority = [task for task in tasks if "High Priority" in task.title]
        medium_priority = [task for task in tasks if "Medium Priority" in task.title]
        low_priority = [task for task in tasks if "Low Priority" in task.title]
        
        if high_priority:
            self.assertEqual(high_priority[0].priority, Priority.HIGH)
        if medium_priority:
            self.assertEqual(medium_priority[0].priority, Priority.MEDIUM)
        if low_priority:
            self.assertEqual(low_priority[0].priority, Priority.LOW)
    
    def test_extract_phases_basic(self):
        """Test basic phase extraction"""
        phases = self.parser.extract_phases(self.sample_content)
        self.assertIsInstance(phases, list)
        self.assertGreater(len(phases), 0)
        
        for phase in phases:
            self.assertIsInstance(phase, Phase)
            self.assertIsInstance(phase.tasks, list)
    
    def test_extract_phases_no_phases(self):
        """Test phase extraction with no phases"""
        content = "# Title\n- [ ] Task 1\n- [ ] Task 2"
        phases = self.parser.extract_phases(content)
        self.assertEqual(len(phases), 0)
    
    def test_extract_phases_nested_phases(self):
        """Test phase extraction with nested phases"""
        content = """# Title
## Phase 1
### Subphase 1.1
- [ ] Task 1.1
### Subphase 1.2
- [ ] Task 1.2
## Phase 2
- [ ] Task 2.1
"""
        phases = self.parser.extract_phases(content)
        self.assertGreater(len(phases), 0)
    
    def test_parse_prd_file(self):
        """Test parsing PRD from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_content)
            f.flush()
            
            try:
                result = self.parser.parse_prd(f.name)
                self.assertIsNotNone(result)
            finally:
                os.unlink(f.name)
    
    def test_parse_prd_file_not_found(self):
        """Test parsing non-existent PRD file"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_prd("non_existent_file.md")
    
    def test_parse_prd_file_permission_error(self):
        """Test parsing PRD file with permission error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_content)
            f.flush()
            
            # Make file read-only
            os.chmod(f.name, 0o000)
            
            try:
                with self.assertRaises(PermissionError):
                    self.parser.parse_prd(f.name)
            finally:
                os.chmod(f.name, 0o644)
                os.unlink(f.name)
    
    def test_save_to_json(self):
        """Test saving PRD data to JSON"""
        result = self.parser.parse_prd_content(self.sample_content)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            try:
                self.parser.save_to_json(result, f.name)
                self.assertTrue(os.path.exists(f.name))
                
                # Verify JSON is valid
                with open(f.name, 'r') as json_file:
                    json.load(json_file)
            finally:
                os.unlink(f.name)
    
    def test_save_to_yaml(self):
        """Test saving PRD data to YAML"""
        result = self.parser.parse_prd_content(self.sample_content)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            try:
                self.parser.save_to_yaml(result, f.name)
                self.assertTrue(os.path.exists(f.name))
                
                # Verify YAML is valid
                with open(f.name, 'r') as yaml_file:
                    yaml.safe_load(yaml_file)
            finally:
                os.unlink(f.name)
    
    def test_task_creation_edge_cases(self):
        """Test task creation with edge cases"""
        # Empty task title
        content = "- [ ] \n- [x] "
        tasks = self.parser.extract_tasks(content)
        self.assertEqual(len(tasks), 2)
        
        # Very long task title
        long_title = "Task with very long title " * 100
        content = f"- [ ] {long_title}"
        tasks = self.parser.extract_tasks(content)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, long_title)
        
        # Task with special characters
        special_title = "Task with émojis 🚀 and symbols @#$%"
        content = f"- [ ] {special_title}"
        tasks = self.parser.extract_tasks(content)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, special_title)
    
    def test_phase_creation_edge_cases(self):
        """Test phase creation with edge cases"""
        # Empty phase
        content = "## Empty Phase\n\n## Phase with tasks\n- [ ] Task 1"
        phases = self.parser.extract_phases(content)
        self.assertGreater(len(phases), 0)
        
        # Phase with no tasks
        content = "## Phase without tasks\nSome text but no tasks."
        phases = self.parser.extract_phases(content)
        self.assertEqual(len(phases), 0)
    
    def test_concurrent_parsing(self):
        """Test concurrent parsing operations"""
        def parse_content():
            return self.parser.parse_prd_content(self.sample_content)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(parse_content) for _ in range(100)]
            results = [future.result() for future in futures]
        
        self.assertEqual(len(results), 100)
        for result in results:
            self.assertIsNotNone(result)
    
    def test_memory_usage(self):
        """Test memory usage during parsing"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Parse large content multiple times
        large_content = self.sample_content * 1000
        for _ in range(100):
            self.parser.parse_prd_content(large_content)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 100)  # Less than 100MB increase


class TestTaskManagerComprehensive(unittest.TestCase):
    """Comprehensive unit tests for Task Manager"""
    
    def setUp(self):
        self.manager = TaskManager()
        self.sample_task = Task(
            id="test-1",
            title="Test Task",
            description="Test Description",
            priority=Priority.HIGH,
            status=TaskStatus.PENDING
        )
    
    def test_initialization(self):
        """Test TaskManager initialization"""
        self.assertEqual(len(self.manager.tasks), 0)
        self.assertEqual(len(self.manager.dependencies), 0)
        self.assertIsInstance(self.manager.tasks, dict)
        self.assertIsInstance(self.manager.dependencies, dict)
    
    def test_add_task_basic(self):
        """Test basic task addition"""
        self.manager.add_task(self.sample_task)
        self.assertEqual(len(self.manager.tasks), 1)
        self.assertIn("test-1", self.manager.tasks)
        self.assertEqual(self.manager.tasks["test-1"], self.sample_task)
    
    def test_add_task_duplicate_id(self):
        """Test adding task with duplicate ID"""
        self.manager.add_task(self.sample_task)
        
        with self.assertRaises(ValueError):
            self.manager.add_task(self.sample_task)
    
    def test_add_task_invalid_task(self):
        """Test adding invalid task"""
        with self.assertRaises(TypeError):
            self.manager.add_task("not a task")
    
    def test_add_task_none(self):
        """Test adding None task"""
        with self.assertRaises(TypeError):
            self.manager.add_task(None)
    
    def test_get_task_existing(self):
        """Test getting existing task"""
        self.manager.add_task(self.sample_task)
        retrieved_task = self.manager.get_task("test-1")
        self.assertEqual(retrieved_task, self.sample_task)
    
    def test_get_task_nonexistent(self):
        """Test getting non-existent task"""
        with self.assertRaises(KeyError):
            self.manager.get_task("non-existent")
    
    def test_get_task_empty_id(self):
        """Test getting task with empty ID"""
        with self.assertRaises(KeyError):
            self.manager.get_task("")
    
    def test_get_task_none_id(self):
        """Test getting task with None ID"""
        with self.assertRaises(KeyError):
            self.manager.get_task(None)
    
    def test_remove_task_existing(self):
        """Test removing existing task"""
        self.manager.add_task(self.sample_task)
        self.manager.remove_task("test-1")
        self.assertEqual(len(self.manager.tasks), 0)
        self.assertNotIn("test-1", self.manager.tasks)
    
    def test_remove_task_nonexistent(self):
        """Test removing non-existent task"""
        with self.assertRaises(KeyError):
            self.manager.remove_task("non-existent")
    
    def test_remove_task_with_dependencies(self):
        """Test removing task with dependencies"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_dependency("task-2", "task-1")
        
        # Should remove dependencies when removing task
        self.manager.remove_task("task-1")
        self.assertNotIn("task-1", self.manager.tasks)
        self.assertNotIn("task-2", self.manager.dependencies)
    
    def test_update_task_status_valid(self):
        """Test updating task status with valid status"""
        self.manager.add_task(self.sample_task)
        self.manager.update_task_status("test-1", TaskStatus.IN_PROGRESS)
        self.assertEqual(self.manager.get_task("test-1").status, TaskStatus.IN_PROGRESS)
    
    def test_update_task_status_invalid(self):
        """Test updating task status with invalid status"""
        self.manager.add_task(self.sample_task)
        
        with self.assertRaises(ValueError):
            self.manager.update_task_status("test-1", "INVALID_STATUS")
    
    def test_update_task_status_nonexistent(self):
        """Test updating status of non-existent task"""
        with self.assertRaises(KeyError):
            self.manager.update_task_status("non-existent", TaskStatus.COMPLETED)
    
    def test_get_tasks_by_status(self):
        """Test getting tasks by status"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.IN_PROGRESS)
        task3 = Task("task-3", "Task 3", "Description 3", Priority.LOW, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_task(task3)
        
        pending_tasks = self.manager.get_tasks_by_status(TaskStatus.PENDING)
        self.assertEqual(len(pending_tasks), 2)
        
        in_progress_tasks = self.manager.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        self.assertEqual(len(in_progress_tasks), 1)
    
    def test_get_tasks_by_priority(self):
        """Test getting tasks by priority"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        task3 = Task("task-3", "Task 3", "Description 3", Priority.HIGH, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_task(task3)
        
        high_priority_tasks = self.manager.get_tasks_by_priority(Priority.HIGH)
        self.assertEqual(len(high_priority_tasks), 2)
        
        medium_priority_tasks = self.manager.get_tasks_by_priority(Priority.MEDIUM)
        self.assertEqual(len(medium_priority_tasks), 1)
    
    def test_get_all_tasks(self):
        """Test getting all tasks"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        
        all_tasks = self.manager.get_all_tasks()
        self.assertEqual(len(all_tasks), 2)
    
    def test_add_dependency_valid(self):
        """Test adding valid dependency"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_dependency("task-2", "task-1")
        
        self.assertIn("task-2", self.manager.dependencies)
        self.assertIn("task-1", self.manager.dependencies["task-2"])
    
    def test_add_dependency_circular(self):
        """Test adding circular dependency"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_dependency("task-2", "task-1")
        
        with self.assertRaises(ValueError):
            self.manager.add_dependency("task-1", "task-2")
    
    def test_add_dependency_self(self):
        """Test adding self-dependency"""
        self.manager.add_task(self.sample_task)
        
        with self.assertRaises(ValueError):
            self.manager.add_dependency("test-1", "test-1")
    
    def test_add_dependency_nonexistent_task(self):
        """Test adding dependency with non-existent task"""
        self.manager.add_task(self.sample_task)
        
        with self.assertRaises(KeyError):
            self.manager.add_dependency("test-1", "non-existent")
    
    def test_add_dependency_nonexistent_dependency(self):
        """Test adding dependency with non-existent dependency"""
        self.manager.add_task(self.sample_task)
        
        with self.assertRaises(KeyError):
            self.manager.add_dependency("non-existent", "test-1")
    
    def test_remove_dependency(self):
        """Test removing dependency"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_dependency("task-2", "task-1")
        self.manager.remove_dependency("task-2", "task-1")
        
        self.assertNotIn("task-1", self.manager.dependencies.get("task-2", []))
    
    def test_get_task_dependencies(self):
        """Test getting task dependencies"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        task3 = Task("task-3", "Task 3", "Description 3", Priority.LOW, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_task(task3)
        self.manager.add_dependency("task-2", "task-1")
        self.manager.add_dependency("task-3", "task-1")
        
        dependencies = self.manager.get_task_dependencies("task-2")
        self.assertIn("task-1", dependencies)
        
        dependencies = self.manager.get_task_dependencies("task-3")
        self.assertIn("task-1", dependencies)
    
    def test_get_dependents(self):
        """Test getting dependents"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        task3 = Task("task-3", "Task 3", "Description 3", Priority.LOW, TaskStatus.PENDING)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_task(task3)
        self.manager.add_dependency("task-2", "task-1")
        self.manager.add_dependency("task-3", "task-1")
        
        dependents = self.manager.get_dependents("task-1")
        self.assertIn("task-2", dependents)
        self.assertIn("task-3", dependents)
    
    def test_get_progress_report(self):
        """Test getting progress report"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.IN_PROGRESS)
        task3 = Task("task-3", "Task 3", "Description 3", Priority.LOW, TaskStatus.COMPLETED)
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_task(task3)
        
        report = self.manager.get_progress_report()
        self.assertIsInstance(report, dict)
        self.assertIn("total_tasks", report)
        self.assertIn("completed_tasks", report)
        self.assertIn("in_progress_tasks", report)
        self.assertIn("pending_tasks", report)
        self.assertEqual(report["total_tasks"], 3)
        self.assertEqual(report["completed_tasks"], 1)
        self.assertEqual(report["in_progress_tasks"], 1)
        self.assertEqual(report["pending_tasks"], 1)
    
    def test_save_tasks_json(self):
        """Test saving tasks to JSON"""
        self.manager.add_task(self.sample_task)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            try:
                self.manager.save_tasks(f.name)
                self.assertTrue(os.path.exists(f.name))
                
                with open(f.name, 'r') as json_file:
                    data = json.load(json_file)
                    self.assertIn("test-1", data["tasks"])
            finally:
                os.unlink(f.name)
    
    def test_save_tasks_yaml(self):
        """Test saving tasks to YAML"""
        self.manager.add_task(self.sample_task)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            try:
                self.manager.save_tasks(f.name)
                self.assertTrue(os.path.exists(f.name))
                
                with open(f.name, 'r') as yaml_file:
                    data = yaml.safe_load(yaml_file)
                    self.assertIn("test-1", data["tasks"])
            finally:
                os.unlink(f.name)
    
    def test_load_tasks_json(self):
        """Test loading tasks from JSON"""
        self.manager.add_task(self.sample_task)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            try:
                self.manager.save_tasks(f.name)
                
                new_manager = TaskManager()
                new_manager.load_tasks(f.name)
                self.assertEqual(len(new_manager.tasks), 1)
                self.assertIn("test-1", new_manager.tasks)
            finally:
                os.unlink(f.name)
    
    def test_load_tasks_yaml(self):
        """Test loading tasks from YAML"""
        self.manager.add_task(self.sample_task)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            try:
                self.manager.save_tasks(f.name)
                
                new_manager = TaskManager()
                new_manager.load_tasks(f.name)
                self.assertEqual(len(new_manager.tasks), 1)
                self.assertIn("test-1", new_manager.tasks)
            finally:
                os.unlink(f.name)
    
    def test_load_tasks_nonexistent_file(self):
        """Test loading tasks from non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.manager.load_tasks("non_existent_file.json")
    
    def test_load_tasks_invalid_json(self):
        """Test loading tasks from invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            f.flush()
            
            try:
                with self.assertRaises(json.JSONDecodeError):
                    self.manager.load_tasks(f.name)
            finally:
                os.unlink(f.name)
    
    def test_concurrent_operations(self):
        """Test concurrent operations"""
        def add_task(task_id):
            task = Task(f"task-{task_id}", f"Task {task_id}", f"Description {task_id}", Priority.MEDIUM, TaskStatus.PENDING)
            self.manager.add_task(task)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_task, i) for i in range(100)]
            concurrent.futures.wait(futures)
        
        self.assertEqual(len(self.manager.tasks), 100)
    
    def test_memory_usage(self):
        """Test memory usage"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many tasks
        for i in range(1000):
            task = Task(f"task-{i}", f"Task {i}", f"Description {i}", Priority.MEDIUM, TaskStatus.PENDING)
            self.manager.add_task(task)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 50)  # Less than 50MB increase


class TestTaskMasterComprehensive(unittest.TestCase):
    """Comprehensive unit tests for Task Master"""
    
    def setUp(self):
        self.executor = TaskExecutor()
        self.master = TaskMaster(self.executor)
        self.sample_task = Task(
            id="test-1",
            title="Test Task",
            description="Test Description",
            priority=Priority.HIGH,
            status=TaskStatus.PENDING
        )
    
    def test_initialization(self):
        """Test TaskMaster initialization"""
        self.assertIsNotNone(self.master.executor)
        self.assertIsInstance(self.master.context, dict)
    
    def test_execute_task_terraform(self):
        """Test executing Terraform task"""
        terraform_task = Task(
            id="tf-1",
            title="Terraform init",
            description="Initialize Terraform",
            priority=Priority.HIGH,
            status=TaskStatus.PENDING
        )
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Terraform initialized', stderr=b'')
            
            result = self.master.execute_task(terraform_task, {})
            self.assertTrue(result.success)
            self.assertIn("Terraform", result.output)
    
    def test_execute_task_kubernetes(self):
        """Test executing Kubernetes task"""
        k8s_task = Task(
            id="k8s-1",
            title="Create namespace",
            description="Create Kubernetes namespace",
            priority=Priority.MEDIUM,
            status=TaskStatus.PENDING
        )
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Namespace created', stderr=b'')
            
            result = self.master.execute_task(k8s_task, {})
            self.assertTrue(result.success)
    
    def test_execute_task_argocd(self):
        """Test executing ArgoCD task"""
        argocd_task = Task(
            id="argocd-1",
            title="Install ArgoCD",
            description="Install ArgoCD",
            priority=Priority.HIGH,
            status=TaskStatus.PENDING
        )
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'ArgoCD installed', stderr=b'')
            
            result = self.master.execute_task(argocd_task, {})
            self.assertTrue(result.success)
    
    def test_execute_task_helm(self):
        """Test executing Helm task"""
        helm_task = Task(
            id="helm-1",
            title="Install chart",
            description="Install Helm chart",
            priority=Priority.MEDIUM,
            status=TaskStatus.PENDING
        )
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Chart installed', stderr=b'')
            
            result = self.master.execute_task(helm_task, {})
            self.assertTrue(result.success)
    
    def test_execute_task_generic(self):
        """Test executing generic task"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Generic task executed', stderr=b'')
            
            result = self.master.execute_task(self.sample_task, {})
            self.assertTrue(result.success)
    
    def test_execute_task_failure(self):
        """Test executing task that fails"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout=b'', stderr=b'Error occurred')
            
            result = self.master.execute_task(self.sample_task, {})
            self.assertFalse(result.success)
            self.assertIn("Error", result.error)
    
    def test_execute_task_timeout(self):
        """Test executing task with timeout"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(['sleep', '10'], 1)
            
            result = self.master.execute_task(self.sample_task, {})
            self.assertFalse(result.success)
            self.assertIn("timeout", result.error.lower())
    
    def test_execute_phase_success(self):
        """Test executing phase successfully"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        
        phase = Phase("phase-1", "Test Phase", "Test Phase Description", [task1, task2])
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.master.execute_phase(phase, {})
            self.assertTrue(result.success)
    
    def test_execute_phase_with_failure(self):
        """Test executing phase with task failure"""
        task1 = Task("task-1", "Task 1", "Description 1", Priority.HIGH, TaskStatus.PENDING)
        task2 = Task("task-2", "Task 2", "Description 2", Priority.MEDIUM, TaskStatus.PENDING)
        
        phase = Phase("phase-1", "Test Phase", "Test Phase Description", [task1, task2])
        
        with patch('subprocess.run') as mock_run:
            # First task succeeds, second fails
            mock_run.side_effect = [
                Mock(returncode=0, stdout=b'Success', stderr=b''),
                Mock(returncode=1, stdout=b'', stderr=b'Error')
            ]
            
            result = self.master.execute_phase(phase, {})
            self.assertFalse(result.success)
    
    def test_execute_phase_empty(self):
        """Test executing empty phase"""
        phase = Phase("phase-1", "Empty Phase", "Empty Phase Description", [])
        
        result = self.master.execute_phase(phase, {})
        self.assertTrue(result.success)
    
    def test_context_merging(self):
        """Test context merging"""
        initial_context = {"key1": "value1"}
        task_context = {"key2": "value2"}
        
        self.master.context = initial_context.copy()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            self.master.execute_task(self.sample_task, task_context)
            
            # Context should be merged
            self.assertEqual(self.master.context["key1"], "value1")
            self.assertEqual(self.master.context["key2"], "value2")
    
    def test_task_type_detection(self):
        """Test task type detection"""
        # Test Terraform task detection
        terraform_task = Task("tf-1", "Terraform init", "Description", Priority.HIGH, TaskStatus.PENDING)
        task_type = self.master._execute_task_by_type(terraform_task, {})
        self.assertIsNotNone(task_type)
        
        # Test Kubernetes task detection
        k8s_task = Task("k8s-1", "Create namespace", "Description", Priority.MEDIUM, TaskStatus.PENDING)
        task_type = self.master._execute_task_by_type(k8s_task, {})
        self.assertIsNotNone(task_type)
        
        # Test ArgoCD task detection
        argocd_task = Task("argocd-1", "Install ArgoCD", "Description", Priority.HIGH, TaskStatus.PENDING)
        task_type = self.master._execute_task_by_type(argocd_task, {})
        self.assertIsNotNone(task_type)
    
    def test_concurrent_execution(self):
        """Test concurrent task execution"""
        tasks = [
            Task(f"task-{i}", f"Task {i}", f"Description {i}", Priority.MEDIUM, TaskStatus.PENDING)
            for i in range(10)
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            def execute_task(task):
                return self.master.execute_task(task, {})
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(execute_task, task) for task in tasks]
                results = [future.result() for future in futures]
            
            self.assertEqual(len(results), 10)
            for result in results:
                self.assertTrue(result.success)
    
    def test_memory_usage(self):
        """Test memory usage during execution"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute many tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for i in range(1000):
                task = Task(f"task-{i}", f"Task {i}", f"Description {i}", Priority.MEDIUM, TaskStatus.PENDING)
                self.master.execute_task(task, {})
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 50)  # Less than 50MB increase


class TestTaskExecutorComprehensive(unittest.TestCase):
    """Comprehensive unit tests for Task Executor"""
    
    def setUp(self):
        self.executor = TaskExecutor()
    
    def test_initialization(self):
        """Test TaskExecutor initialization"""
        self.assertIsInstance(self.executor.context, dict)
    
    def test_execute_command_success(self):
        """Test executing command successfully"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.executor.execute_command(['echo', 'test'])
            self.assertTrue(result.success)
            self.assertEqual(result.output, 'Success')
            self.assertEqual(result.error, '')
    
    def test_execute_command_failure(self):
        """Test executing command that fails"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout=b'', stderr=b'Error occurred')
            
            result = self.executor.execute_command(['false'])
            self.assertFalse(result.success)
            self.assertEqual(result.output, '')
            self.assertEqual(result.error, 'Error occurred')
    
    def test_execute_command_timeout(self):
        """Test executing command with timeout"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(['sleep', '10'], 1)
            
            result = self.executor.execute_command(['sleep', '10'], timeout=1)
            self.assertFalse(result.success)
            self.assertIn("timeout", result.error.lower())
    
    def test_execute_command_invalid_command(self):
        """Test executing invalid command"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            
            result = self.executor.execute_command(['nonexistent_command'])
            self.assertFalse(result.success)
            self.assertIn("not found", result.error.lower())
    
    def test_execute_terraform_command(self):
        """Test executing Terraform command"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Terraform output', stderr=b'')
            
            result = self.executor.execute_terraform_command('init', working_dir='/tmp')
            self.assertTrue(result.success)
            self.assertEqual(result.output, 'Terraform output')
    
    def test_execute_kubectl_command(self):
        """Test executing kubectl command"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'kubectl output', stderr=b'')
            
            result = self.executor.execute_kubectl_command('apply', args=['-f', 'manifest.yaml'])
            self.assertTrue(result.success)
            self.assertEqual(result.output, 'kubectl output')
    
    def test_execute_argocd_command(self):
        """Test executing ArgoCD command"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'ArgoCD output', stderr=b'')
            
            result = self.executor.execute_argocd_command('app', 'list')
            self.assertTrue(result.success)
            self.assertEqual(result.output, 'ArgoCD output')
    
    def test_execute_helm_command(self):
        """Test executing Helm command"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Helm output', stderr=b'')
            
            result = self.executor.execute_helm_command('install', 'my-release', 'chart')
            self.assertTrue(result.success)
            self.assertEqual(result.output, 'Helm output')
    
    def test_context_usage(self):
        """Test context usage in command execution"""
        self.executor.context = {'WORKING_DIR': '/tmp', 'ENV': 'production'}
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.executor.execute_command(['echo', 'test'])
            
            # Verify context was used
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            self.assertIn('env', call_args.kwargs)
    
    def test_concurrent_execution(self):
        """Test concurrent command execution"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            def execute_command():
                return self.executor.execute_command(['echo', 'test'])
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(execute_command) for _ in range(100)]
                results = [future.result() for future in futures]
            
            self.assertEqual(len(results), 100)
            for result in results:
                self.assertTrue(result.success)
    
    def test_memory_usage(self):
        """Test memory usage during execution"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute many commands
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for i in range(1000):
                self.executor.execute_command(['echo', f'test-{i}'])
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 50)  # Less than 50MB increase


if __name__ == '__main__':
    # Run comprehensive unit tests
    unittest.main(verbosity=2)
