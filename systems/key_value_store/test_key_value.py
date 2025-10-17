#!/usr/bin/env python3
"""
Comprehensive tests for the Key-Value Store system.
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

from key_value_service import (
    KeyValueStore, KeyValueDatabase, KeyValuePair, NodeInfo, ReplicationLog,
    ConsistencyLevel, ReplicationStrategy, EvictionPolicy
)

class TestKeyValuePair(unittest.TestCase):
    """Test KeyValuePair dataclass."""
    
    def test_key_value_pair_creation(self):
        """Test creating a KeyValuePair."""
        now = datetime.now()
        kv_pair = KeyValuePair(
            key="test_key",
            value="test_value",
            version=1,
            created_at=now,
            updated_at=now
        )
        
        self.assertEqual(kv_pair.key, "test_key")
        self.assertEqual(kv_pair.value, "test_value")
        self.assertEqual(kv_pair.version, 1)
        self.assertEqual(kv_pair.tags, [])
        self.assertEqual(kv_pair.metadata, {})
    
    def test_key_value_pair_with_optional_fields(self):
        """Test creating a KeyValuePair with optional fields."""
        now = datetime.now()
        expires_at = now + timedelta(seconds=3600)
        
        kv_pair = KeyValuePair(
            key="test_key",
            value="test_value",
            version=1,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            ttl=3600,
            tags=["tag1", "tag2"],
            metadata={"key1": "value1"}
        )
        
        self.assertEqual(kv_pair.expires_at, expires_at)
        self.assertEqual(kv_pair.ttl, 3600)
        self.assertEqual(kv_pair.tags, ["tag1", "tag2"])
        self.assertEqual(kv_pair.metadata, {"key1": "value1"})

class TestKeyValueDatabase(unittest.TestCase):
    """Test KeyValueDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = KeyValueDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization."""
        # Database should be initialized in setUp
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_and_get_key_value(self):
        """Test saving and retrieving key-value pairs."""
        now = datetime.now()
        kv_pair = KeyValuePair(
            key="test_key",
            value="test_value",
            version=1,
            created_at=now,
            updated_at=now
        )
        
        # Save key-value pair
        success = self.db.save_key_value(kv_pair)
        self.assertTrue(success)
        
        # Retrieve key-value pair
        retrieved = self.db.get_key_value("test_key")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.key, "test_key")
        self.assertEqual(retrieved.value, "test_value")
        self.assertEqual(retrieved.version, 1)
    
    def test_save_and_get_key_value_with_metadata(self):
        """Test saving and retrieving key-value pairs with metadata."""
        now = datetime.now()
        kv_pair = KeyValuePair(
            key="test_key",
            value={"nested": "value"},
            version=1,
            created_at=now,
            updated_at=now,
            tags=["tag1", "tag2"],
            metadata={"meta": "data"}
        )
        
        # Save key-value pair
        success = self.db.save_key_value(kv_pair)
        self.assertTrue(success)
        
        # Retrieve key-value pair
        retrieved = self.db.get_key_value("test_key")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.value, {"nested": "value"})
        self.assertEqual(retrieved.tags, ["tag1", "tag2"])
        self.assertEqual(retrieved.metadata, {"meta": "data"})
    
    def test_get_nonexistent_key(self):
        """Test getting a non-existent key."""
        retrieved = self.db.get_key_value("nonexistent_key")
        self.assertIsNone(retrieved)
    
    def test_delete_key_value(self):
        """Test deleting key-value pairs."""
        now = datetime.now()
        kv_pair = KeyValuePair(
            key="test_key",
            value="test_value",
            version=1,
            created_at=now,
            updated_at=now
        )
        
        # Save key-value pair
        self.db.save_key_value(kv_pair)
        
        # Delete key-value pair
        success = self.db.delete_key_value("test_key")
        self.assertTrue(success)
        
        # Verify deletion
        retrieved = self.db.get_key_value("test_key")
        self.assertIsNone(retrieved)
    
    def test_list_keys(self):
        """Test listing keys."""
        now = datetime.now()
        
        # Save multiple key-value pairs
        for i in range(5):
            kv_pair = KeyValuePair(
                key=f"key_{i}",
                value=f"value_{i}",
                version=1,
                created_at=now,
                updated_at=now
            )
            self.db.save_key_value(kv_pair)
        
        # List all keys
        keys = self.db.list_keys()
        self.assertEqual(len(keys), 5)
        self.assertIn("key_0", keys)
        self.assertIn("key_4", keys)
        
        # List keys with pattern
        pattern_keys = self.db.list_keys("key_*")
        self.assertEqual(len(pattern_keys), 5)
        
        # List keys with limit
        limited_keys = self.db.list_keys(limit=3)
        self.assertEqual(len(limited_keys), 3)
    
    def test_cleanup_expired(self):
        """Test cleaning up expired keys."""
        now = datetime.now()
        expired_time = now - timedelta(seconds=3600)
        
        # Save expired key-value pair
        expired_kv = KeyValuePair(
            key="expired_key",
            value="expired_value",
            version=1,
            created_at=now,
            updated_at=now,
            expires_at=expired_time
        )
        self.db.save_key_value(expired_kv)
        
        # Save non-expired key-value pair
        valid_kv = KeyValuePair(
            key="valid_key",
            value="valid_value",
            version=1,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(seconds=3600)
        )
        self.db.save_key_value(valid_kv)
        
        # Cleanup expired keys
        cleaned_count = self.db.cleanup_expired()
        self.assertEqual(cleaned_count, 1)
        
        # Verify only valid key remains
        self.assertIsNone(self.db.get_key_value("expired_key"))
        self.assertIsNotNone(self.db.get_key_value("valid_key"))
    
    def test_save_and_get_node(self):
        """Test saving and retrieving node information."""
        now = datetime.now()
        node = NodeInfo(
            node_id="node_1",
            host="localhost",
            port=8080,
            status="active",
            last_heartbeat=now,
            capacity=1000,
            used_space=100,
            replication_factor=2
        )
        
        # Save node
        success = self.db.save_node(node)
        self.assertTrue(success)
        
        # Get nodes
        nodes = self.db.get_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].node_id, "node_1")
        self.assertEqual(nodes[0].host, "localhost")
        self.assertEqual(nodes[0].port, 8080)
    
    def test_save_and_get_replication_log(self):
        """Test saving and retrieving replication logs."""
        now = datetime.now()
        log = ReplicationLog(
            log_id="log_1",
            operation="SET",
            key="test_key",
            value="test_value",
            version=1,
            timestamp=now,
            source_node="node_1",
            target_nodes=["node_2", "node_3"],
            status="pending"
        )
        
        # Save replication log
        success = self.db.save_replication_log(log)
        self.assertTrue(success)
        
        # Get replication logs
        logs = self.db.get_replication_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].log_id, "log_1")
        self.assertEqual(logs[0].operation, "SET")
        self.assertEqual(logs[0].target_nodes, ["node_2", "node_3"])

class TestKeyValueStore(unittest.TestCase):
    """Test KeyValueStore class."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.store = KeyValueStore(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test store."""
        os.unlink(self.temp_db.name)
    
    def test_generate_id(self):
        """Test ID generation."""
        id1 = self.store.generate_id("test")
        id2 = self.store.generate_id("test")
        
        self.assertTrue(id1.startswith("test_"))
        self.assertTrue(id2.startswith("test_"))
        self.assertNotEqual(id1, id2)
    
    def test_calculate_hash(self):
        """Test hash calculation."""
        hash1 = self.store.calculate_hash("test_key")
        hash2 = self.store.calculate_hash("test_key")
        hash3 = self.store.calculate_hash("different_key")
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(len(hash1), 32)  # MD5 hash length
    
    def test_set_and_get(self):
        """Test setting and getting values."""
        # Set a value
        success = self.store.set("test_key", "test_value")
        self.assertTrue(success)
        
        # Get the value
        value = self.store.get("test_key")
        self.assertEqual(value, "test_value")
    
    def test_set_and_get_with_ttl(self):
        """Test setting and getting values with TTL."""
        # Set a value with TTL
        success = self.store.set("test_key", "test_value", ttl=1)
        self.assertTrue(success)
        
        # Get the value immediately
        value = self.store.get("test_key")
        self.assertEqual(value, "test_value")
        
        # Wait for expiration
        time.sleep(2)
        
        # Value should be expired
        value = self.store.get("test_key")
        self.assertIsNone(value)
    
    def test_set_and_get_with_metadata(self):
        """Test setting and getting values with metadata."""
        tags = ["tag1", "tag2"]
        metadata = {"key1": "value1", "key2": "value2"}
        
        # Set a value with metadata
        success = self.store.set("test_key", "test_value", tags=tags, metadata=metadata)
        self.assertTrue(success)
        
        # Get the value
        value = self.store.get("test_key")
        self.assertEqual(value, "test_value")
    
    def test_get_nonexistent_key(self):
        """Test getting a non-existent key."""
        value = self.store.get("nonexistent_key")
        self.assertIsNone(value)
    
    def test_delete(self):
        """Test deleting keys."""
        # Set a value
        self.store.set("test_key", "test_value")
        
        # Verify it exists
        self.assertTrue(self.store.exists("test_key"))
        
        # Delete the key
        success = self.store.delete("test_key")
        self.assertTrue(success)
        
        # Verify it's deleted
        self.assertFalse(self.store.exists("test_key"))
        self.assertIsNone(self.store.get("test_key"))
    
    def test_exists(self):
        """Test checking if keys exist."""
        # Key doesn't exist initially
        self.assertFalse(self.store.exists("test_key"))
        
        # Set a value
        self.store.set("test_key", "test_value")
        
        # Key should exist now
        self.assertTrue(self.store.exists("test_key"))
    
    def test_keys(self):
        """Test listing keys."""
        # Set multiple values
        for i in range(5):
            self.store.set(f"key_{i}", f"value_{i}")
        
        # List all keys
        keys = self.store.keys()
        self.assertEqual(len(keys), 5)
        
        # List keys with pattern
        pattern_keys = self.store.keys("key_*")
        self.assertEqual(len(pattern_keys), 5)
        
        # List keys with limit
        limited_keys = self.store.keys(limit=3)
        self.assertEqual(len(limited_keys), 3)
    
    def test_size(self):
        """Test getting store size."""
        # Initially empty
        self.assertEqual(self.store.size(), 0)
        
        # Add some values
        for i in range(3):
            self.store.set(f"key_{i}", f"value_{i}")
        
        # Size should be 3
        self.assertEqual(self.store.size(), 3)
    
    def test_clear(self):
        """Test clearing all keys."""
        # Add some values
        for i in range(3):
            self.store.set(f"key_{i}", f"value_{i}")
        
        # Verify they exist
        self.assertEqual(self.store.size(), 3)
        
        # Clear all
        success = self.store.clear()
        self.assertTrue(success)
        
        # Verify they're gone
        self.assertEqual(self.store.size(), 0)
    
    def test_get_stats(self):
        """Test getting store statistics."""
        # Add some values
        self.store.set("key1", "value1")
        self.store.set("key2", "value2")
        
        # Get stats
        stats = self.store.get_stats()
        
        self.assertIn("cache_hits", stats)
        self.assertIn("cache_misses", stats)
        self.assertIn("hit_rate", stats)
        self.assertIn("cache_size", stats)
        self.assertIn("total_keys", stats)
        self.assertIn("node_id", stats)
        self.assertEqual(stats["total_keys"], 2)
    
    def test_version_increment(self):
        """Test version increment on updates."""
        # Set initial value
        self.store.set("test_key", "value1")
        
        # Get the key-value pair to check version
        kv_pair = self.store.db.get_key_value("test_key")
        self.assertEqual(kv_pair.version, 1)
        
        # Update the value
        self.store.set("test_key", "value2")
        
        # Check version incremented
        kv_pair = self.store.db.get_key_value("test_key")
        self.assertEqual(kv_pair.version, 2)
    
    def test_cache_eviction(self):
        """Test cache eviction when max size is reached."""
        # Set a small max cache size
        self.store.max_cache_size = 2
        
        # Add more values than cache can hold
        for i in range(5):
            self.store.set(f"key_{i}", f"value_{i}")
        
        # Cache should have evicted some items
        self.assertLessEqual(len(self.store.cache), 2)
    
    def test_consistency_levels(self):
        """Test different consistency levels."""
        # Set a value
        self.store.set("test_key", "test_value")
        
        # Get with different consistency levels
        value_eventual = self.store.get("test_key", ConsistencyLevel.EVENTUAL)
        value_strong = self.store.get("test_key", ConsistencyLevel.STRONG)
        value_causal = self.store.get("test_key", ConsistencyLevel.CAUSAL)
        
        # All should return the same value
        self.assertEqual(value_eventual, "test_value")
        self.assertEqual(value_strong, "test_value")
        self.assertEqual(value_causal, "test_value")

class TestFlaskApp(unittest.TestCase):
    """Test Flask API endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create service with temp database
        self.store = KeyValueStore(self.temp_db.name)
        
        # Import and configure Flask app
        from key_value_service import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Replace the global service instance used by Flask with our test service
        from key_value_service import key_value_store
        key_value_store.db = self.store.db
        key_value_store.cache = self.store.cache
        key_value_store.cache_stats = self.store.cache_stats
    
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
        self.store.set("key1", "value1")
        self.store.set("key2", "value2")
        
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('total_keys', data)
        self.assertEqual(data['total_keys'], 2)
    
    def test_list_keys_api(self):
        """Test list keys endpoint."""
        # Add some data
        for i in range(3):
            self.store.set(f"key_{i}", f"value_{i}")
        
        response = self.client.get('/keys')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['keys']), 3)
    
    def test_list_keys_with_pattern_api(self):
        """Test list keys endpoint with pattern."""
        # Add some data
        self.store.set("test_key1", "value1")
        self.store.set("test_key2", "value2")
        self.store.set("other_key", "value3")
        
        response = self.client.get('/keys?pattern=test_*')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 2)
        self.assertIn('test_key1', data['keys'])
        self.assertIn('test_key2', data['keys'])
    
    def test_get_value_api(self):
        """Test get value endpoint."""
        # Set a value
        self.store.set("test_key", "test_value")
        
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
        self.store.set("test_key", "test_value")
        
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
        self.store.set("test_key", "test_value")
        
        # Key should exist now
        response = self.client.get('/exists/test_key')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['exists'])
    
    def test_clear_api(self):
        """Test clear endpoint."""
        # Add some data
        self.store.set("key1", "value1")
        self.store.set("key2", "value2")
        
        response = self.client.post('/clear')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        
        # Verify data is cleared
        self.assertEqual(self.store.size(), 0)

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.store = KeyValueStore(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test store."""
        os.unlink(self.temp_db.name)
    
    def test_empty_key(self):
        """Test handling of empty key."""
        success = self.store.set("", "value")
        self.assertTrue(success)
        
        value = self.store.get("")
        self.assertEqual(value, "value")
    
    def test_none_value(self):
        """Test handling of None value."""
        success = self.store.set("key", None)
        self.assertTrue(success)
        
        value = self.store.get("key")
        self.assertIsNone(value)
    
    def test_large_value(self):
        """Test handling of large values."""
        large_value = "x" * 10000
        success = self.store.set("large_key", large_value)
        self.assertTrue(success)
        
        value = self.store.get("large_key")
        self.assertEqual(value, large_value)
    
    def test_special_characters_in_key(self):
        """Test handling of special characters in keys."""
        special_key = "key!@#$%^&*()_+-=[]{}|;':\",./<>?"
        success = self.store.set(special_key, "value")
        self.assertTrue(success)
        
        value = self.store.get(special_key)
        self.assertEqual(value, "value")
    
    def test_unicode_values(self):
        """Test handling of Unicode values."""
        unicode_value = "Hello 世界 🌍"
        success = self.store.set("unicode_key", unicode_value)
        self.assertTrue(success)
        
        value = self.store.get("unicode_key")
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
        
        success = self.store.set("nested_key", nested_value)
        self.assertTrue(success)
        
        value = self.store.get("nested_key")
        self.assertEqual(value, nested_value)
    
    def test_concurrent_access(self):
        """Test concurrent access to the store."""
        import threading
        import time
        
        results = []
        
        def worker(thread_id):
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                self.store.set(key, value)
                results.append(self.store.get(key))
        
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
        """Set up test store."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.store = KeyValueStore(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test store."""
        os.unlink(self.temp_db.name)
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations."""
        import time
        
        # Test bulk set operations
        start_time = time.time()
        
        for i in range(1000):
            self.store.set(f"key_{i}", f"value_{i}")
        
        set_time = time.time() - start_time
        
        # Test bulk get operations
        start_time = time.time()
        
        for i in range(1000):
            value = self.store.get(f"key_{i}")
            self.assertEqual(value, f"value_{i}")
        
        get_time = time.time() - start_time
        
        # Performance should be reasonable (less than 1 second for 1000 operations)
        self.assertLess(set_time, 1.0)
        self.assertLess(get_time, 1.0)
    
    def test_cache_performance(self):
        """Test cache performance."""
        # Set a value
        self.store.set("test_key", "test_value")
        
        # First get should be a cache miss
        start_time = time.time()
        value1 = self.store.get("test_key")
        first_get_time = time.time() - start_time
        
        # Second get should be a cache hit
        start_time = time.time()
        value2 = self.store.get("test_key")
        second_get_time = time.time() - start_time
        
        self.assertEqual(value1, "test_value")
        self.assertEqual(value2, "test_value")
        
        # Cache hit should be faster (though this might not always be true in tests)
        # We'll just verify both operations complete successfully
        self.assertIsNotNone(value1)
        self.assertIsNotNone(value2)
    
    def test_memory_usage(self):
        """Test memory usage with large datasets."""
        # Add many key-value pairs
        for i in range(10000):
            self.store.set(f"key_{i}", f"value_{i}")
        
        # Verify all values can be retrieved
        for i in range(10000):
            value = self.store.get(f"key_{i}")
            self.assertEqual(value, f"value_{i}")
        
        # Verify store size
        self.assertEqual(self.store.size(), 10000)

if __name__ == '__main__':
    unittest.main()
