#!/usr/bin/env python3
"""
Comprehensive test suite for Load Balancer Service.
"""

import unittest
import tempfile
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from load_balancer_service import (
    BackendServer, LoadBalancerConfig, RequestMetrics, HealthChecker,
    CircuitBreaker, RateLimiter, LoadBalancer, app
)

class TestBackendServer(unittest.TestCase):
    """Test BackendServer model."""
    
    def test_backend_server_creation(self):
        """Test BackendServer creation with all fields."""
        server = BackendServer(
            server_id="server1",
            host="localhost",
            port=8080,
            weight=2,
            max_connections=100,
            is_healthy=True,
            active_connections=5,
            total_requests=1000,
            response_time_avg=0.5,
            health_check_path="/health",
            health_check_interval=30,
            timeout=5
        )
        
        self.assertEqual(server.server_id, "server1")
        self.assertEqual(server.host, "localhost")
        self.assertEqual(server.port, 8080)
        self.assertEqual(server.weight, 2)
        self.assertEqual(server.max_connections, 100)
        self.assertEqual(server.is_healthy, True)
        self.assertEqual(server.active_connections, 5)
        self.assertEqual(server.total_requests, 1000)
        self.assertEqual(server.response_time_avg, 0.5)
        self.assertEqual(server.health_check_path, "/health")
        self.assertEqual(server.health_check_interval, 30)
        self.assertEqual(server.timeout, 5)
    
    def test_backend_server_defaults(self):
        """Test BackendServer with default values."""
        server = BackendServer(
            server_id="server2",
            host="example.com",
            port=9000
        )
        
        self.assertEqual(server.weight, 1)
        self.assertEqual(server.max_connections, 100)
        self.assertEqual(server.is_healthy, True)
        self.assertEqual(server.active_connections, 0)
        self.assertEqual(server.total_requests, 0)
        self.assertEqual(server.response_time_avg, 0.0)
        self.assertEqual(server.health_check_path, "/health")
        self.assertEqual(server.health_check_interval, 30)
        self.assertEqual(server.timeout, 5)
        self.assertIsNotNone(server.last_health_check)
    
    def test_backend_server_url(self):
        """Test BackendServer URL property."""
        server = BackendServer(
            server_id="server3",
            host="api.example.com",
            port=443
        )
        
        self.assertEqual(server.url, "http://api.example.com:443")
        self.assertEqual(server.health_check_url, "http://api.example.com:443/health")

class TestLoadBalancerConfig(unittest.TestCase):
    """Test LoadBalancerConfig model."""
    
    def test_config_creation(self):
        """Test LoadBalancerConfig creation with all fields."""
        config = LoadBalancerConfig(
            algorithm="least_connections",
            health_check_enabled=True,
            health_check_interval=60,
            session_persistence=True,
            session_timeout=7200,
            rate_limit_enabled=True,
            rate_limit_requests=500,
            rate_limit_window=1800,
            circuit_breaker_enabled=True,
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout=120,
            ssl_termination=True,
            ssl_cert_path="/path/to/cert.pem",
            ssl_key_path="/path/to/key.pem"
        )
        
        self.assertEqual(config.algorithm, "least_connections")
        self.assertEqual(config.health_check_enabled, True)
        self.assertEqual(config.health_check_interval, 60)
        self.assertEqual(config.session_persistence, True)
        self.assertEqual(config.session_timeout, 7200)
        self.assertEqual(config.rate_limit_enabled, True)
        self.assertEqual(config.rate_limit_requests, 500)
        self.assertEqual(config.rate_limit_window, 1800)
        self.assertEqual(config.circuit_breaker_enabled, True)
        self.assertEqual(config.circuit_breaker_failure_threshold, 3)
        self.assertEqual(config.circuit_breaker_recovery_timeout, 120)
        self.assertEqual(config.ssl_termination, True)
        self.assertEqual(config.ssl_cert_path, "/path/to/cert.pem")
        self.assertEqual(config.ssl_key_path, "/path/to/key.pem")
    
    def test_config_defaults(self):
        """Test LoadBalancerConfig with default values."""
        config = LoadBalancerConfig()
        
        self.assertEqual(config.algorithm, "round_robin")
        self.assertEqual(config.health_check_enabled, True)
        self.assertEqual(config.health_check_interval, 30)
        self.assertEqual(config.session_persistence, False)
        self.assertEqual(config.session_timeout, 3600)
        self.assertEqual(config.rate_limit_enabled, True)
        self.assertEqual(config.rate_limit_requests, 1000)
        self.assertEqual(config.rate_limit_window, 3600)
        self.assertEqual(config.circuit_breaker_enabled, True)
        self.assertEqual(config.circuit_breaker_failure_threshold, 5)
        self.assertEqual(config.circuit_breaker_recovery_timeout, 60)
        self.assertEqual(config.ssl_termination, False)
        self.assertEqual(config.ssl_cert_path, "")
        self.assertEqual(config.ssl_key_path, "")

class TestRequestMetrics(unittest.TestCase):
    """Test RequestMetrics model."""
    
    def test_request_metrics_creation(self):
        """Test RequestMetrics creation with all fields."""
        now = datetime.now()
        metrics = RequestMetrics(
            timestamp=now,
            client_ip="192.168.1.1",
            backend_server="server1",
            response_time=0.5,
            status_code=200,
            bytes_sent=1024,
            user_agent="Mozilla/5.0"
        )
        
        self.assertEqual(metrics.timestamp, now)
        self.assertEqual(metrics.client_ip, "192.168.1.1")
        self.assertEqual(metrics.backend_server, "server1")
        self.assertEqual(metrics.response_time, 0.5)
        self.assertEqual(metrics.status_code, 200)
        self.assertEqual(metrics.bytes_sent, 1024)
        self.assertEqual(metrics.user_agent, "Mozilla/5.0")
    
    def test_request_metrics_defaults(self):
        """Test RequestMetrics with default values."""
        metrics = RequestMetrics(
            timestamp=datetime.now(),
            client_ip="192.168.1.2",
            backend_server="server2",
            response_time=0.3,
            status_code=404,
            bytes_sent=512
        )
        
        self.assertEqual(metrics.user_agent, "")
        self.assertIsNotNone(metrics.timestamp)

class TestCircuitBreaker(unittest.TestCase):
    """Test CircuitBreaker class."""
    
    def test_circuit_breaker_creation(self):
        """Test CircuitBreaker creation."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        self.assertEqual(cb.failure_threshold, 3)
        self.assertEqual(cb.recovery_timeout, 60)
        self.assertEqual(cb.failure_count, 0)
        self.assertIsNone(cb.last_failure_time)
        self.assertEqual(cb.state, "CLOSED")
    
    def test_circuit_breaker_success(self):
        """Test successful call through circuit breaker."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        self.assertEqual(result, "success")
        self.assertEqual(cb.state, "CLOSED")
        self.assertEqual(cb.failure_count, 0)
    
    def test_circuit_breaker_failure(self):
        """Test failed call through circuit breaker."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        
        def failure_func():
            raise Exception("Test error")
        
        # First failure
        with self.assertRaises(Exception):
            cb.call(failure_func)
        self.assertEqual(cb.state, "CLOSED")
        self.assertEqual(cb.failure_count, 1)
        
        # Second failure - should open circuit
        with self.assertRaises(Exception):
            cb.call(failure_func)
        self.assertEqual(cb.state, "OPEN")
        self.assertEqual(cb.failure_count, 2)
        
        # Third call should be blocked
        with self.assertRaises(Exception) as context:
            cb.call(failure_func)
        self.assertIn("Circuit breaker is OPEN", str(context.exception))
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)  # Very short timeout
        
        def failure_func():
            raise Exception("Test error")
        
        # Trigger failure
        with self.assertRaises(Exception):
            cb.call(failure_func)
        self.assertEqual(cb.state, "OPEN")
        
        # Wait for recovery timeout
        time.sleep(0.2)
        
        # Should be in HALF_OPEN state and allow retry
        def success_func():
            return "recovered"
        
        result = cb.call(success_func)
        self.assertEqual(result, "recovered")
        self.assertEqual(cb.state, "CLOSED")

class TestRateLimiter(unittest.TestCase):
    """Test RateLimiter class."""
    
    def test_rate_limiter_creation(self):
        """Test RateLimiter creation."""
        rl = RateLimiter(max_requests=10, window_seconds=60)
        
        self.assertEqual(rl.max_requests, 10)
        self.assertEqual(rl.window_seconds, 60)
        self.assertEqual(len(rl.requests), 0)
    
    def test_rate_limiter_allowed(self):
        """Test rate limiter allowing requests."""
        rl = RateLimiter(max_requests=3, window_seconds=60)
        
        # Should allow first 3 requests
        self.assertTrue(rl.is_allowed("client1"))
        self.assertTrue(rl.is_allowed("client1"))
        self.assertTrue(rl.is_allowed("client1"))
        
        # Should block 4th request
        self.assertFalse(rl.is_allowed("client1"))
    
    def test_rate_limiter_different_clients(self):
        """Test rate limiter with different clients."""
        rl = RateLimiter(max_requests=2, window_seconds=60)
        
        # Each client should have separate limits
        self.assertTrue(rl.is_allowed("client1"))
        self.assertTrue(rl.is_allowed("client2"))
        self.assertTrue(rl.is_allowed("client1"))
        self.assertTrue(rl.is_allowed("client2"))
        
        # Both should be blocked now
        self.assertFalse(rl.is_allowed("client1"))
        self.assertFalse(rl.is_allowed("client2"))
    
    def test_rate_limiter_window_expiry(self):
        """Test rate limiter window expiry."""
        rl = RateLimiter(max_requests=1, window_seconds=0.1)  # Very short window
        
        # First request should be allowed
        self.assertTrue(rl.is_allowed("client1"))
        
        # Second request should be blocked
        self.assertFalse(rl.is_allowed("client1"))
        
        # Wait for window to expire
        time.sleep(0.2)
        
        # Should be allowed again
        self.assertTrue(rl.is_allowed("client1"))

class TestLoadBalancer(unittest.TestCase):
    """Test LoadBalancer class."""
    
    def setUp(self):
        """Set up test load balancer."""
        self.config = LoadBalancerConfig(
            algorithm="round_robin",
            health_check_enabled=False,  # Disable for testing
            rate_limit_enabled=False,    # Disable for testing
            circuit_breaker_enabled=False  # Disable for testing
        )
        self.lb = LoadBalancer(self.config)
    
    def test_add_server(self):
        """Test adding a server."""
        server = BackendServer(
            server_id="test1",
            host="localhost",
            port=8080
        )
        
        self.lb.add_server(server)
        self.assertEqual(len(self.lb.servers), 1)
        self.assertEqual(self.lb.servers[0].server_id, "test1")
    
    def test_remove_server(self):
        """Test removing a server."""
        server1 = BackendServer("test1", "localhost", 8080)
        server2 = BackendServer("test2", "localhost", 8081)
        
        self.lb.add_server(server1)
        self.lb.add_server(server2)
        self.assertEqual(len(self.lb.servers), 2)
        
        self.lb.remove_server("test1")
        self.assertEqual(len(self.lb.servers), 1)
        self.assertEqual(self.lb.servers[0].server_id, "test2")
    
    def test_get_healthy_servers(self):
        """Test getting healthy servers."""
        server1 = BackendServer("test1", "localhost", 8080, is_healthy=True)
        server2 = BackendServer("test2", "localhost", 8081, is_healthy=False)
        
        self.lb.add_server(server1)
        self.lb.add_server(server2)
        
        healthy_servers = self.lb.get_healthy_servers()
        self.assertEqual(len(healthy_servers), 1)
        self.assertEqual(healthy_servers[0].server_id, "test1")
    
    def test_round_robin_selection(self):
        """Test round robin server selection."""
        server1 = BackendServer("test1", "localhost", 8080)
        server2 = BackendServer("test2", "localhost", 8081)
        server3 = BackendServer("test3", "localhost", 8082)
        
        self.lb.add_server(server1)
        self.lb.add_server(server2)
        self.lb.add_server(server3)
        
        # Should cycle through servers
        selected1 = self.lb.select_server()
        selected2 = self.lb.select_server()
        selected3 = self.lb.select_server()
        selected4 = self.lb.select_server()
        
        self.assertEqual(selected1.server_id, "test1")
        self.assertEqual(selected2.server_id, "test2")
        self.assertEqual(selected3.server_id, "test3")
        self.assertEqual(selected4.server_id, "test1")  # Back to first
    
    def test_least_connections_selection(self):
        """Test least connections server selection."""
        self.lb.config.algorithm = "least_connections"
        
        server1 = BackendServer("test1", "localhost", 8080, active_connections=5)
        server2 = BackendServer("test2", "localhost", 8081, active_connections=2)
        server3 = BackendServer("test3", "localhost", 8082, active_connections=8)
        
        self.lb.add_server(server1)
        self.lb.add_server(server2)
        self.lb.add_server(server3)
        
        # Should select server with least connections
        selected = self.lb.select_server()
        self.assertEqual(selected.server_id, "test2")
    
    def test_weighted_round_robin_selection(self):
        """Test weighted round robin server selection."""
        self.lb.config.algorithm = "weighted_round_robin"
        
        server1 = BackendServer("test1", "localhost", 8080, weight=1)
        server2 = BackendServer("test2", "localhost", 8081, weight=3)
        
        self.lb.add_server(server1)
        self.lb.add_server(server2)
        
        # With weights 1:3, server2 should be selected more often
        selections = [self.lb.select_server().server_id for _ in range(8)]
        server2_count = selections.count("test2")
        server1_count = selections.count("test1")
        
        # Server2 should be selected about 3 times more often
        self.assertGreater(server2_count, server1_count)
    
    def test_ip_hash_selection(self):
        """Test IP hash server selection."""
        self.lb.config.algorithm = "ip_hash"
        
        server1 = BackendServer("test1", "localhost", 8080)
        server2 = BackendServer("test2", "localhost", 8081)
        server3 = BackendServer("test3", "localhost", 8082)
        
        self.lb.add_server(server1)
        self.lb.add_server(server2)
        self.lb.add_server(server3)
        
        # Same IP should always select same server
        selected1 = self.lb.select_server(client_ip="192.168.1.1")
        selected2 = self.lb.select_server(client_ip="192.168.1.1")
        self.assertEqual(selected1.server_id, selected2.server_id)
        
        # Different IP might select different server
        selected3 = self.lb.select_server(client_ip="192.168.1.2")
        # Note: This might be the same server due to hash collision, which is fine
    
    def test_no_healthy_servers(self):
        """Test behavior when no healthy servers available."""
        server = BackendServer("test1", "localhost", 8080, is_healthy=False)
        self.lb.add_server(server)
        
        selected = self.lb.select_server()
        self.assertIsNone(selected)
    
    def test_session_persistence(self):
        """Test session persistence."""
        self.lb.config.session_persistence = True
        
        server1 = BackendServer("test1", "localhost", 8080)
        server2 = BackendServer("test2", "localhost", 8081)
        
        self.lb.add_server(server1)
        self.lb.add_server(server2)
        
        # First selection
        selected1 = self.lb.select_server(session_id="session123")
        self.assertIsNotNone(selected1)
        
        # Same session should select same server
        selected2 = self.lb.select_server(session_id="session123")
        self.assertEqual(selected1.server_id, selected2.server_id)
        
        # Different session might select different server
        selected3 = self.lb.select_server(session_id="session456")
        # Note: This might be the same server due to round robin, which is fine
    
    @patch('requests.request')
    def test_forward_request_success(self, mock_request):
        """Test successful request forwarding."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"success": true}'
        mock_request.return_value = mock_response
        
        server = BackendServer("test1", "localhost", 8080)
        self.lb.add_server(server)
        
        status, headers, content = self.lb.forward_request(
            method="GET",
            path="/test",
            headers={"User-Agent": "Test"},
            client_ip="192.168.1.1"
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(content, b'{"success": true}')
        self.assertEqual(server.total_requests, 1)
    
    @patch('requests.request')
    def test_forward_request_failure(self, mock_request):
        """Test request forwarding failure."""
        # Mock failed response
        mock_request.side_effect = Exception("Connection failed")
        
        server = BackendServer("test1", "localhost", 8080)
        self.lb.add_server(server)
        
        status, headers, content = self.lb.forward_request(
            method="GET",
            path="/test",
            headers={"User-Agent": "Test"},
            client_ip="192.168.1.1"
        )
        
        self.assertEqual(status, 502)
        self.assertIn(b"Bad Gateway", content)
    
    def test_forward_request_no_servers(self):
        """Test request forwarding with no servers."""
        status, headers, content = self.lb.forward_request(
            method="GET",
            path="/test",
            headers={"User-Agent": "Test"},
            client_ip="192.168.1.1"
        )
        
        self.assertEqual(status, 503)
        self.assertIn(b"No healthy servers", content)
    
    def test_record_metrics(self):
        """Test metrics recording."""
        server = BackendServer("test1", "localhost", 8080)
        self.lb.add_server(server)
        
        # Record some metrics
        self.lb._record_metrics(
            client_ip="192.168.1.1",
            backend_server="test1",
            response_time=0.5,
            status_code=200,
            bytes_sent=1024,
            user_agent="Test"
        )
        
        self.assertEqual(len(self.lb.metrics), 1)
        metric = self.lb.metrics[0]
        self.assertEqual(metric.client_ip, "192.168.1.1")
        self.assertEqual(metric.backend_server, "test1")
        self.assertEqual(metric.response_time, 0.5)
        self.assertEqual(metric.status_code, 200)
        self.assertEqual(metric.bytes_sent, 1024)
    
    def test_get_metrics(self):
        """Test getting metrics."""
        server = BackendServer("test1", "localhost", 8080)
        self.lb.add_server(server)
        
        # Record some metrics
        self.lb._record_metrics(
            client_ip="192.168.1.1",
            backend_server="test1",
            response_time=0.5,
            status_code=200,
            bytes_sent=1024,
            user_agent="Test"
        )
        
        metrics = self.lb.get_metrics()
        
        self.assertEqual(metrics['total_requests'], 1)
        self.assertEqual(metrics['avg_response_time'], 0.5)
        self.assertEqual(metrics['error_rate'], 0.0)
        self.assertIn('server_metrics', metrics)
        self.assertIn('test1', metrics['server_metrics'])

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
        self.assertIn(b'Load Balancer Dashboard', response.data)
    
    def test_get_metrics_api(self):
        """Test get metrics API."""
        response = self.client.get('/api/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('metrics', data)
        self.assertIn('timestamp', data)
    
    def test_get_servers_api(self):
        """Test get servers API."""
        response = self.client.get('/api/servers')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('servers', data)
        self.assertGreater(len(data['servers']), 0)
    
    def test_add_server_api(self):
        """Test add server API."""
        response = self.client.post('/api/servers', json={
            'server_id': 'test_server',
            'host': 'test.example.com',
            'port': 9000,
            'weight': 2
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('added successfully', data['message'])
    
    def test_add_server_missing_fields(self):
        """Test add server API with missing fields."""
        response = self.client.post('/api/servers', json={
            'server_id': 'test_server'
            # Missing host and port
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_remove_server_api(self):
        """Test remove server API."""
        response = self.client.delete('/api/servers/test_server')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('removed successfully', data['message'])
    
    def test_get_config_api(self):
        """Test get config API."""
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('config', data)
    
    def test_update_config_api(self):
        """Test update config API."""
        response = self.client.post('/api/config', json={
            'algorithm': 'least_connections',
            'session_persistence': True
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('updated successfully', data['message'])
    
    @patch('requests.request')
    def test_proxy_request(self, mock_request):
        """Test request proxying."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"message": "success"}'
        mock_request.return_value = mock_response
        
        response = self.client.get('/api/test')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'success', response.data)
    
    @patch('requests.request')
    def test_proxy_request_failure(self, mock_request):
        """Test request proxying failure."""
        # Mock failed response
        mock_request.side_effect = Exception("Connection failed")
        
        response = self.client.get('/api/test')
        self.assertEqual(response.status_code, 502)
        self.assertIn(b'Bad Gateway', response.data)

if __name__ == '__main__':
    unittest.main()
