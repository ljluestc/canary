"""
Monitoring System Implementation
Comprehensive system monitoring with metrics collection and alerting
"""

import time
import threading
import psutil
import json
import redis
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class Metric:
    """Metric data structure"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE

@dataclass
class AlertRule:
    """Alert rule data structure"""
    rule_id: str
    name: str
    metric_name: str
    condition: str  # e.g., ">", "<", "==", "!="
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown: int = 300  # seconds
    last_triggered: Optional[datetime] = None

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    rule_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    message: str = ""

@dataclass
class NotificationChannel:
    """Notification channel data structure"""
    channel_id: str
    name: str
    channel_type: str  # email, slack, webhook, etc.
    config: Dict[str, Any]
    enabled: bool = True

@dataclass
class SystemInfo:
    """System information data structure"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: Tuple[float, float, float]
    timestamp: datetime

class MonitoringSystem:
    """Comprehensive system monitoring"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Core data structures
        self.metrics = defaultdict(list)  # metric_name -> List[Metric]
        self.alert_rules = {}  # rule_id -> AlertRule
        self.active_alerts = {}  # alert_id -> Alert
        self.notification_channels = {}  # channel_id -> NotificationChannel
        
        # System monitoring
        self.system_info_history = deque(maxlen=1000)  # Keep last 1000 system info records
        self.metric_history = defaultdict(lambda: deque(maxlen=1000))  # metric_name -> deque
        
        # Threading
        self.lock = threading.RLock()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.alert_processor = threading.Thread(target=self._alert_processing_loop, daemon=True)
        self.alert_processor.start()
        
        # Configuration
        self.monitoring_interval = 10  # seconds
        self.alert_check_interval = 5  # seconds
        self.metric_retention_days = 30
        self.cleanup_interval = 3600  # 1 hour
        
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize default metrics
        self._initialize_default_metrics()
    
    def _initialize_default_metrics(self):
        """Initialize default system metrics"""
        # CPU metrics
        self.add_metric("system_cpu_percent", psutil.cpu_percent(), MetricType.GAUGE)
        self.add_metric("system_cpu_count", psutil.cpu_count(), MetricType.GAUGE)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.add_metric("system_memory_percent", memory.percent, MetricType.GAUGE)
        self.add_metric("system_memory_available", memory.available, MetricType.GAUGE)
        self.add_metric("system_memory_total", memory.total, MetricType.GAUGE)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.add_metric("system_disk_percent", disk.percent, MetricType.GAUGE)
        self.add_metric("system_disk_free", disk.free, MetricType.GAUGE)
        self.add_metric("system_disk_total", disk.total, MetricType.GAUGE)
        
        # Network metrics
        network = psutil.net_io_counters()
        self.add_metric("system_network_bytes_sent", network.bytes_sent, MetricType.COUNTER)
        self.add_metric("system_network_bytes_recv", network.bytes_recv, MetricType.COUNTER)
        
        # Process metrics
        self.add_metric("system_process_count", len(psutil.pids()), MetricType.GAUGE)
    
    def add_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, 
                  labels: Dict[str, str] = None) -> Metric:
        """Add a metric"""
        with self.lock:
            metric = Metric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {},
                metric_type=metric_type
            )
            
            self.metrics[name].append(metric)
            self.metric_history[name].append(metric)
            
            # Persist to Redis
            self._persist_metric(metric)
            
            return metric
    
    def get_metric(self, name: str, start_time: Optional[datetime] = None, 
                  end_time: Optional[datetime] = None) -> List[Metric]:
        """Get metrics by name and time range"""
        with self.lock:
            if name not in self.metrics:
                return []
            
            metrics = self.metrics[name]
            
            if start_time and end_time:
                return [m for m in metrics if start_time <= m.timestamp <= end_time]
            elif start_time:
                return [m for m in metrics if m.timestamp >= start_time]
            elif end_time:
                return [m for m in metrics if m.timestamp <= end_time]
            else:
                return metrics
    
    def get_metric_summary(self, name: str, start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> Dict[str, float]:
        """Get metric summary statistics"""
        metrics = self.get_metric(name, start_time, end_time)
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0,
            "latest": values[-1] if values else 0
        }
    
    def create_alert_rule(self, rule_id: str, name: str, metric_name: str, 
                         condition: str, threshold: float, severity: AlertSeverity,
                         cooldown: int = 300) -> AlertRule:
        """Create an alert rule"""
        with self.lock:
            rule = AlertRule(
                rule_id=rule_id,
                name=name,
                metric_name=metric_name,
                condition=condition,
                threshold=threshold,
                severity=severity,
                cooldown=cooldown
            )
            
            self.alert_rules[rule_id] = rule
            self._persist_alert_rule(rule)
            
            return rule
    
    def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        with self.lock:
            if rule_id not in self.alert_rules:
                return False
            
            del self.alert_rules[rule_id]
            self.redis_client.delete(f"alert_rule:{rule_id}")
            return True
    
    def create_notification_channel(self, channel_id: str, name: str, 
                                  channel_type: str, config: Dict[str, Any]) -> NotificationChannel:
        """Create a notification channel"""
        with self.lock:
            channel = NotificationChannel(
                channel_id=channel_id,
                name=name,
                channel_type=channel_type,
                config=config
            )
            
            self.notification_channels[channel_id] = channel
            self._persist_notification_channel(channel)
            
            return channel
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                time.sleep(self.monitoring_interval)
                
                with self.lock:
                    # Collect system metrics
                    self._collect_system_metrics()
                    
                    # Clean up old metrics
                    self._cleanup_old_metrics()
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.add_metric("system_cpu_percent", cpu_percent, MetricType.GAUGE)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.add_metric("system_memory_percent", memory.percent, MetricType.GAUGE)
            self.add_metric("system_memory_available", memory.available, MetricType.GAUGE)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.add_metric("system_disk_percent", disk.percent, MetricType.GAUGE)
            self.add_metric("system_disk_free", disk.free, MetricType.GAUGE)
            
            # Network metrics
            network = psutil.net_io_counters()
            self.add_metric("system_network_bytes_sent", network.bytes_sent, MetricType.COUNTER)
            self.add_metric("system_network_bytes_recv", network.bytes_recv, MetricType.COUNTER)
            
            # Process metrics
            process_count = len(psutil.pids())
            self.add_metric("system_process_count", process_count, MetricType.GAUGE)
            
            # Load average
            load_avg = psutil.getloadavg()
            self.add_metric("system_load_1min", load_avg[0], MetricType.GAUGE)
            self.add_metric("system_load_5min", load_avg[1], MetricType.GAUGE)
            self.add_metric("system_load_15min", load_avg[2], MetricType.GAUGE)
            
            # Store system info
            system_info = SystemInfo(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_io={"bytes_sent": network.bytes_sent, "bytes_recv": network.bytes_recv},
                process_count=process_count,
                load_average=load_avg,
                timestamp=datetime.now()
            )
            self.system_info_history.append(system_info)
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _alert_processing_loop(self):
        """Alert processing loop"""
        while True:
            try:
                time.sleep(self.alert_check_interval)
                
                with self.lock:
                    # Check all alert rules
                    for rule in self.alert_rules.values():
                        if not rule.enabled:
                            continue
                        
                        # Check cooldown
                        if (rule.last_triggered and 
                            (datetime.now() - rule.last_triggered).total_seconds() < rule.cooldown):
                            continue
                        
                        # Get latest metric value
                        latest_metrics = self.get_metric(rule.metric_name)
                        if not latest_metrics:
                            continue
                        
                        latest_metric = latest_metrics[-1]
                        
                        # Check condition
                        if self._evaluate_condition(latest_metric.value, rule.condition, rule.threshold):
                            # Trigger alert
                            self._trigger_alert(rule, latest_metric.value)
                            rule.last_triggered = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Error in alert processing loop: {e}")
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        else:
            return False
    
    def _trigger_alert(self, rule: AlertRule, current_value: float):
        """Trigger an alert"""
        alert_id = f"alert_{int(time.time())}_{rule.rule_id}"
        
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            created_at=datetime.now(),
            message=f"Alert: {rule.name} - {rule.metric_name} {rule.condition} {rule.threshold} (current: {current_value})"
        )
        
        self.active_alerts[alert_id] = alert
        
        # Send notifications
        self._send_notifications(alert)
        
        # Persist alert
        self._persist_alert(alert)
        
        self.logger.warning(f"Alert triggered: {alert.message}")
    
    def _send_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        for channel in self.notification_channels.values():
            if not channel.enabled:
                continue
            
            try:
                if channel.channel_type == "email":
                    self._send_email_notification(channel, alert)
                elif channel.channel_type == "slack":
                    self._send_slack_notification(channel, alert)
                elif channel.channel_type == "webhook":
                    self._send_webhook_notification(channel, alert)
            except Exception as e:
                self.logger.error(f"Error sending notification via {channel.channel_type}: {e}")
    
    def _send_email_notification(self, channel: NotificationChannel, alert: Alert):
        """Send email notification"""
        config = channel.config
        
        msg = MIMEMultipart()
        msg['From'] = config['from_email']
        msg['To'] = config['to_email']
        msg['Subject'] = f"Alert: {alert.metric_name}"
        
        body = f"""
        Alert Details:
        - Rule: {alert.rule_id}
        - Metric: {alert.metric_name}
        - Current Value: {alert.current_value}
        - Threshold: {alert.threshold}
        - Severity: {alert.severity.value}
        - Time: {alert.created_at}
        - Message: {alert.message}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email (simplified - in production use proper SMTP config)
        # server = smtplib.SMTP(config['smtp_host'], config['smtp_port'])
        # server.starttls()
        # server.login(config['username'], config['password'])
        # server.send_message(msg)
        # server.quit()
        
        print(f"Email notification sent: {alert.message}")
    
    def _send_slack_notification(self, channel: NotificationChannel, alert: Alert):
        """Send Slack notification"""
        config = channel.config
        
        payload = {
            "text": f"Alert: {alert.metric_name}",
            "attachments": [
                {
                    "color": "danger" if alert.severity == AlertSeverity.CRITICAL else "warning",
                    "fields": [
                        {"title": "Rule", "value": alert.rule_id, "short": True},
                        {"title": "Metric", "value": alert.metric_name, "short": True},
                        {"title": "Current Value", "value": str(alert.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold), "short": True},
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Time", "value": alert.created_at.isoformat(), "short": True}
                    ]
                }
            ]
        }
        
        # Send to Slack webhook (simplified)
        # requests.post(config['webhook_url'], json=payload)
        
        print(f"Slack notification sent: {alert.message}")
    
    def _send_webhook_notification(self, channel: NotificationChannel, alert: Alert):
        """Send webhook notification"""
        config = channel.config
        
        payload = {
            "alert_id": alert.alert_id,
            "rule_id": alert.rule_id,
            "metric_name": alert.metric_name,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat(),
            "message": alert.message
        }
        
        # Send webhook (simplified)
        # requests.post(config['url'], json=payload, headers=config.get('headers', {}))
        
        print(f"Webhook notification sent: {alert.message}")
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self.lock:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # Move to resolved alerts (in production, store in database)
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alert resolved: {alert_id}")
            return True
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        with self.lock:
            return list(self.active_alerts.values())
    
    def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        with self.lock:
            return list(self.alert_rules.values())
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health summary"""
        with self.lock:
            # Get latest system info
            if not self.system_info_history:
                return {}
            
            latest_info = self.system_info_history[-1]
            
            # Get metric summaries
            cpu_summary = self.get_metric_summary("system_cpu_percent")
            memory_summary = self.get_metric_summary("system_memory_percent")
            disk_summary = self.get_metric_summary("system_disk_percent")
            
            # Calculate health score
            health_score = 100
            if cpu_summary.get("latest", 0) > 80:
                health_score -= 20
            if memory_summary.get("latest", 0) > 80:
                health_score -= 20
            if disk_summary.get("latest", 0) > 90:
                health_score -= 30
            
            return {
                "health_score": max(0, health_score),
                "status": "healthy" if health_score > 80 else "warning" if health_score > 50 else "critical",
                "cpu_percent": cpu_summary.get("latest", 0),
                "memory_percent": memory_summary.get("latest", 0),
                "disk_percent": disk_summary.get("latest", 0),
                "process_count": latest_info.process_count,
                "load_average": latest_info.load_average,
                "active_alerts": len(self.active_alerts),
                "total_metrics": sum(len(metrics) for metrics in self.metrics.values()),
                "timestamp": latest_info.timestamp.isoformat()
            }
    
    def get_dashboard_data(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get dashboard data for the specified time range"""
        with self.lock:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # Get metrics for time range
            cpu_metrics = self.get_metric("system_cpu_percent", start_time, end_time)
            memory_metrics = self.get_metric("system_memory_percent", start_time, end_time)
            disk_metrics = self.get_metric("system_disk_percent", start_time, end_time)
            
            # Convert to chart data
            chart_data = {
                "cpu": [{"timestamp": m.timestamp.isoformat(), "value": m.value} for m in cpu_metrics],
                "memory": [{"timestamp": m.timestamp.isoformat(), "value": m.value} for m in memory_metrics],
                "disk": [{"timestamp": m.timestamp.isoformat(), "value": m.value} for m in disk_metrics]
            }
            
            # Get alerts for time range
            alerts = [alert for alert in self.active_alerts.values() 
                     if start_time <= alert.created_at <= end_time]
            
            return {
                "chart_data": chart_data,
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "metric_name": alert.metric_name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "created_at": alert.created_at.isoformat()
                    }
                    for alert in alerts
                ],
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours": time_range_hours
                }
            }
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics"""
        cutoff_time = datetime.now() - timedelta(days=self.metric_retention_days)
        
        for metric_name in list(self.metrics.keys()):
            # Remove old metrics
            self.metrics[metric_name] = [
                m for m in self.metrics[metric_name] 
                if m.timestamp > cutoff_time
            ]
            
            # Remove empty metric lists
            if not self.metrics[metric_name]:
                del self.metrics[metric_name]
    
    def _persist_metric(self, metric: Metric):
        """Persist metric to Redis"""
        metric_data = {
            "name": metric.name,
            "value": str(metric.value),
            "timestamp": metric.timestamp.isoformat(),
            "labels": json.dumps(metric.labels),
            "metric_type": metric.metric_type.value
        }
        
        # Store in time-series format
        key = f"metric:{metric.name}:{int(metric.timestamp.timestamp())}"
        self.redis_client.hset(key, mapping=metric_data)
        self.redis_client.expire(key, self.metric_retention_days * 24 * 3600)
    
    def _persist_alert_rule(self, rule: AlertRule):
        """Persist alert rule to Redis"""
        rule_data = {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "metric_name": rule.metric_name,
            "condition": rule.condition,
            "threshold": str(rule.threshold),
            "severity": rule.severity.value,
            "enabled": str(rule.enabled),
            "cooldown": str(rule.cooldown),
            "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
        }
        
        self.redis_client.hset(f"alert_rule:{rule.rule_id}", mapping=rule_data)
    
    def _persist_notification_channel(self, channel: NotificationChannel):
        """Persist notification channel to Redis"""
        channel_data = {
            "channel_id": channel.channel_id,
            "name": channel.name,
            "channel_type": channel.channel_type,
            "config": json.dumps(channel.config),
            "enabled": str(channel.enabled)
        }
        
        self.redis_client.hset(f"notification_channel:{channel.channel_id}", mapping=channel_data)
    
    def _persist_alert(self, alert: Alert):
        """Persist alert to Redis"""
        alert_data = {
            "alert_id": alert.alert_id,
            "rule_id": alert.rule_id,
            "metric_name": alert.metric_name,
            "current_value": str(alert.current_value),
            "threshold": str(alert.threshold),
            "severity": alert.severity.value,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat(),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "message": alert.message
        }
        
        self.redis_client.hset(f"alert:{alert.alert_id}", mapping=alert_data)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        with self.lock:
            return {
                "total_metrics": sum(len(metrics) for metrics in self.metrics.values()),
                "metric_types": len(self.metrics),
                "alert_rules": len(self.alert_rules),
                "active_alerts": len(self.active_alerts),
                "notification_channels": len(self.notification_channels),
                "system_info_records": len(self.system_info_history),
                "monitoring_interval": self.monitoring_interval,
                "alert_check_interval": self.alert_check_interval
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize monitoring system
    monitoring = MonitoringSystem()
    
    # Create alert rules
    monitoring.create_alert_rule(
        "cpu_high", "High CPU Usage", "system_cpu_percent", ">", 80.0, AlertSeverity.HIGH
    )
    monitoring.create_alert_rule(
        "memory_high", "High Memory Usage", "system_memory_percent", ">", 85.0, AlertSeverity.HIGH
    )
    monitoring.create_alert_rule(
        "disk_high", "High Disk Usage", "system_disk_percent", ">", 90.0, AlertSeverity.CRITICAL
    )
    
    # Create notification channels
    monitoring.create_notification_channel(
        "email_channel", "Email Alerts", "email", {
            "from_email": "alerts@example.com",
            "to_email": "admin@example.com",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "username": "alerts",
            "password": "password"
        }
    )
    
    # Add custom metrics
    monitoring.add_metric("custom_metric", 75.5, MetricType.GAUGE, {"service": "api"})
    monitoring.add_metric("request_count", 1000, MetricType.COUNTER, {"endpoint": "/api/users"})
    
    # Get system health
    health = monitoring.get_system_health()
    print(f"System health: {health}")
    
    # Get dashboard data
    dashboard = monitoring.get_dashboard_data(1)  # Last hour
    print(f"Dashboard data: {len(dashboard['chart_data']['cpu'])} CPU data points")
    
    # Get system stats
    stats = monitoring.get_system_stats()
    print(f"System stats: {stats}")
