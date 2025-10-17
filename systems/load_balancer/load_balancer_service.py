#!/usr/bin/env python3
"""
Load Balancer Service

A comprehensive load balancing system with features like:
- Multiple load balancing algorithms (Round Robin, Least Connections, Weighted Round Robin)
- Health checking and monitoring
- Session persistence
- SSL termination
- Rate limiting
- Circuit breaker pattern
- Metrics collection
"""

import os
import time
import json
import random
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, render_template_string
import requests
from collections import defaultdict, deque
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackendServer:
    """Backend server configuration."""
    server_id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 100
    is_healthy: bool = True
    active_connections: int = 0
    total_requests: int = 0
    response_time_avg: float = 0.0
    last_health_check: datetime = None
    health_check_path: str = "/health"
    health_check_interval: int = 30  # seconds
    timeout: int = 5  # seconds
    
    def __post_init__(self):
        if self.last_health_check is None:
            self.last_health_check = datetime.now()
    
    @property
    def url(self) -> str:
        """Get full URL for the server."""
        return f"http://{self.host}:{self.port}"
    
    @property
    def health_check_url(self) -> str:
        """Get health check URL."""
        return f"{self.url}{self.health_check_path}"

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration."""
    algorithm: str = "round_robin"  # round_robin, least_connections, weighted_round_robin, ip_hash
    health_check_enabled: bool = True
    health_check_interval: int = 30
    session_persistence: bool = False
    session_timeout: int = 3600  # seconds
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 1000
    rate_limit_window: int = 3600  # seconds
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60  # seconds
    ssl_termination: bool = False
    ssl_cert_path: str = ""
    ssl_key_path: str = ""

@dataclass
class RequestMetrics:
    """Request metrics for monitoring."""
    timestamp: datetime
    client_ip: str
    backend_server: str
    response_time: float
    status_code: int
    bytes_sent: int
    user_agent: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class HealthChecker:
    """Health checking service for backend servers."""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.running = False
        self.thread = None
    
    def start(self, servers: List[BackendServer]):
        """Start health checking."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._health_check_loop, args=(servers,))
        self.thread.daemon = True
        self.thread.start()
        logger.info("Health checker started")
    
    def stop(self):
        """Stop health checking."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Health checker stopped")
    
    def _health_check_loop(self, servers: List[BackendServer]):
        """Health check loop."""
        while self.running:
            for server in servers:
                self._check_server_health(server)
            time.sleep(self.config.health_check_interval)
    
    def _check_server_health(self, server: BackendServer):
        """Check health of a single server."""
        try:
            start_time = time.time()
            response = requests.get(
                server.health_check_url,
                timeout=server.timeout,
                headers={'User-Agent': 'LoadBalancer-HealthCheck/1.0'}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                server.is_healthy = True
                server.response_time_avg = self._update_avg_response_time(
                    server.response_time_avg, response_time
                )
            else:
                server.is_healthy = False
                logger.warning(f"Server {server.server_id} health check failed: {response.status_code}")
            
            server.last_health_check = datetime.now()
            
        except Exception as e:
            server.is_healthy = False
            logger.error(f"Health check failed for server {server.server_id}: {e}")
            server.last_health_check = datetime.now()
    
    def _update_avg_response_time(self, current_avg: float, new_time: float) -> float:
        """Update average response time using exponential moving average."""
        alpha = 0.1  # Smoothing factor
        if current_avg == 0:
            return new_time
        return alpha * new_time + (1 - alpha) * current_avg

class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class RateLimiter:
    """Rate limiting implementation."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for client IP."""
        with self.lock:
            now = time.time()
            client_requests = self.requests[client_ip]
            
            # Remove old requests outside the window
            while client_requests and client_requests[0] <= now - self.window_seconds:
                client_requests.popleft()
            
            # Check if under limit
            if len(client_requests) < self.max_requests:
                client_requests.append(now)
                return True
            
            return False

class LoadBalancer:
    """Main load balancer implementation."""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.servers: List[BackendServer] = []
        self.current_index = 0
        self.health_checker = HealthChecker(config)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests, 
            config.rate_limit_window
        ) if config.rate_limit_enabled else None
        self.session_storage: Dict[str, str] = {}  # session_id -> server_id
        self.metrics: List[RequestMetrics] = []
        self.metrics_lock = threading.Lock()
    
    def add_server(self, server: BackendServer):
        """Add a backend server."""
        self.servers.append(server)
        if self.config.circuit_breaker_enabled:
            self.circuit_breakers[server.server_id] = CircuitBreaker(
                self.config.circuit_breaker_failure_threshold,
                self.config.circuit_breaker_recovery_timeout
            )
        logger.info(f"Added server: {server.server_id} at {server.url}")
    
    def remove_server(self, server_id: str):
        """Remove a backend server."""
        self.servers = [s for s in self.servers if s.server_id != server_id]
        if server_id in self.circuit_breakers:
            del self.circuit_breakers[server_id]
        logger.info(f"Removed server: {server_id}")
    
    def get_healthy_servers(self) -> List[BackendServer]:
        """Get list of healthy servers."""
        return [s for s in self.servers if s.is_healthy]
    
    def select_server(self, client_ip: str = None, session_id: str = None) -> Optional[BackendServer]:
        """Select a backend server using the configured algorithm."""
        healthy_servers = self.get_healthy_servers()
        
        if not healthy_servers:
            logger.warning("No healthy servers available")
            return None
        
        # Session persistence
        if self.config.session_persistence and session_id:
            if session_id in self.session_storage:
                server_id = self.session_storage[session_id]
                server = next((s for s in healthy_servers if s.server_id == server_id), None)
                if server:
                    return server
        
        # Select server based on algorithm
        if self.config.algorithm == "round_robin":
            server = self._round_robin_selection(healthy_servers)
        elif self.config.algorithm == "least_connections":
            server = self._least_connections_selection(healthy_servers)
        elif self.config.algorithm == "weighted_round_robin":
            server = self._weighted_round_robin_selection(healthy_servers)
        elif self.config.algorithm == "ip_hash":
            server = self._ip_hash_selection(healthy_servers, client_ip)
        else:
            server = self._round_robin_selection(healthy_servers)
        
        # Store session if persistence is enabled
        if self.config.session_persistence and session_id and server:
            self.session_storage[session_id] = server.server_id
        
        return server
    
    def _round_robin_selection(self, servers: List[BackendServer]) -> BackendServer:
        """Round robin server selection."""
        if not servers:
            return None
        
        server = servers[self.current_index % len(servers)]
        self.current_index = (self.current_index + 1) % len(servers)
        return server
    
    def _least_connections_selection(self, servers: List[BackendServer]) -> BackendServer:
        """Least connections server selection."""
        if not servers:
            return None
        
        return min(servers, key=lambda s: s.active_connections)
    
    def _weighted_round_robin_selection(self, servers: List[BackendServer]) -> BackendServer:
        """Weighted round robin server selection."""
        if not servers:
            return None
        
        # Simple weighted selection based on server weights
        total_weight = sum(s.weight for s in servers)
        if total_weight == 0:
            return servers[0]
        
        # Use current index for weighted selection
        target_weight = self.current_index % total_weight
        current_weight = 0
        
        for server in servers:
            current_weight += server.weight
            if current_weight > target_weight:
                self.current_index = (self.current_index + 1) % total_weight
                return server
        
        return servers[-1]
    
    def _ip_hash_selection(self, servers: List[BackendServer], client_ip: str) -> BackendServer:
        """IP hash server selection."""
        if not servers or not client_ip:
            return servers[0] if servers else None
        
        # Create hash from client IP
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        return servers[hash_value % len(servers)]
    
    def forward_request(self, method: str, path: str, headers: Dict, data: bytes = None,
                       client_ip: str = None, session_id: str = None) -> Tuple[int, Dict, bytes]:
        """Forward request to selected backend server."""
        # Rate limiting
        if self.rate_limiter and not self.rate_limiter.is_allowed(client_ip or "unknown"):
            return 429, {"Content-Type": "application/json"}, b'{"error": "Rate limit exceeded"}'
        
        # Select server
        server = self.select_server(client_ip, session_id)
        if not server:
            return 503, {"Content-Type": "application/json"}, b'{"error": "No healthy servers available"}'
        
        # Circuit breaker protection
        if self.config.circuit_breaker_enabled and server.server_id in self.circuit_breakers:
            try:
                return self.circuit_breakers[server.server_id].call(
                    self._make_request, server, method, path, headers, data
                )
            except Exception as e:
                logger.error(f"Circuit breaker triggered for server {server.server_id}: {e}")
                return 503, {"Content-Type": "application/json"}, b'{"error": "Service temporarily unavailable"}'
        else:
            return self._make_request(server, method, path, headers, data)
    
    def _make_request(self, server: BackendServer, method: str, path: str, 
                     headers: Dict, data: bytes = None) -> Tuple[int, Dict, bytes]:
        """Make actual request to backend server."""
        start_time = time.time()
        
        try:
            # Update connection count
            server.active_connections += 1
            server.total_requests += 1
            
            # Prepare request
            url = f"{server.url}{path}"
            request_headers = dict(headers)
            request_headers['X-Forwarded-For'] = headers.get('X-Forwarded-For', 'unknown')
            request_headers['X-Forwarded-Proto'] = 'http'
            
            # Make request
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers,
                data=data,
                timeout=server.timeout,
                allow_redirects=False
            )
            
            response_time = time.time() - start_time
            
            # Record metrics
            self._record_metrics(
                client_ip=headers.get('X-Forwarded-For', 'unknown'),
                backend_server=server.server_id,
                response_time=response_time,
                status_code=response.status_code,
                bytes_sent=len(response.content),
                user_agent=headers.get('User-Agent', '')
            )
            
            return (
                response.status_code,
                dict(response.headers),
                response.content
            )
            
        except Exception as e:
            logger.error(f"Request failed to server {server.server_id}: {e}")
            return 502, {"Content-Type": "application/json"}, b'{"error": "Bad Gateway"}'
        
        finally:
            # Update connection count
            server.active_connections = max(0, server.active_connections - 1)
    
    def _record_metrics(self, client_ip: str, backend_server: str, response_time: float,
                       status_code: int, bytes_sent: int, user_agent: str):
        """Record request metrics."""
        with self.metrics_lock:
            metric = RequestMetrics(
                timestamp=datetime.now(),
                client_ip=client_ip,
                backend_server=backend_server,
                response_time=response_time,
                status_code=status_code,
                bytes_sent=bytes_sent,
                user_agent=user_agent
            )
            self.metrics.append(metric)
            
            # Keep only last 1000 metrics to prevent memory issues
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
    
    def get_metrics(self, last_minutes: int = 60) -> Dict:
        """Get load balancer metrics."""
        cutoff_time = datetime.now() - timedelta(minutes=last_minutes)
        
        with self.metrics_lock:
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'requests_per_second': 0,
                'server_metrics': {}
            }
        
        # Calculate metrics
        total_requests = len(recent_metrics)
        avg_response_time = statistics.mean(m.response_time for m in recent_metrics)
        error_requests = len([m for m in recent_metrics if m.status_code >= 400])
        error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0
        requests_per_second = total_requests / (last_minutes * 60)
        
        # Server-specific metrics
        server_metrics = {}
        for server in self.servers:
            server_requests = [m for m in recent_metrics if m.backend_server == server.server_id]
            server_metrics[server.server_id] = {
                'total_requests': len(server_requests),
                'avg_response_time': statistics.mean(m.response_time for m in server_requests) if server_requests else 0,
                'error_rate': (len([m for m in server_requests if m.status_code >= 400]) / len(server_requests) * 100) if server_requests else 0,
                'is_healthy': server.is_healthy,
                'active_connections': server.active_connections,
                'total_requests_all_time': server.total_requests
            }
        
        return {
            'total_requests': total_requests,
            'avg_response_time': round(avg_response_time, 3),
            'error_rate': round(error_rate, 2),
            'requests_per_second': round(requests_per_second, 2),
            'server_metrics': server_metrics
        }
    
    def start_health_checking(self):
        """Start health checking."""
        self.health_checker.start(self.servers)
    
    def stop_health_checking(self):
        """Stop health checking."""
        self.health_checker.stop()

# Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'load-balancer-secret-key'

# Initialize load balancer
config = LoadBalancerConfig()
load_balancer = LoadBalancer(config)

# Add some default backend servers
load_balancer.add_server(BackendServer(
    server_id="server1",
    host="localhost",
    port=5001,
    weight=1
))
load_balancer.add_server(BackendServer(
    server_id="server2", 
    host="localhost",
    port=5002,
    weight=1
))
load_balancer.add_server(BackendServer(
    server_id="server3",
    host="localhost", 
    port=5003,
    weight=2
))

# Start health checking
load_balancer.start_health_checking()

@app.route('/')
def index():
    """Load balancer dashboard."""
    metrics = load_balancer.get_metrics()
    healthy_servers = load_balancer.get_healthy_servers()
    
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Load Balancer Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .metric { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .server { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .healthy { border-left: 5px solid #4CAF50; }
            .unhealthy { border-left: 5px solid #f44336; }
            .status { font-weight: bold; }
            .healthy .status { color: #4CAF50; }
            .unhealthy .status { color: #f44336; }
        </style>
    </head>
    <body>
        <h1>Load Balancer Dashboard</h1>
        
        <h2>Overall Metrics</h2>
        <div class="metric">
            <strong>Total Requests (Last Hour):</strong> {{ metrics.total_requests }}
        </div>
        <div class="metric">
            <strong>Average Response Time:</strong> {{ "%.3f"|format(metrics.avg_response_time) }}s
        </div>
        <div class="metric">
            <strong>Error Rate:</strong> {{ "%.2f"|format(metrics.error_rate) }}%
        </div>
        <div class="metric">
            <strong>Requests Per Second:</strong> {{ "%.2f"|format(metrics.requests_per_second) }}
        </div>
        
        <h2>Backend Servers</h2>
        {% for server in load_balancer.servers %}
        <div class="server {{ 'healthy' if server.is_healthy else 'unhealthy' }}">
            <div class="status">{{ 'HEALTHY' if server.is_healthy else 'UNHEALTHY' }}</div>
            <strong>{{ server.server_id }}</strong> - {{ server.url }}
            <br>Active Connections: {{ server.active_connections }} / {{ server.max_connections }}
            <br>Total Requests: {{ server.total_requests }}
            <br>Weight: {{ server.weight }}
            <br>Avg Response Time: {{ "%.3f"|format(server.response_time_avg) }}s
        </div>
        {% endfor %}
        
        <h2>Server Metrics (Last Hour)</h2>
        {% for server_id, server_metrics in metrics.server_metrics.items() %}
        <div class="metric">
            <strong>{{ server_id }}:</strong>
            <br>Requests: {{ server_metrics.total_requests }}
            <br>Avg Response Time: {{ "%.3f"|format(server_metrics.avg_response_time) }}s
            <br>Error Rate: {{ "%.2f"|format(server_metrics.error_rate) }}%
        </div>
        {% endfor %}
        
        <script>
            // Auto-refresh every 30 seconds
            setTimeout(function() {
                location.reload();
            }, 30000);
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(html_template, 
                                metrics=metrics, 
                                load_balancer=load_balancer)

@app.route('/api/metrics')
def get_metrics():
    """Get load balancer metrics API."""
    metrics = load_balancer.get_metrics()
    return jsonify({
        'success': True,
        'metrics': metrics,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/servers')
def get_servers():
    """Get backend servers API."""
    servers_data = []
    for server in load_balancer.servers:
        servers_data.append({
            'server_id': server.server_id,
            'host': server.host,
            'port': server.port,
            'url': server.url,
            'weight': server.weight,
            'is_healthy': server.is_healthy,
            'active_connections': server.active_connections,
            'max_connections': server.max_connections,
            'total_requests': server.total_requests,
            'response_time_avg': server.response_time_avg,
            'last_health_check': server.last_health_check.isoformat() if server.last_health_check else None
        })
    
    return jsonify({
        'success': True,
        'servers': servers_data
    })

@app.route('/api/servers', methods=['POST'])
def add_server():
    """Add a new backend server."""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['server_id', 'host', 'port']):
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    server = BackendServer(
        server_id=data['server_id'],
        host=data['host'],
        port=data['port'],
        weight=data.get('weight', 1),
        max_connections=data.get('max_connections', 100),
        health_check_path=data.get('health_check_path', '/health'),
        timeout=data.get('timeout', 5)
    )
    
    load_balancer.add_server(server)
    
    return jsonify({
        'success': True,
        'message': f'Server {server.server_id} added successfully'
    })

@app.route('/api/servers/<server_id>', methods=['DELETE'])
def remove_server(server_id):
    """Remove a backend server."""
    load_balancer.remove_server(server_id)
    
    return jsonify({
        'success': True,
        'message': f'Server {server_id} removed successfully'
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get load balancer configuration."""
    return jsonify({
        'success': True,
        'config': asdict(load_balancer.config)
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update load balancer configuration."""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No configuration provided'})
    
    # Update configuration
    for key, value in data.items():
        if hasattr(load_balancer.config, key):
            setattr(load_balancer.config, key, value)
    
    return jsonify({
        'success': True,
        'message': 'Configuration updated successfully'
    })

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy_request(path):
    """Proxy requests to backend servers."""
    # Get client IP
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Get session ID for persistence
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = f"session_{int(time.time())}_{random.randint(1000, 9999)}"
    
    # Forward request
    status_code, headers, content = load_balancer.forward_request(
        method=request.method,
        path=f'/{path}',
        headers=dict(request.headers),
        data=request.get_data(),
        client_ip=client_ip,
        session_id=session_id
    )
    
    # Create response
    response = app.response_class(
        content,
        status=status_code,
        headers=headers
    )
    
    # Set session cookie if not present
    if not request.cookies.get('session_id'):
        response.set_cookie('session_id', session_id, max_age=load_balancer.config.session_timeout)
    
    return response

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=8080)
    finally:
        load_balancer.stop_health_checking()
