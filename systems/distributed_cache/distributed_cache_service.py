#!/usr/bin/env python3
"""
Distributed Cache Service

A high-performance, distributed caching system with features like:
- Multi-node cluster support
- Consistent hashing for data distribution
- Replication and fault tolerance
- Cache eviction policies
- Real-time monitoring and metrics
- Automatic failover and recovery
"""

import json
import sqlite3
import time
import hashlib
import threading
import socket
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NodeStatus(Enum):
    """Node status in the cluster."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    RECOVERING = "recovering"

class ConsistencyLevel(Enum):
    """Consistency levels for cache operations."""
    EVENTUAL = "eventual"
    STRONG = "strong"
    QUORUM = "quorum"

class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    RANDOM = "random"

@dataclass
class CacheNode:
    """Represents a node in the distributed cache cluster."""
    node_id: str
    host: str
    port: int
    status: NodeStatus
    last_heartbeat: datetime
    capacity: int
    used_space: int
    hash_ring_position: int
    replication_factor: int = 3
    
    def is_healthy(self) -> bool:
        """Check if the node is healthy."""
        return (self.status == NodeStatus.ACTIVE and 
                (datetime.now() - self.last_heartbeat).seconds < 30)

@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None
    ttl: Optional[int] = None
    version: int = 1
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False

@dataclass
class ClusterConfig:
    """Configuration for the distributed cache cluster."""
    cluster_id: str
    replication_factor: int = 3
    consistency_level: ConsistencyLevel = ConsistencyLevel.QUORUM
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    max_cache_size: int = 10000
    heartbeat_interval: int = 30
    recovery_timeout: int = 300

class ConsistentHashRing:
    """Consistent hash ring for data distribution."""
    
    def __init__(self, nodes: List[CacheNode] = None):
        self.nodes = nodes or []
        self.hash_ring = []
        self._build_ring()
    
    def _build_ring(self):
        """Build the hash ring from nodes."""
        self.hash_ring = []
        for node in self.nodes:
            if node.is_healthy():
                # Add multiple virtual nodes for better distribution
                for i in range(100):  # 100 virtual nodes per physical node
                    virtual_node_id = f"{node.node_id}_{i}"
                    hash_value = self._hash(virtual_node_id)
                    self.hash_ring.append((hash_value, node))
        
        self.hash_ring.sort(key=lambda x: x[0])
    
    def _hash(self, key: str) -> int:
        """Calculate hash for a key."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def get_nodes_for_key(self, key: str, replication_factor: int = 3) -> List[CacheNode]:
        """Get nodes responsible for a key."""
        if not self.hash_ring:
            return []
        
        key_hash = self._hash(key)
        
        # Find the first node with hash >= key_hash
        start_index = 0
        for i, (hash_value, node) in enumerate(self.hash_ring):
            if hash_value >= key_hash:
                start_index = i
                break
        
        # Get nodes in order (wrapping around if necessary)
        nodes = []
        for i in range(replication_factor):
            index = (start_index + i) % len(self.hash_ring)
            _, node = self.hash_ring[index]
            if node not in nodes:  # Avoid duplicates
                nodes.append(node)
        
        return nodes
    
    def add_node(self, node: CacheNode):
        """Add a node to the hash ring."""
        self.nodes.append(node)
        self._build_ring()
    
    def remove_node(self, node_id: str):
        """Remove a node from the hash ring."""
        self.nodes = [n for n in self.nodes if n.node_id != node_id]
        self._build_ring()
    
    def update_node_status(self, node_id: str, status: NodeStatus):
        """Update node status and rebuild ring."""
        for node in self.nodes:
            if node.node_id == node_id:
                node.status = status
                break
        self._build_ring()

class DistributedCacheDatabase:
    """Database layer for the distributed cache."""
    
    def __init__(self, db_path: str = "distributed_cache.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Cache entries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at TEXT,
                    last_accessed TEXT,
                    expires_at TEXT,
                    ttl INTEGER,
                    version INTEGER,
                    tags TEXT,
                    metadata TEXT
                )
            ''')
            
            # Cluster nodes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cluster_nodes (
                    node_id TEXT PRIMARY KEY,
                    host TEXT,
                    port INTEGER,
                    status TEXT,
                    last_heartbeat TEXT,
                    capacity INTEGER,
                    used_space INTEGER,
                    hash_ring_position INTEGER,
                    replication_factor INTEGER
                )
            ''')
            
            # Cluster config table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cluster_config (
                    config_key TEXT PRIMARY KEY,
                    config_value TEXT
                )
            ''')
            
            # Cache statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_stats (
                    stat_name TEXT PRIMARY KEY,
                    stat_value INTEGER,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
    
    def save_cache_entry(self, entry: CacheEntry) -> bool:
        """Save a cache entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                value_blob = pickle.dumps(entry.value)
                tags_json = json.dumps(entry.tags)
                metadata_json = json.dumps(entry.metadata)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_entries
                    (key, value, created_at, last_accessed, expires_at, ttl, version, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.key,
                    value_blob,
                    entry.created_at.isoformat(),
                    entry.last_accessed.isoformat(),
                    entry.expires_at.isoformat() if entry.expires_at else None,
                    entry.ttl,
                    entry.version,
                    tags_json,
                    metadata_json
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving cache entry: {e}")
            return False
    
    def get_cache_entry(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT key, value, created_at, last_accessed, expires_at, ttl, version, tags, metadata
                    FROM cache_entries WHERE key = ?
                ''', (key,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                value = pickle.loads(row[1])
                tags = json.loads(row[7]) if row[7] else []
                metadata = json.loads(row[8]) if row[8] else {}
                
                return CacheEntry(
                    key=row[0],
                    value=value,
                    created_at=datetime.fromisoformat(row[2]),
                    last_accessed=datetime.fromisoformat(row[3]),
                    expires_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    ttl=row[5],
                    version=row[6],
                    tags=tags,
                    metadata=metadata
                )
        except Exception as e:
            logger.error(f"Error getting cache entry: {e}")
            return None
    
    def delete_cache_entry(self, key: str) -> bool:
        """Delete a cache entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting cache entry: {e}")
            return False
    
    def list_cache_keys(self, pattern: str = "*", limit: int = 1000) -> List[str]:
        """List cache keys matching a pattern."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if pattern == "*":
                    cursor.execute('SELECT key FROM cache_entries LIMIT ?', (limit,))
                else:
                    sql_pattern = pattern.replace('*', '%')
                    cursor.execute('SELECT key FROM cache_entries WHERE key LIKE ? LIMIT ?', (sql_pattern, limit))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error listing cache keys: {e}")
            return []
    
    def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM cache_entries
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                ''', (datetime.now().isoformat(),))
                
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    def save_cluster_node(self, node: CacheNode) -> bool:
        """Save cluster node information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cluster_nodes
                    (node_id, host, port, status, last_heartbeat, capacity, used_space, hash_ring_position, replication_factor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    node.node_id,
                    node.host,
                    node.port,
                    node.status.value,
                    node.last_heartbeat.isoformat(),
                    node.capacity,
                    node.used_space,
                    node.hash_ring_position,
                    node.replication_factor
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving cluster node: {e}")
            return False
    
    def get_cluster_nodes(self) -> List[CacheNode]:
        """Get all cluster nodes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT node_id, host, port, status, last_heartbeat, capacity, used_space, hash_ring_position, replication_factor
                    FROM cluster_nodes
                ''')
                
                nodes = []
                for row in cursor.fetchall():
                    nodes.append(CacheNode(
                        node_id=row[0],
                        host=row[1],
                        port=row[2],
                        status=NodeStatus(row[3]),
                        last_heartbeat=datetime.fromisoformat(row[4]),
                        capacity=row[5],
                        used_space=row[6],
                        hash_ring_position=row[7],
                        replication_factor=row[8]
                    ))
                
                return nodes
        except Exception as e:
            logger.error(f"Error getting cluster nodes: {e}")
            return []

class DistributedCacheService:
    """Main distributed cache service."""
    
    def __init__(self, node_id: str = None, host: str = "localhost", port: int = 8080, 
                 db_path: str = "distributed_cache.db"):
        self.node_id = node_id or str(uuid.uuid4())
        self.host = host
        self.port = port
        self.db = DistributedCacheDatabase(db_path)
        self.hash_ring = ConsistentHashRing()
        self.config = ClusterConfig(cluster_id=str(uuid.uuid4()))
        self.local_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
        self.lock = threading.RLock()
        
        # Register this node
        self._register_node()
        
        # Start background tasks
        self.start_background_tasks()
    
    def generate_id(self, prefix: str = "") -> str:
        """Generate a unique ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def _register_node(self):
        """Register this node in the cluster."""
        node = CacheNode(
            node_id=self.node_id,
            host=self.host,
            port=self.port,
            status=NodeStatus.ACTIVE,
            last_heartbeat=datetime.now(),
            capacity=10000,
            used_space=0,
            hash_ring_position=0,
            replication_factor=self.config.replication_factor
        )
        
        self.db.save_cluster_node(node)
        self.hash_ring.add_node(node)
    
    def start_background_tasks(self):
        """Start background maintenance tasks."""
        def heartbeat_task():
            while True:
                try:
                    self._send_heartbeat()
                    time.sleep(self.config.heartbeat_interval)
                except Exception as e:
                    logger.error(f"Error in heartbeat task: {e}")
        
        def cleanup_task():
            while True:
                try:
                    self._cleanup_expired_entries()
                    time.sleep(60)  # Run every minute
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        def health_check_task():
            while True:
                try:
                    self._check_node_health()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Error in health check task: {e}")
        
        # Start background threads
        threading.Thread(target=heartbeat_task, daemon=True).start()
        threading.Thread(target=cleanup_task, daemon=True).start()
        threading.Thread(target=health_check_task, daemon=True).start()
    
    def _send_heartbeat(self):
        """Send heartbeat to update node status."""
        # Update local node status
        for node in self.hash_ring.nodes:
            if node.node_id == self.node_id:
                node.last_heartbeat = datetime.now()
                node.status = NodeStatus.ACTIVE
                self.db.save_cluster_node(node)
                break
    
    def _cleanup_expired_entries(self):
        """Clean up expired cache entries."""
        with self.lock:
            # Clean up local cache
            expired_keys = []
            for key, entry in self.local_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.local_cache[key]
                self.cache_stats["size"] -= 1
            
            # Clean up database
            self.db.cleanup_expired_entries()
    
    def _check_node_health(self):
        """Check health of all nodes in the cluster."""
        current_time = datetime.now()
        
        for node in self.hash_ring.nodes:
            if node.node_id != self.node_id:
                # Check if node is healthy
                if not node.is_healthy():
                    if node.status == NodeStatus.ACTIVE:
                        logger.warning(f"Node {node.node_id} appears to be down")
                        node.status = NodeStatus.FAILED
                        self.db.save_cluster_node(node)
                        self.hash_ring.update_node_status(node.node_id, NodeStatus.FAILED)
    
    def get(self, key: str, consistency: ConsistencyLevel = None) -> Optional[Any]:
        """Get a value from the cache."""
        consistency = consistency or self.config.consistency_level
        
        with self.lock:
            # Check local cache first
            if key in self.local_cache:
                entry = self.local_cache[key]
                if not entry.is_expired():
                    entry.last_accessed = datetime.now()
                    self.cache_stats["hits"] += 1
                    return entry.value
                else:
                    # Remove expired entry
                    del self.local_cache[key]
                    self.cache_stats["size"] -= 1
            
            # Cache miss
            self.cache_stats["misses"] += 1
            
            # Get from database
            entry = self.db.get_cache_entry(key)
            if entry and not entry.is_expired():
                # Add to local cache
                self._add_to_local_cache(entry)
                return entry.value
            
            return None
    
    def set(self, key: str, value: Any, ttl: int = None, tags: List[str] = None,
            metadata: Dict[str, Any] = None) -> bool:
        """Set a value in the cache."""
        with self.lock:
            # Calculate expiration
            expires_at = None
            if ttl:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                expires_at=expires_at,
                ttl=ttl,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Save to database
            if not self.db.save_cache_entry(entry):
                return False
            
            # Add to local cache
            self._add_to_local_cache(entry)
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        with self.lock:
            # Remove from local cache
            if key in self.local_cache:
                del self.local_cache[key]
                self.cache_stats["size"] -= 1
            
            # Delete from database
            return self.db.delete_cache_entry(key)
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return self.get(key) is not None
    
    def keys(self, pattern: str = "*", limit: int = 100000) -> List[str]:
        """List keys matching a pattern."""
        return self.db.list_cache_keys(pattern, limit)
    
    def size(self) -> int:
        """Get the number of cache entries."""
        return len(self.db.list_cache_keys(limit=100000))  # Use a large limit for size calculation
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self.lock:
            self.local_cache.clear()
            self.cache_stats["size"] = 0
            
            # Clear database
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cache_entries')
                conn.commit()
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            hit_rate = 0
            total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            if total_requests > 0:
                hit_rate = self.cache_stats["hits"] / total_requests
            
            return {
                "node_id": self.node_id,
                "cache_hits": self.cache_stats["hits"],
                "cache_misses": self.cache_stats["misses"],
                "hit_rate": hit_rate,
                "local_cache_size": self.cache_stats["size"],
                "total_cache_size": self.size(),
                "cache_evictions": self.cache_stats["evictions"],
                "cluster_nodes": len(self.hash_ring.nodes),
                "healthy_nodes": len([n for n in self.hash_ring.nodes if n.is_healthy()]),
                "consistency_level": self.config.consistency_level.value,
                "eviction_policy": self.config.eviction_policy.value
            }
    
    def _add_to_local_cache(self, entry: CacheEntry):
        """Add an entry to the local cache."""
        if len(self.local_cache) >= self.config.max_cache_size:
            self._evict_from_local_cache()
        
        self.local_cache[entry.key] = entry
        self.cache_stats["size"] += 1
    
    def _evict_from_local_cache(self):
        """Evict an entry from the local cache."""
        if not self.local_cache:
            return
        
        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Remove least recently used
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k].last_accessed)
            del self.local_cache[oldest_key]
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used (simplified)
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k].version)
            del self.local_cache[oldest_key]
        elif self.config.eviction_policy == EvictionPolicy.RANDOM:
            # Remove random entry
            key_to_remove = random.choice(list(self.local_cache.keys()))
            del self.local_cache[key_to_remove]
        
        self.cache_stats["evictions"] += 1
        self.cache_stats["size"] -= 1
    
    def add_cluster_node(self, node_id: str, host: str, port: int) -> bool:
        """Add a node to the cluster."""
        node = CacheNode(
            node_id=node_id,
            host=host,
            port=port,
            status=NodeStatus.ACTIVE,
            last_heartbeat=datetime.now(),
            capacity=10000,
            used_space=0,
            hash_ring_position=0,
            replication_factor=self.config.replication_factor
        )
        
        if self.db.save_cluster_node(node):
            self.hash_ring.add_node(node)
            return True
        return False
    
    def remove_cluster_node(self, node_id: str) -> bool:
        """Remove a node from the cluster."""
        # Remove from hash ring
        self.hash_ring.remove_node(node_id)
        
        # Remove from database
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cluster_nodes WHERE node_id = ?', (node_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing cluster node: {e}")
            return False
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information."""
        nodes = self.db.get_cluster_nodes()
        healthy_nodes = [n for n in nodes if n.is_healthy()]
        
        return {
            "cluster_id": self.config.cluster_id,
            "total_nodes": len(nodes),
            "healthy_nodes": len(healthy_nodes),
            "replication_factor": self.config.replication_factor,
            "consistency_level": self.config.consistency_level.value,
            "eviction_policy": self.config.eviction_policy.value,
            "nodes": [
                {
                    "node_id": node.node_id,
                    "host": node.host,
                    "port": node.port,
                    "status": node.status.value,
                    "last_heartbeat": node.last_heartbeat.isoformat(),
                    "capacity": node.capacity,
                    "used_space": node.used_space
                }
                for node in nodes
            ]
        }

# Flask API
from flask import Flask, request, jsonify

app = Flask(__name__)
distributed_cache_service = DistributedCacheService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "node_id": distributed_cache_service.node_id})

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get cache statistics."""
    return jsonify(distributed_cache_service.get_stats())

@app.route('/cluster', methods=['GET'])
def get_cluster_info():
    """Get cluster information."""
    return jsonify(distributed_cache_service.get_cluster_info())

@app.route('/keys', methods=['GET'])
def list_keys():
    """List cache keys."""
    pattern = request.args.get('pattern', '*')
    limit = int(request.args.get('limit', 1000))
    
    keys = distributed_cache_service.keys(pattern, limit)
    return jsonify({"keys": keys, "count": len(keys)})

@app.route('/get/<key>', methods=['GET'])
def get_value(key):
    """Get a value by key."""
    consistency = request.args.get('consistency', 'quorum')
    
    try:
        consistency_level = ConsistencyLevel(consistency)
    except ValueError:
        return jsonify({"error": "Invalid consistency level"}), 400
    
    value = distributed_cache_service.get(key, consistency_level)
    
    if value is None:
        return jsonify({"error": "Key not found"}), 404
    
    return jsonify({"key": key, "value": value})

@app.route('/set', methods=['POST'])
def set_value():
    """Set a key-value pair."""
    data = request.get_json()
    
    if not data or 'key' not in data or 'value' not in data:
        return jsonify({"error": "Missing key or value"}), 400
    
    key = data['key']
    value = data['value']
    ttl = data.get('ttl')
    tags = data.get('tags', [])
    metadata = data.get('metadata', {})
    
    success = distributed_cache_service.set(key, value, ttl, tags, metadata)
    
    if success:
        return jsonify({"success": True, "key": key})
    else:
        return jsonify({"error": "Failed to set key"}), 500

@app.route('/delete/<key>', methods=['DELETE'])
def delete_value(key):
    """Delete a key-value pair."""
    success = distributed_cache_service.delete(key)
    
    if success:
        return jsonify({"success": True, "key": key})
    else:
        return jsonify({"error": "Key not found"}), 404

@app.route('/exists/<key>', methods=['GET'])
def check_exists(key):
    """Check if a key exists."""
    exists = distributed_cache_service.exists(key)
    return jsonify({"key": key, "exists": exists})

@app.route('/clear', methods=['POST'])
def clear_all():
    """Clear all cache entries."""
    success = distributed_cache_service.clear()
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to clear cache"}), 500

@app.route('/cluster/nodes', methods=['POST'])
def add_cluster_node():
    """Add a node to the cluster."""
    data = request.get_json()
    
    if not data or 'node_id' not in data or 'host' not in data or 'port' not in data:
        return jsonify({"error": "Missing node_id, host, or port"}), 400
    
    success = distributed_cache_service.add_cluster_node(
        data['node_id'], data['host'], data['port']
    )
    
    if success:
        return jsonify({"success": True, "node_id": data['node_id']})
    else:
        return jsonify({"error": "Failed to add node"}), 500

@app.route('/cluster/nodes/<node_id>', methods=['DELETE'])
def remove_cluster_node(node_id):
    """Remove a node from the cluster."""
    success = distributed_cache_service.remove_cluster_node(node_id)
    
    if success:
        return jsonify({"success": True, "node_id": node_id})
    else:
        return jsonify({"error": "Failed to remove node"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
