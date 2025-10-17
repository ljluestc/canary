"""
Unit tests for PRD parser functionality.
"""

import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from prd_parser import PRDParser, Task, Phase, TaskStatus, Priority, PRDMetadata


class TestTask:
    """Test Task dataclass."""
    
    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(
            id="test_task_1",
            title="Test task",
            phase="Test Phase",
            priority="high"
        )
        
        assert task.id == "test_task_1"
        assert task.title == "Test task"
        assert task.phase == "Test Phase"
        assert task.priority == "high"
        assert task.status == TaskStatus.PENDING.value
        assert task.dependencies == []
        assert task.section == ""
        assert task.line_number == 0
    
    def test_task_with_dependencies(self):
        """Test task creation with dependencies."""
        task = Task(
            id="test_task_2",
            title="Test task with deps",
            phase="Test Phase",
            priority="medium",
            dependencies=["dep1", "dep2"]
        )
        
        assert task.dependencies == ["dep1", "dep2"]
    
    def test_task_to_dict(self):
        """Test task to dictionary conversion."""
        task = Task(
            id="test_task_3",
            title="Test task",
            phase="Test Phase",
            priority="low",
            dependencies=["dep1"]
        )
        
        task_dict = task.to_dict()
        
        assert isinstance(task_dict, dict)
        assert task_dict["id"] == "test_task_3"
        assert task_dict["title"] == "Test task"
        assert task_dict["phase"] == "Test Phase"
        assert task_dict["priority"] == "low"
        assert task_dict["dependencies"] == ["dep1"]


class TestPhase:
    """Test Phase dataclass."""
    
    def test_phase_creation(self):
        """Test basic phase creation."""
        tasks = [
            Task(id="task1", title="Task 1", phase="Test Phase", priority="high"),
            Task(id="task2", title="Task 2", phase="Test Phase", priority="medium")
        ]
        
        phase = Phase(
            name="Test Phase",
            priority="high",
            tasks=tasks
        )
        
        assert phase.name == "Test Phase"
        assert phase.priority == "high"
        assert len(phase.tasks) == 2
        assert phase.tasks[0].id == "task1"
        assert phase.tasks[1].id == "task2"
    
    def test_phase_to_dict(self):
        """Test phase to dictionary conversion."""
        tasks = [
            Task(id="task1", title="Task 1", phase="Test Phase", priority="high")
        ]
        
        phase = Phase(
            name="Test Phase",
            priority="high",
            tasks=tasks
        )
        
        phase_dict = phase.to_dict()
        
        assert isinstance(phase_dict, dict)
        assert phase_dict["name"] == "Test Phase"
        assert phase_dict["priority"] == "high"
        assert len(phase_dict["tasks"]) == 1
        assert phase_dict["tasks"][0]["id"] == "task1"


class TestPRDMetadata:
    """Test PRDMetadata dataclass."""
    
    def test_metadata_creation(self):
        """Test basic metadata creation."""
        metadata = PRDMetadata(
            title="Test Project",
            sections=["Section 1", "Section 2"],
            total_tasks=10,
            total_phases=3
        )
        
        assert metadata.title == "Test Project"
        assert len(metadata.sections) == 2
        assert metadata.total_tasks == 10
        assert metadata.total_phases == 3
    
    def test_metadata_to_dict(self):
        """Test metadata to dictionary conversion."""
        metadata = PRDMetadata(
            title="Test Project",
            sections=["Section 1"],
            total_tasks=5,
            total_phases=2
        )
        
        metadata_dict = metadata.to_dict()
        
        assert isinstance(metadata_dict, dict)
        assert metadata_dict["title"] == "Test Project"
        assert metadata_dict["total_tasks"] == 5
        assert metadata_dict["total_phases"] == 2


class TestPRDParser:
    """Test PRDParser functionality."""
    
    def test_parser_initialization(self, temp_prd_file):
        """Test parser initialization."""
        parser = PRDParser(temp_prd_file)
        
        assert parser.prd_file_path == temp_prd_file
        assert parser.content == ""
        assert parser.lines == []
        assert parser.tasks == []
        assert parser.phases == []
        assert parser.metadata is None
    
    def test_load_file(self, temp_prd_file):
        """Test file loading."""
        parser = PRDParser(temp_prd_file)
        parser.load()
        
        assert len(parser.content) > 0
        assert len(parser.lines) > 0
        assert "Test Product Requirements Document" in parser.content
    
    def test_extract_metadata(self, temp_prd_file):
        """Test metadata extraction."""
        parser = PRDParser(temp_prd_file)
        parser.load()
        parser._extract_metadata()
        
        assert parser.metadata is not None
        assert parser.metadata.title == "Test Product Requirements Document"
        assert len(parser.metadata.sections) > 0
        assert "## 1. Executive Summary" in parser.metadata.sections
    
    def test_extract_phases(self, temp_prd_file):
        """Test phase extraction."""
        parser = PRDParser(temp_prd_file)
        parser.load()
        parser._extract_phases()
        
        assert len(parser.phases) == 2
        assert parser.phases[0].name == "Infrastructure Setup"
        assert parser.phases[0].priority == "critical"
        assert parser.phases[1].name == "Blue-Green Implementation"
        assert parser.phases[1].priority == "high"
        
        # Check tasks in phases
        assert len(parser.phases[0].tasks) == 3
        assert len(parser.phases[1].tasks) == 3
        
        # Check task details
        first_task = parser.phases[0].tasks[0]
        assert first_task.title == "Create Terraform configurations for kind cluster"
        assert first_task.priority == "critical"
        assert first_task.status == TaskStatus.PENDING.value
    
    def test_extract_feature_tasks(self, temp_prd_file):
        """Test feature task extraction."""
        parser = PRDParser(temp_prd_file)
        parser.load()
        parser._extract_feature_tasks()
        
        # Should extract tasks from feature requirements section
        feature_tasks = [task for task in parser.tasks if task.phase == "Feature Implementation"]
        assert len(feature_tasks) >= 2  # At least 2 feature tasks
        
        # Check blue-green tasks
        bg_tasks = [task for task in feature_tasks if "blue-green" in task.title.lower()]
        assert len(bg_tasks) >= 1
        
        # Check canary tasks
        canary_tasks = [task for task in feature_tasks if "canary" in task.title.lower()]
        assert len(canary_tasks) >= 1
    
    def test_full_parse(self, temp_prd_file):
        """Test complete parsing."""
        parser = PRDParser(temp_prd_file)
        result = parser.parse()
        
        # Check result structure
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "phases" in result
        assert "tasks" in result
        
        # Check metadata
        metadata = result["metadata"]
        assert metadata["title"] == "Test Product Requirements Document"
        assert metadata["total_phases"] == 2
        assert metadata["total_tasks"] > 0
        
        # Check phases
        phases = result["phases"]
        assert len(phases) == 2
        assert phases[0]["name"] == "Infrastructure Setup"
        assert phases[1]["name"] == "Blue-Green Implementation"
        
        # Check tasks
        tasks = result["tasks"]
        assert len(tasks) > 0
        
        # Verify task structure
        for task in tasks:
            assert "id" in task
            assert "title" in task
            assert "phase" in task
            assert "priority" in task
            assert "status" in task
            assert "dependencies" in task
    
    def test_task_id_generation(self, temp_prd_file):
        """Test task ID generation."""
        parser = PRDParser(temp_prd_file)
        result = parser.parse()
        
        tasks = result["tasks"]
        
        # Check that all task IDs are unique
        task_ids = [task["id"] for task in tasks]
        assert len(task_ids) == len(set(task_ids))
        
        # Check ID format
        for task_id in task_ids:
            assert isinstance(task_id, str)
            assert len(task_id) > 0
    
    def test_priority_extraction(self, temp_prd_file):
        """Test priority extraction from phases."""
        parser = PRDParser(temp_prd_file)
        result = parser.parse()
        
        phases = result["phases"]
        
        # Check that priorities are correctly extracted
        priorities = [phase["priority"] for phase in phases]
        assert "critical" in priorities
        assert "high" in priorities
    
    def test_save_to_json(self, temp_prd_file):
        """Test saving to JSON file."""
        parser = PRDParser(temp_prd_file)
        result = parser.parse()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            parser.save_to_json(temp_file.name)
            
            # Verify file was created and contains valid JSON
            assert os.path.exists(temp_file.name)
            
            with open(temp_file.name, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["metadata"]["title"] == result["metadata"]["title"]
            assert len(saved_data["phases"]) == len(result["phases"])
            assert len(saved_data["tasks"]) == len(result["tasks"])
            
            os.unlink(temp_file.name)
    
    def test_save_to_yaml(self, temp_prd_file):
        """Test saving to YAML file."""
        parser = PRDParser(temp_prd_file)
        result = parser.parse()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            parser.save_to_yaml(temp_file.name)
            
            # Verify file was created and contains valid YAML
            assert os.path.exists(temp_file.name)
            
            with open(temp_file.name, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data["metadata"]["title"] == result["metadata"]["title"]
            assert len(saved_data["phases"]) == len(result["phases"])
            assert len(saved_data["tasks"]) == len(result["tasks"])
            
            os.unlink(temp_file.name)
    
    def test_parse_prd_convenience_function(self, temp_prd_file):
        """Test the convenience parse_prd function."""
        from prd_parser import parse_prd
        
        result = parse_prd(temp_prd_file)
        
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "phases" in result
        assert "tasks" in result
        assert result["metadata"]["title"] == "Test Product Requirements Document"
    
    def test_empty_file_handling(self):
        """Test handling of empty PRD file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write("")
            temp_file.flush()
            
            parser = PRDParser(temp_file.name)
            result = parser.parse()
            
            assert result["metadata"]["title"] == ""
            assert len(result["phases"]) == 0
            assert len(result["tasks"]) == 0
            
            os.unlink(temp_file.name)
    
    def test_malformed_prd_handling(self):
        """Test handling of malformed PRD content."""
        malformed_content = """
# Test PRD
## 4. Feature Requirements
- [ ] Task without proper phase
## 6. Implementation Phases
### Phase 1: Test Phase (Priority: Invalid)
- [ ] Task in invalid phase
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(malformed_content)
            temp_file.flush()
            
            parser = PRDParser(temp_file.name)
            result = parser.parse()
            
            # Should still parse what it can
            assert result["metadata"]["title"] == "Test PRD"
            assert len(result["phases"]) >= 0
            assert len(result["tasks"]) >= 0
            
            os.unlink(temp_file.name)
    
    def test_line_number_tracking(self, temp_prd_file):
        """Test that line numbers are correctly tracked."""
        parser = PRDParser(temp_prd_file)
        result = parser.parse()
        
        tasks = result["tasks"]
        
        # All tasks should have line numbers
        for task in tasks:
            assert "line_number" in task
            assert isinstance(task["line_number"], int)
            assert task["line_number"] > 0
    
    def test_section_tracking(self, temp_prd_file):
        """Test that sections are correctly tracked."""
        parser = PRDParser(temp_prd_file)
        result = parser.parse()
        
        tasks = result["tasks"]
        
        # Check that tasks have appropriate sections
        for task in tasks:
            assert "section" in task
            assert isinstance(task["section"], str)
            assert len(task["section"]) > 0
