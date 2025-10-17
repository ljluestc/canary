#!/usr/bin/env python3
"""
CDN (Content Delivery Network) Service

A comprehensive CDN system for content delivery, caching, edge computing,
and global content distribution with support for various content types,
caching strategies, and performance optimization.
"""

import sqlite3
import hashlib
import time
import json
import logging
import random
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import math
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Content type enumeration."""
    STATIC = "static"
    DYNAMIC = "dynamic"
    STREAMING = "streaming"
    API = "api"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"

class CacheStrategy(Enum):
    """Cache strategy enumeration."""
    NO_CACHE = "no_cache"
    CACHE_FIRST = "cache_first"
    NETWORK_FIRST = "network_first"
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"
    CACHE_ONLY = "cache_only"

class EdgeLocation(Enum):
    """Edge location enumeration."""
    US_EAST = "us_east"
    US_WEST = "us_west"
    EU_WEST = "eu_west"
    EU_CENTRAL = "eu_central"
    ASIA_PACIFIC = "asia_pacific"
    ASIA_SOUTH = "asia_south"

class ContentStatus(Enum):
    """Content status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class Content:
    """Content model."""
    content_id: str
    url: str
    content_type: ContentType
    file_size: int
    mime_type: str
    cache_strategy: CacheStrategy = CacheStrategy.CACHE_FIRST
    ttl: int = 3600  # Time to live in seconds
    status: ContentStatus = ContentStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    checksum: str = ""

@dataclass
class EdgeNode:
    """Edge node model."""
    node_id: str
    location: EdgeLocation
    ip_address: str
    is_active: bool = True
    capacity: int = 1000000000  # 1GB in bytes
    used_capacity: int = 0
    latency_ms: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)

@dataclass
class CacheEntry:
    """Cache entry model."""
    cache_id: str
    content_id: str
    node_id: str
    url: str
    content_data: bytes
    content_type: ContentType
    mime_type: str
    file_size: int
    ttl: int
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(seconds=3600))
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    checksum: str = ""

@dataclass
class RequestLog:
    """Request log model."""
    log_id: str
    content_id: str
    node_id: str
    client_ip: str
    user_agent: str
    request_time: datetime = field(default_factory=datetime.now)
    response_time: int = 0  # milliseconds
    status_code: int = 200
    cache_hit: bool = False
    bytes_transferred: int = 0

@dataclass
class PurgeRequest:
    """Purge request model."""
    purge_id: str
    content_id: str
    url_pattern: str
    status: str = "pending"  # pending, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class CDNDatabase:
    """Database operations for CDN service."""
    
    def __init__(self, db_path: str = "cdn.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content (
                content_id TEXT PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                content_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type TEXT NOT NULL,
                cache_strategy TEXT DEFAULT 'cache_first',
                ttl INTEGER DEFAULT 3600,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                checksum TEXT DEFAULT ''
            )
        ''')
        
        # Edge nodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edge_nodes (
                node_id TEXT PRIMARY KEY,
                location TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                capacity INTEGER DEFAULT 1000000000,
                used_capacity INTEGER DEFAULT 0,
                latency_ms INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cache entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                cache_id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                url TEXT NOT NULL,
                content_data BLOB NOT NULL,
                content_type TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                ttl INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                checksum TEXT DEFAULT '',
                FOREIGN KEY (content_id) REFERENCES content (content_id),
                FOREIGN KEY (node_id) REFERENCES edge_nodes (node_id)
            )
        ''')
        
        # Request logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_logs (
                log_id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                client_ip TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time INTEGER DEFAULT 0,
                status_code INTEGER DEFAULT 200,
                cache_hit BOOLEAN DEFAULT 0,
                bytes_transferred INTEGER DEFAULT 0,
                FOREIGN KEY (content_id) REFERENCES content (content_id),
                FOREIGN KEY (node_id) REFERENCES edge_nodes (node_id)
            )
        ''')
        
        # Purge requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purge_requests (
                purge_id TEXT PRIMARY KEY,
                content_id TEXT,
                url_pattern TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content (content_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_content(self, content: Content) -> bool:
        """Save content to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO content 
                (content_id, url, content_type, file_size, mime_type, cache_strategy,
                 ttl, status, created_at, updated_at, last_accessed, access_count, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                content.content_id, content.url, content.content_type.value,
                content.file_size, content.mime_type, content.cache_strategy.value,
                content.ttl, content.status.value, content.created_at, content.updated_at,
                content.last_accessed, content.access_count, content.checksum
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving content: {e}")
            return False
    
    def get_content(self, content_id: str) -> Optional[Content]:
        """Get content by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM content WHERE content_id = ?', (content_id,))
            row = cursor.fetchone()
            
            if row:
                content = Content(
                    content_id=row[0],
                    url=row[1],
                    content_type=ContentType(row[2]),
                    file_size=row[3],
                    mime_type=row[4],
                    cache_strategy=CacheStrategy(row[5]),
                    ttl=row[6],
                    status=ContentStatus(row[7]),
                    created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                    last_accessed=datetime.fromisoformat(row[10]) if row[10] else None,
                    access_count=row[11] or 0,
                    checksum=row[12] or ""
                )
                conn.close()
                return content
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting content: {e}")
            return None
    
    def get_content_by_url(self, url: str) -> Optional[Content]:
        """Get content by URL."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM content WHERE url = ?', (url,))
            row = cursor.fetchone()
            
            if row:
                content = Content(
                    content_id=row[0],
                    url=row[1],
                    content_type=ContentType(row[2]),
                    file_size=row[3],
                    mime_type=row[4],
                    cache_strategy=CacheStrategy(row[5]),
                    ttl=row[6],
                    status=ContentStatus(row[7]),
                    created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                    last_accessed=datetime.fromisoformat(row[10]) if row[10] else None,
                    access_count=row[11] or 0,
                    checksum=row[12] or ""
                )
                conn.close()
                return content
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting content by URL: {e}")
            return None
    
    def save_edge_node(self, node: EdgeNode) -> bool:
        """Save edge node to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO edge_nodes 
                (node_id, location, ip_address, is_active, capacity, used_capacity,
                 latency_ms, created_at, last_heartbeat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                node.node_id, node.location.value, node.ip_address, node.is_active,
                node.capacity, node.used_capacity, node.latency_ms, node.created_at,
                node.last_heartbeat
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving edge node: {e}")
            return False
    
    def get_edge_nodes(self, location: EdgeLocation = None) -> List[EdgeNode]:
        """Get edge nodes, optionally filtered by location."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if location:
                cursor.execute('''
                    SELECT * FROM edge_nodes 
                    WHERE location = ? AND is_active = 1
                    ORDER BY latency_ms ASC
                ''', (location.value,))
            else:
                cursor.execute('''
                    SELECT * FROM edge_nodes 
                    WHERE is_active = 1
                    ORDER BY latency_ms ASC
                ''')
            
            nodes = []
            for row in cursor.fetchall():
                node = EdgeNode(
                    node_id=row[0],
                    location=EdgeLocation(row[1]),
                    ip_address=row[2],
                    is_active=bool(row[3]),
                    capacity=row[4] or 1000000000,
                    used_capacity=row[5] or 0,
                    latency_ms=row[6] or 0,
                    created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                    last_heartbeat=datetime.fromisoformat(row[8]) if row[8] else datetime.now()
                )
                nodes.append(node)
            
            conn.close()
            return nodes
        except Exception as e:
            logger.error(f"Error getting edge nodes: {e}")
            return []
    
    def save_cache_entry(self, cache_entry: CacheEntry) -> bool:
        """Save cache entry to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (cache_id, content_id, node_id, url, content_data, content_type,
                 mime_type, file_size, ttl, created_at, expires_at, last_accessed,
                 access_count, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cache_entry.cache_id, cache_entry.content_id, cache_entry.node_id,
                cache_entry.url, cache_entry.content_data, cache_entry.content_type.value,
                cache_entry.mime_type, cache_entry.file_size, cache_entry.ttl,
                cache_entry.created_at, cache_entry.expires_at, cache_entry.last_accessed,
                cache_entry.access_count, cache_entry.checksum
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving cache entry: {e}")
            return False
    
    def get_cache_entry(self, content_id: str, node_id: str) -> Optional[CacheEntry]:
        """Get cache entry by content ID and node ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM cache_entries 
                WHERE content_id = ? AND node_id = ?
            ''', (content_id, node_id))
            
            row = cursor.fetchone()
            if row:
                cache_entry = CacheEntry(
                    cache_id=row[0],
                    content_id=row[1],
                    node_id=row[2],
                    url=row[3],
                    content_data=row[4],
                    content_type=ContentType(row[5]),
                    mime_type=row[6],
                    file_size=row[7],
                    ttl=row[8],
                    created_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                    expires_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
                    last_accessed=datetime.fromisoformat(row[11]) if row[11] else datetime.now(),
                    access_count=row[12] or 0,
                    checksum=row[13] or ""
                )
                conn.close()
                return cache_entry
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting cache entry: {e}")
            return None
    
    def get_cache_entries_by_node(self, node_id: str) -> List[CacheEntry]:
        """Get all cache entries for a node."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM cache_entries 
                WHERE node_id = ?
                ORDER BY last_accessed DESC
            ''', (node_id,))
            
            entries = []
            for row in cursor.fetchall():
                cache_entry = CacheEntry(
                    cache_id=row[0],
                    content_id=row[1],
                    node_id=row[2],
                    url=row[3],
                    content_data=row[4],
                    content_type=ContentType(row[5]),
                    mime_type=row[6],
                    file_size=row[7],
                    ttl=row[8],
                    created_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                    expires_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
                    last_accessed=datetime.fromisoformat(row[11]) if row[11] else datetime.now(),
                    access_count=row[12] or 0,
                    checksum=row[13] or ""
                )
                entries.append(cache_entry)
            
            conn.close()
            return entries
        except Exception as e:
            logger.error(f"Error getting cache entries by node: {e}")
            return []
    
    def save_request_log(self, log: RequestLog) -> bool:
        """Save request log to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO request_logs 
                (log_id, content_id, node_id, client_ip, user_agent, request_time,
                 response_time, status_code, cache_hit, bytes_transferred)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log.log_id, log.content_id, log.node_id, log.client_ip, log.user_agent,
                log.request_time, log.response_time, log.status_code, log.cache_hit,
                log.bytes_transferred
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving request log: {e}")
            return False
    
    def get_request_logs(self, content_id: str = None, node_id: str = None, 
                        limit: int = 100) -> List[RequestLog]:
        """Get request logs with optional filtering."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            where_conditions = []
            params = []
            
            if content_id:
                where_conditions.append("content_id = ?")
                params.append(content_id)
            
            if node_id:
                where_conditions.append("node_id = ?")
                params.append(node_id)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            params.append(limit)
            
            cursor.execute(f'''
                SELECT * FROM request_logs 
                WHERE {where_clause}
                ORDER BY request_time DESC
                LIMIT ?
            ''', params)
            
            logs = []
            for row in cursor.fetchall():
                log = RequestLog(
                    log_id=row[0],
                    content_id=row[1],
                    node_id=row[2],
                    client_ip=row[3],
                    user_agent=row[4],
                    request_time=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                    response_time=row[6] or 0,
                    status_code=row[7] or 200,
                    cache_hit=bool(row[8]),
                    bytes_transferred=row[9] or 0
                )
                logs.append(log)
            
            conn.close()
            return logs
        except Exception as e:
            logger.error(f"Error getting request logs: {e}")
            return []

class CDNService:
    """CDN service with content delivery and caching."""
    
    def __init__(self, db_path: str = "cdn.db"):
        self.db = CDNDatabase(db_path)
        self.initialize_default_data()
    
    def initialize_default_data(self):
        """Initialize default edge nodes and content."""
        # Create default edge nodes
        edge_nodes = [
            EdgeNode(
                node_id="node_us_east_001",
                location=EdgeLocation.US_EAST,
                ip_address="192.168.1.10",
                latency_ms=10
            ),
            EdgeNode(
                node_id="node_us_west_001",
                location=EdgeLocation.US_WEST,
                ip_address="192.168.1.11",
                latency_ms=15
            ),
            EdgeNode(
                node_id="node_eu_west_001",
                location=EdgeLocation.EU_WEST,
                ip_address="192.168.1.12",
                latency_ms=20
            ),
            EdgeNode(
                node_id="node_asia_pacific_001",
                location=EdgeLocation.ASIA_PACIFIC,
                ip_address="192.168.1.13",
                latency_ms=25
            )
        ]
        
        for node in edge_nodes:
            self.db.save_edge_node(node)
        
        # Create default content
        default_content = [
            Content(
                content_id="content_001",
                url="https://example.com/logo.png",
                content_type=ContentType.IMAGE,
                file_size=1024,
                mime_type="image/png",
                cache_strategy=CacheStrategy.CACHE_FIRST,
                ttl=86400  # 24 hours
            ),
            Content(
                content_id="content_002",
                url="https://example.com/style.css",
                content_type=ContentType.STATIC,
                file_size=2048,
                mime_type="text/css",
                cache_strategy=CacheStrategy.CACHE_FIRST,
                ttl=3600  # 1 hour
            ),
            Content(
                content_id="content_003",
                url="https://example.com/api/data",
                content_type=ContentType.API,
                file_size=512,
                mime_type="application/json",
                cache_strategy=CacheStrategy.NETWORK_FIRST,
                ttl=300  # 5 minutes
            )
        ]
        
        for content in default_content:
            self.db.save_content(content)
    
    def generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def calculate_checksum(self, data: bytes) -> str:
        """Calculate MD5 checksum for data."""
        return hashlib.md5(data).hexdigest()
    
    def get_content_type_from_url(self, url: str) -> ContentType:
        """Determine content type from URL."""
        if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            return ContentType.IMAGE
        elif url.endswith(('.mp4', '.avi', '.mov', '.webm')):
            return ContentType.VIDEO
        elif url.endswith(('.css', '.js', '.html', '.xml')):
            return ContentType.STATIC
        elif '/api/' in url:
            return ContentType.API
        else:
            return ContentType.STATIC
    
    def get_mime_type(self, url: str) -> str:
        """Get MIME type from URL."""
        mime_type, _ = mimetypes.guess_type(url)
        return mime_type or "application/octet-stream"
    
    def add_content(self, url: str, content_data: bytes, 
                   content_type: ContentType = None, ttl: int = 3600,
                   cache_strategy: CacheStrategy = CacheStrategy.CACHE_FIRST) -> Optional[Content]:
        """Add content to CDN."""
        content_id = self.generate_id("content")
        
        if content_type is None:
            content_type = self.get_content_type_from_url(url)
        
        mime_type = self.get_mime_type(url)
        checksum = self.calculate_checksum(content_data)
        
        content = Content(
            content_id=content_id,
            url=url,
            content_type=content_type,
            file_size=len(content_data),
            mime_type=mime_type,
            cache_strategy=cache_strategy,
            ttl=ttl,
            checksum=checksum
        )
        
        if self.db.save_content(content):
            return content
        return None
    
    def get_content(self, content_id: str) -> Optional[Content]:
        """Get content by ID."""
        return self.db.get_content(content_id)
    
    def get_content_by_url(self, url: str) -> Optional[Content]:
        """Get content by URL."""
        return self.db.get_content_by_url(url)
    
    def find_best_edge_node(self, client_location: EdgeLocation = None) -> Optional[EdgeNode]:
        """Find the best edge node for serving content."""
        nodes = self.db.get_edge_nodes(client_location)
        
        if not nodes:
            # If no nodes in specific location, get all active nodes
            nodes = self.db.get_edge_nodes()
        
        if not nodes:
            return None
        
        # Select node with lowest latency and available capacity
        best_node = None
        best_score = float('inf')
        
        for node in nodes:
            # Simple scoring: latency + capacity usage percentage
            capacity_usage = (node.used_capacity / node.capacity) * 100
            score = node.latency_ms + capacity_usage
            
            if score < best_score:
                best_score = score
                best_node = node
        
        return best_node
    
    def cache_content(self, content: Content, node: EdgeNode, content_data: bytes) -> Optional[CacheEntry]:
        """Cache content on edge node."""
        # Check if node has enough capacity
        if node.used_capacity + content.file_size > node.capacity:
            return None
        
        cache_id = self.generate_id("cache")
        expires_at = datetime.now() + timedelta(seconds=content.ttl)
        
        cache_entry = CacheEntry(
            cache_id=cache_id,
            content_id=content.content_id,
            node_id=node.node_id,
            url=content.url,
            content_data=content_data,
            content_type=content.content_type,
            mime_type=content.mime_type,
            file_size=content.file_size,
            ttl=content.ttl,
            expires_at=expires_at,
            checksum=content.checksum
        )
        
        if self.db.save_cache_entry(cache_entry):
            # Update node capacity
            node.used_capacity += content.file_size
            self.db.save_edge_node(node)
            return cache_entry
        return None
    
    def get_cached_content(self, content_id: str, node_id: str) -> Optional[CacheEntry]:
        """Get cached content from edge node."""
        cache_entry = self.db.get_cache_entry(content_id, node_id)
        
        if cache_entry and cache_entry.expires_at > datetime.now():
            # Update access statistics
            cache_entry.last_accessed = datetime.now()
            cache_entry.access_count += 1
            self.db.save_cache_entry(cache_entry)
            return cache_entry
        
        return None
    
    def serve_content(self, url: str, client_ip: str, user_agent: str,
                     client_location: EdgeLocation = None) -> Dict[str, Any]:
        """Serve content through CDN."""
        start_time = time.time()
        
        # Find content
        content = self.get_content_by_url(url)
        if not content:
            return {
                'success': False,
                'error': 'Content not found',
                'status_code': 404
            }
        
        # Find best edge node
        node = self.find_best_edge_node(client_location)
        if not node:
            return {
                'success': False,
                'error': 'No available edge nodes',
                'status_code': 503
            }
        
        # Try to get from cache first
        cache_entry = self.get_cached_content(content.content_id, node.node_id)
        cache_hit = cache_entry is not None
        
        if not cache_hit:
            # Simulate fetching from origin server
            # In real implementation, this would fetch from origin
            content_data = b"Simulated content data for " + url.encode()
            
            # Cache the content
            cache_entry = self.cache_content(content, node, content_data)
            if not cache_entry:
                return {
                    'success': False,
                    'error': 'Failed to cache content',
                    'status_code': 507
                }
        
        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)
        
        # Log the request
        log_id = self.generate_id("log")
        log = RequestLog(
            log_id=log_id,
            content_id=content.content_id,
            node_id=node.node_id,
            client_ip=client_ip,
            user_agent=user_agent,
            response_time=response_time,
            cache_hit=cache_hit,
            bytes_transferred=content.file_size
        )
        self.db.save_request_log(log)
        
        # Update content access statistics
        content.last_accessed = datetime.now()
        content.access_count += 1
        self.db.save_content(content)
        
        return {
            'success': True,
            'content_id': content.content_id,
            'node_id': node.node_id,
            'url': content.url,
            'content_type': content.content_type.value,
            'mime_type': content.mime_type,
            'file_size': content.file_size,
            'cache_hit': cache_hit,
            'response_time_ms': response_time,
            'node_location': node.location.value,
            'node_ip': node.ip_address,
            'status_code': 200
        }
    
    def purge_content(self, url_pattern: str, content_id: str = None) -> Optional[PurgeRequest]:
        """Purge content from cache."""
        purge_id = self.generate_id("purge")
        
        purge_request = PurgeRequest(
            purge_id=purge_id,
            content_id=content_id,
            url_pattern=url_pattern
        )
        
        # In real implementation, this would trigger cache invalidation
        # across all edge nodes
        purge_request.status = "completed"
        purge_request.completed_at = datetime.now()
        
        return purge_request
    
    def get_analytics(self, content_id: str = None, node_id: str = None,
                     start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get CDN analytics."""
        logs = self.db.get_request_logs(content_id, node_id, limit=1000)
        
        if not logs:
            return {
                'total_requests': 0,
                'cache_hit_rate': 0.0,
                'average_response_time': 0.0,
                'total_bytes_transferred': 0,
                'requests_by_status': {},
                'requests_by_node': {}
            }
        
        total_requests = len(logs)
        cache_hits = sum(1 for log in logs if log.cache_hit)
        cache_hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0
        
        total_response_time = sum(log.response_time for log in logs)
        average_response_time = total_response_time / total_requests if total_requests > 0 else 0
        
        total_bytes = sum(log.bytes_transferred for log in logs)
        
        # Group by status code
        status_counts = {}
        for log in logs:
            status = log.status_code
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Group by node
        node_counts = {}
        for log in logs:
            node = log.node_id
            node_counts[node] = node_counts.get(node, 0) + 1
        
        return {
            'total_requests': total_requests,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'average_response_time': round(average_response_time, 2),
            'total_bytes_transferred': total_bytes,
            'requests_by_status': status_counts,
            'requests_by_node': node_counts
        }
    
    def get_node_status(self) -> List[Dict[str, Any]]:
        """Get status of all edge nodes."""
        nodes = self.db.get_edge_nodes()
        
        status_list = []
        for node in nodes:
            cache_entries = self.db.get_cache_entries_by_node(node.node_id)
            total_cached_size = sum(entry.file_size for entry in cache_entries)
            
            status_list.append({
                'node_id': node.node_id,
                'location': node.location.value,
                'ip_address': node.ip_address,
                'is_active': node.is_active,
                'capacity_gb': round(node.capacity / (1024**3), 2),
                'used_capacity_gb': round(total_cached_size / (1024**3), 2),
                'capacity_usage_percent': round((total_cached_size / node.capacity) * 100, 2),
                'latency_ms': node.latency_ms,
                'cached_entries': len(cache_entries),
                'last_heartbeat': node.last_heartbeat.isoformat()
            })
        
        return status_list

# Global service instance
cdn_service = CDNService()

# Flask app for API
from flask import Flask, request, jsonify, render_template_string, Response

app = Flask(__name__)

@app.route('/')
def index():
    """Index page."""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CDN Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .content { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .content h3 { margin-top: 0; }
            .content-meta { color: #666; font-size: 14px; }
            .tabs { border-bottom: 1px solid #ddd; margin-bottom: 20px; }
            .tab { display: inline-block; padding: 10px 20px; cursor: pointer; border-bottom: 2px solid transparent; }
            .tab.active { border-bottom-color: #007cba; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .analytics { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 10px 0; }
            .metric { display: inline-block; margin-right: 20px; }
            .metric-value { font-size: 24px; font-weight: bold; color: #007cba; }
            .metric-label { font-size: 12px; color: #666; }
            .node-status { background: #f9f9f9; padding: 10px; margin: 5px 0; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CDN Service</h1>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('content')">Content Management</div>
                <div class="tab" onclick="showTab('serve')">Content Serving</div>
                <div class="tab" onclick="showTab('analytics')">Analytics</div>
                <div class="tab" onclick="showTab('nodes')">Edge Nodes</div>
            </div>
            
            <div id="content" class="tab-content active">
                <h2>Content Management</h2>
                <form id="contentForm">
                    <div class="form-group">
                        <label for="url">Content URL:</label>
                        <input type="url" id="url" name="url" required>
                    </div>
                    <div class="form-group">
                        <label for="content_type">Content Type:</label>
                        <select id="content_type" name="content_type">
                            <option value="static">Static</option>
                            <option value="image">Image</option>
                            <option value="video">Video</option>
                            <option value="api">API</option>
                            <option value="streaming">Streaming</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="cache_strategy">Cache Strategy:</label>
                        <select id="cache_strategy" name="cache_strategy">
                            <option value="cache_first">Cache First</option>
                            <option value="network_first">Network First</option>
                            <option value="stale_while_revalidate">Stale While Revalidate</option>
                            <option value="cache_only">Cache Only</option>
                            <option value="no_cache">No Cache</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="ttl">TTL (seconds):</label>
                        <input type="number" id="ttl" name="ttl" value="3600" min="0">
                    </div>
                    <button type="submit">Add Content</button>
                </form>
            </div>
            
            <div id="serve" class="tab-content">
                <h2>Content Serving</h2>
                <form id="serveForm">
                    <div class="form-group">
                        <label for="serve_url">Content URL:</label>
                        <input type="url" id="serve_url" name="serve_url" required>
                    </div>
                    <div class="form-group">
                        <label for="client_location">Client Location:</label>
                        <select id="client_location" name="client_location">
                            <option value="us_east">US East</option>
                            <option value="us_west">US West</option>
                            <option value="eu_west">EU West</option>
                            <option value="eu_central">EU Central</option>
                            <option value="asia_pacific">Asia Pacific</option>
                            <option value="asia_south">Asia South</option>
                        </select>
                    </div>
                    <button type="submit">Serve Content</button>
                </form>
                <div id="serveResults"></div>
            </div>
            
            <div id="analytics" class="tab-content">
                <h2>Analytics Dashboard</h2>
                <div class="form-group">
                    <label for="analytics_content_id">Content ID (optional):</label>
                    <input type="text" id="analytics_content_id" name="analytics_content_id">
                </div>
                <div class="form-group">
                    <label for="analytics_node_id">Node ID (optional):</label>
                    <input type="text" id="analytics_node_id" name="analytics_node_id">
                </div>
                <button onclick="loadAnalytics()">Load Analytics</button>
                <div id="analyticsResults"></div>
            </div>
            
            <div id="nodes" class="tab-content">
                <h2>Edge Node Status</h2>
                <button onclick="loadNodeStatus()">Refresh Node Status</button>
                <div id="nodeStatusResults"></div>
            </div>
        </div>
        
        <script>
            function showTab(tabName) {
                // Hide all tab contents
                const contents = document.querySelectorAll('.tab-content');
                contents.forEach(content => content.classList.remove('active'));
                
                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked tab
                event.target.classList.add('active');
            }
            
            document.getElementById('contentForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/api/content', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    alert(result.success ? 'Content added successfully! ID: ' + result.content_id : 'Error: ' + result.error);
                    if (result.success) {
                        e.target.reset();
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            document.getElementById('serveForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/api/serve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    
                    const resultsDiv = document.getElementById('serveResults');
                    if (result.success) {
                        resultsDiv.innerHTML = `
                            <div class="analytics">
                                <h3>Content Served</h3>
                                <p><strong>Content ID:</strong> ${result.content_id}</p>
                                <p><strong>Node ID:</strong> ${result.node_id}</p>
                                <p><strong>Node Location:</strong> ${result.node_location}</p>
                                <p><strong>Node IP:</strong> ${result.node_ip}</p>
                                <p><strong>Content Type:</strong> ${result.content_type}</p>
                                <p><strong>MIME Type:</strong> ${result.mime_type}</p>
                                <p><strong>File Size:</strong> ${result.file_size} bytes</p>
                                <p><strong>Cache Hit:</strong> ${result.cache_hit ? 'Yes' : 'No'}</p>
                                <p><strong>Response Time:</strong> ${result.response_time_ms} ms</p>
                            </div>
                        `;
                    } else {
                        resultsDiv.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            async function loadAnalytics() {
                const contentId = document.getElementById('analytics_content_id').value;
                const nodeId = document.getElementById('analytics_node_id').value;
                
                try {
                    let url = '/api/analytics';
                    const params = new URLSearchParams();
                    if (contentId) params.append('content_id', contentId);
                    if (nodeId) params.append('node_id', nodeId);
                    if (params.toString()) url += '?' + params.toString();
                    
                    const response = await fetch(url);
                    const analytics = await response.json();
                    
                    const resultsDiv = document.getElementById('analyticsResults');
                    resultsDiv.innerHTML = `
                        <div class="analytics">
                            <h3>CDN Analytics</h3>
                            <div class="metric">
                                <div class="metric-value">${analytics.total_requests.toLocaleString()}</div>
                                <div class="metric-label">Total Requests</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${analytics.cache_hit_rate}%</div>
                                <div class="metric-label">Cache Hit Rate</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${analytics.average_response_time}ms</div>
                                <div class="metric-label">Avg Response Time</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${(analytics.total_bytes_transferred / 1024 / 1024).toFixed(2)}MB</div>
                                <div class="metric-label">Bytes Transferred</div>
                            </div>
                        </div>
                    `;
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
            
            async function loadNodeStatus() {
                try {
                    const response = await fetch('/api/nodes/status');
                    const nodes = await response.json();
                    
                    const resultsDiv = document.getElementById('nodeStatusResults');
                    let html = '<h3>Edge Node Status</h3>';
                    
                    nodes.forEach(node => {
                        html += `
                            <div class="node-status">
                                <h4>${node.node_id}</h4>
                                <p><strong>Location:</strong> ${node.location}</p>
                                <p><strong>IP Address:</strong> ${node.ip_address}</p>
                                <p><strong>Status:</strong> ${node.is_active ? 'Active' : 'Inactive'}</p>
                                <p><strong>Capacity:</strong> ${node.used_capacity_gb}GB / ${node.capacity_gb}GB (${node.capacity_usage_percent}%)</p>
                                <p><strong>Latency:</strong> ${node.latency_ms}ms</p>
                                <p><strong>Cached Entries:</strong> ${node.cached_entries}</p>
                                <p><strong>Last Heartbeat:</strong> ${node.last_heartbeat}</p>
                            </div>
                        `;
                    });
                    
                    resultsDiv.innerHTML = html;
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/api/content', methods=['POST'])
def add_content():
    """Add content to CDN."""
    data = request.get_json()
    
    required_fields = ['url']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        from cdn_service import ContentType, CacheStrategy
        
        content_type = ContentType(data.get('content_type', 'static'))
        cache_strategy = CacheStrategy(data.get('cache_strategy', 'cache_first'))
        ttl = int(data.get('ttl', 3600))
        
        # Simulate content data
        content_data = b"Simulated content data for " + data['url'].encode()
        
        content = cdn_service.add_content(
            url=data['url'],
            content_data=content_data,
            content_type=content_type,
            ttl=ttl,
            cache_strategy=cache_strategy
        )
        
        if content:
            return jsonify({'success': True, 'content_id': content.content_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to add content'})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid content type or cache strategy'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/serve', methods=['POST'])
def serve_content():
    """Serve content through CDN."""
    data = request.get_json()
    
    required_fields = ['serve_url']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        from cdn_service import EdgeLocation
        
        client_location = EdgeLocation(data.get('client_location', 'us_east'))
        client_ip = request.remote_addr or '127.0.0.1'
        user_agent = request.headers.get('User-Agent', 'CDN-Client/1.0')
        
        result = cdn_service.serve_content(
            url=data['serve_url'],
            client_ip=client_ip,
            user_agent=user_agent,
            client_location=client_location
        )
        
        return jsonify(result)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid client location'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics')
def get_analytics():
    """Get CDN analytics."""
    content_id = request.args.get('content_id')
    node_id = request.args.get('node_id')
    
    try:
        analytics = cdn_service.get_analytics(content_id, node_id)
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/nodes/status')
def get_node_status():
    """Get edge node status."""
    try:
        status = cdn_service.get_node_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'cdn_system'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
