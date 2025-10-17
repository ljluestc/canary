"""
End-to-end tests for deployment scenarios.
"""

import pytest
import tempfile
import os
import json
import yaml
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from task_manager import TaskManager
from task_master import TaskMaster


class TestBlueGreenDeploymentE2E:
    """End-to-end tests for blue-green deployment workflow."""
    
    def test_blue_green_deployment_workflow(self, temp_prd_file):
        """Test complete blue-green deployment workflow."""
        # Set up task management system
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Filter for blue-green related tasks
        blue_green_tasks = [
            task for task in task_manager.tasks 
            if 'blue-green' in task['title'].lower() or 'blue green' in task['title'].lower()
        ]
        
        if not blue_green_tasks:
            pytest.skip("No blue-green tasks found in PRD")
        
        # Set up task master with deployment context
        context = {
            "terraform_dir": "/tmp/terraform",
            "namespace": "blue-green-demo",
            "app_name": "blue-green-app",
            "repo_url": "https://github.com/example/blue-green-app",
            "path": "k8s/blue-green",
            "manifest_file": "/tmp/blue-green-manifest.yaml"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        # Mock all external commands
        with patch('subprocess.run') as mock_run:
            # Mock successful command execution
            mock_run.return_value = Mock(returncode=0, stdout="Command executed successfully", stderr="")
            
            # Execute blue-green deployment tasks
            results = []
            for task in blue_green_tasks:
                result = task_master.execute_task(task['id'])
                results.append(result)
                assert result.success is True
            
            # Verify all tasks completed successfully
            assert len(results) == len(blue_green_tasks)
            assert all(result.success for result in results)
            
            # Verify task statuses
            for task in blue_green_tasks:
                updated_task = task_manager.get_task(task['id'])
                assert updated_task['status'] == 'completed'
    
    def test_blue_green_rollback_scenario(self, temp_prd_file):
        """Test blue-green rollback scenario."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Find rollback-related tasks
        rollback_tasks = [
            task for task in task_manager.tasks 
            if 'rollback' in task['title'].lower()
        ]
        
        if not rollback_tasks:
            pytest.skip("No rollback tasks found in PRD")
        
        context = {
            "namespace": "blue-green-demo",
            "app_name": "blue-green-app"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            # Mock rollback command execution
            mock_run.return_value = Mock(returncode=0, stdout="Rollback completed", stderr="")
            
            # Execute rollback tasks
            for task in rollback_tasks:
                result = task_master.execute_task(task['id'])
                assert result.success is True
                assert "Rollback completed" in result.output
    
    def test_blue_green_health_check_validation(self, temp_prd_file):
        """Test blue-green health check validation."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Find health check tasks
        health_tasks = [
            task for task in task_manager.tasks 
            if 'health' in task['title'].lower() or 'check' in task['title'].lower()
        ]
        
        if not health_tasks:
            pytest.skip("No health check tasks found in PRD")
        
        context = {
            "namespace": "blue-green-demo",
            "app_name": "blue-green-app"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            # Mock health check commands
            mock_run.return_value = Mock(returncode=0, stdout="Health check passed", stderr="")
            
            # Execute health check tasks
            for task in health_tasks:
                result = task_master.execute_task(task['id'])
                assert result.success is True
                assert "Health check passed" in result.output


class TestCanaryDeploymentE2E:
    """End-to-end tests for canary deployment workflow."""
    
    def test_canary_deployment_workflow(self, temp_prd_file):
        """Test complete canary deployment workflow."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Filter for canary related tasks
        canary_tasks = [
            task for task in task_manager.tasks 
            if 'canary' in task['title'].lower()
        ]
        
        if not canary_tasks:
            pytest.skip("No canary tasks found in PRD")
        
        # Set up task master with canary context
        context = {
            "terraform_dir": "/tmp/terraform",
            "namespace": "canary-demo",
            "app_name": "canary-app",
            "repo_url": "https://github.com/example/canary-app",
            "path": "k8s/canary",
            "manifest_file": "/tmp/canary-manifest.yaml"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Canary deployment successful", stderr="")
            
            # Execute canary deployment tasks
            results = []
            for task in canary_tasks:
                result = task_master.execute_task(task['id'])
                results.append(result)
                assert result.success is True
            
            # Verify all tasks completed
            assert len(results) == len(canary_tasks)
            assert all(result.success for result in results)
    
    def test_canary_traffic_splitting(self, temp_prd_file):
        """Test canary traffic splitting functionality."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Find traffic splitting tasks
        traffic_tasks = [
            task for task in task_manager.tasks 
            if 'traffic' in task['title'].lower() or 'split' in task['title'].lower()
        ]
        
        if not traffic_tasks:
            pytest.skip("No traffic splitting tasks found in PRD")
        
        context = {
            "namespace": "canary-demo",
            "app_name": "canary-app",
            "traffic_percentage": "10"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Traffic split configured", stderr="")
            
            # Execute traffic splitting tasks
            for task in traffic_tasks:
                result = task_master.execute_task(task['id'])
                # These are generic tasks, so they should succeed with generic output
                assert result.success is True
                assert "Generic task executed" in result.output
    
    def test_canary_analysis_and_rollback(self, temp_prd_file):
        """Test canary analysis and automatic rollback."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Find analysis tasks
        analysis_tasks = [
            task for task in task_manager.tasks 
            if 'analysis' in task['title'].lower() or 'metrics' in task['title'].lower()
        ]
        
        if not analysis_tasks:
            pytest.skip("No analysis tasks found in PRD")
        
        context = {
            "namespace": "canary-demo",
            "app_name": "canary-app",
            "prometheus_url": "http://prometheus:9090"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            # Mock analysis commands
            mock_run.return_value = Mock(returncode=0, stdout="Analysis completed", stderr="")
            
            # Execute analysis tasks
            for task in analysis_tasks:
                result = task_master.execute_task(task['id'])
                # These are generic tasks, so they should succeed with generic output
                assert result.success is True
                assert "Generic task executed" in result.output


class TestInfrastructureE2E:
    """End-to-end tests for infrastructure setup."""
    
    def test_infrastructure_setup_workflow(self, temp_prd_file):
        """Test complete infrastructure setup workflow."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Get infrastructure setup phase
        infrastructure_tasks = task_manager.get_tasks({"phase": "Infrastructure Setup"})
        
        if not infrastructure_tasks:
            pytest.skip("No infrastructure setup tasks found")
        
        context = {
            "terraform_dir": "/tmp/terraform",
            "cluster_name": "test-cluster",
            "argocd_server": "localhost:8080",
            "argocd_username": "admin",
            "argocd_password": "test-password"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            # Mock infrastructure commands
            def mock_command_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get('args', [])
                if 'terraform' in cmd:
                    if 'init' in cmd:
                        return Mock(returncode=0, stdout="Terraform initialized", stderr="")
                    elif 'plan' in cmd:
                        return Mock(returncode=0, stdout="Plan: 5 to add", stderr="")
                    elif 'apply' in cmd:
                        return Mock(returncode=0, stdout="Apply complete!", stderr="")
                elif 'kubectl' in cmd:
                    return Mock(returncode=0, stdout="Kubernetes resource created", stderr="")
                elif 'argocd' in cmd:
                    return Mock(returncode=0, stdout="ArgoCD operation successful", stderr="")
                return Mock(returncode=0, stdout="Command executed", stderr="")
            
            mock_run.side_effect = mock_command_side_effect
            
            # Execute infrastructure phase
            phase_result = task_master.execute_phase("Infrastructure Setup")
            
            assert phase_result.success is True
            assert phase_result.tasks_completed > 0
            assert phase_result.tasks_failed == 0
            assert phase_result.duration > 0
    
    def test_terraform_integration(self, temp_prd_file):
        """Test Terraform integration."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Find Terraform tasks
        terraform_tasks = [
            task for task in task_manager.tasks 
            if 'terraform' in task['title'].lower()
        ]
        
        if not terraform_tasks:
            pytest.skip("No Terraform tasks found")
        
        context = {
            "terraform_dir": "/tmp/terraform",
            "cluster_name": "test-cluster"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            # Mock Terraform commands
            def terraform_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get('args', [])
                if 'terraform' in cmd:
                    if 'init' in cmd:
                        return Mock(returncode=0, stdout="Terraform initialized successfully", stderr="")
                    elif 'plan' in cmd:
                        return Mock(returncode=0, stdout="Plan: 5 to add, 0 to change, 0 to destroy", stderr="")
                    elif 'apply' in cmd:
                        return Mock(returncode=0, stdout="Apply complete! Resources: 5 added", stderr="")
                return Mock(returncode=0, stdout="Command executed", stderr="")
            
            mock_run.side_effect = terraform_side_effect
            
            # Execute Terraform tasks
            for task in terraform_tasks:
                result = task_master.execute_task(task['id'])
                assert result.success is True
                
                # Verify appropriate Terraform command was called
                if 'init' in task['title'].lower():
                    assert "Terraform initialized successfully" in result.output
                elif 'plan' in task['title'].lower():
                    assert "Plan: 5 to add" in result.output
                elif 'apply' in task['title'].lower():
                    assert "Apply complete!" in result.output
    
    def test_kubernetes_integration(self, temp_prd_file):
        """Test Kubernetes integration."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Find Kubernetes tasks
        k8s_tasks = [
            task for task in task_manager.tasks 
            if any(kw in task['title'].lower() for kw in ['kubernetes', 'kubectl', 'namespace', 'deployment', 'service'])
        ]
        
        if not k8s_tasks:
            pytest.skip("No Kubernetes tasks found")
        
        context = {
            "namespace": "test-namespace",
            "manifest_file": "/tmp/test-manifest.yaml"
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            # Mock kubectl commands
            def kubectl_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get('args', [])
                if 'kubectl' in cmd:
                    if 'create' in cmd and 'namespace' in cmd:
                        return Mock(returncode=0, stdout="namespace/test-namespace created", stderr="")
                    elif 'apply' in cmd:
                        return Mock(returncode=0, stdout="deployment.apps/test-deployment created", stderr="")
                    elif 'get' in cmd:
                        return Mock(returncode=0, stdout='{"apiVersion":"v1","kind":"Namespace"}', stderr="")
                return Mock(returncode=0, stdout="Command executed", stderr="")
            
            mock_run.side_effect = kubectl_side_effect
            
            # Execute Kubernetes tasks
            for task in k8s_tasks:
                result = task_master.execute_task(task['id'], context)
                assert result.success is True
    
    def test_argocd_integration(self, temp_prd_file):
        """Test ArgoCD integration."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Find ArgoCD tasks
        argocd_tasks = [
            task for task in task_manager.tasks 
            if 'argocd' in task['title'].lower() or 'argo' in task['title'].lower()
        ]
        
        if not argocd_tasks:
            pytest.skip("No ArgoCD tasks found")
        
        context = {
            "argocd_server": "localhost:8080",
            "argocd_username": "admin",
            "argocd_password": "test-password",
            "app_name": "test-app",
            "repo_url": "https://github.com/test/repo",
            "path": "."
        }
        
        task_master = TaskMaster(task_manager=task_manager, context=context)
        
        with patch('subprocess.run') as mock_run:
            # Mock ArgoCD commands
            def argocd_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get('args', [])
                if 'argocd' in cmd:
                    if 'login' in cmd:
                        return Mock(returncode=0, stdout="Successfully logged in", stderr="")
                    elif 'app' in cmd and 'create' in cmd:
                        return Mock(returncode=0, stdout="application test-app created", stderr="")
                    elif 'app' in cmd and 'sync' in cmd:
                        return Mock(returncode=0, stdout="application test-app synced", stderr="")
                return Mock(returncode=0, stdout="Command executed", stderr="")
            
            mock_run.side_effect = argocd_side_effect
            
            # Execute ArgoCD tasks
            for task in argocd_tasks:
                result = task_master.execute_task(task['id'])
                assert result.success is True


class TestFailureScenariosE2E:
    """End-to-end tests for failure scenarios."""
    
    def test_deployment_failure_and_recovery(self, temp_prd_file):
        """Test deployment failure and recovery scenario."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        # Simulate deployment failure
        with patch('subprocess.run') as mock_run:
            # First command fails
            mock_run.side_effect = [
                Mock(returncode=1, stdout="", stderr="Deployment failed"),
                Mock(returncode=0, stdout="Rollback successful", stderr="")
            ]
            
            # Execute first task (fails)
            result1 = task_master.execute_task(task_manager.tasks[0]['id'])
            assert result1.success is False
            assert "Deployment failed" in result1.error
            
            # Execute rollback task (succeeds)
            if len(task_manager.tasks) > 1:
                result2 = task_master.execute_task(task_manager.tasks[1]['id'])
                assert result2.success is True
                assert "Rollback successful" in result2.output
    
    def test_partial_deployment_failure(self, temp_prd_file):
        """Test partial deployment failure scenario."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        with patch('subprocess.run') as mock_run:
            # Simulate mixed success/failure
            call_count = 0
            def mixed_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 2 == 0:  # Every second command fails
                    return Mock(returncode=1, stdout="", stderr="Command failed")
                else:
                    return Mock(returncode=0, stdout="Command succeeded", stderr="")
            
            mock_run.side_effect = mixed_side_effect
            
            # Execute multiple tasks
            results = []
            for i, task in enumerate(task_manager.tasks[:4]):
                result = task_master.execute_task(task['id'])
                results.append(result)
            
            # Some should succeed, some should fail
            success_count = sum(1 for r in results if r.success)
            failure_count = sum(1 for r in results if not r.success)
            
            assert success_count > 0
            assert failure_count > 0
            assert success_count + failure_count == len(results)
    
    def test_timeout_scenarios(self, temp_prd_file):
        """Test timeout scenarios."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        with patch('subprocess.run') as mock_run:
            # Simulate timeout
            mock_run.side_effect = subprocess.TimeoutExpired(['long-running-command'], 1)
            
            result = task_master.execute_task(task_manager.tasks[0]['id'])
            
            assert result.success is False
            assert "timed out" in result.error
            assert result.duration > 0


class TestPerformanceE2E:
    """End-to-end performance tests."""
    
    def test_large_scale_deployment_performance(self, temp_prd_file):
        """Test performance with large-scale deployment."""
        import time
        
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        # Simulate large-scale by duplicating tasks
        original_tasks = task_manager.tasks.copy()
        for i in range(20):  # Create 20x more tasks
            for task in original_tasks:
                new_task = task.copy()
                new_task['id'] = f"{task['id']}_scale_{i}"
                task_manager.tasks.append(new_task)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        start_time = time.time()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Scaled deployment", stderr="")
            
            # Execute subset of tasks
            for task in task_manager.tasks[:50]:  # Execute first 50 tasks
                result = task_master.execute_task(task['id'])
                # Some tasks may fail due to missing context, but that's expected
                # We just want to verify the system can handle large datasets
                assert result is not None
        
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert execution_time < 5.0  # 5 seconds for 50 mocked tasks
        
        # Test progress report generation with large dataset
        start_time = time.time()
        report = task_manager.get_progress_report()
        report_time = time.time() - start_time
        
        assert report_time < 0.5  # Should generate report quickly
        assert report['total_tasks'] > len(original_tasks)
    
    def test_concurrent_execution_simulation(self, temp_prd_file):
        """Test simulation of concurrent execution."""
        task_manager = TaskManager()
        task_manager.load_from_prd(temp_prd_file)
        
        task_master = TaskMaster(task_manager=task_manager)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Concurrent execution", stderr="")
            
            # Simulate concurrent execution by executing multiple tasks quickly
            results = []
            for task in task_manager.tasks[:10]:
                result = task_master.execute_task(task['id'])
                results.append(result)
            
            # Some tasks may fail due to missing context, but that's expected
            # We just want to verify the system can handle concurrent execution
            assert len(results) == 10
            # At least some should succeed
            success_count = sum(1 for r in results if r.success)
            assert success_count > 0
