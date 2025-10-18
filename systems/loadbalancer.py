"""
Load Balancer System Implementation
High-performance load balancing with health checks and failover
"""

import time
import threading
import socket
import requests
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import redis
from enum import Enum
import statistics
import random
import hashlib
import ssl
from urllib.parse import urlparse

class LoadBalancingAlgorithm(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    RANDOM = "random"

class HealthCheckType(Enum):
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    PING = "ping"

class ServerStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    DRAINING = "draining"

@dataclass
class Server:
    """Server data structure"""
    server_id: str
    host: str
    port: int
    weight: int = 1
    status: ServerStatus = ServerStatus.HEALTHY
    active_connections: int = 0
    total_requests: int = 0
    response_time: float = 0.0
    last_health_check: Optional[datetime] = None
    health_check_path: str = "/health"
    health_check_interval: int = 30
    max_connections: int = 1000
    ssl_enabled: bool = False
    tags: List[str] = field(default_factory=list)

@dataclass
class HealthCheck:
    """Health check data structure"""
    server_id: str
    check_type: HealthCheckType
    path: str
    interval: int
    timeout: int
    expected_status: int = 200
    expected_response: str = ""
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    max_failures: int = 3

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN
    health_check_interval: int = 30
    health_check_timeout: int = 5
    max_retries: int = 3
    retry_delay: int = 1
    sticky_sessions: bool = False
    session_timeout: int = 3600
    enable_ssl: bool = False
    ssl_cert_path: str = ""
    ssl_key_path: str = ""

@dataclass
class RequestStats:
    """Request statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    requests_per_second: float = 0.0
    last_request_time: Optional[datetime] = None

class LoadBalancer:
    """High-performance load balancer system"""
    
    def __init__(self, config: LoadBalancerConfig = None):
        self.config = config or LoadBalancerConfig()
        
        # Core data structures
        self.servers = {}  # server_id -> Server
        self.health_checks = {}  # server_id -> HealthCheck
        self.server_weights = {}  # server_id -> weight
        self.server_connections = defaultdict(int)  # server_id -> connection_count
        self.server_response_times = defaultdict(list)  # server_id -> List[response_time]
        self.server_round_robin_index = defaultdict(int)  # server_id -> index
        
        # Session management
        self.sticky_sessions = {}  # session_id -> server_id
        self.session_servers = defaultdict(set)  # server_id -> Set[session_id]
        
        # Statistics
        self.request_stats = RequestStats()
        self.server_stats = defaultdict(RequestStats)  # server_id -> RequestStats
        
        # Threading
        self.lock = threading.RLock()
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
        self.stats_thread = threading.Thread(target=self._update_stats_loop, daemon=True)
        self.stats_thread.start()
        
        # Configuration
        self.health_check_interval = self.config.health_check_interval
        self.health_check_timeout = self.config.health_check_timeout
        self.max_retries = self.config.max_retries
        self.retry_delay = self.config.retry_delay
    
    def add_server(self, server_id: str, host: str, port: int, weight: int = 1,
                  health_check_path: str = "/health", ssl_enabled: bool = False,
                  tags: List[str] = None) -> bool:
        """Add a server to the load balancer"""
        with self.lock:
            server = Server(
                server_id=server_id,
                host=host,
                port=port,
                weight=weight,
                health_check_path=health_check_path,
                ssl_enabled=ssl_enabled,
                tags=tags or []
            )
            
            self.servers[server_id] = server
            self.server_weights[server_id] = weight
            
            # Create health check
            health_check = HealthCheck(
                server_id=server_id,
                check_type=HealthCheckType.HTTPS if ssl_enabled else HealthCheckType.HTTP,
                path=health_check_path,
                interval=self.health_check_interval,
                timeout=self.health_check_timeout
            )
            self.health_checks[server_id] = health_check
            
            return True
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the load balancer"""
        with self.lock:
            if server_id not in self.servers:
                return False
            
            # Drain connections if server is active
            if self.servers[server_id].status == ServerStatus.HEALTHY:
                self.servers[server_id].status = ServerStatus.DRAINING
            
            # Remove from all data structures
            del self.servers[server_id]
            del self.health_checks[server_id]
            del self.server_weights[server_id]
            del self.server_connections[server_id]
            del self.server_response_times[server_id]
            del self.server_round_robin_index[server_id]
            del self.server_stats[server_id]
            
            # Remove sessions
            if server_id in self.session_servers:
                for session_id in self.session_servers[server_id]:
                    if session_id in self.sticky_sessions:
                        del self.sticky_sessions[session_id]
                del self.session_servers[server_id]
            
            return True
    
    def update_server_weight(self, server_id: str, weight: int) -> bool:
        """Update server weight"""
        with self.lock:
            if server_id not in self.servers:
                return False
            
            self.servers[server_id].weight = weight
            self.server_weights[server_id] = weight
            return True
    
    def set_server_status(self, server_id: str, status: ServerStatus) -> bool:
        """Set server status"""
        with self.lock:
            if server_id not in self.servers:
                return False
            
            self.servers[server_id].status = status
            return True
    
    def get_healthy_servers(self) -> List[Server]:
        """Get list of healthy servers"""
        with self.lock:
            return [server for server in self.servers.values() 
                   if server.status == ServerStatus.HEALTHY]
    
    def select_server(self, client_ip: str = None, session_id: str = None) -> Optional[Server]:
        """Select a server using the configured algorithm"""
        with self.lock:
            healthy_servers = self.get_healthy_servers()
            if not healthy_servers:
                return None
            
            # Check sticky sessions first
            if self.config.sticky_sessions and session_id:
                if session_id in self.sticky_sessions:
                    server_id = self.sticky_sessions[session_id]
                    if server_id in self.servers and self.servers[server_id].status == ServerStatus.HEALTHY:
                        return self.servers[server_id]
            
            # Select server based on algorithm
            if self.config.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
                return self._round_robin_selection(healthy_servers)
            elif self.config.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
                return self._least_connections_selection(healthy_servers)
            elif self.config.algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
                return self._least_response_time_selection(healthy_servers)
            elif self.config.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_selection(healthy_servers)
            elif self.config.algorithm == LoadBalancingAlgorithm.IP_HASH:
                return self._ip_hash_selection(healthy_servers, client_ip)
            elif self.config.algorithm == LoadBalancingAlgorithm.RANDOM:
                return self._random_selection(healthy_servers)
            else:
                return self._round_robin_selection(healthy_servers)
    
    def _round_robin_selection(self, servers: List[Server]) -> Server:
        """Round robin server selection"""
        if not servers:
            return None
        
        # Use a simple round robin with index tracking
        server_ids = [s.server_id for s in servers]
        index = self.server_round_robin_index['global'] % len(server_ids)
        self.server_round_robin_index['global'] += 1
        
        return self.servers[server_ids[index]]
    
    def _least_connections_selection(self, servers: List[Server]) -> Server:
        """Least connections server selection"""
        if not servers:
            return None
        
        min_connections = min(server.active_connections for server in servers)
        candidates = [server for server in servers if server.active_connections == min_connections]
        
        # If multiple servers have same connection count, use round robin
        return random.choice(candidates)
    
    def _least_response_time_selection(self, servers: List[Server]) -> Server:
        """Least response time server selection"""
        if not servers:
            return None
        
        min_response_time = min(server.response_time for server in servers if server.response_time > 0)
        candidates = [server for server in servers if server.response_time == min_response_time]
        
        # If no response time data, use round robin
        if not candidates:
            return self._round_robin_selection(servers)
        
        return random.choice(candidates)
    
    def _weighted_round_robin_selection(self, servers: List[Server]) -> Server:
        """Weighted round robin server selection"""
        if not servers:
            return None
        
        # Calculate total weight
        total_weight = sum(server.weight for server in servers)
        if total_weight == 0:
            return random.choice(servers)
        
        # Weighted selection
        random_weight = random.randint(1, total_weight)
        current_weight = 0
        
        for server in servers:
            current_weight += server.weight
            if random_weight <= current_weight:
                return server
        
        return servers[-1]  # Fallback
    
    def _ip_hash_selection(self, servers: List[Server], client_ip: str) -> Server:
        """IP hash server selection"""
        if not servers or not client_ip:
            return random.choice(servers) if servers else None
        
        # Hash client IP to select server
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        index = hash_value % len(servers)
        return servers[index]
    
    def _random_selection(self, servers: List[Server]) -> Server:
        """Random server selection"""
        return random.choice(servers) if servers else None
    
    def forward_request(self, request_data: dict, client_ip: str = None, 
                       session_id: str = None) -> Tuple[bool, dict, str]:
        """Forward request to selected server"""
        server = self.select_server(client_ip, session_id)
        if not server:
            return False, {"error": "No healthy servers available"}, ""
        
        # Update connection count
        self.server_connections[server.server_id] += 1
        server.active_connections += 1
        
        # Update statistics
        self.request_stats.total_requests += 1
        self.server_stats[server.server_id].total_requests += 1
        
        start_time = time.time()
        
        try:
            # Forward request to server
            response = self._send_request_to_server(server, request_data)
            
            # Update response time
            response_time = time.time() - start_time
            self._update_server_response_time(server.server_id, response_time)
            
            # Update statistics
            self.request_stats.successful_requests += 1
            self.server_stats[server.server_id].successful_requests += 1
            
            # Update sticky session
            if self.config.sticky_sessions and session_id:
                self.sticky_sessions[session_id] = server.server_id
                self.session_servers[server.server_id].add(session_id)
            
            return True, response, server.server_id
            
        except Exception as e:
            # Update statistics
            self.request_stats.failed_requests += 1
            self.server_stats[server.server_id].failed_requests += 1
            
            return False, {"error": str(e)}, server.server_id
            
        finally:
            # Update connection count
            self.server_connections[server.server_id] -= 1
            server.active_connections -= 1
    
    def _send_request_to_server(self, server: Server, request_data: dict) -> dict:
        """Send request to specific server"""
        # This is a simplified implementation
        # In a real system, you would forward the actual HTTP request
        
        url = f"{'https' if server.ssl_enabled else 'http'}://{server.host}:{server.port}"
        
        try:
            # Simulate request forwarding
            response = requests.get(url, timeout=self.health_check_timeout)
            return {
                "status_code": response.status_code,
                "content": response.text,
                "headers": dict(response.headers)
            }
        except Exception as e:
            raise Exception(f"Failed to forward request to {server.server_id}: {str(e)}")
    
    def _update_server_response_time(self, server_id: str, response_time: float):
        """Update server response time"""
        self.server_response_times[server_id].append(response_time)
        
        # Keep only recent response times (last 100)
        if len(self.server_response_times[server_id]) > 100:
            self.server_response_times[server_id] = self.server_response_times[server_id][-100:]
        
        # Update server's average response time
        if server_id in self.servers:
            self.servers[server_id].response_time = statistics.mean(self.server_response_times[server_id])
    
    def _health_check_loop(self):
        """Health check loop running in background"""
        while True:
            try:
                time.sleep(self.health_check_interval)
                
                with self.lock:
                    for server_id, health_check in self.health_checks.items():
                        if server_id not in self.servers:
                            continue
                        
                        self._perform_health_check(server_id, health_check)
                
            except Exception as e:
                print(f"Error in health check loop: {e}")
    
    def _perform_health_check(self, server_id: str, health_check: HealthCheck):
        """Perform health check on a server"""
        server = self.servers[server_id]
        
        try:
            # Perform health check based on type
            if health_check.check_type == HealthCheckType.HTTP:
                success = self._http_health_check(server, health_check)
            elif health_check.check_type == HealthCheckType.HTTPS:
                success = self._https_health_check(server, health_check)
            elif health_check.check_type == HealthCheckType.TCP:
                success = self._tcp_health_check(server, health_check)
            else:
                success = False
            
            # Update health check results
            health_check.last_check = datetime.now()
            
            if success:
                health_check.consecutive_failures = 0
                if server.status != ServerStatus.HEALTHY:
                    server.status = ServerStatus.HEALTHY
                    print(f"Server {server_id} is now healthy")
            else:
                health_check.consecutive_failures += 1
                if health_check.consecutive_failures >= health_check.max_failures:
                    if server.status == ServerStatus.HEALTHY:
                        server.status = ServerStatus.UNHEALTHY
                        print(f"Server {server_id} is now unhealthy")
        
        except Exception as e:
            print(f"Health check failed for server {server_id}: {e}")
            health_check.consecutive_failures += 1
    
    def _http_health_check(self, server: Server, health_check: HealthCheck) -> bool:
        """HTTP health check"""
        try:
            url = f"http://{server.host}:{server.port}{health_check.path}"
            response = requests.get(url, timeout=health_check.timeout)
            return response.status_code == health_check.expected_status
        except:
            return False
    
    def _https_health_check(self, server: Server, health_check: HealthCheck) -> bool:
        """HTTPS health check"""
        try:
            url = f"https://{server.host}:{server.port}{health_check.path}"
            response = requests.get(url, timeout=health_check.timeout, verify=False)
            return response.status_code == health_check.expected_status
        except:
            return False
    
    def _tcp_health_check(self, server: Server, health_check: HealthCheck) -> bool:
        """TCP health check"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(health_check.timeout)
            result = sock.connect_ex((server.host, server.port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _update_stats_loop(self):
        """Update statistics in background"""
        while True:
            try:
                time.sleep(60)  # Update every minute
                
                with self.lock:
                    self._update_request_stats()
                
            except Exception as e:
                print(f"Error in stats update loop: {e}")
    
    def _update_request_stats(self):
        """Update request statistics"""
        # Update average response time
        if self.server_response_times:
            all_response_times = []
            for response_times in self.server_response_times.values():
                all_response_times.extend(response_times)
            
            if all_response_times:
                self.request_stats.average_response_time = statistics.mean(all_response_times)
        
        # Update requests per second (simplified)
        current_time = datetime.now()
        if self.request_stats.last_request_time:
            time_diff = (current_time - self.request_stats.last_request_time).total_seconds()
            if time_diff > 0:
                self.request_stats.requests_per_second = self.request_stats.total_requests / time_diff
        
        self.request_stats.last_request_time = current_time
    
    def get_server_stats(self, server_id: str = None) -> dict:
        """Get server statistics"""
        with self.lock:
            if server_id:
                if server_id not in self.servers:
                    return {}
                
                server = self.servers[server_id]
                stats = self.server_stats[server_id]
                
                return {
                    "server_id": server_id,
                    "host": server.host,
                    "port": server.port,
                    "status": server.status.value,
                    "weight": server.weight,
                    "active_connections": server.active_connections,
                    "total_requests": stats.total_requests,
                    "successful_requests": stats.successful_requests,
                    "failed_requests": stats.failed_requests,
                    "average_response_time": server.response_time,
                    "last_health_check": server.last_health_check.isoformat() if server.last_health_check else None
                }
            else:
                # Return all server stats
                return {
                    server_id: self.get_server_stats(server_id)
                    for server_id in self.servers.keys()
                }
    
    def get_load_balancer_stats(self) -> dict:
        """Get load balancer statistics"""
        with self.lock:
            healthy_servers = len(self.get_healthy_servers())
            total_servers = len(self.servers)
            
            return {
                "total_servers": total_servers,
                "healthy_servers": healthy_servers,
                "unhealthy_servers": total_servers - healthy_servers,
                "algorithm": self.config.algorithm.value,
                "sticky_sessions_enabled": self.config.sticky_sessions,
                "total_requests": self.request_stats.total_requests,
                "successful_requests": self.request_stats.successful_requests,
                "failed_requests": self.request_stats.failed_requests,
                "average_response_time": self.request_stats.average_response_time,
                "requests_per_second": self.request_stats.requests_per_second,
                "active_sessions": len(self.sticky_sessions)
            }
    
    def drain_server(self, server_id: str) -> bool:
        """Drain a server (stop accepting new connections)"""
        with self.lock:
            if server_id not in self.servers:
                return False
            
            self.servers[server_id].status = ServerStatus.DRAINING
            return True
    
    def enable_server(self, server_id: str) -> bool:
        """Enable a server"""
        with self.lock:
            if server_id not in self.servers:
                return False
            
            self.servers[server_id].status = ServerStatus.HEALTHY
            return True
    
    def disable_server(self, server_id: str) -> bool:
        """Disable a server"""
        with self.lock:
            if server_id not in self.servers:
                return False
            
            self.servers[server_id].status = ServerStatus.UNHEALTHY
            return True


# Example usage and testing
if __name__ == "__main__":
    # Initialize load balancer
    config = LoadBalancerConfig(
        algorithm=LoadBalancingAlgorithm.ROUND_ROBIN,
        sticky_sessions=True
    )
    lb = LoadBalancer(config)
    
    # Add servers
    lb.add_server("server1", "192.168.1.10", 8080, weight=1)
    lb.add_server("server2", "192.168.1.11", 8080, weight=2)
    lb.add_server("server3", "192.168.1.12", 8080, weight=1)
    
    # Simulate requests
    for i in range(10):
        success, response, server_id = lb.forward_request(
            {"method": "GET", "path": "/api/test"},
            client_ip="192.168.1.100",
            session_id=f"session_{i}"
        )
        print(f"Request {i}: {success}, Server: {server_id}")
    
    # Get statistics
    stats = lb.get_load_balancer_stats()
    print(f"Load balancer stats: {stats}")
    
    # Get server stats
    server_stats = lb.get_server_stats()
    print(f"Server stats: {server_stats}")
