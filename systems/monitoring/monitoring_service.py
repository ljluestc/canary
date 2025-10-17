#!/usr/bin/env python3
"""
Monitoring Service with Prometheus and Grafana

A comprehensive monitoring system with features like:
- Prometheus metrics collection
- Grafana dashboard integration
- Health checks and alerts
- Performance monitoring
- Log aggregation
- Custom metrics
- Alerting rules
"""

import os
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, render_template_string
import psutil
import requests
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('disk_usage_percent', 'Disk usage percentage')
CUSTOM_METRICS = Gauge('custom_metrics', 'Custom application metrics', ['metric_name'])

@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: str
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '==', '!='
    severity: str  # 'critical', 'warning', 'info'
    message: str
    enabled: bool = True
    cooldown: int = 300  # seconds
    last_triggered: datetime = None
    
    def __post_init__(self):
        if self.last_triggered is None:
            self.last_triggered = datetime.now()

@dataclass
class Alert:
    """Active alert."""
    id: str
    rule_name: str
    message: str
    severity: str
    triggered_at: datetime
    resolved_at: datetime = None
    is_resolved: bool = False

@dataclass
class ServiceHealth:
    """Service health status."""
    service_name: str
    status: str  # 'healthy', 'unhealthy', 'degraded'
    response_time: float
    last_check: datetime
    error_message: str = ""
    uptime: float = 0.0
    version: str = ""

class MetricsCollector:
    """System metrics collector."""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.collection_interval = 30  # seconds
    
    def start(self):
        """Start metrics collection."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._collect_metrics_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Metrics collector started")
    
    def stop(self):
        """Stop metrics collection."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Metrics collector stopped")
    
    def _collect_metrics_loop(self):
        """Main metrics collection loop."""
        while self.running:
            try:
                self._collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self):
        """Collect system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            DISK_USAGE.set(disk.percent)
            
            # Active connections (simplified)
            connections = len(psutil.net_connections())
            ACTIVE_CONNECTIONS.set(connections)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

class HealthChecker:
    """Service health checker."""
    
    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.running = False
        self.thread = None
        self.check_interval = 60  # seconds
    
    def add_service(self, service_name: str, health_url: str, version: str = ""):
        """Add a service to health checking."""
        self.services[service_name] = ServiceHealth(
            service_name=service_name,
            status="unknown",
            response_time=0.0,
            last_check=datetime.now(),
            version=version
        )
        logger.info(f"Added service for health checking: {service_name}")
    
    def start(self):
        """Start health checking."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._health_check_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Health checker started")
    
    def stop(self):
        """Stop health checking."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Health checker stopped")
    
    def _health_check_loop(self):
        """Main health check loop."""
        while self.running:
            for service_name, service in self.services.items():
                self._check_service_health(service)
            time.sleep(self.check_interval)
    
    def _check_service_health(self, service: ServiceHealth):
        """Check health of a single service."""
        try:
            start_time = time.time()
            
            # Try to get health endpoint
            health_url = f"http://localhost:5000/health"  # Default health endpoint
            response = requests.get(health_url, timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                service.status = "healthy"
                service.response_time = response_time
                service.error_message = ""
            else:
                service.status = "unhealthy"
                service.error_message = f"HTTP {response.status_code}"
            
            service.last_check = datetime.now()
            
        except requests.exceptions.Timeout:
            service.status = "unhealthy"
            service.error_message = "Timeout"
            service.last_check = datetime.now()
        except requests.exceptions.ConnectionError:
            service.status = "unhealthy"
            service.error_message = "Connection refused"
            service.last_check = datetime.now()
        except Exception as e:
            service.status = "unhealthy"
            service.error_message = str(e)
            service.last_check = datetime.now()
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get health status of a service."""
        return self.services.get(service_name)
    
    def get_all_services_health(self) -> Dict[str, ServiceHealth]:
        """Get health status of all services."""
        return self.services.copy()

class AlertManager:
    """Alert management system."""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: List[Alert] = []
        self.running = False
        self.thread = None
        self.check_interval = 30  # seconds
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def start(self):
        """Start alert checking."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._alert_check_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Alert manager started")
    
    def stop(self):
        """Stop alert checking."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Alert manager stopped")
    
    def _alert_check_loop(self):
        """Main alert checking loop."""
        while self.running:
            try:
                self._check_alerts()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error checking alerts: {e}")
                time.sleep(self.check_interval)
    
    def _check_alerts(self):
        """Check all alert rules."""
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check if rule is in cooldown
            if rule.last_triggered and (datetime.now() - rule.last_triggered).total_seconds() < rule.cooldown:
                continue
            
            # Evaluate rule condition
            if self._evaluate_rule(rule):
                self._trigger_alert(rule)
    
    def _evaluate_rule(self, rule: AlertRule) -> bool:
        """Evaluate an alert rule."""
        try:
            # Get current metric value based on condition
            if rule.condition == "cpu_usage":
                current_value = psutil.cpu_percent()
            elif rule.condition == "memory_usage":
                current_value = psutil.virtual_memory().percent
            elif rule.condition == "disk_usage":
                current_value = psutil.disk_usage('/').percent
            else:
                return False
            
            # Apply operator
            if rule.operator == ">":
                return current_value > rule.threshold
            elif rule.operator == "<":
                return current_value < rule.threshold
            elif rule.operator == ">=":
                return current_value >= rule.threshold
            elif rule.operator == "<=":
                return current_value <= rule.threshold
            elif rule.operator == "==":
                return current_value == rule.threshold
            elif rule.operator == "!=":
                return current_value != rule.threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {e}")
            return False
    
    def _trigger_alert(self, rule: AlertRule):
        """Trigger an alert for a rule."""
        alert = Alert(
            id=f"{rule.name}_{int(time.time())}",
            rule_name=rule.name,
            message=rule.message,
            severity=rule.severity,
            triggered_at=datetime.now()
        )
        
        self.active_alerts.append(alert)
        rule.last_triggered = datetime.now()
        
        logger.warning(f"Alert triggered: {rule.name} - {rule.message}")
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        for alert in self.active_alerts:
            if alert.id == alert_id and not alert.is_resolved:
                alert.is_resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert_id}")
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [alert for alert in self.active_alerts if not alert.is_resolved]
    
    def get_all_alerts(self) -> List[Alert]:
        """Get all alerts (active and resolved)."""
        return self.active_alerts.copy()

class MonitoringService:
    """Main monitoring service."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self.start_time = datetime.now()
        
        # Initialize default alert rules
        self._setup_default_alerts()
        
        # Add default services
        self._setup_default_services()
    
    def _setup_default_alerts(self):
        """Setup default alert rules."""
        alerts = [
            AlertRule(
                name="high_cpu_usage",
                condition="cpu_usage",
                threshold=80.0,
                operator=">",
                severity="warning",
                message="CPU usage is above 80%"
            ),
            AlertRule(
                name="critical_cpu_usage",
                condition="cpu_usage",
                threshold=95.0,
                operator=">",
                severity="critical",
                message="CPU usage is above 95%"
            ),
            AlertRule(
                name="high_memory_usage",
                condition="memory_usage",
                threshold=85.0,
                operator=">",
                severity="warning",
                message="Memory usage is above 85%"
            ),
            AlertRule(
                name="high_disk_usage",
                condition="disk_usage",
                threshold=90.0,
                operator=">",
                severity="warning",
                message="Disk usage is above 90%"
            )
        ]
        
        for alert in alerts:
            self.alert_manager.add_rule(alert)
    
    def _setup_default_services(self):
        """Setup default services for monitoring."""
        services = [
            ("tinyurl", "http://localhost:5000/health"),
            ("newsfeed", "http://localhost:5001/health"),
            ("google-docs", "http://localhost:5002/health"),
            ("quora", "http://localhost:5003/health"),
            ("load-balancer", "http://localhost:8080/health")
        ]
        
        for service_name, health_url in services:
            self.health_checker.add_service(service_name, health_url)
    
    def start(self):
        """Start all monitoring services."""
        self.metrics_collector.start()
        self.health_checker.start()
        self.alert_manager.start()
        logger.info("Monitoring service started")
    
    def stop(self):
        """Stop all monitoring services."""
        self.metrics_collector.stop()
        self.health_checker.stop()
        self.alert_manager.stop()
        logger.info("Monitoring service stopped")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available,
                'memory_total': memory.total,
                'disk_usage': disk.percent,
                'disk_free': disk.free,
                'disk_total': disk.total,
                'uptime': (datetime.now() - self.start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_services_health(self) -> Dict[str, Any]:
        """Get health status of all services."""
        services = self.health_checker.get_all_services_health()
        
        result = {}
        for service_name, service in services.items():
            result[service_name] = {
                'status': service.status,
                'response_time': service.response_time,
                'last_check': service.last_check.isoformat(),
                'error_message': service.error_message,
                'uptime': service.uptime,
                'version': service.version
            }
        
        return result
    
    def get_alerts(self) -> Dict[str, Any]:
        """Get all alerts."""
        active_alerts = self.alert_manager.get_active_alerts()
        all_alerts = self.alert_manager.get_all_alerts()
        
        return {
            'active_alerts': [asdict(alert) for alert in active_alerts],
            'all_alerts': [asdict(alert) for alert in all_alerts],
            'total_active': len(active_alerts),
            'total_resolved': len([a for a in all_alerts if a.is_resolved])
        }

# Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'monitoring-secret-key'

# Initialize monitoring service
monitoring_service = MonitoringService()

# Start monitoring
monitoring_service.start()

@app.route('/')
def index():
    """Monitoring dashboard."""
    system_metrics = monitoring_service.get_system_metrics()
    services_health = monitoring_service.get_services_health()
    alerts = monitoring_service.get_alerts()
    
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Monitoring Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .metric { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .service { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .healthy { border-left: 5px solid #4CAF50; }
            .unhealthy { border-left: 5px solid #f44336; }
            .warning { border-left: 5px solid #ff9800; }
            .alert { background: #ffebee; padding: 10px; margin: 5px 0; border-radius: 3px; }
            .critical { background: #ffcdd2; }
            .warning { background: #fff3e0; }
            .status { font-weight: bold; }
            .healthy .status { color: #4CAF50; }
            .unhealthy .status { color: #f44336; }
            .warning .status { color: #ff9800; }
        </style>
    </head>
    <body>
        <h1>Monitoring Dashboard</h1>
        
        <h2>System Metrics</h2>
        <div class="metric">
            <strong>CPU Usage:</strong> {{ "%.1f"|format(system_metrics.cpu_usage) }}%
        </div>
        <div class="metric">
            <strong>Memory Usage:</strong> {{ "%.1f"|format(system_metrics.memory_usage) }}% 
            ({{ "%.1f"|format(system_metrics.memory_available / 1024 / 1024 / 1024) }}GB available)
        </div>
        <div class="metric">
            <strong>Disk Usage:</strong> {{ "%.1f"|format(system_metrics.disk_usage) }}%
            ({{ "%.1f"|format(system_metrics.disk_free / 1024 / 1024 / 1024) }}GB free)
        </div>
        <div class="metric">
            <strong>Uptime:</strong> {{ "%.0f"|format(system_metrics.uptime / 3600) }} hours
        </div>
        
        <h2>Service Health</h2>
        {% for service_name, service in services_health.items() %}
        <div class="service {{ service.status }}">
            <div class="status">{{ service.status.upper() }}</div>
            <strong>{{ service_name }}</strong>
            <br>Response Time: {{ "%.3f"|format(service.response_time) }}s
            <br>Last Check: {{ service.last_check }}
            {% if service.error_message %}
            <br>Error: {{ service.error_message }}
            {% endif %}
        </div>
        {% endfor %}
        
        <h2>Active Alerts ({{ alerts.total_active }})</h2>
        {% for alert in alerts.active_alerts %}
        <div class="alert {{ alert.severity }}">
            <strong>{{ alert.severity.upper() }}:</strong> {{ alert.message }}
            <br>Rule: {{ alert.rule_name }} | Triggered: {{ alert.triggered_at }}
        </div>
        {% endfor %}
        
        {% if alerts.total_active == 0 %}
        <div class="metric">
            <strong>No active alerts</strong>
        </div>
        {% endif %}
        
        <h2>Links</h2>
        <p><a href="/metrics">Prometheus Metrics</a></p>
        <p><a href="/api/metrics">API Metrics</a></p>
        <p><a href="/api/health">API Health</a></p>
        <p><a href="/api/alerts">API Alerts</a></p>
        
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
                                system_metrics=system_metrics,
                                services_health=services_health,
                                alerts=alerts)

@app.route('/metrics')
def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/api/metrics')
def get_metrics():
    """Get system metrics API."""
    metrics = monitoring_service.get_system_metrics()
    return jsonify({
        'success': True,
        'metrics': metrics
    })

@app.route('/api/health')
def get_health():
    """Get services health API."""
    health = monitoring_service.get_services_health()
    return jsonify({
        'success': True,
        'health': health
    })

@app.route('/api/alerts')
def get_alerts():
    """Get alerts API."""
    alerts = monitoring_service.get_alerts()
    return jsonify({
        'success': True,
        'alerts': alerts
    })

@app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert."""
    monitoring_service.alert_manager.resolve_alert(alert_id)
    return jsonify({
        'success': True,
        'message': f'Alert {alert_id} resolved'
    })

@app.route('/api/rules', methods=['GET'])
def get_rules():
    """Get alert rules API."""
    rules = [asdict(rule) for rule in monitoring_service.alert_manager.rules]
    return jsonify({
        'success': True,
        'rules': rules
    })

@app.route('/api/rules', methods=['POST'])
def add_rule():
    """Add alert rule API."""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['name', 'condition', 'threshold', 'operator', 'severity', 'message']):
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    rule = AlertRule(
        name=data['name'],
        condition=data['condition'],
        threshold=data['threshold'],
        operator=data['operator'],
        severity=data['severity'],
        message=data['message'],
        enabled=data.get('enabled', True),
        cooldown=data.get('cooldown', 300)
    )
    
    monitoring_service.alert_manager.add_rule(rule)
    
    return jsonify({
        'success': True,
        'message': f'Rule {rule.name} added successfully'
    })

@app.route('/health')
def health_check():
    """Health check endpoint for the monitoring service itself."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': (datetime.now() - monitoring_service.start_time).total_seconds()
    })

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=9090)
    finally:
        monitoring_service.stop()
