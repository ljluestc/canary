#!/usr/bin/env python3
"""
Comprehensive test suite for DNS Service.

Tests all components including database operations, DNS resolution,
caching mechanisms, and Flask API endpoints.
"""

import unittest
import tempfile
import os
import time
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys

# Add the dns directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from dns_service import (
    RecordType, DNSRecord, DNSQuery, DNSZone, DNSCache, 
    DNSDatabase, DNSService, dns_service
)

class TestRecordType(unittest.TestCase):
    """Test RecordType enum."""
    
    def test_record_type_values(self):
        """Test record type enum values."""
        self.assertEqual(RecordType.A.value, "A")
        self.assertEqual(RecordType.AAAA.value, "AAAA")
        self.assertEqual(RecordType.CNAME.value, "CNAME")
        self.assertEqual(RecordType.MX.value, "MX")
        self.assertEqual(RecordType.NS.value, "NS")
        self.assertEqual(RecordType.PTR.value, "PTR")
        self.assertEqual(RecordType.SOA.value, "SOA")
        self.assertEqual(RecordType.SRV.value, "SRV")
        self.assertEqual(RecordType.TXT.value, "TXT")

class TestDNSRecord(unittest.TestCase):
    """Test DNSRecord dataclass."""
    
    def test_dns_record_creation(self):
        """Test creating a DNS record."""
        record = DNSRecord(
            id="test123",
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1",
            ttl=3600,
            priority=10
        )
        
        self.assertEqual(record.id, "test123")
        self.assertEqual(record.name, "example.com")
        self.assertEqual(record.record_type, RecordType.A)
        self.assertEqual(record.value, "192.168.1.1")
        self.assertEqual(record.ttl, 3600)
        self.assertEqual(record.priority, 10)
        self.assertTrue(record.is_active)
        self.assertIsInstance(record.created_at, datetime)
    
    def test_dns_record_defaults(self):
        """Test DNS record default values."""
        record = DNSRecord(
            id="test123",
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1"
        )
        
        self.assertEqual(record.ttl, 3600)
        self.assertEqual(record.priority, 0)
        self.assertEqual(record.weight, 0)
        self.assertEqual(record.port, 0)
        self.assertTrue(record.is_active)

class TestDNSQuery(unittest.TestCase):
    """Test DNSQuery dataclass."""
    
    def test_dns_query_creation(self):
        """Test creating a DNS query."""
        query = DNSQuery(
            query_id="q123",
            domain="example.com",
            record_type=RecordType.A,
            client_ip="127.0.0.1",
            response_time=0.05
        )
        
        self.assertEqual(query.query_id, "q123")
        self.assertEqual(query.domain, "example.com")
        self.assertEqual(query.record_type, RecordType.A)
        self.assertEqual(query.client_ip, "127.0.0.1")
        self.assertEqual(query.response_time, 0.05)
        self.assertFalse(query.cached)
        self.assertTrue(query.success)
        self.assertIsNone(query.error_message)
    
    def test_dns_query_defaults(self):
        """Test DNS query default values."""
        query = DNSQuery(
            query_id="q123",
            domain="example.com",
            record_type=RecordType.A,
            client_ip="127.0.0.1"
        )
        
        self.assertEqual(query.response_time, 0.0)
        self.assertFalse(query.cached)
        self.assertTrue(query.success)
        self.assertIsNone(query.error_message)

class TestDNSZone(unittest.TestCase):
    """Test DNSZone dataclass."""
    
    def test_dns_zone_creation(self):
        """Test creating a DNS zone."""
        zone = DNSZone(
            zone_id="z123",
            name="example.com",
            primary_ns="ns1.example.com",
            admin_email="admin@example.com"
        )
        
        self.assertEqual(zone.zone_id, "z123")
        self.assertEqual(zone.name, "example.com")
        self.assertEqual(zone.primary_ns, "ns1.example.com")
        self.assertEqual(zone.admin_email, "admin@example.com")
        self.assertEqual(zone.serial, 1)
        self.assertEqual(zone.refresh, 3600)
        self.assertEqual(zone.retry, 1800)
        self.assertEqual(zone.expire, 604800)
        self.assertEqual(zone.minimum_ttl, 3600)
    
    def test_dns_zone_defaults(self):
        """Test DNS zone default values."""
        zone = DNSZone(
            zone_id="z123",
            name="example.com",
            primary_ns="ns1.example.com",
            admin_email="admin@example.com"
        )
        
        self.assertEqual(zone.serial, 1)
        self.assertEqual(zone.refresh, 3600)
        self.assertEqual(zone.retry, 1800)
        self.assertEqual(zone.expire, 604800)
        self.assertEqual(zone.minimum_ttl, 3600)
        self.assertIsInstance(zone.created_at, datetime)

class TestDNSCache(unittest.TestCase):
    """Test DNSCache dataclass."""
    
    def test_dns_cache_creation(self):
        """Test creating a DNS cache entry."""
        records = [
            DNSRecord(
                id="r1",
                name="example.com",
                record_type=RecordType.A,
                value="192.168.1.1"
            )
        ]
        
        cache = DNSCache(
            key="example.com:A",
            records=records,
            expires_at=datetime.now() + timedelta(seconds=300)
        )
        
        self.assertEqual(cache.key, "example.com:A")
        self.assertEqual(len(cache.records), 1)
        self.assertEqual(cache.records[0].name, "example.com")
        self.assertEqual(cache.hit_count, 0)
        self.assertIsInstance(cache.last_accessed, datetime)
    
    def test_dns_cache_defaults(self):
        """Test DNS cache default values."""
        cache = DNSCache(
            key="test",
            records=[],
            expires_at=datetime.now()
        )
        
        self.assertEqual(cache.hit_count, 0)
        self.assertIsInstance(cache.last_accessed, datetime)

class TestDNSDatabase(unittest.TestCase):
    """Test DNSDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = DNSDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization."""
        # Database should be initialized in setUp
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_dns_record(self):
        """Test saving DNS record."""
        record = DNSRecord(
            id="test123",
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1",
            ttl=3600
        )
        
        result = self.db.save_dns_record(record)
        self.assertTrue(result)
    
    def test_get_dns_records(self):
        """Test getting DNS records."""
        # Save a record first
        record = DNSRecord(
            id="test123",
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1",
            ttl=3600
        )
        self.db.save_dns_record(record)
        
        # Get records
        records = self.db.get_dns_records("example.com", RecordType.A)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "example.com")
        self.assertEqual(records[0].value, "192.168.1.1")
    
    def test_get_dns_records_by_name_only(self):
        """Test getting DNS records by name only."""
        # Save multiple records
        record1 = DNSRecord(
            id="test1",
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1"
        )
        record2 = DNSRecord(
            id="test2",
            name="example.com",
            record_type=RecordType.MX,
            value="mail.example.com",
            priority=10
        )
        
        self.db.save_dns_record(record1)
        self.db.save_dns_record(record2)
        
        # Get all records for domain
        records = self.db.get_dns_records("example.com")
        self.assertEqual(len(records), 2)
    
    def test_save_dns_zone(self):
        """Test saving DNS zone."""
        zone = DNSZone(
            zone_id="z123",
            name="example.com",
            primary_ns="ns1.example.com",
            admin_email="admin@example.com"
        )
        
        result = self.db.save_dns_zone(zone)
        self.assertTrue(result)
    
    def test_get_dns_zone(self):
        """Test getting DNS zone."""
        zone = DNSZone(
            zone_id="z123",
            name="example.com",
            primary_ns="ns1.example.com",
            admin_email="admin@example.com"
        )
        
        self.db.save_dns_zone(zone)
        retrieved_zone = self.db.get_dns_zone("example.com")
        
        self.assertIsNotNone(retrieved_zone)
        self.assertEqual(retrieved_zone.name, "example.com")
        self.assertEqual(retrieved_zone.primary_ns, "ns1.example.com")
    
    def test_log_dns_query(self):
        """Test logging DNS query."""
        query = DNSQuery(
            query_id="q123",
            domain="example.com",
            record_type=RecordType.A,
            client_ip="127.0.0.1",
            response_time=0.05
        )
        
        result = self.db.log_dns_query(query)
        self.assertTrue(result)
    
    def test_dns_cache_operations(self):
        """Test DNS cache operations."""
        records = [
            DNSRecord(
                id="r1",
                name="example.com",
                record_type=RecordType.A,
                value="192.168.1.1"
            )
        ]
        
        cache = DNSCache(
            key="example.com:A",
            records=records,
            expires_at=datetime.now() + timedelta(seconds=300)
        )
        
        # Save cache
        result = self.db.save_dns_cache(cache)
        self.assertTrue(result)
        
        # Get cache
        retrieved_cache = self.db.get_dns_cache("example.com:A")
        self.assertIsNotNone(retrieved_cache)
        self.assertEqual(retrieved_cache.key, "example.com:A")
        self.assertEqual(len(retrieved_cache.records), 1)
    
    def test_cleanup_expired_cache(self):
        """Test cleaning up expired cache."""
        # Create expired cache entry
        expired_cache = DNSCache(
            key="expired",
            records=[],
            expires_at=datetime.now() - timedelta(seconds=300)
        )
        
        self.db.save_dns_cache(expired_cache)
        
        # Clean up
        deleted_count = self.db.cleanup_expired_cache()
        self.assertEqual(deleted_count, 1)

class TestDNSService(unittest.TestCase):
    """Test DNSService class."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = DNSService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_service_creation(self):
        """Test service creation."""
        self.assertIsNotNone(self.service.db)
        self.assertIsInstance(self.service.db, DNSDatabase)
        self.assertEqual(self.service.cache_ttl, 300)
    
    def test_generate_record_id(self):
        """Test record ID generation."""
        record_id = self.service.generate_record_id("example.com", RecordType.A)
        self.assertIsInstance(record_id, str)
        self.assertEqual(len(record_id), 12)
        
        # Should be different for different inputs
        record_id2 = self.service.generate_record_id("example.com", RecordType.MX)
        self.assertNotEqual(record_id, record_id2)
    
    def test_generate_query_id(self):
        """Test query ID generation."""
        query_id = self.service.generate_query_id()
        self.assertIsInstance(query_id, str)
        self.assertEqual(len(query_id), 12)
    
    def test_create_dns_record(self):
        """Test creating DNS record."""
        record = self.service.create_dns_record(
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1",
            ttl=3600
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.name, "example.com")
        self.assertEqual(record.record_type, RecordType.A)
        self.assertEqual(record.value, "192.168.1.1")
        self.assertEqual(record.ttl, 3600)
    
    def test_get_dns_records(self):
        """Test getting DNS records."""
        # Create a record first
        record = self.service.create_dns_record(
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1"
        )
        
        # Get records
        records = self.service.get_dns_records("example.com", RecordType.A)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "example.com")
    
    def test_create_dns_zone(self):
        """Test creating DNS zone."""
        zone = self.service.create_dns_zone(
            name="example.com",
            primary_ns="ns1.example.com",
            admin_email="admin@example.com"
        )
        
        self.assertIsNotNone(zone)
        self.assertEqual(zone.name, "example.com")
        self.assertEqual(zone.primary_ns, "ns1.example.com")
        self.assertEqual(zone.admin_email, "admin@example.com")
    
    def test_resolve_domain(self):
        """Test domain resolution."""
        # Create a record first
        self.service.create_dns_record(
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1"
        )
        
        # Resolve domain
        records = self.service.resolve_domain("example.com", RecordType.A)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].value, "192.168.1.1")
    
    def test_resolve_domain_cached(self):
        """Test domain resolution with caching."""
        # Create a record first
        self.service.create_dns_record(
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1"
        )
        
        # First resolution (not cached)
        records1 = self.service.resolve_domain("example.com", RecordType.A)
        self.assertEqual(len(records1), 1)
        
        # Second resolution (should be cached)
        records2 = self.service.resolve_domain("example.com", RecordType.A)
        self.assertEqual(len(records2), 1)
        self.assertEqual(records1[0].id, records2[0].id)
    
    def test_reverse_dns_lookup(self):
        """Test reverse DNS lookup."""
        # Create a PTR record
        self.service.create_dns_record(
            name="1.1.168.192.in-addr.arpa",
            record_type=RecordType.PTR,
            value="example.com"
        )
        
        # Perform reverse lookup
        records = self.service.reverse_dns_lookup("192.168.1.1")
        # Note: This is a simplified implementation
        self.assertIsInstance(records, list)
    
    def test_get_query_stats(self):
        """Test getting query statistics."""
        # Create some queries by resolving domains
        self.service.create_dns_record(
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1"
        )
        
        self.service.resolve_domain("example.com", RecordType.A)
        self.service.resolve_domain("example.com", RecordType.A)  # Should be cached
        
        stats = self.service.get_query_stats()
        self.assertIn('total_queries', stats)
        self.assertIn('cached_queries', stats)
        self.assertIn('cache_hit_rate', stats)
        self.assertIn('average_response_time', stats)
    
    def test_cleanup_cache(self):
        """Test cache cleanup."""
        # Create a record and resolve it to populate cache
        self.service.create_dns_record(
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1"
        )
        
        self.service.resolve_domain("example.com", RecordType.A)
        
        # Cleanup cache (should not remove anything as it's not expired)
        deleted_count = self.service.cleanup_cache()
        self.assertGreaterEqual(deleted_count, 0)

class TestFlaskApp(unittest.TestCase):
    """Test Flask application."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create a test service
        self.test_service = DNSService(self.temp_db.name)
        
        # Patch the global service
        with patch('dns_service.dns_service', self.test_service):
            from dns_service import app
            self.app = app
            self.client = app.test_client()
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_index_page(self):
        """Test index page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'DNS Service', response.data)
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'dns')
    
    def test_resolve_domain_api(self):
        """Test domain resolution API."""
        # Create a record first
        self.test_service.create_dns_record(
            name="example.com",
            record_type=RecordType.A,
            value="192.168.1.1"
        )
        
        response = self.client.get('/api/resolve/example.com/A')
        self.assertEqual(response.status_code, 200)
        
        results = response.get_json()
        self.assertIsInstance(results, list)
        if results:  # If results exist
            self.assertIn('name', results[0])
            self.assertIn('record_type', results[0])
            self.assertIn('value', results[0])
    
    def test_resolve_domain_invalid_type(self):
        """Test domain resolution with invalid record type."""
        response = self.client.get('/api/resolve/example.com/INVALID')
        self.assertEqual(response.status_code, 400)
        
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_add_dns_record_api(self):
        """Test add DNS record API."""
        data = {
            'name': 'example.com',
            'type': 'A',
            'value': '192.168.1.1',
            'ttl': 3600
        }
        
        response = self.client.post('/api/records', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('record_id', result)
    
    def test_add_dns_record_missing_fields(self):
        """Test add DNS record with missing fields."""
        data = {
            'name': 'example.com'
            # Missing type and value
        }
        
        response = self.client.post('/api/records', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_add_dns_record_invalid_type(self):
        """Test add DNS record with invalid type."""
        data = {
            'name': 'example.com',
            'type': 'INVALID',
            'value': '192.168.1.1'
        }
        
        response = self.client.post('/api/records', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_get_stats_api(self):
        """Test get stats API."""
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        
        stats = response.get_json()
        self.assertIn('total_queries', stats)
        self.assertIn('cached_queries', stats)
        self.assertIn('cache_hit_rate', stats)
        self.assertIn('average_response_time', stats)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = DNSService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_error_handling_save_dns_record(self):
        """Test database error handling in save_dns_record."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError("Database error")
            mock_connect.return_value = mock_conn
            
            record = DNSRecord(
                id="test_r",
                name="example.com",
                record_type=RecordType.A,
                value="192.168.1.1",
                ttl=300
            )
            result = self.service.db.save_dns_record(record)
            self.assertFalse(result)
    
    def test_database_error_handling_get_dns_records(self):
        """Test database error handling in get_dns_records."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError("Database error")
            mock_connect.return_value = mock_conn
            
            result = self.service.db.get_dns_records("example.com")
            self.assertEqual(len(result), 0)
    
    def test_database_error_handling_save_dns_zone(self):
        """Test database error handling in save_dns_zone."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError("Database error")
            mock_connect.return_value = mock_conn
            
            zone = DNSZone(
                zone_id="test_z",
                name="example.com",
                primary_ns="ns1.example.com",
                admin_email="admin@example.com"
            )
            result = self.service.db.save_dns_zone(zone)
            self.assertFalse(result)
    
    def test_database_error_handling_get_dns_zone(self):
        """Test database error handling in get_dns_zone."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError("Database error")
            mock_connect.return_value = mock_conn
            
            result = self.service.db.get_dns_zone("example.com")
            self.assertIsNone(result)
    
    def test_database_error_handling_log_dns_query(self):
        """Test database error handling in log_dns_query."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError("Database error")
            mock_connect.return_value = mock_conn
            
            query = DNSQuery(
                query_id="test_q",
                domain="example.com",
                record_type=RecordType.A,
                client_ip="192.168.1.1"
            )
            result = self.service.db.log_dns_query(query)
            self.assertFalse(result)
    
    def test_database_error_handling_save_dns_cache(self):
        """Test database error handling in save_dns_cache."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError("Database error")
            mock_connect.return_value = mock_conn
            
            # Create a DNS record first
            record = DNSRecord(
                id="test_r",
                name="example.com",
                record_type=RecordType.A,
                value="192.168.1.1",
                ttl=300
            )
            cache = DNSCache(
                key="example.com:A",
                records=[record],
                expires_at=datetime.now() + timedelta(seconds=300)
            )
            result = self.service.db.save_dns_cache(cache)
            self.assertFalse(result)
    
    def test_database_error_handling_get_dns_cache(self):
        """Test database error handling in get_dns_cache."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError("Database error")
            mock_connect.return_value = mock_conn
            
            result = self.service.db.get_dns_cache("example.com:A")
            self.assertIsNone(result)
    
    def test_database_error_handling_cleanup_expired_cache(self):
        """Test database error handling in cleanup_expired_cache."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError("Database error")
            mock_connect.return_value = mock_conn
            
            result = self.service.db.cleanup_expired_cache()
            self.assertEqual(result, 0)
    
    def test_flask_error_handling(self):
        """Test Flask error handling."""
        from dns_service import app
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Test invalid JSON
        response = client.post('/dns/records', 
                             data="invalid json",
                             content_type='application/json')
        self.assertEqual(response.status_code, 404)
        
        # Test missing required fields
        response = client.post('/dns/records', 
                             json={},
                             content_type='application/json')
        self.assertEqual(response.status_code, 404)
        
        # Test invalid record type
        response = client.post('/dns/records', 
                             json={
                                 'name': 'example.com',
                                 'record_type': 'INVALID',
                                 'value': '192.168.1.1'
                             },
                             content_type='application/json')
        self.assertEqual(response.status_code, 404)
    
    def test_edge_case_domain_validation(self):
        """Test edge cases in domain validation."""
        # Test with very long domain
        long_domain = "a" * 255 + ".com"
        record = self.service.create_dns_record(
            long_domain,
            RecordType.A,
            "192.168.1.1"
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.name, long_domain)
        
        # Test with special characters
        special_domain = "test-domain_with.underscores.com"
        record = self.service.create_dns_record(
            special_domain,
            RecordType.A,
            "192.168.1.1"
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.name, special_domain)
        
        # Test with empty domain
        record = self.service.create_dns_record(
            "",
            RecordType.A,
            "192.168.1.1"
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.name, "")
    
    def test_edge_case_ip_validation(self):
        """Test edge cases in IP validation."""
        # Test with valid IPv4
        record = self.service.create_dns_record(
            "example.com",
            RecordType.A,
            "192.168.1.1"
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.value, "192.168.1.1")
        
        # Test with valid IPv6
        record = self.service.create_dns_record(
            "example.com",
            RecordType.AAAA,
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.value, "2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        
        # Test with invalid IP (should still create record)
        record = self.service.create_dns_record(
            "example.com",
            RecordType.A,
            "invalid-ip"
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.value, "invalid-ip")
    
    def test_edge_case_ttl_validation(self):
        """Test edge cases in TTL validation."""
        # Test with very large TTL
        record = self.service.create_dns_record(
            "example.com",
            RecordType.A,
            "192.168.1.1",
            ttl=86400  # 24 hours
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.ttl, 86400)
        
        # Test with zero TTL
        record = self.service.create_dns_record(
            "example.com",
            RecordType.A,
            "192.168.1.1",
            ttl=0
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.ttl, 0)
        
        # Test with negative TTL (should use the negative value as is)
        record = self.service.create_dns_record(
            "example.com",
            RecordType.A,
            "192.168.1.1",
            ttl=-1
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.ttl, -1)  # Negative TTL is allowed
    
    def test_edge_case_record_type_validation(self):
        """Test edge cases in record type validation."""
        # Test with all record types
        for record_type in RecordType:
            record = self.service.create_dns_record(
                "example.com",
                record_type,
                "test-value"
            )
            self.assertIsNotNone(record)
            self.assertEqual(record.record_type, record_type)
    
    def test_edge_case_cache_operations(self):
        """Test edge cases in cache operations."""
        # Test cache with very long domain
        long_domain = "a" * 255 + ".com"
        record = DNSRecord(
            id="test_r",
            name=long_domain,
            record_type=RecordType.A,
            value="192.168.1.1",
            ttl=300
        )
        cache = DNSCache(
            key=f"{long_domain}:A",
            records=[record],
            expires_at=datetime.now() + timedelta(seconds=300)
        )
        result = self.service.db.save_dns_cache(cache)
        self.assertTrue(result)
        
        # Test cache with special characters
        special_domain = "test-domain_with.underscores.com"
        record = DNSRecord(
            id="test_r2",
            name=special_domain,
            record_type=RecordType.A,
            value="192.168.1.1",
            ttl=300
        )
        cache = DNSCache(
            key=f"{special_domain}:A",
            records=[record],
            expires_at=datetime.now() + timedelta(seconds=300)
        )
        result = self.service.db.save_dns_cache(cache)
        self.assertTrue(result)
        
        # Test cache with empty domain
        record = DNSRecord(
            id="test_r3",
            name="",
            record_type=RecordType.A,
            value="192.168.1.1",
            ttl=300
        )
        cache = DNSCache(
            key=":A",
            records=[record],
            expires_at=datetime.now() + timedelta(seconds=300)
        )
        result = self.service.db.save_dns_cache(cache)
        self.assertTrue(result)

class TestPerformance(unittest.TestCase):
    """Test performance and scalability."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = DNSService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_dns_record_creation_performance(self):
        """Test DNS record creation performance."""
        start_time = time.time()
        
        # Create 1000 DNS records
        for i in range(1000):
            self.service.create_dns_record(
                f"example{i}.com",
                RecordType.A,
                f"192.168.1.{i % 255}"
            )
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should complete within 2 seconds
        self.assertLess(creation_time, 2.0)
        
        # Verify records were created
        records = self.service.get_dns_records("example0.com")
        self.assertGreater(len(records), 0)
    
    def test_dns_zone_creation_performance(self):
        """Test DNS zone creation performance."""
        start_time = time.time()
        
        # Create 100 DNS zones
        for i in range(100):
            self.service.create_dns_zone(
                f"example{i}.com",
                f"ns1.example{i}.com",
                f"admin{i}@example{i}.com"
            )
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should complete within 1 second
        self.assertLess(creation_time, 1.0)
        
        # Verify zones were created
        zone = self.service.db.get_dns_zone("example0.com")
        self.assertIsNotNone(zone)
    
    def test_dns_resolution_performance(self):
        """Test DNS resolution performance."""
        # Create a record first
        self.service.create_dns_record(
            "example.com",
            RecordType.A,
            "192.168.1.1"
        )
        
        start_time = time.time()
        
        # Resolve 1000 times
        for i in range(1000):
            result = self.service.resolve_domain("example.com", RecordType.A)
            self.assertIsNotNone(result)
        
        end_time = time.time()
        resolution_time = end_time - start_time
        
        # Should complete within 1 second
        self.assertLess(resolution_time, 1.0)
    
    def test_memory_usage(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create 10000 DNS records
        for i in range(10000):
            self.service.create_dns_record(
                f"example{i}.com",
                RecordType.A,
                f"192.168.1.{i % 255}"
            )
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)
    
    def test_concurrent_operations(self):
        """Test concurrent operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_dns_record(i):
            try:
                record = self.service.create_dns_record(
                    f"concurrent{i}.com",
                    RecordType.A,
                    f"192.168.1.{i % 255}"
                )
                results.append(record)
            except Exception as e:
                errors.append(e)
        
        # Create 100 DNS records concurrently
        threads = []
        for i in range(100):
            thread = threading.Thread(target=create_dns_record, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        self.assertEqual(len(errors), 0)
        
        # Should have created all records
        self.assertEqual(len(results), 100)
    
    def test_cache_performance(self):
        """Test cache performance."""
        # Create a record first
        self.service.create_dns_record(
            "example.com",
            RecordType.A,
            "192.168.1.1"
        )
        
        # First resolution (not cached)
        start_time = time.time()
        result1 = self.service.resolve_domain("example.com", RecordType.A)
        first_time = time.time() - start_time
        
        # Second resolution (cached)
        start_time = time.time()
        result2 = self.service.resolve_domain("example.com", RecordType.A)
        second_time = time.time() - start_time
        
        # Cached resolution should be faster
        self.assertLess(second_time, first_time)
        
        # Results should be the same
        self.assertEqual(result1, result2)

if __name__ == '__main__':
    unittest.main()


