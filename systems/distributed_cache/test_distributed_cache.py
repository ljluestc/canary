#!/usr/bin/env python3
"""
Comprehensive tests for the Distributed Cache system.
"""

import unittest
import tempfile
import os
import time
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from distributed_cache_service import (
    DistributedCacheService, DistributedCacheDatabase, CacheNode, CacheEntry,
    ConsistentHashRing, ClusterConfig, NodeStatus, ConsistencyLevel, EvictionPolicy
)

class TestCacheNode(unittest.TestCase):
    """Test CacheNode class."""
    
    def test_cache_node_creation(self):
        """Test creating a CacheNode."""
        node = CacheNode(
            node_id="node_1",
            host="localhost",
            port=8080,
            status=NodeStatus.ACTIVE,
            last_heartbeat=datetime.now(),
            capacity=1000,
            used_space=100,
            hash_ring_position=0
        )
        
        self.assertEqual(node.node_id, "node_1")
        self.assertEqual(node.host, "localhost")
        self.assertEqual(node.port, 8080)
        self.assertEqual(node.status, NodeStatus.ACTIVE)
        self.assertEqual(node.capacity, 1000)
        self.assertEqual(node.used_space, 100)
    
    def test_cache_node_is_healthy(self):
        """Test node health check."""
        # Healthy node
        healthy_node = CacheNode(
            node_id="node_1",
            host="localhost",
            port=8080,
            status=NodeStatus.ACTIVE,
            last_heartbeat=datetime.now(),
            capacity=1000,
            used_space=100,
            hash_ring_position=0
        )
        self.assertTrue(healthy_node.is_healthy())
        
        # Unhealthy node (old heartbeat)
        unhealthy_node = CacheNode(
            node_id="node_2",
            host="localhost",
            port=8081,
            status=NodeStatus.ACTIVE,
            last_heartbeat=datetime.now() - timedelta(seconds=60),
            capacity=1000,
            used_space=100,
            hash_ring_position=0
        )
        self.assertFalse(unhealthy_node.is_healthy())
        
        # Failed node
        failed_node = CacheNode(
            node_id="node_3",
            host="localhost",
            port=8082,
            status=NodeStatus.FAILED,
            last_heartbeat=datetime.now(),
            capacity=1000,
            used_space=100,
            hash_ring_position=0
        )
        self.assertFalse(failed_node.is_healthy())

class TestCacheEntry(unittest.TestCase):
    """Test CacheEntry class."""
    
    def test_cache_entry_creation(self):
        """Test creating a CacheEntry."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        self.assertEqual(entry.key, "test_key")
        self.assertEqual(entry.value, "test_value")
        self.assertEqual(entry.tags, [])
        self.assertEqual(entry.metadata, {})
    
    def test_cache_entry_with_optional_fields(self):
        """Test creating a CacheEntry with optional fields."""
        now = datetime.now()
        expires_at = now + timedelta(seconds=3600)
        
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            last_accessed=now,
            expires_at=expires_at,
            ttl=3600,
            version=2,
            tags=["tag1", "tag2"],
            metadata={"key1": "value1"}
        )
        
        self.assertEqual(entry.expires_at, expires_at)
        self.assertEqual(entry.ttl, 3600)
        self.assertEqual(entry.version, 2)
        self.assertEqual(entry.tags, ["tag1", "tag2"])
        self.assertEqual(entry.metadata, {"key1": "value1"})
    
    def test_cache_entry_is_expired(self):
        """Test cache entry expiration check."""
        # Not expired
        now = datetime.now()
        future_time = now + timedelta(seconds=3600)
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            last_accessed=now,
            expires_at=future_time
        )
        self.assertFalse(entry.is_expired())
        
        # Expired
        past_time = now - timedelta(seconds=3600)
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            last_accessed=now,
            expires_at=past_time
        )
        self.assertTrue(entry.is_expired())
        
        # No expiration
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            last_accessed=now
        )
        self.assertFalse(entry.is_expired())

class TestConsistentHashRing(unittest.TestCase):
    """Test ConsistentHashRing class."""
    
    def test_hash_ring_creation(self):
        """Test creating a hash ring."""
        nodes = [
            CacheNode("node_1", "localhost", 8080, NodeStatus.ACTIVE, datetime.now(), 1000, 0, 0),
            CacheNode("node_2", "localhost", 8081, NodeStatus.ACTIVE, datetime.now(), 1000, 0, 0)
        ]
        
        hash_ring = ConsistentHashRing(nodes)
        self.assertEqual(len(hash_ring.nodes), 2)
        self.assertGreater(len(hash_ring.hash_ring), 0)
    
    def test_get_nodes_for_key(self):
        """Test getting nodes for a key."""
        nodes = [
            CacheNode("node_1", "localhost", 8080, NodeStatus.ACTIVE, datetime.now(), 1000, 0, 0),
            CacheNode("node_2", "localhost", 8081, NodeStatus.ACTIVE, datetime.now(), 1000, 0, 0),
            CacheNode("node_3", "localhost", 8082, NodeStatus.ACTIVE, datetime.now(), 1000, 0, 0)
        ]
        
        hash_ring = ConsistentHashRing(nodes)
        responsible_nodes = hash_ring.get_nodes_for_key("test_key", replication_factor=2)
        
        self.assertEqual(len(responsible_nodes), 2)
        self.assertTrue(all(node.is_healthy() for node in responsible_nodes))
    
    def test_add_and_remove_node(self):
        """Test adding and removing nodes."""
        nodes = [
            CacheNode("node_1", "localhost", 8080, NodeStatus.ACTIVE, datetime.now(), 1000, 0, 0)
        ]
        
        hash_ring = ConsistentHashRing(nodes)
        self.assertEqual(len(hash_ring.nodes), 1)
        
        # Add node
        new_node = CacheNode("node_2", "localhost", 8081, NodeStatus.ACTIVE, datetime.now(), 1000, 0, 0)
        hash_ring.add_node(new_node)
        self.assertEqual(len(hash_ring.nodes), 2)
        
        # Remove node
        hash_ring.remove_node("node_2")
        self.assertEqual(len(hash_ring.nodes), 1)
    
    def test_update_node_status(self):
        """Test updating node status."""
        nodes = [
            CacheNode("node_1", "localhost", 8080, NodeStatus.ACTIVE, datetime.now(), 1000, 0, 0)
        ]
        
        hash_ring = ConsistentHashRing(nodes)
        hash_ring.update_node_status("node_1", NodeStatus.FAILED)
        
        self.assertEqual(hash_ring.nodes[0].status, NodeStatus.FAILED)

class TestDistributedCacheDatabase(unittest.TestCase):
    """Test DistributedCacheDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = DistributedCacheDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization."""
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_and_get_cache_entry(self):
        """Test saving and retrieving cache entries."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        # Save cache entry
        success = self.db.save_cache_entry(entry)
        self.assertTrue(success)
        
        # Retrieve cache entry
        retrieved = self.db.get_cache_entry("test_key")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.key, "test_key")
        self.assertEqual(retrieved.value, "test_value")
    
    def test_save_and_get_cache_entry_with_metadata(self):
        """Test saving and retrieving cache entries with metadata."""
        entry = CacheEntry(
            key="test_key",
            value={"nested": "value"},
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            tags=["tag1", "tag2"],
            metadata={"key1": "value1"}
        )
        
        # Save cache entry
        success = self.db.save_cache_entry(entry)
        self.assertTrue(success)
        
        # Retrieve cache entry
        retrieved = self.db.get_cache_entry("test_key")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.value, {"nested": "value"})
        self.assertEqual(retrieved.tags, ["tag1", "tag2"])
        self.assertEqual(retrieved.metadata, {"key1": "value1"})
    
    def test_get_nonexistent_cache_entry(self):
        """Test getting a non-existent cache entry."""
        retrieved = self.db.get_cache_entry("nonexistent_key")
        self.assertIsNone(retrieved)
    
    def test_delete_cache_entry(self):
        """Test deleting cache entries."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        # Save cache entry
        self.db.save_cache_entry(entry)
        
        # Delete cache entry
        success = self.db.delete_cache_entry("test_key")
        self.assertTrue(success)
        
        # Verify deletion
        retrieved = self.db.get_cache_entry("test_key")
        self.assertIsNone(retrieved)
    
    def test_list_cache_keys(self):
        """Test listing cache keys."""
        # Save multiple cache entries
        for i in range(5):
            entry = CacheEntry(
                key=f"key_{i}",
                value=f"value_{i}",
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )
            self.db.save_cache_entry(entry)
        
        # List all keys
        keys = self.db.list_cache_keys()
        self.assertEqual(len(keys), 5)
        self.assertIn("key_0", keys)
        self.assertIn("key_4", keys)
        
        # List keys with pattern
        pattern_keys = self.db.list_cache_keys("key_*")
        self.assertEqual(len(pattern_keys), 5)
        
        # List keys with limit
        limited_keys = self.db.list_cache_keys(limit=3)
        self.assertEqual(len(limited_keys), 3)
    
    def test_cleanup_expired_entries(self):
        """Test cleaning up expired cache entries."""
        now = datetime.now()
        expired_time = now - timedelta(seconds=3600)
        
        # Save expired cache entry
        expired_entry = CacheEntry(
            key="expired_key",
            value="expired_value",
            created_at=now,
            last_accessed=now,
            expires_at=expired_time
        )
        self.db.save_cache_entry(expired_entry)
        
        # Save non-expired cache entry
        valid_entry = CacheEntry(
            key="valid_key",
            value="valid_value",
            created_at=now,
            last_accessed=now,
            expires_at=now + timedelta(seconds=3600)
        )
        self.db.save_cache_entry(valid_entry)
        
        # Cleanup expired entries
        cleaned_count = self.db.cleanup_expired_entries()
        self.assertEqual(cleaned_count, 1)
        
        # Verify only valid entry remains
        self.assertIsNone(self.db.get_cache_entry("expired_key"))
        self.assertIsNotNone(self.db.get_cache_entry("valid_key"))
    
    def test_save_and_get_cluster_node(self):
        """Test saving and retrieving cluster nodes."""
        node = CacheNode(
            node_id="node_1",
            host="localhost",
            port=8080,
            status=NodeStatus.ACTIVE,
            last_heartbeat=datetime.now(),
            capacity=1000,
            used_space=100,
            hash_ring_position=0,
            replication_factor=3
        )
        
        # Save cluster node
        success = self.db.save_cluster_node(node)
        self.assertTrue(success)
        
        # Get cluster nodes
        nodes = self.db.get_cluster_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].node_id, "node_1")
        self.assertEqual(nodes[0].host, "localhost")
        self.assertEqual(nodes[0].port, 8080)

class TestDistributedCacheService(unittest.TestCase):
    """Test DistributedCacheService class."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = DistributedCacheService(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_generate_id(self):
        """Test ID generation."""
        id1 = self.service.generate_id("test")
        id2 = self.service.generate_id("test")
        
        self.assertTrue(id1.startswith("test_"))
        self.assertTrue(id2.startswith("test_"))
        self.assertNotEqual(id1, id2)
    
    def test_set_and_get(self):
        """Test setting and getting values."""
        # Set a value
        success = self.service.set("test_key", "test_value")
        self.assertTrue(success)
        
        # Get the value
        value = self.service.get("test_key")
        self.assertEqual(value, "test_value")
    
    def test_set_and_get_with_ttl(self):
        """Test setting and getting values with TTL."""
        # Set a value with TTL
        success = self.service.set("test_key", "test_value", ttl=1)
        self.assertTrue(success)
        
        # Get the value immediately
        value = self.service.get("test_key")
        self.assertEqual(value, "test_value")
        
        # Wait for expiration
        time.sleep(2)
        
        # Value should be expired
        value = self.service.get("test_key")
        self.assertIsNone(value)
    
    def test_set_and_get_with_metadata(self):
        """Test setting and getting values with metadata."""
        tags = ["tag1", "tag2"]
        metadata = {"key1": "value1", "key2": "value2"}
        
        # Set a value with metadata
        success = self.service.set("test_key", "test_value", tags=tags, metadata=metadata)
        self.assertTrue(success)
        
        # Get the value
        value = self.service.get("test_key")
        self.assertEqual(value, "test_value")
    
    def test_get_nonexistent_key(self):
        """Test getting a non-existent key."""
        value = self.service.get("nonexistent_key")
        self.assertIsNone(value)
    
    def test_delete(self):
        """Test deleting keys."""
        # Set a value
        self.service.set("test_key", "test_value")
        
        # Verify it exists
        self.assertTrue(self.service.exists("test_key"))
        
        # Delete the key
        success = self.service.delete("test_key")
        self.assertTrue(success)
        
        # Verify it's deleted
        self.assertFalse(self.service.exists("test_key"))
        self.assertIsNone(self.service.get("test_key"))
    
    def test_exists(self):
        """Test checking if keys exist."""
        # Key doesn't exist initially
        self.assertFalse(self.service.exists("test_key"))
        
        # Set a value
        self.service.set("test_key", "test_value")
        
        # Key should exist now
        self.assertTrue(self.service.exists("test_key"))
    
    def test_keys(self):
        """Test listing keys."""
        # Set multiple values
        for i in range(5):
            self.service.set(f"key_{i}", f"value_{i}")
        
        # List all keys
        keys = self.service.keys()
        self.assertEqual(len(keys), 5)
        
        # List keys with pattern
        pattern_keys = self.service.keys("key_*")
        self.assertEqual(len(pattern_keys), 5)
        
        # List keys with limit
        limited_keys = self.service.keys(limit=3)
        self.assertEqual(len(limited_keys), 3)
    
    def test_size(self):
        """Test getting cache size."""
        # Initially empty
        self.assertEqual(self.service.size(), 0)
        
        # Add some values
        for i in range(3):
            self.service.set(f"key_{i}", f"value_{i}")
        
        # Size should be 3
        self.assertEqual(self.service.size(), 3)
    
    def test_clear(self):
        """Test clearing all keys."""
        # Add some values
        for i in range(3):
            self.service.set(f"key_{i}", f"value_{i}")
        
        # Verify they exist
        self.assertEqual(self.service.size(), 3)
        
        # Clear all
        success = self.service.clear()
        self.assertTrue(success)
        
        # Verify they're gone
        self.assertEqual(self.service.size(), 0)
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        # Add some values
        self.service.set("key1", "value1")
        self.service.set("key2", "value2")
        
        # Get stats
        stats = self.service.get_stats()
        
        self.assertIn("node_id", stats)
        self.assertIn("cache_hits", stats)
        self.assertIn("cache_misses", stats)
        self.assertIn("hit_rate", stats)
        self.assertIn("local_cache_size", stats)
        self.assertIn("total_cache_size", stats)
        self.assertIn("cluster_nodes", stats)
        self.assertIn("healthy_nodes", stats)
        self.assertEqual(stats["total_cache_size"], 2)
    
    def test_add_cluster_node(self):
        """Test adding a cluster node."""
        success = self.service.add_cluster_node("node_2", "localhost", 8081)
        self.assertTrue(success)
        
        # Verify node was added
        cluster_info = self.service.get_cluster_info()
        self.assertEqual(cluster_info["total_nodes"], 2)
    
    def test_remove_cluster_node(self):
        """Test removing a cluster node."""
        # Add a node first
        self.service.add_cluster_node("node_2", "localhost", 8081)
        
        # Remove the node
        success = self.service.remove_cluster_node("node_2")
        self.assertTrue(success)
        
        # Verify node was removed
        cluster_info = self.service.get_cluster_info()
        self.assertEqual(cluster_info["total_nodes"], 1)
    
    def test_get_cluster_info(self):
        """Test getting cluster information."""
        cluster_info = self.service.get_cluster_info()
        
        self.assertIn("cluster_id", cluster_info)
        self.assertIn("total_nodes", cluster_info)
        self.assertIn("healthy_nodes", cluster_info)
        self.assertIn("replication_factor", cluster_info)
        self.assertIn("consistency_level", cluster_info)
        self.assertIn("eviction_policy", cluster_info)
        self.assertIn("nodes", cluster_info)
        self.assertEqual(cluster_info["total_nodes"], 1)  # Only this node initially

class TestFlaskApp(unittest.TestCase):
    """Test Flask API endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create service with temp database
        self.service = DistributedCacheService(db_path=self.temp_db.name)
        
        # Import and configure Flask app
        from distributed_cache_service import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Replace the global service instance used by Flask with our test service
        from distributed_cache_service import distributed_cache_service
        distributed_cache_service.db = self.service.db
        distributed_cache_service.hash_ring = self.service.hash_ring
        distributed_cache_service.config = self.service.config
        distributed_cache_service.local_cache = self.service.local_cache
        distributed_cache_service.cache_stats = self.service.cache_stats
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_health_check_api(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('node_id', data)
    
    def test_stats_api(self):
        """Test stats endpoint."""
        # Add some data
        self.service.set("key1", "value1")
        self.service.set("key2", "value2")
        
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('total_cache_size', data)
        self.assertEqual(data['total_cache_size'], 2)
    
    def test_cluster_api(self):
        """Test cluster info endpoint."""
        response = self.client.get('/cluster')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('cluster_id', data)
        self.assertIn('total_nodes', data)
        self.assertIn('healthy_nodes', data)
    
    def test_list_keys_api(self):
        """Test list keys endpoint."""
        # Add some data
        for i in range(3):
            self.service.set(f"key_{i}", f"value_{i}")
        
        response = self.client.get('/keys')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['keys']), 3)
    
    def test_get_value_api(self):
        """Test get value endpoint."""
        # Set a value
        self.service.set("test_key", "test_value")
        
        response = self.client.get('/get/test_key')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['key'], 'test_key')
        self.assertEqual(data['value'], 'test_value')
    
    def test_get_nonexistent_value_api(self):
        """Test get value endpoint for non-existent key."""
        response = self.client.get('/get/nonexistent_key')
        self.assertEqual(response.status_code, 404)
        
        data = response.get_json()
        self.assertEqual(data['error'], 'Key not found')
    
    def test_set_value_api(self):
        """Test set value endpoint."""
        data = {
            'key': 'test_key',
            'value': 'test_value',
            'ttl': 3600,
            'tags': ['tag1', 'tag2'],
            'metadata': {'key1': 'value1'}
        }
        
        response = self.client.post('/set', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertEqual(result['key'], 'test_key')
    
    def test_set_value_missing_data_api(self):
        """Test set value endpoint with missing data."""
        data = {'key': 'test_key'}  # Missing value
        
        response = self.client.post('/set', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing key or value')
    
    def test_delete_value_api(self):
        """Test delete value endpoint."""
        # Set a value first
        self.service.set("test_key", "test_value")
        
        response = self.client.delete('/delete/test_key')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertEqual(result['key'], 'test_key')
    
    def test_delete_nonexistent_value_api(self):
        """Test delete value endpoint for non-existent key."""
        response = self.client.delete('/delete/nonexistent_key')
        self.assertEqual(response.status_code, 404)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Key not found')
    
    def test_exists_api(self):
        """Test exists endpoint."""
        # Key doesn't exist initially
        response = self.client.get('/exists/nonexistent_key')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertFalse(data['exists'])
        
        # Set a value
        self.service.set("test_key", "test_value")
        
        # Key should exist now
        response = self.client.get('/exists/test_key')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['exists'])
    
    def test_clear_api(self):
        """Test clear endpoint."""
        # Add some data
        self.service.set("key1", "value1")
        self.service.set("key2", "value2")
        
        response = self.client.post('/clear')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        
        # Verify data is cleared
        self.assertEqual(self.service.size(), 0)
    
    def test_add_cluster_node_api(self):
        """Test add cluster node endpoint."""
        data = {
            'node_id': 'node_2',
            'host': 'localhost',
            'port': 8081
        }
        
        response = self.client.post('/cluster/nodes', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertEqual(result['node_id'], 'node_2')
    
    def test_add_cluster_node_missing_data_api(self):
        """Test add cluster node endpoint with missing data."""
        data = {'node_id': 'node_2'}  # Missing host and port
        
        response = self.client.post('/cluster/nodes', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing node_id, host, or port')
    
    def test_remove_cluster_node_api(self):
        """Test remove cluster node endpoint."""
        # Add a node first
        self.service.add_cluster_node("node_2", "localhost", 8081)
        
        response = self.client.delete('/cluster/nodes/node_2')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertEqual(result['node_id'], 'node_2')

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = DistributedCacheService(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_empty_key(self):
        """Test handling of empty key."""
        success = self.service.set("", "value")
        self.assertTrue(success)
        
        value = self.service.get("")
        self.assertEqual(value, "value")
    
    def test_none_value(self):
        """Test handling of None value."""
        success = self.service.set("key", None)
        self.assertTrue(success)
        
        value = self.service.get("key")
        self.assertIsNone(value)
    
    def test_large_value(self):
        """Test handling of large values."""
        large_value = "x" * 10000
        success = self.service.set("large_key", large_value)
        self.assertTrue(success)
        
        value = self.service.get("large_key")
        self.assertEqual(value, large_value)
    
    def test_special_characters_in_key(self):
        """Test handling of special characters in keys."""
        special_key = "key!@#$%^&*()_+-=[]{}|;':\",./<>?"
        success = self.service.set(special_key, "value")
        self.assertTrue(success)
        
        value = self.service.get(special_key)
        self.assertEqual(value, "value")
    
    def test_unicode_values(self):
        """Test handling of Unicode values."""
        unicode_value = "Hello 世界 🌍"
        success = self.service.set("unicode_key", unicode_value)
        self.assertTrue(success)
        
        value = self.service.get("unicode_key")
        self.assertEqual(value, unicode_value)
    
    def test_nested_objects(self):
        """Test handling of nested objects."""
        nested_value = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            },
            "list": [1, 2, 3, "string"],
            "boolean": True,
            "null": None
        }
        
        success = self.service.set("nested_key", nested_value)
        self.assertTrue(success)
        
        value = self.service.get("nested_key")
        self.assertEqual(value, nested_value)
    
    def test_concurrent_access(self):
        """Test concurrent access to the cache."""
        import threading
        import time
        
        results = []
        
        def worker(thread_id):
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                self.service.set(key, value)
                results.append(self.service.get(key))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations succeeded
        self.assertEqual(len(results), 50)
        self.assertTrue(all(result is not None for result in results))

class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = DistributedCacheService(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations."""
        import time
        
        # Test bulk set operations
        start_time = time.time()
        
        for i in range(1000):
            self.service.set(f"key_{i}", f"value_{i}")
        
        set_time = time.time() - start_time
        
        # Test bulk get operations
        start_time = time.time()
        
        for i in range(1000):
            value = self.service.get(f"key_{i}")
            self.assertEqual(value, f"value_{i}")
        
        get_time = time.time() - start_time
        
        # Performance should be reasonable (less than 2 seconds for 1000 operations)
        self.assertLess(set_time, 2.0)
        self.assertLess(get_time, 2.0)
    
    def test_cache_performance(self):
        """Test cache performance."""
        # Set a value
        self.service.set("test_key", "test_value")
        
        # First get should be a cache miss
        start_time = time.time()
        value1 = self.service.get("test_key")
        first_get_time = time.time() - start_time
        
        # Second get should be a cache hit
        start_time = time.time()
        value2 = self.service.get("test_key")
        second_get_time = time.time() - start_time
        
        self.assertEqual(value1, "test_value")
        self.assertEqual(value2, "test_value")
        
        # Both operations should complete successfully
        self.assertIsNotNone(value1)
        self.assertIsNotNone(value2)
    
    def test_memory_usage(self):
        """Test memory usage with large datasets."""
        # Add many key-value pairs
        for i in range(10000):
            self.service.set(f"key_{i}", f"value_{i}")
        
        # Verify all values can be retrieved
        for i in range(10000):
            value = self.service.get(f"key_{i}")
            self.assertEqual(value, f"value_{i}")
        
        # Verify cache size
        self.assertEqual(self.service.size(), 10000)

if __name__ == '__main__':
    unittest.main()
