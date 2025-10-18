"""
DNS System Implementation
High-performance DNS server with caching and load balancing
"""

import time
import threading
import socket
import json
import redis
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import hashlib
import struct
import random
import ipaddress

class RecordType(Enum):
    A = 1
    AAAA = 28
    CNAME = 5
    MX = 15
    NS = 2
    PTR = 12
    SOA = 6
    TXT = 16
    SRV = 33

class QueryClass(Enum):
    IN = 1
    CH = 3
    HS = 4

class ResponseCode(Enum):
    NO_ERROR = 0
    FORMAT_ERROR = 1
    SERVER_FAILURE = 2
    NAME_ERROR = 3
    NOT_IMPLEMENTED = 4
    REFUSED = 5

@dataclass
class DNSRecord:
    """DNS record data structure"""
    name: str
    record_type: RecordType
    record_class: QueryClass
    ttl: int
    data: str
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0

@dataclass
class DNSQuery:
    """DNS query data structure"""
    query_id: int
    name: str
    record_type: RecordType
    record_class: QueryClass
    client_ip: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DNSResponse:
    """DNS response data structure"""
    query_id: int
    response_code: ResponseCode
    answers: List[DNSRecord] = field(default_factory=list)
    authorities: List[DNSRecord] = field(default_factory=list)
    additional: List[DNSRecord] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Zone:
    """DNS zone data structure"""
    zone_name: str
    primary_ns: str
    admin_email: str
    serial: int
    refresh: int
    retry: int
    expire: int
    minimum_ttl: int
    records: Dict[str, List[DNSRecord]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class DNSSystem:
    """High-performance DNS server system"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Core data structures
        self.records = {}  # name -> List[DNSRecord]
        self.zones = {}  # zone_name -> Zone
        self.cache = {}  # query_key -> (DNSResponse, expiry_time)
        
        # Statistics
        self.query_stats = defaultdict(int)  # record_type -> count
        self.response_stats = defaultdict(int)  # response_code -> count
        self.client_stats = defaultdict(int)  # client_ip -> count
        self.performance_stats = deque(maxlen=1000)  # List of response times
        
        # Threading
        self.lock = threading.RLock()
        self.cache_cleanup_thread = threading.Thread(target=self._cache_cleanup_loop, daemon=True)
        self.cache_cleanup_thread.start()
        self.stats_thread = threading.Thread(target=self._stats_loop, daemon=True)
        self.stats_thread.start()
        
        # Configuration
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 10000
        self.cleanup_interval = 60  # 1 minute
        self.stats_interval = 300  # 5 minutes
        self.default_ttl = 3600  # 1 hour
        
        # Load balancing
        self.load_balancing_enabled = True
        self.health_check_interval = 30  # 30 seconds
        self.unhealthy_servers = set()
        
        # Initialize default records
        self._initialize_default_records()
    
    def _initialize_default_records(self):
        """Initialize default DNS records"""
        # Add some common records
        self.add_record("localhost", RecordType.A, "127.0.0.1", ttl=3600)
        self.add_record("localhost", RecordType.AAAA, "::1", ttl=3600)
        self.add_record("example.com", RecordType.A, "93.184.216.34", ttl=3600)
        self.add_record("example.com", RecordType.AAAA, "2606:2800:220:1:248:1893:25c8:1946", ttl=3600)
        self.add_record("example.com", RecordType.MX, "mail.example.com", ttl=3600, priority=10)
        self.add_record("www.example.com", RecordType.CNAME, "example.com", ttl=3600)
    
    def add_record(self, name: str, record_type: RecordType, data: str, 
                  ttl: int = None, priority: int = 0) -> DNSRecord:
        """Add a DNS record"""
        with self.lock:
            ttl = ttl or self.default_ttl
            
            record = DNSRecord(
                name=name.lower(),
                record_type=record_type,
                record_class=QueryClass.IN,
                ttl=ttl,
                data=data,
                priority=priority
            )
            
            if name not in self.records:
                self.records[name] = []
            
            self.records[name].append(record)
            
            # Persist to Redis
            self._persist_record(record)
            
            return record
    
    def remove_record(self, name: str, record_type: RecordType, data: str = None) -> bool:
        """Remove a DNS record"""
        with self.lock:
            if name not in self.records:
                return False
            
            records = self.records[name]
            if data:
                # Remove specific record
                records[:] = [r for r in records if not (r.record_type == record_type and r.data == data)]
            else:
                # Remove all records of this type
                records[:] = [r for r in records if r.record_type != record_type]
            
            if not records:
                del self.records[name]
            
            # Remove from Redis
            self._remove_record_from_redis(name, record_type, data)
            
            return True
    
    def create_zone(self, zone_name: str, primary_ns: str, admin_email: str,
                   serial: int = 1, refresh: int = 3600, retry: int = 1800,
                   expire: int = 604800, minimum_ttl: int = 3600) -> Zone:
        """Create a DNS zone"""
        with self.lock:
            zone = Zone(
                zone_name=zone_name.lower(),
                primary_ns=primary_ns,
                admin_email=admin_email,
                serial=serial,
                refresh=refresh,
                retry=retry,
                expire=expire,
                minimum_ttl=minimum_ttl
            )
            
            self.zones[zone_name] = zone
            
            # Persist to Redis
            self._persist_zone(zone)
            
            return zone
    
    def add_zone_record(self, zone_name: str, name: str, record_type: RecordType,
                       data: str, ttl: int = None, priority: int = 0) -> bool:
        """Add a record to a zone"""
        with self.lock:
            if zone_name not in self.zones:
                return False
            
            zone = self.zones[zone_name]
            ttl = ttl or zone.minimum_ttl
            
            record = DNSRecord(
                name=name.lower(),
                record_type=record_type,
                record_class=QueryClass.IN,
                ttl=ttl,
                data=data,
                priority=priority
            )
            
            if name not in zone.records:
                zone.records[name] = []
            
            zone.records[name].append(record)
            zone.updated_at = datetime.now()
            zone.serial += 1
            
            # Also add to global records
            self.add_record(name, record_type, data, ttl, priority)
            
            # Persist zone
            self._persist_zone(zone)
            
            return True
    
    def query(self, name: str, record_type: RecordType, client_ip: str = "127.0.0.1") -> DNSResponse:
        """Process a DNS query"""
        start_time = time.time()
        
        with self.lock:
            # Create query object
            query = DNSQuery(
                query_id=random.randint(1, 65535),
                name=name.lower(),
                record_type=record_type,
                record_class=QueryClass.IN,
                client_ip=client_ip
            )
            
            # Check cache first
            cache_key = f"{name}:{record_type.value}"
            if cache_key in self.cache:
                cached_response, expiry_time = self.cache[cache_key]
                if time.time() < expiry_time:
                    # Update access count
                    for record in cached_response.answers:
                        if record.name in self.records:
                            for r in self.records[record.name]:
                                if r.record_type == record.record_type and r.data == record.data:
                                    r.access_count += 1
                                    r.last_accessed = datetime.now()
                    
                    # Update statistics
                    self.query_stats[record_type] += 1
                    self.client_stats[client_ip] += 1
                    
                    return cached_response
            
            # Process query
            response = self._process_query(query)
            
            # Cache response
            if response.response_code == ResponseCode.NO_ERROR:
                self.cache[cache_key] = (response, time.time() + self.cache_ttl)
                
                # Limit cache size
                if len(self.cache) > self.max_cache_size:
                    self._cleanup_cache()
            
            # Update statistics
            self.query_stats[record_type] += 1
            self.response_stats[response.response_code] += 1
            self.client_stats[client_ip] += 1
            
            # Record performance
            response_time = time.time() - start_time
            self.performance_stats.append(response_time)
            
            return response
    
    def _process_query(self, query: DNSQuery) -> DNSResponse:
        """Process a DNS query"""
        response = DNSResponse(
            query_id=query.query_id,
            response_code=ResponseCode.NO_ERROR
        )
        
        # Look for exact match
        if query.name in self.records:
            matching_records = [
                r for r in self.records[query.name]
                if r.record_type == query.record_type
            ]
            
            if matching_records:
                response.answers = matching_records
                
                # Update access count
                for record in matching_records:
                    record.access_count += 1
                    record.last_accessed = datetime.now()
                
                return response
        
        # Look for CNAME records
        cname_records = self._find_cname_records(query.name)
        if cname_records:
            response.answers = cname_records
            
            # Follow CNAME chain
            for cname in cname_records:
                target_name = cname.data
                target_records = self._find_records(target_name, query.record_type)
                if target_records:
                    response.answers.extend(target_records)
            
            return response
        
        # Look for wildcard records
        wildcard_records = self._find_wildcard_records(query.name, query.record_type)
        if wildcard_records:
            response.answers = wildcard_records
            return response
        
        # Check zones
        zone_records = self._find_zone_records(query.name, query.record_type)
        if zone_records:
            response.answers = zone_records
            return response
        
        # No records found
        response.response_code = ResponseCode.NAME_ERROR
        return response
    
    def _find_cname_records(self, name: str) -> List[DNSRecord]:
        """Find CNAME records for a name"""
        if name not in self.records:
            return []
        
        return [r for r in self.records[name] if r.record_type == RecordType.CNAME]
    
    def _find_records(self, name: str, record_type: RecordType) -> List[DNSRecord]:
        """Find records for a name and type"""
        if name not in self.records:
            return []
        
        return [r for r in self.records[name] if r.record_type == record_type]
    
    def _find_wildcard_records(self, name: str, record_type: RecordType) -> List[DNSRecord]:
        """Find wildcard records for a name"""
        # Simple wildcard matching - in production, use proper wildcard logic
        parts = name.split('.')
        if len(parts) < 2:
            return []
        
        # Try different wildcard patterns
        for i in range(1, len(parts)):
            wildcard_name = '*.' + '.'.join(parts[i:])
            if wildcard_name in self.records:
                matching_records = [
                    r for r in self.records[wildcard_name]
                    if r.record_type == record_type
                ]
                if matching_records:
                    return matching_records
        
        return []
    
    def _find_zone_records(self, name: str, record_type: RecordType) -> List[DNSRecord]:
        """Find records in zones"""
        for zone in self.zones.values():
            if name.endswith('.' + zone.zone_name) or name == zone.zone_name:
                if name in zone.records:
                    return [r for r in zone.records[name] if r.record_type == record_type]
        
        return []
    
    def get_records(self, name: str = None, record_type: RecordType = None) -> List[DNSRecord]:
        """Get DNS records"""
        with self.lock:
            if name:
                records = self.records.get(name, [])
                if record_type:
                    records = [r for r in records if r.record_type == record_type]
                return records
            else:
                all_records = []
                for name_records in self.records.values():
                    all_records.extend(name_records)
                
                if record_type:
                    all_records = [r for r in all_records if r.record_type == record_type]
                
                return all_records
    
    def get_zone_records(self, zone_name: str) -> List[DNSRecord]:
        """Get all records in a zone"""
        with self.lock:
            if zone_name not in self.zones:
                return []
            
            zone = self.zones[zone_name]
            all_records = []
            for name_records in zone.records.values():
                all_records.extend(name_records)
            
            return all_records
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get DNS server statistics"""
        with self.lock:
            total_queries = sum(self.query_stats.values())
            total_responses = sum(self.response_stats.values())
            
            return {
                "total_queries": total_queries,
                "total_responses": total_responses,
                "query_stats": dict(self.query_stats),
                "response_stats": {rc.name: count for rc, count in self.response_stats.items()},
                "top_clients": dict(sorted(self.client_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                "total_records": sum(len(records) for records in self.records.values()),
                "total_zones": len(self.zones),
                "cache_size": len(self.cache),
                "average_response_time": statistics.mean(self.performance_stats) if self.performance_stats else 0,
                "max_response_time": max(self.performance_stats) if self.performance_stats else 0,
                "min_response_time": min(self.performance_stats) if self.performance_stats else 0
            }
    
    def get_zone_statistics(self, zone_name: str) -> Dict[str, Any]:
        """Get statistics for a specific zone"""
        with self.lock:
            if zone_name not in self.zones:
                return {}
            
            zone = self.zones[zone_name]
            total_records = sum(len(records) for records in zone.records.values())
            
            return {
                "zone_name": zone.zone_name,
                "primary_ns": zone.primary_ns,
                "admin_email": zone.admin_email,
                "serial": zone.serial,
                "total_records": total_records,
                "created_at": zone.created_at.isoformat(),
                "updated_at": zone.updated_at.isoformat(),
                "refresh": zone.refresh,
                "retry": zone.retry,
                "expire": zone.expire,
                "minimum_ttl": zone.minimum_ttl
            }
    
    def _cache_cleanup_loop(self):
        """Cache cleanup loop"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                
                with self.lock:
                    self._cleanup_cache()
                
            except Exception as e:
                print(f"Error in cache cleanup loop: {e}")
    
    def _stats_loop(self):
        """Statistics update loop"""
        while True:
            try:
                time.sleep(self.stats_interval)
                
                with self.lock:
                    # Update record access statistics
                    for name, records in self.records.items():
                        for record in records:
                            if record.last_accessed:
                                # Update TTL based on access patterns
                                if record.access_count > 100:
                                    record.ttl = min(record.ttl * 2, 86400)  # Max 24 hours
                                elif record.access_count < 10:
                                    record.ttl = max(record.ttl // 2, 300)  # Min 5 minutes
                
            except Exception as e:
                print(f"Error in stats loop: {e}")
    
    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self.cache.items()
            if current_time >= expiry_time
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def _persist_record(self, record: DNSRecord):
        """Persist record to Redis"""
        record_data = {
            "name": record.name,
            "record_type": record.record_type.value,
            "record_class": record.record_class.value,
            "ttl": str(record.ttl),
            "data": record.data,
            "priority": str(record.priority),
            "created_at": record.created_at.isoformat(),
            "last_accessed": record.last_accessed.isoformat() if record.last_accessed else None,
            "access_count": str(record.access_count)
        }
        
        key = f"dns_record:{record.name}:{record.record_type.value}:{record.data}"
        self.redis_client.hset(key, mapping=record_data)
        self.redis_client.expire(key, record.ttl)
    
    def _remove_record_from_redis(self, name: str, record_type: RecordType, data: str = None):
        """Remove record from Redis"""
        if data:
            key = f"dns_record:{name}:{record_type.value}:{data}"
            self.redis_client.delete(key)
        else:
            # Remove all records of this type for this name
            pattern = f"dns_record:{name}:{record_type.value}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
    
    def _persist_zone(self, zone: Zone):
        """Persist zone to Redis"""
        zone_data = {
            "zone_name": zone.zone_name,
            "primary_ns": zone.primary_ns,
            "admin_email": zone.admin_email,
            "serial": str(zone.serial),
            "refresh": str(zone.refresh),
            "retry": str(zone.retry),
            "expire": str(zone.expire),
            "minimum_ttl": str(zone.minimum_ttl),
            "created_at": zone.created_at.isoformat(),
            "updated_at": zone.updated_at.isoformat()
        }
        
        self.redis_client.hset(f"dns_zone:{zone.zone_name}", mapping=zone_data)
        
        # Persist zone records
        for name, records in zone.records.items():
            for record in records:
                self._persist_record(record)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        with self.lock:
            return {
                "total_records": sum(len(records) for records in self.records.values()),
                "total_zones": len(self.zones),
                "cache_size": len(self.cache),
                "max_cache_size": self.max_cache_size,
                "cache_ttl": self.cache_ttl,
                "default_ttl": self.default_ttl,
                "load_balancing_enabled": self.load_balancing_enabled,
                "unhealthy_servers": len(self.unhealthy_servers),
                "performance_samples": len(self.performance_stats)
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize DNS system
    dns = DNSSystem()
    
    # Add some records
    dns.add_record("test.example.com", RecordType.A, "192.168.1.100", ttl=3600)
    dns.add_record("test.example.com", RecordType.AAAA, "2001:db8::1", ttl=3600)
    dns.add_record("mail.example.com", RecordType.A, "192.168.1.101", ttl=3600)
    dns.add_record("example.com", RecordType.MX, "mail.example.com", ttl=3600, priority=10)
    dns.add_record("www.example.com", RecordType.CNAME, "example.com", ttl=3600)
    
    # Create a zone
    zone = dns.create_zone("example.com", "ns1.example.com", "admin@example.com")
    dns.add_zone_record("example.com", "ns1.example.com", RecordType.A, "192.168.1.1")
    dns.add_zone_record("example.com", "ns2.example.com", RecordType.A, "192.168.1.2")
    
    # Query some records
    response1 = dns.query("test.example.com", RecordType.A)
    print(f"Query test.example.com A: {response1.response_code.name}")
    print(f"Answers: {[r.data for r in response1.answers]}")
    
    response2 = dns.query("example.com", RecordType.MX)
    print(f"Query example.com MX: {response2.response_code.name}")
    print(f"Answers: {[r.data for r in response2.answers]}")
    
    response3 = dns.query("www.example.com", RecordType.A)
    print(f"Query www.example.com A: {response3.response_code.name}")
    print(f"Answers: {[r.data for r in response3.answers]}")
    
    # Get statistics
    stats = dns.get_statistics()
    print(f"DNS Statistics: {stats}")
    
    # Get zone statistics
    zone_stats = dns.get_zone_statistics("example.com")
    print(f"Zone Statistics: {zone_stats}")
    
    # Get system stats
    system_stats = dns.get_system_stats()
    print(f"System Stats: {system_stats}")
