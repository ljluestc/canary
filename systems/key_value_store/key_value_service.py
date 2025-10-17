#!/usr/bin/env python3
"""
Mussel Key-Value Store Service

A high-performance, distributed key-value store with caching, replication,
and consistency guarantees. Supports both in-memory and persistent storage.
"""

import json
import sqlite3
import threading
import time
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsistencyLevel(Enum):
    """Consistency levels for read operations."""
    EVENTUAL = "eventual"
    STRONG = "strong"
    CAUSAL = "causal"

class ReplicationStrategy(Enum):
    """Replication strategies."""
    MASTER_SLAVE = "master_slave"
    MASTER_MASTER = "master_master"
    QUORUM = "quorum"

class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    RANDOM = "random"

@dataclass
class KeyValuePair:
    """Represents a key-value pair with metadata."""
    key: str
    value: Any
    version: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    ttl: Optional[int] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class NodeInfo:
    """Information about a cluster node."""
    node_id: str
    host: str
    port: int
    status: str
    last_heartbeat: datetime
    capacity: int
    used_space: int
    replication_factor: int = 1

@dataclass
class ReplicationLog:
    """Log entry for replication operations."""
    log_id: str
    operation: str
    key: str
    value: Any
    version: int
    timestamp: datetime
    source_node: str
    target_nodes: List[str]
    status: str

class KeyValueDatabase:
    """Database layer for the key-value store."""
    
    def __init__(self, db_path: str = "key_value.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Key-value pairs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_value_pairs (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    version INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    expires_at TEXT,
                    ttl INTEGER,
                    tags TEXT,
                    metadata TEXT
                )
            ''')
            
            # Nodes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    host TEXT,
                    port INTEGER,
                    status TEXT,
                    last_heartbeat TEXT,
                    capacity INTEGER,
                    used_space INTEGER,
                    replication_factor INTEGER
                )
            ''')
            
            # Replication log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS replication_log (
                    log_id TEXT PRIMARY KEY,
                    operation TEXT,
                    key TEXT,
                    value BLOB,
                    version INTEGER,
                    timestamp TEXT,
                    source_node TEXT,
                    target_nodes TEXT,
                    status TEXT
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
    
    def save_key_value(self, kv_pair: KeyValuePair) -> bool:
        """Save a key-value pair."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Serialize value and metadata
                value_blob = pickle.dumps(kv_pair.value)
                tags_json = json.dumps(kv_pair.tags)
                metadata_json = json.dumps(kv_pair.metadata)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO key_value_pairs
                    (key, value, version, created_at, updated_at, expires_at, ttl, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    kv_pair.key,
                    value_blob,
                    kv_pair.version,
                    kv_pair.created_at.isoformat(),
                    kv_pair.updated_at.isoformat(),
                    kv_pair.expires_at.isoformat() if kv_pair.expires_at else None,
                    kv_pair.ttl,
                    tags_json,
                    metadata_json
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving key-value pair: {e}")
            return False
    
    def get_key_value(self, key: str) -> Optional[KeyValuePair]:
        """Get a key-value pair by key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT key, value, version, created_at, updated_at, expires_at, ttl, tags, metadata
                    FROM key_value_pairs
                    WHERE key = ?
                ''', (key,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Deserialize value and metadata
                value = pickle.loads(row[1])
                tags = json.loads(row[7]) if row[7] else []
                metadata = json.loads(row[8]) if row[8] else {}
                
                return KeyValuePair(
                    key=row[0],
                    value=value,
                    version=row[2],
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                    expires_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    ttl=row[6],
                    tags=tags,
                    metadata=metadata
                )
        except Exception as e:
            logger.error(f"Error getting key-value pair: {e}")
            return None
    
    def delete_key_value(self, key: str) -> bool:
        """Delete a key-value pair."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM key_value_pairs WHERE key = ?', (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting key-value pair: {e}")
            return False
    
    def list_keys(self, pattern: str = "*", limit: int = 100) -> List[str]:
        """List keys matching a pattern."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if pattern == "*":
                    cursor.execute('SELECT key FROM key_value_pairs LIMIT ?', (limit,))
                else:
                    # Convert * to % for SQL LIKE pattern
                    sql_pattern = pattern.replace('*', '%')
                    cursor.execute('SELECT key FROM key_value_pairs WHERE key LIKE ? LIMIT ?', (sql_pattern, limit))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error listing keys: {e}")
            return []
    
    def cleanup_expired(self) -> int:
        """Clean up expired key-value pairs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM key_value_pairs
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                ''', (datetime.now().isoformat(),))
                
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up expired keys: {e}")
            return 0
    
    def save_node(self, node: NodeInfo) -> bool:
        """Save node information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO nodes
                    (node_id, host, port, status, last_heartbeat, capacity, used_space, replication_factor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    node.node_id,
                    node.host,
                    node.port,
                    node.status,
                    node.last_heartbeat.isoformat(),
                    node.capacity,
                    node.used_space,
                    node.replication_factor
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving node: {e}")
            return False
    
    def get_nodes(self) -> List[NodeInfo]:
        """Get all nodes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT node_id, host, port, status, last_heartbeat, capacity, used_space, replication_factor
                    FROM nodes
                ''')
                
                nodes = []
                for row in cursor.fetchall():
                    nodes.append(NodeInfo(
                        node_id=row[0],
                        host=row[1],
                        port=row[2],
                        status=row[3],
                        last_heartbeat=datetime.fromisoformat(row[4]),
                        capacity=row[5],
                        used_space=row[6],
                        replication_factor=row[7]
                    ))
                
                return nodes
        except Exception as e:
            logger.error(f"Error getting nodes: {e}")
            return []
    
    def save_replication_log(self, log: ReplicationLog) -> bool:
        """Save replication log entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                value_blob = pickle.dumps(log.value)
                target_nodes_json = json.dumps(log.target_nodes)
                
                cursor.execute('''
                    INSERT INTO replication_log
                    (log_id, operation, key, value, version, timestamp, source_node, target_nodes, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log.log_id,
                    log.operation,
                    log.key,
                    value_blob,
                    log.version,
                    log.timestamp.isoformat(),
                    log.source_node,
                    target_nodes_json,
                    log.status
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving replication log: {e}")
            return False
    
    def get_replication_logs(self, limit: int = 100) -> List[ReplicationLog]:
        """Get replication logs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT log_id, operation, key, value, version, timestamp, source_node, target_nodes, status
                    FROM replication_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                logs = []
                for row in cursor.fetchall():
                    value = pickle.loads(row[3])
                    target_nodes = json.loads(row[7])
                    
                    logs.append(ReplicationLog(
                        log_id=row[0],
                        operation=row[1],
                        key=row[2],
                        value=value,
                        version=row[3],
                        timestamp=datetime.fromisoformat(row[5]),
                        source_node=row[6],
                        target_nodes=target_nodes,
                        status=row[8]
                    ))
                
                return logs
        except Exception as e:
            logger.error(f"Error getting replication logs: {e}")
            return []

class KeyValueStore:
    """Main key-value store service."""
    
    def __init__(self, db_path: str = "key_value.db", node_id: str = None):
        self.db = KeyValueDatabase(db_path)
        self.node_id = node_id or str(uuid.uuid4())
        self.cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
        self.lock = threading.RLock()
        self.eviction_policy = EvictionPolicy.LRU
        self.max_cache_size = 1000
        self.consistency_level = ConsistencyLevel.STRONG
        self.replication_strategy = ReplicationStrategy.MASTER_SLAVE
        
        # Start background tasks
        self.start_background_tasks()
    
    def start_background_tasks(self):
        """Start background maintenance tasks."""
        def cleanup_task():
            while True:
                try:
                    self.cleanup_expired_keys()
                    time.sleep(60)  # Run every minute
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        def heartbeat_task():
            while True:
                try:
                    self.send_heartbeat()
                    time.sleep(30)  # Send heartbeat every 30 seconds
                except Exception as e:
                    logger.error(f"Error in heartbeat task: {e}")
        
        # Start background threads
        threading.Thread(target=cleanup_task, daemon=True).start()
        threading.Thread(target=heartbeat_task, daemon=True).start()
    
    def generate_id(self, prefix: str = "") -> str:
        """Generate a unique ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def calculate_hash(self, key: str) -> str:
        """Calculate hash for key distribution."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str, consistency: ConsistencyLevel = None) -> Optional[Any]:
        """Get a value by key."""
        consistency = consistency or self.consistency_level
        
        with self.lock:
            # Check cache first
            if key in self.cache:
                kv_pair = self.cache[key]
                # Check if expired
                if kv_pair.expires_at and kv_pair.expires_at < datetime.now():
                    del self.cache[key]
                    self.cache_stats["size"] -= 1
                    self.db.delete_key_value(key)
                    return None
                self.cache_stats["hits"] += 1
                return kv_pair.value
            
            # Cache miss
            self.cache_stats["misses"] += 1
            
            # Get from database
            kv_pair = self.db.get_key_value(key)
            if not kv_pair:
                return None
            
            # Check if expired
            if kv_pair.expires_at and kv_pair.expires_at < datetime.now():
                self.db.delete_key_value(key)
                return None
            
            # Add to cache
            self._add_to_cache(kv_pair)
            
            return kv_pair.value
    
    def set(self, key: str, value: Any, ttl: int = None, tags: List[str] = None, 
            metadata: Dict[str, Any] = None) -> bool:
        """Set a key-value pair."""
        with self.lock:
            # Get existing version
            existing = self.db.get_key_value(key)
            version = (existing.version + 1) if existing else 1
            
            # Calculate expiration
            expires_at = None
            if ttl:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            # Create key-value pair
            kv_pair = KeyValuePair(
                key=key,
                value=value,
                version=version,
                created_at=existing.created_at if existing else datetime.now(),
                updated_at=datetime.now(),
                expires_at=expires_at,
                ttl=ttl,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Save to database
            if not self.db.save_key_value(kv_pair):
                return False
            
            # Add to cache
            self._add_to_cache(kv_pair)
            
            # Replicate if needed
            self._replicate_operation("SET", key, value, version)
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete a key-value pair."""
        with self.lock:
            # Remove from cache
            if key in self.cache:
                del self.cache[key]
                self.cache_stats["size"] -= 1
            
            # Delete from database
            if not self.db.delete_key_value(key):
                return False
            
            # Replicate deletion
            self._replicate_operation("DELETE", key, None, 0)
            
            return True
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return self.get(key) is not None
    
    def keys(self, pattern: str = "*", limit: int = 10000) -> List[str]:
        """List keys matching a pattern."""
        return self.db.list_keys(pattern, limit)
    
    def size(self) -> int:
        """Get the number of key-value pairs."""
        return len(self.db.list_keys(limit=100000))  # Use a large limit for size calculation
    
    def clear(self) -> bool:
        """Clear all key-value pairs."""
        with self.lock:
            self.cache.clear()
            self.cache_stats["size"] = 0
            
            # Clear database
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM key_value_pairs')
                conn.commit()
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache and store statistics."""
        with self.lock:
            hit_rate = 0
            total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            if total_requests > 0:
                hit_rate = self.cache_stats["hits"] / total_requests
            
            return {
                "cache_hits": self.cache_stats["hits"],
                "cache_misses": self.cache_stats["misses"],
                "hit_rate": hit_rate,
                "cache_size": self.cache_stats["size"],
                "cache_evictions": self.cache_stats["evictions"],
                "total_keys": self.size(),
                "node_id": self.node_id,
                "consistency_level": self.consistency_level.value,
                "replication_strategy": self.replication_strategy.value
            }
    
    def _add_to_cache(self, kv_pair: KeyValuePair):
        """Add a key-value pair to cache."""
        if len(self.cache) >= self.max_cache_size:
            self._evict_from_cache()
        
        self.cache[kv_pair.key] = kv_pair
        self.cache_stats["size"] += 1
    
    def _evict_from_cache(self):
        """Evict an item from cache based on policy."""
        if not self.cache:
            return
        
        if self.eviction_policy == EvictionPolicy.LRU:
            # Remove least recently used
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].updated_at)
            del self.cache[oldest_key]
        elif self.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used (simplified)
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].version)
            del self.cache[oldest_key]
        elif self.eviction_policy == EvictionPolicy.RANDOM:
            # Remove random item
            import random
            key_to_remove = random.choice(list(self.cache.keys()))
            del self.cache[key_to_remove]
        
        self.cache_stats["evictions"] += 1
        self.cache_stats["size"] -= 1
    
    def _replicate_operation(self, operation: str, key: str, value: Any, version: int):
        """Replicate operation to other nodes."""
        # This is a simplified replication - in a real system, this would
        # send the operation to other nodes in the cluster
        log = ReplicationLog(
            log_id=self.generate_id("log"),
            operation=operation,
            key=key,
            value=value,
            version=version,
            timestamp=datetime.now(),
            source_node=self.node_id,
            target_nodes=[],
            status="pending"
        )
        
        self.db.save_replication_log(log)
    
    def cleanup_expired_keys(self) -> int:
        """Clean up expired keys from database."""
        return self.db.cleanup_expired()
    
    def send_heartbeat(self):
        """Send heartbeat to cluster."""
        # This is a simplified heartbeat - in a real system, this would
        # send heartbeat to other nodes
        node = NodeInfo(
            node_id=self.node_id,
            host="localhost",
            port=8080,
            status="active",
            last_heartbeat=datetime.now(),
            capacity=10000,
            used_space=self.size(),
            replication_factor=1
        )
        
        self.db.save_node(node)

# Flask API
from flask import Flask, request, jsonify

app = Flask(__name__)
key_value_store = KeyValueStore()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "node_id": key_value_store.node_id})

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get store statistics."""
    return jsonify(key_value_store.get_stats())

@app.route('/keys', methods=['GET'])
def list_keys():
    """List keys."""
    pattern = request.args.get('pattern', '*')
    limit = int(request.args.get('limit', 100))
    
    keys = key_value_store.keys(pattern, limit)
    return jsonify({"keys": keys, "count": len(keys)})

@app.route('/get/<key>', methods=['GET'])
def get_value(key):
    """Get a value by key."""
    consistency = request.args.get('consistency', 'strong')
    
    try:
        consistency_level = ConsistencyLevel(consistency)
    except ValueError:
        return jsonify({"error": "Invalid consistency level"}), 400
    
    value = key_value_store.get(key, consistency_level)
    
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
    
    success = key_value_store.set(key, value, ttl, tags, metadata)
    
    if success:
        return jsonify({"success": True, "key": key})
    else:
        return jsonify({"error": "Failed to set key"}), 500

@app.route('/delete/<key>', methods=['DELETE'])
def delete_value(key):
    """Delete a key-value pair."""
    success = key_value_store.delete(key)
    
    if success:
        return jsonify({"success": True, "key": key})
    else:
        return jsonify({"error": "Key not found"}), 404

@app.route('/exists/<key>', methods=['GET'])
def check_exists(key):
    """Check if a key exists."""
    exists = key_value_store.exists(key)
    return jsonify({"key": key, "exists": exists})

@app.route('/clear', methods=['POST'])
def clear_all():
    """Clear all key-value pairs."""
    success = key_value_store.clear()
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to clear store"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
