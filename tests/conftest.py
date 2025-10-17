"""
Pytest configuration and shared fixtures for the canary deployment system tests.
"""

import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "task-manager"))
sys.path.insert(0, str(project_root / "task-master"))

from prd_parser import PRDParser, Task, Phase, TaskStatus, Priority
from task_manager import TaskManager


@pytest.fixture
def sample_prd_content():
    """Sample PRD content for testing."""
    return """# Test Product Requirements Document

## 1. Executive Summary
This is a test PRD for validation.

## 4. Feature Requirements

### 4.1 Blue-Green Deployment Features
- [ ] Deploy application with blue-green strategy
- [ ] Access preview environment before promotion
- [ ] Manual promotion of new version

### 4.2 Canary Deployment Features
- [ ] Deploy application with canary strategy
- [ ] Gradual traffic shifting (10% → 25% → 50% → 75% → 100%)
- [ ] Automated analysis based on metrics

## 6. Implementation Phases

### Phase 1: Infrastructure Setup (Priority: Critical)
- [ ] Create Terraform configurations for kind cluster
- [ ] Install ArgoCD
- [ ] Install Argo Rollouts

### Phase 2: Blue-Green Implementation (Priority: High)
- [ ] Create Kubernetes namespace
- [ ] Create Rollout manifest with blue-green strategy
- [ ] Create active and preview services
"""


@pytest.fixture
def temp_prd_file(sample_prd_content):
    """Create a temporary PRD file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_prd_content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def sample_tasks_data():
    """Sample tasks data structure."""
    return {
        'metadata': {
            'title': 'Test Project',
            'sections': ['1. Executive Summary', '4. Feature Requirements', '6. Implementation Phases'],
            'total_tasks': 8,
            'total_phases': 2
        },
        'phases': [
            {
                'name': 'Infrastructure Setup',
                'priority': 'critical',
                'tasks': [
                    {
                        'id': 'phase_1_task_1',
                        'title': 'Create Terraform configurations for kind cluster',
                        'phase': 'Infrastructure Setup',
                        'priority': 'critical',
                        'status': 'pending',
                        'dependencies': [],
                        'section': 'Phase 1',
                        'line_number': 15
                    }
                ]
            }
        ],
        'tasks': [
            {
                'id': 'phase_1_task_1',
                'title': 'Create Terraform configurations for kind cluster',
                'phase': 'Infrastructure Setup',
                'priority': 'critical',
                'status': 'pending',
                'dependencies': [],
                'section': 'Phase 1',
                'line_number': 15
            }
        ]
    }


@pytest.fixture
def temp_tasks_file(sample_tasks_data):
    """Create a temporary tasks JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_tasks_data, f)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_tasks_yaml_file(sample_tasks_data):
    """Create a temporary tasks YAML file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_tasks_data, f)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing command execution."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout=b"Command executed successfully",
            stderr=b""
        )
        yield mock_run


@pytest.fixture
def mock_kubectl():
    """Mock kubectl commands."""
    with patch('subprocess.run') as mock_run:
        def kubectl_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if 'kubectl' in cmd:
                if 'get' in cmd:
                    return Mock(returncode=0, stdout=b'{"apiVersion":"v1","kind":"Namespace","metadata":{"name":"test"}}')
                elif 'apply' in cmd:
                    return Mock(returncode=0, stdout=b'namespace/test created')
                elif 'delete' in cmd:
                    return Mock(returncode=0, stdout=b'namespace "test" deleted')
            return Mock(returncode=0, stdout=b"Command executed successfully")
        
        mock_run.side_effect = kubectl_side_effect
        yield mock_run


@pytest.fixture
def mock_terraform():
    """Mock Terraform commands."""
    with patch('subprocess.run') as mock_run:
        def terraform_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if 'terraform' in cmd:
                if 'init' in cmd:
                    return Mock(returncode=0, stdout=b'Terraform initialized successfully')
                elif 'plan' in cmd:
                    return Mock(returncode=0, stdout=b'Plan: 5 to add, 0 to change, 0 to destroy')
                elif 'apply' in cmd:
                    return Mock(returncode=0, stdout=b'Apply complete! Resources: 5 added, 0 changed, 0 destroyed')
                elif 'destroy' in cmd:
                    return Mock(returncode=0, stdout=b'Destroy complete! Resources: 5 destroyed')
            return Mock(returncode=0, stdout=b"Command executed successfully")
        
        mock_run.side_effect = terraform_side_effect
        yield mock_run


@pytest.fixture
def mock_argocd():
    """Mock ArgoCD CLI commands."""
    with patch('subprocess.run') as mock_run:
        def argocd_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if 'argocd' in cmd:
                if 'login' in cmd:
                    return Mock(returncode=0, stdout=b'Successfully logged in')
                elif 'app' in cmd and 'create' in cmd:
                    return Mock(returncode=0, stdout=b'application test-app created')
                elif 'app' in cmd and 'sync' in cmd:
                    return Mock(returncode=0, stdout=b'application test-app synced')
                elif 'app' in cmd and 'get' in cmd:
                    return Mock(returncode=0, stdout=b'Name: test-app\nStatus: Synced')
            return Mock(returncode=0, stdout=b"Command executed successfully")
        
        mock_run.side_effect = argocd_side_effect
        yield mock_run


@pytest.fixture
def test_environment():
    """Set up test environment variables."""
    env_vars = {
        'KUBECONFIG': '/tmp/test-kubeconfig',
        'TF_VAR_cluster_name': 'test-cluster',
        'ARGOCD_SERVER': 'localhost:8080',
        'ARGOCD_USERNAME': 'admin',
        'ARGOCD_PASSWORD': 'test-password'
    }
    
    original_env = {}
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield env_vars
    
    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class MockExecutionResult:
    """Mock execution result for testing."""
    def __init__(self, success=True, output="", error="", duration=1.0):
        self.success = success
        self.output = output
        self.error = error
        self.duration = duration


@pytest.fixture
def mock_execution_result():
    """Mock execution result fixture."""
    return MockExecutionResult
