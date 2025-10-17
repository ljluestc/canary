#!/usr/bin/env python3
"""
Comprehensive test suite for Monitoring Service.
"""

import unittest
import tempfile
import os
import sys
import time
import requests
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from monitoring_service import (
    AlertRule, Alert, ServiceHealth, MetricsCollector, HealthChecker,
    AlertManager, MonitoringService, app
)

class TestAlertRule(unittest.TestCase):
    """Test AlertRule model."""
    
    def test_alert_rule_creation(self):
        """Test AlertRule creation with all fields."""
        rule = AlertRule(
            name="test_rule",
            condition="cpu_usage",
            threshold=80.0,
            operator=">",
            severity="warning",
            message="CPU usage is high",
            enabled=True,
            cooldown=300
        )
        
        self.assertEqual(rule.name, "test_rule")
        self.assertEqual(rule.condition, "cpu_usage")
        self.assertEqual(rule.threshold, 80.0)
        self.assertEqual(rule.operator, ">")
        self.assertEqual(rule.severity, "warning")
        self.assertEqual(rule.message, "CPU usage is high")
        self.assertEqual(rule.enabled, True)
        self.assertEqual(rule.cooldown, 300)
        self.assertIsNotNone(rule.last_triggered)
    
    def test_alert_rule_defaults(self):
        """Test AlertRule with default values."""
        rule = AlertRule(
            name="default_rule",
            condition="memory_usage",
            threshold=90.0,
            operator=">=",
            severity="critical",
            message="Memory usage is critical"
        )
        
        self.assertEqual(rule.enabled, True)
        self.assertEqual(rule.cooldown, 300)
        self.assertIsNotNone(rule.last_triggered)

class TestAlert(unittest.TestCase):
    """Test Alert model."""
    
    def test_alert_creation(self):
        """Test Alert creation with all fields."""
        now = datetime.now()
        alert = Alert(
            id="alert123",
            rule_name="test_rule",
            message="Test alert message",
            severity="warning",
            triggered_at=now,
            resolved_at=now + timedelta(minutes=5),
            is_resolved=True
        )
        
        self.assertEqual(alert.id, "alert123")
        self.assertEqual(alert.rule_name, "test_rule")
        self.assertEqual(alert.message, "Test alert message")
        self.assertEqual(alert.severity, "warning")
        self.assertEqual(alert.triggered_at, now)
        self.assertEqual(alert.is_resolved, True)
        self.assertIsNotNone(alert.resolved_at)
    
    def test_alert_defaults(self):
        """Test Alert with default values."""
        alert = Alert(
            id="alert456",
            rule_name="default_rule",
            message="Default alert",
            severity="info",
            triggered_at=datetime.now()
        )
        
        self.assertIsNone(alert.resolved_at)
        self.assertEqual(alert.is_resolved, False)

class TestServiceHealth(unittest.TestCase):
    """Test ServiceHealth model."""
    
    def test_service_health_creation(self):
        """Test ServiceHealth creation with all fields."""
        now = datetime.now()
        health = ServiceHealth(
            service_name="test_service",
            status="healthy",
            response_time=0.5,
            last_check=now,
            error_message="",
            uptime=3600.0,
            version="1.0.0"
        )
        
        self.assertEqual(health.service_name, "test_service")
        self.assertEqual(health.status, "healthy")
        self.assertEqual(health.response_time, 0.5)
        self.assertEqual(health.last_check, now)
        self.assertEqual(health.error_message, "")
        self.assertEqual(health.uptime, 3600.0)
        self.assertEqual(health.version, "1.0.0")
    
    def test_service_health_defaults(self):
        """Test ServiceHealth with default values."""
        health = ServiceHealth(
            service_name="default_service",
            status="unknown",
            response_time=0.0,
            last_check=datetime.now()
        )
        
        self.assertEqual(health.error_message, "")
        self.assertEqual(health.uptime, 0.0)
        self.assertEqual(health.version, "")

class TestMetricsCollector(unittest.TestCase):
    """Test MetricsCollector class."""
    
    def setUp(self):
        """Set up test metrics collector."""
        self.collector = MetricsCollector()
        self.collector.collection_interval = 0.1  # Fast collection for testing
    
    def test_metrics_collector_creation(self):
        """Test MetricsCollector creation."""
        self.assertFalse(self.collector.running)
        self.assertIsNone(self.collector.thread)
        self.assertEqual(self.collector.collection_interval, 0.1)
    
    def test_start_stop(self):
        """Test starting and stopping metrics collector."""
        self.collector.start()
        self.assertTrue(self.collector.running)
        self.assertIsNotNone(self.collector.thread)
        
        # Let it run briefly
        time.sleep(0.2)
        
        self.collector.stop()
        self.assertFalse(self.collector.running)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection."""
        # Mock system metrics
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=70.0)
        
        # Mock net_connections
        with patch('psutil.net_connections') as mock_connections:
            mock_connections.return_value = [Mock(), Mock()]  # 2 connections
            
            self.collector._collect_system_metrics()
            
            # Verify metrics were set (we can't easily test Prometheus metrics directly)
            # but we can verify the methods were called
            mock_cpu.assert_called_once()
            mock_memory.assert_called_once()
            mock_disk.assert_called_once()

class TestHealthChecker(unittest.TestCase):
    """Test HealthChecker class."""
    
    def setUp(self):
        """Set up test health checker."""
        self.checker = HealthChecker()
        self.checker.check_interval = 0.1  # Fast checking for testing
    
    def test_health_checker_creation(self):
        """Test HealthChecker creation."""
        self.assertEqual(len(self.checker.services), 0)
        self.assertFalse(self.checker.running)
        self.assertIsNone(self.checker.thread)
    
    def test_add_service(self):
        """Test adding a service."""
        self.checker.add_service("test_service", "http://localhost:8080/health", "1.0.0")
        
        self.assertEqual(len(self.checker.services), 1)
        self.assertIn("test_service", self.checker.services)
        
        service = self.checker.services["test_service"]
        self.assertEqual(service.service_name, "test_service")
        self.assertEqual(service.status, "unknown")
        self.assertEqual(service.version, "1.0.0")
    
    def test_get_service_health(self):
        """Test getting service health."""
        self.checker.add_service("test_service", "http://localhost:8080/health")
        
        health = self.checker.get_service_health("test_service")
        self.assertIsNotNone(health)
        self.assertEqual(health.service_name, "test_service")
        
        # Test non-existent service
        health = self.checker.get_service_health("nonexistent")
        self.assertIsNone(health)
    
    def test_get_all_services_health(self):
        """Test getting all services health."""
        self.checker.add_service("service1", "http://localhost:8080/health")
        self.checker.add_service("service2", "http://localhost:8081/health")
        
        all_health = self.checker.get_all_services_health()
        self.assertEqual(len(all_health), 2)
        self.assertIn("service1", all_health)
        self.assertIn("service2", all_health)
    
    @patch('requests.get')
    def test_check_service_health_success(self, mock_get):
        """Test successful service health check."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        service = ServiceHealth(
            service_name="test_service",
            status="unknown",
            response_time=0.0,
            last_check=datetime.now()
        )
        
        self.checker._check_service_health(service)
        
        self.assertEqual(service.status, "healthy")
        self.assertGreater(service.response_time, 0)
        self.assertEqual(service.error_message, "")
    
    @patch('requests.get')
    def test_check_service_health_failure(self, mock_get):
        """Test failed service health check."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        service = ServiceHealth(
            service_name="test_service",
            status="unknown",
            response_time=0.0,
            last_check=datetime.now()
        )
        
        self.checker._check_service_health(service)
        
        self.assertEqual(service.status, "unhealthy")
        self.assertIn("HTTP 500", service.error_message)
    
    @patch('requests.get')
    def test_check_service_health_timeout(self, mock_get):
        """Test service health check timeout."""
        # Mock timeout
        mock_get.side_effect = requests.exceptions.Timeout()
        
        service = ServiceHealth(
            service_name="test_service",
            status="unknown",
            response_time=0.0,
            last_check=datetime.now()
        )
        
        self.checker._check_service_health(service)
        
        self.assertEqual(service.status, "unhealthy")
        self.assertEqual(service.error_message, "Timeout")
    
    @patch('requests.get')
    def test_check_service_health_connection_error(self, mock_get):
        """Test service health check connection error."""
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        service = ServiceHealth(
            service_name="test_service",
            status="unknown",
            response_time=0.0,
            last_check=datetime.now()
        )
        
        self.checker._check_service_health(service)
        
        self.assertEqual(service.status, "unhealthy")
        self.assertEqual(service.error_message, "Connection refused")

class TestAlertManager(unittest.TestCase):
    """Test AlertManager class."""
    
    def setUp(self):
        """Set up test alert manager."""
        self.manager = AlertManager()
        self.manager.check_interval = 0.1  # Fast checking for testing
    
    def test_alert_manager_creation(self):
        """Test AlertManager creation."""
        self.assertEqual(len(self.manager.rules), 0)
        self.assertEqual(len(self.manager.active_alerts), 0)
        self.assertFalse(self.manager.running)
        self.assertIsNone(self.manager.thread)
    
    def test_add_rule(self):
        """Test adding an alert rule."""
        rule = AlertRule(
            name="test_rule",
            condition="cpu_usage",
            threshold=80.0,
            operator=">",
            severity="warning",
            message="CPU usage is high"
        )
        
        self.manager.add_rule(rule)
        self.assertEqual(len(self.manager.rules), 1)
        self.assertEqual(self.manager.rules[0].name, "test_rule")
    
    def test_resolve_alert(self):
        """Test resolving an alert."""
        alert = Alert(
            id="alert123",
            rule_name="test_rule",
            message="Test alert",
            severity="warning",
            triggered_at=datetime.now()
        )
        
        self.manager.active_alerts.append(alert)
        self.assertFalse(alert.is_resolved)
        
        self.manager.resolve_alert("alert123")
        self.assertTrue(alert.is_resolved)
        self.assertIsNotNone(alert.resolved_at)
    
    def test_resolve_nonexistent_alert(self):
        """Test resolving non-existent alert."""
        # Should not raise an exception
        self.manager.resolve_alert("nonexistent")
    
    def test_get_active_alerts(self):
        """Test getting active alerts."""
        alert1 = Alert("alert1", "rule1", "Message 1", "warning", datetime.now())
        alert2 = Alert("alert2", "rule2", "Message 2", "critical", datetime.now())
        alert3 = Alert("alert3", "rule3", "Message 3", "info", datetime.now())
        alert3.is_resolved = True
        
        self.manager.active_alerts = [alert1, alert2, alert3]
        
        active_alerts = self.manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 2)
        self.assertIn(alert1, active_alerts)
        self.assertIn(alert2, active_alerts)
        self.assertNotIn(alert3, active_alerts)
    
    def test_get_all_alerts(self):
        """Test getting all alerts."""
        alert1 = Alert("alert1", "rule1", "Message 1", "warning", datetime.now())
        alert2 = Alert("alert2", "rule2", "Message 2", "critical", datetime.now())
        
        self.manager.active_alerts = [alert1, alert2]
        
        all_alerts = self.manager.get_all_alerts()
        self.assertEqual(len(all_alerts), 2)
        self.assertIn(alert1, all_alerts)
        self.assertIn(alert2, all_alerts)
    
    @patch('psutil.cpu_percent')
    def test_evaluate_rule_cpu_high(self, mock_cpu):
        """Test evaluating CPU usage rule."""
        mock_cpu.return_value = 85.0
        
        rule = AlertRule(
            name="high_cpu",
            condition="cpu_usage",
            threshold=80.0,
            operator=">",
            severity="warning",
            message="CPU is high"
        )
        
        result = self.manager._evaluate_rule(rule)
        self.assertTrue(result)
    
    @patch('psutil.cpu_percent')
    def test_evaluate_rule_cpu_low(self, mock_cpu):
        """Test evaluating CPU usage rule with low usage."""
        mock_cpu.return_value = 50.0
        
        rule = AlertRule(
            name="high_cpu",
            condition="cpu_usage",
            threshold=80.0,
            operator=">",
            severity="warning",
            message="CPU is high"
        )
        
        result = self.manager._evaluate_rule(rule)
        self.assertFalse(result)
    
    @patch('psutil.virtual_memory')
    def test_evaluate_rule_memory(self, mock_memory):
        """Test evaluating memory usage rule."""
        mock_memory.return_value = Mock(percent=90.0)
        
        rule = AlertRule(
            name="high_memory",
            condition="memory_usage",
            threshold=85.0,
            operator=">=",
            severity="critical",
            message="Memory is critical"
        )
        
        result = self.manager._evaluate_rule(rule)
        self.assertTrue(result)
    
    def test_evaluate_rule_unknown_condition(self):
        """Test evaluating rule with unknown condition."""
        rule = AlertRule(
            name="unknown_rule",
            condition="unknown_metric",
            threshold=50.0,
            operator=">",
            severity="warning",
            message="Unknown metric"
        )
        
        result = self.manager._evaluate_rule(rule)
        self.assertFalse(result)
    
    def test_trigger_alert(self):
        """Test triggering an alert."""
        rule = AlertRule(
            name="test_rule",
            condition="cpu_usage",
            threshold=80.0,
            operator=">",
            severity="warning",
            message="CPU is high"
        )
        
        initial_count = len(self.manager.active_alerts)
        self.manager._trigger_alert(rule)
        
        self.assertEqual(len(self.manager.active_alerts), initial_count + 1)
        self.assertIsNotNone(rule.last_triggered)
        
        alert = self.manager.active_alerts[-1]
        self.assertEqual(alert.rule_name, "test_rule")
        self.assertEqual(alert.message, "CPU is high")
        self.assertEqual(alert.severity, "warning")

class TestMonitoringService(unittest.TestCase):
    """Test MonitoringService class."""
    
    def setUp(self):
        """Set up test monitoring service."""
        self.service = MonitoringService()
    
    def test_monitoring_service_creation(self):
        """Test MonitoringService creation."""
        self.assertIsNotNone(self.service.metrics_collector)
        self.assertIsNotNone(self.service.health_checker)
        self.assertIsNotNone(self.service.alert_manager)
        self.assertIsNotNone(self.service.start_time)
    
    def test_setup_default_alerts(self):
        """Test default alert setup."""
        # Should have some default alerts
        self.assertGreater(len(self.service.alert_manager.rules), 0)
        
        # Check for common alert types
        rule_names = [rule.name for rule in self.service.alert_manager.rules]
        self.assertIn("high_cpu_usage", rule_names)
        self.assertIn("high_memory_usage", rule_names)
    
    def test_setup_default_services(self):
        """Test default service setup."""
        # Should have some default services
        self.assertGreater(len(self.service.health_checker.services), 0)
        
        # Check for common services
        service_names = list(self.service.health_checker.services.keys())
        self.assertIn("tinyurl", service_names)
        self.assertIn("newsfeed", service_names)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test getting system metrics."""
        # Mock system metrics
        mock_cpu.return_value = 45.0
        mock_memory.return_value = Mock(percent=60.0, available=1024*1024*1024, total=2*1024*1024*1024)
        mock_disk.return_value = Mock(percent=70.0, free=500*1024*1024*1024, total=1000*1024*1024*1024)
        
        metrics = self.service.get_system_metrics()
        
        self.assertEqual(metrics['cpu_usage'], 45.0)
        self.assertEqual(metrics['memory_usage'], 60.0)
        self.assertEqual(metrics['disk_usage'], 70.0)
        self.assertIn('uptime', metrics)
        self.assertIn('timestamp', metrics)
    
    def test_get_services_health(self):
        """Test getting services health."""
        health = self.service.get_services_health()
        
        self.assertIsInstance(health, dict)
        self.assertGreater(len(health), 0)
        
        # Check structure of health data
        for service_name, service_data in health.items():
            self.assertIn('status', service_data)
            self.assertIn('response_time', service_data)
            self.assertIn('last_check', service_data)
            self.assertIn('error_message', service_data)
            self.assertIn('uptime', service_data)
            self.assertIn('version', service_data)
    
    def test_get_alerts(self):
        """Test getting alerts."""
        alerts = self.service.get_alerts()
        
        self.assertIn('active_alerts', alerts)
        self.assertIn('all_alerts', alerts)
        self.assertIn('total_active', alerts)
        self.assertIn('total_resolved', alerts)
        
        self.assertIsInstance(alerts['active_alerts'], list)
        self.assertIsInstance(alerts['all_alerts'], list)
        self.assertIsInstance(alerts['total_active'], int)
        self.assertIsInstance(alerts['total_resolved'], int)

class TestFlaskApp(unittest.TestCase):
    """Test Flask application endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_index_page(self):
        """Test dashboard page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Monitoring Dashboard', response.data)
    
    def test_prometheus_metrics(self):
        """Test Prometheus metrics endpoint."""
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'http_requests_total', response.data)
    
    def test_get_metrics_api(self):
        """Test get metrics API."""
        response = self.client.get('/api/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('metrics', data)
    
    def test_get_health_api(self):
        """Test get health API."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('health', data)
    
    def test_get_alerts_api(self):
        """Test get alerts API."""
        response = self.client.get('/api/alerts')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('alerts', data)
    
    def test_resolve_alert_api(self):
        """Test resolve alert API."""
        response = self.client.post('/api/alerts/test_alert/resolve')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('resolved', data['message'])
    
    def test_get_rules_api(self):
        """Test get rules API."""
        response = self.client.get('/api/rules')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('rules', data)
    
    def test_add_rule_api(self):
        """Test add rule API."""
        response = self.client.post('/api/rules', json={
            'name': 'test_rule',
            'condition': 'cpu_usage',
            'threshold': 90.0,
            'operator': '>',
            'severity': 'critical',
            'message': 'CPU is critical'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('added successfully', data['message'])
    
    def test_add_rule_missing_fields(self):
        """Test add rule API with missing fields."""
        response = self.client.post('/api/rules', json={
            'name': 'incomplete_rule'
            # Missing required fields
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('uptime', data)

if __name__ == '__main__':
    unittest.main()
