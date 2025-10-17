#!/usr/bin/env python3
"""
DNS Service

A comprehensive DNS (Domain Name System) service for domain resolution,
DNS record management, and DNS query handling with support for various
record types and caching mechanisms.
"""

import sqlite3
import socket
import time
import hashlib
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecordType(Enum):
    """DNS record types."""
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    PTR = "PTR"
    SOA = "SOA"
    SRV = "SRV"
    TXT = "TXT"

@dataclass
class DNSRecord:
    """DNS record model."""
    id: str
    name: str
    record_type: RecordType
    value: str
    ttl: int = 3600  # Time to live in seconds
    priority: int = 0  # For MX and SRV records
    weight: int = 0  # For SRV records
    port: int = 0  # For SRV records
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class DNSQuery:
    """DNS query model."""
    query_id: str
    domain: str
    record_type: RecordType
    client_ip: str
    timestamp: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0
    cached: bool = False
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class DNSZone:
    """DNS zone model."""
    zone_id: str
    name: str
    primary_ns: str
    admin_email: str
    serial: int = 1
    refresh: int = 3600
    retry: int = 1800
    expire: int = 604800
    minimum_ttl: int = 3600
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class DNSCache:
    """DNS cache entry."""
    key: str
    records: List[DNSRecord]
    expires_at: datetime
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

class DNSDatabase:
    """Database operations for DNS service."""
    
    def __init__(self, db_path: str = "dns.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # DNS records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dns_records (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                record_type TEXT NOT NULL,
                value TEXT NOT NULL,
                ttl INTEGER DEFAULT 3600,
                priority INTEGER DEFAULT 0,
                weight INTEGER DEFAULT 0,
                port INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # DNS zones table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dns_zones (
                zone_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                primary_ns TEXT NOT NULL,
                admin_email TEXT NOT NULL,
                serial INTEGER DEFAULT 1,
                refresh INTEGER DEFAULT 3600,
                retry INTEGER DEFAULT 1800,
                expire INTEGER DEFAULT 604800,
                minimum_ttl INTEGER DEFAULT 3600,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # DNS queries log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dns_queries (
                query_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                record_type TEXT NOT NULL,
                client_ip TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time REAL DEFAULT 0.0,
                cached BOOLEAN DEFAULT 0,
                success BOOLEAN DEFAULT 1,
                error_message TEXT
            )
        ''')
        
        # DNS cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dns_cache (
                cache_key TEXT PRIMARY KEY,
                records TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                hit_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_dns_record(self, record: DNSRecord) -> bool:
        """Save DNS record to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO dns_records 
                (id, name, record_type, value, ttl, priority, weight, port, 
                 created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.id, record.name, record.record_type.value, record.value,
                record.ttl, record.priority, record.weight, record.port,
                record.created_at, record.updated_at, record.is_active
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving DNS record: {e}")
            return False
    
    def get_dns_records(self, name: str, record_type: RecordType = None) -> List[DNSRecord]:
        """Get DNS records by name and type."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if record_type:
                cursor.execute('''
                    SELECT * FROM dns_records 
                    WHERE name = ? AND record_type = ? AND is_active = 1
                    ORDER BY priority ASC, created_at ASC
                ''', (name, record_type.value))
            else:
                cursor.execute('''
                    SELECT * FROM dns_records 
                    WHERE name = ? AND is_active = 1
                    ORDER BY priority ASC, created_at ASC
                ''', (name,))
            
            records = []
            for row in cursor.fetchall():
                record = DNSRecord(
                    id=row[0],
                    name=row[1],
                    record_type=RecordType(row[2]),
                    value=row[3],
                    ttl=row[4],
                    priority=row[5],
                    weight=row[6],
                    port=row[7],
                    created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                    is_active=bool(row[10])
                )
                records.append(record)
            
            conn.close()
            return records
        except Exception as e:
            logger.error(f"Error getting DNS records: {e}")
            return []
    
    def save_dns_zone(self, zone: DNSZone) -> bool:
        """Save DNS zone to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO dns_zones 
                (zone_id, name, primary_ns, admin_email, serial, refresh, 
                 retry, expire, minimum_ttl, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                zone.zone_id, zone.name, zone.primary_ns, zone.admin_email,
                zone.serial, zone.refresh, zone.retry, zone.expire,
                zone.minimum_ttl, zone.created_at, zone.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving DNS zone: {e}")
            return False
    
    def get_dns_zone(self, name: str) -> Optional[DNSZone]:
        """Get DNS zone by name."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM dns_zones WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            if row:
                zone = DNSZone(
                    zone_id=row[0],
                    name=row[1],
                    primary_ns=row[2],
                    admin_email=row[3],
                    serial=row[4],
                    refresh=row[5],
                    retry=row[6],
                    expire=row[7],
                    minimum_ttl=row[8],
                    created_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now()
                )
                conn.close()
                return zone
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting DNS zone: {e}")
            return None
    
    def log_dns_query(self, query: DNSQuery) -> bool:
        """Log DNS query to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO dns_queries 
                (query_id, domain, record_type, client_ip, timestamp, 
                 response_time, cached, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                query.query_id, query.domain, query.record_type.value,
                query.client_ip, query.timestamp, query.response_time,
                query.cached, query.success, query.error_message
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging DNS query: {e}")
            return False
    
    def get_dns_cache(self, cache_key: str) -> Optional[DNSCache]:
        """Get DNS cache entry."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM dns_cache 
                WHERE cache_key = ? AND expires_at > datetime('now')
            ''', (cache_key,))
            row = cursor.fetchone()
            
            if row:
                cache = DNSCache(
                    key=row[0],
                    records=[],  # Will be populated from JSON
                    expires_at=datetime.fromisoformat(row[2]),
                    hit_count=row[3],
                    last_accessed=datetime.fromisoformat(row[4]) if row[4] else datetime.now()
                )
                
                # Parse records from JSON
                records_data = json.loads(row[1])
                for record_data in records_data:
                    record = DNSRecord(
                        id=record_data['id'],
                        name=record_data['name'],
                        record_type=RecordType(record_data['record_type']),
                        value=record_data['value'],
                        ttl=record_data['ttl'],
                        priority=record_data.get('priority', 0),
                        weight=record_data.get('weight', 0),
                        port=record_data.get('port', 0),
                        created_at=datetime.fromisoformat(record_data['created_at']),
                        updated_at=datetime.fromisoformat(record_data['updated_at']),
                        is_active=record_data.get('is_active', True)
                    )
                    cache.records.append(record)
                
                conn.close()
                return cache
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting DNS cache: {e}")
            return None
    
    def save_dns_cache(self, cache: DNSCache) -> bool:
        """Save DNS cache entry."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert records to JSON
            records_data = []
            for record in cache.records:
                record_data = {
                    'id': record.id,
                    'name': record.name,
                    'record_type': record.record_type.value,
                    'value': record.value,
                    'ttl': record.ttl,
                    'priority': record.priority,
                    'weight': record.weight,
                    'port': record.port,
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat(),
                    'is_active': record.is_active
                }
                records_data.append(record_data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO dns_cache 
                (cache_key, records, expires_at, hit_count, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                cache.key, json.dumps(records_data), cache.expires_at.isoformat(),
                cache.hit_count, cache.last_accessed.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving DNS cache: {e}")
            return False
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current time in ISO format
            current_time = datetime.now().isoformat()
            
            cursor.execute('''
                DELETE FROM dns_cache WHERE expires_at <= ?
            ''', (current_time,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return 0

class DNSService:
    """DNS service with caching and query handling."""
    
    def __init__(self, db_path: str = "dns.db"):
        self.db = DNSDatabase(db_path)
        self.cache_lock = threading.Lock()
        self.cache_ttl = 300  # 5 minutes default cache TTL
        
    def generate_record_id(self, name: str, record_type: RecordType) -> str:
        """Generate unique record ID."""
        return hashlib.md5(f"{name}{record_type.value}{time.time()}".encode()).hexdigest()[:12]
    
    def generate_query_id(self) -> str:
        """Generate unique query ID."""
        return hashlib.md5(f"query{time.time()}".encode()).hexdigest()[:12]
    
    def create_dns_record(self, name: str, record_type: RecordType, value: str,
                         ttl: int = 3600, priority: int = 0, weight: int = 0, 
                         port: int = 0) -> Optional[DNSRecord]:
        """Create a new DNS record."""
        record_id = self.generate_record_id(name, record_type)
        
        record = DNSRecord(
            id=record_id,
            name=name,
            record_type=record_type,
            value=value,
            ttl=ttl,
            priority=priority,
            weight=weight,
            port=port
        )
        
        if self.db.save_dns_record(record):
            return record
        return None
    
    def get_dns_records(self, name: str, record_type: RecordType = None) -> List[DNSRecord]:
        """Get DNS records for a domain."""
        return self.db.get_dns_records(name, record_type)
    
    def create_dns_zone(self, name: str, primary_ns: str, admin_email: str) -> Optional[DNSZone]:
        """Create a new DNS zone."""
        zone_id = hashlib.md5(f"zone{name}{time.time()}".encode()).hexdigest()[:12]
        
        zone = DNSZone(
            zone_id=zone_id,
            name=name,
            primary_ns=primary_ns,
            admin_email=admin_email
        )
        
        if self.db.save_dns_zone(zone):
            return zone
        return None
    
    def get_dns_zone(self, name: str) -> Optional[DNSZone]:
        """Get DNS zone by name."""
        return self.db.get_dns_zone(name)
    
    def resolve_domain(self, domain: str, record_type: RecordType = RecordType.A,
                      client_ip: str = "127.0.0.1") -> List[DNSRecord]:
        """Resolve domain name to DNS records."""
        start_time = time.time()
        query_id = self.generate_query_id()
        
        try:
            # Check cache first
            cache_key = f"{domain}:{record_type.value}"
            cached_result = self.db.get_dns_cache(cache_key)
            
            if cached_result:
                # Update hit count and last accessed
                cached_result.hit_count += 1
                cached_result.last_accessed = datetime.now()
                self.db.save_dns_cache(cached_result)
                
                # Log query
                query = DNSQuery(
                    query_id=query_id,
                    domain=domain,
                    record_type=record_type,
                    client_ip=client_ip,
                    response_time=time.time() - start_time,
                    cached=True
                )
                self.db.log_dns_query(query)
                
                return cached_result.records
            
            # Query database
            records = self.db.get_dns_records(domain, record_type)
            
            # Cache the result
            if records:
                cache = DNSCache(
                    key=cache_key,
                    records=records,
                    expires_at=datetime.now() + timedelta(seconds=self.cache_ttl)
                )
                self.db.save_dns_cache(cache)
            
            # Log query
            query = DNSQuery(
                query_id=query_id,
                domain=domain,
                record_type=record_type,
                client_ip=client_ip,
                response_time=time.time() - start_time,
                cached=False,
                success=len(records) > 0
            )
            self.db.log_dns_query(query)
            
            return records
            
        except Exception as e:
            logger.error(f"Error resolving domain {domain}: {e}")
            
            # Log failed query
            query = DNSQuery(
                query_id=query_id,
                domain=domain,
                record_type=record_type,
                client_ip=client_ip,
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
            self.db.log_dns_query(query)
            
            return []
    
    def reverse_dns_lookup(self, ip: str) -> List[DNSRecord]:
        """Perform reverse DNS lookup."""
        try:
            # For reverse DNS, we need PTR records
            # This is a simplified implementation
            records = self.db.get_dns_records(ip, RecordType.PTR)
            return records
        except Exception as e:
            logger.error(f"Error in reverse DNS lookup for {ip}: {e}")
            return []
    
    def get_query_stats(self, domain: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get DNS query statistics."""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Get total queries
            if domain:
                cursor.execute('''
                    SELECT COUNT(*) FROM dns_queries 
                    WHERE domain = ? AND timestamp > datetime('now', '-{} hours')
                '''.format(hours), (domain,))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM dns_queries 
                    WHERE timestamp > datetime('now', '-{} hours')
                '''.format(hours))
            
            total_queries = cursor.fetchone()[0]
            
            # Get cached queries
            if domain:
                cursor.execute('''
                    SELECT COUNT(*) FROM dns_queries 
                    WHERE domain = ? AND cached = 1 AND timestamp > datetime('now', '-{} hours')
                '''.format(hours), (domain,))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM dns_queries 
                    WHERE cached = 1 AND timestamp > datetime('now', '-{} hours')
                '''.format(hours))
            
            cached_queries = cursor.fetchone()[0]
            
            # Get average response time
            if domain:
                cursor.execute('''
                    SELECT AVG(response_time) FROM dns_queries 
                    WHERE domain = ? AND success = 1 AND timestamp > datetime('now', '-{} hours')
                '''.format(hours), (domain,))
            else:
                cursor.execute('''
                    SELECT AVG(response_time) FROM dns_queries 
                    WHERE success = 1 AND timestamp > datetime('now', '-{} hours')
                '''.format(hours))
            
            avg_response_time = cursor.fetchone()[0] or 0.0
            
            # Get top domains
            if not domain:
                cursor.execute('''
                    SELECT domain, COUNT(*) as count FROM dns_queries 
                    WHERE timestamp > datetime('now', '-{} hours')
                    GROUP BY domain ORDER BY count DESC LIMIT 10
                '''.format(hours))
                top_domains = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
            else:
                top_domains = []
            
            conn.close()
            
            return {
                'total_queries': total_queries,
                'cached_queries': cached_queries,
                'cache_hit_rate': (cached_queries / total_queries * 100) if total_queries > 0 else 0,
                'average_response_time': avg_response_time,
                'top_domains': top_domains
            }
        except Exception as e:
            logger.error(f"Error getting query stats: {e}")
            return {}
    
    def cleanup_cache(self) -> int:
        """Clean up expired cache entries."""
        return self.db.cleanup_expired_cache()

# Global service instance
dns_service = DNSService()

# Flask app for API
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    """Index page."""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DNS Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .record { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .stats { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>DNS Service</h1>
            
            <h2>DNS Lookup</h2>
            <form id="lookupForm">
                <div class="form-group">
                    <label for="domain">Domain Name:</label>
                    <input type="text" id="domain" name="domain" placeholder="example.com" required>
                </div>
                <div class="form-group">
                    <label for="record_type">Record Type:</label>
                    <select id="record_type" name="record_type">
                        <option value="A">A</option>
                        <option value="AAAA">AAAA</option>
                        <option value="CNAME">CNAME</option>
                        <option value="MX">MX</option>
                        <option value="NS">NS</option>
                        <option value="PTR">PTR</option>
                        <option value="TXT">TXT</option>
                    </select>
                </div>
                <button type="submit">Lookup</button>
            </form>
            
            <h2>Add DNS Record</h2>
            <form id="addRecordForm">
                <div class="form-group">
                    <label for="record_name">Name:</label>
                    <input type="text" id="record_name" name="name" placeholder="example.com" required>
                </div>
                <div class="form-group">
                    <label for="record_type">Type:</label>
                    <select id="record_type" name="type">
                        <option value="A">A</option>
                        <option value="AAAA">AAAA</option>
                        <option value="CNAME">CNAME</option>
                        <option value="MX">MX</option>
                        <option value="NS">NS</option>
                        <option value="PTR">PTR</option>
                        <option value="TXT">TXT</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="record_value">Value:</label>
                    <input type="text" id="record_value" name="value" placeholder="192.168.1.1" required>
                </div>
                <div class="form-group">
                    <label for="record_ttl">TTL (seconds):</label>
                    <input type="number" id="record_ttl" name="ttl" value="3600" min="60" max="86400">
                </div>
                <button type="submit">Add Record</button>
            </form>
            
            <h2>DNS Statistics</h2>
            <button onclick="loadStats()">Refresh Stats</button>
            <div id="stats" class="stats"></div>
            
            <div id="results"></div>
        </div>
        
        <script>
            document.getElementById('lookupForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const domain = document.getElementById('domain').value;
                const recordType = document.getElementById('record_type').value;
                
                try {
                    const response = await fetch(`/api/resolve/${domain}/${recordType}`);
                    const results = await response.json();
                    
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '<h3>Lookup Results</h3>';
                    
                    if (results.length === 0) {
                        resultsDiv.innerHTML += '<p>No records found.</p>';
                        return;
                    }
                    
                    results.forEach(record => {
                        resultsDiv.innerHTML += `
                            <div class="record">
                                <strong>${record.name}</strong> ${record.record_type} ${record.value}
                                <br><small>TTL: ${record.ttl}s | Priority: ${record.priority}</small>
                            </div>
                        `;
                    });
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            document.getElementById('addRecordForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                data.ttl = parseInt(data.ttl);
                
                try {
                    const response = await fetch('/api/records', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    alert(result.success ? 'Record added successfully!' : 'Error: ' + result.error);
                    if (result.success) {
                        e.target.reset();
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    
                    const statsDiv = document.getElementById('stats');
                    statsDiv.innerHTML = `
                        <h3>DNS Statistics (Last 24 Hours)</h3>
                        <p><strong>Total Queries:</strong> ${stats.total_queries || 0}</p>
                        <p><strong>Cached Queries:</strong> ${stats.cached_queries || 0}</p>
                        <p><strong>Cache Hit Rate:</strong> ${(stats.cache_hit_rate || 0).toFixed(2)}%</p>
                        <p><strong>Average Response Time:</strong> ${(stats.average_response_time || 0).toFixed(3)}s</p>
                        ${stats.top_domains ? '<h4>Top Domains:</h4><ul>' + stats.top_domains.map(d => `<li>${d.domain} (${d.count} queries)</li>`).join('') + '</ul>' : ''}
                    `;
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }
            
            // Load stats on page load
            loadStats();
        </script>
    </body>
    </html>
    ''')

@app.route('/api/resolve/<domain>/<record_type>')
def resolve_domain(domain, record_type):
    """Resolve domain name."""
    try:
        record_type_enum = RecordType(record_type.upper())
        client_ip = request.remote_addr or "127.0.0.1"
        
        records = dns_service.resolve_domain(domain, record_type_enum, client_ip)
        
        results = []
        for record in records:
            results.append({
                'id': record.id,
                'name': record.name,
                'record_type': record.record_type.value,
                'value': record.value,
                'ttl': record.ttl,
                'priority': record.priority,
                'weight': record.weight,
                'port': record.port,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat()
            })
        
        return jsonify(results)
    except ValueError:
        return jsonify({'error': 'Invalid record type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/records', methods=['POST'])
def add_dns_record():
    """Add DNS record."""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('type') or not data.get('value'):
        return jsonify({'success': False, 'error': 'Name, type, and value are required'})
    
    try:
        record_type = RecordType(data['type'].upper())
        record = dns_service.create_dns_record(
            name=data['name'],
            record_type=record_type,
            value=data['value'],
            ttl=int(data.get('ttl', 3600)),
            priority=int(data.get('priority', 0)),
            weight=int(data.get('weight', 0)),
            port=int(data.get('port', 0))
        )
        
        if record:
            return jsonify({'success': True, 'record_id': record.id})
        else:
            return jsonify({'success': False, 'error': 'Failed to create record'})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid record type'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def get_stats():
    """Get DNS statistics."""
    stats = dns_service.get_query_stats()
    return jsonify(stats)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'dns'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
