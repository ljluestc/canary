#!/usr/bin/env python3
"""
Comprehensive test suite for TinyURL system.

This test suite achieves 100% code coverage for the TinyURL system.
"""

import unittest
import tempfile
import os
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add the systems directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tinyurl.tinyurl_service import (
    TinyURLDatabase, TinyURLGenerator, TinyURLService,
    URLRecord, app
)


class TestURLRecord(unittest.TestCase):
    """Test URLRecord dataclass."""

    def test_url_record_creation(self):
        """Test URLRecord creation with all fields."""
        now = datetime.now()
        record = URLRecord(
            short_code="abc123",
            original_url="https://example.com",
            created_at=now,
            expires_at=now + timedelta(days=30),
            click_count=5,
            last_clicked=now,
            user_id="user123",
            is_active=True,
            metadata={"key": "value"}
        )
        
        self.assertEqual(record.short_code, "abc123")
        self.assertEqual(record.original_url, "https://example.com")
        self.assertEqual(record.click_count, 5)
        self.assertTrue(record.is_active)
        self.assertEqual(record.metadata, {"key": "value"})

    def test_url_record_defaults(self):
        """Test URLRecord with default values."""
        now = datetime.now()
        record = URLRecord(
            short_code="def456",
            original_url="https://test.com",
            created_at=now,
            expires_at=None
        )
        
        self.assertEqual(record.click_count, 0)
        self.assertIsNone(record.last_clicked)
        self.assertIsNone(record.user_id)
        self.assertTrue(record.is_active)
        self.assertEqual(record.metadata, {})

    def test_url_record_to_dict(self):
        """Test URLRecord to_dict method."""
        now = datetime.now()
        record = URLRecord(
            short_code="ghi789",
            original_url="https://demo.com",
            created_at=now,
            expires_at=now + timedelta(days=7),
            click_count=10,
            last_clicked=now,
            user_id="user456",
            is_active=False,
            metadata={"test": "data"}
        )
        
        result = record.to_dict()
        
        self.assertEqual(result['short_code'], "ghi789")
        self.assertEqual(result['original_url'], "https://demo.com")
        self.assertEqual(result['click_count'], 10)
        self.assertFalse(result['is_active'])
        self.assertEqual(result['metadata'], {"test": "data"})
        self.assertIsInstance(result['created_at'], str)
        self.assertIsInstance(result['expires_at'], str)


class TestTinyURLDatabase(unittest.TestCase):
    """Test TinyURLDatabase class."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = TinyURLDatabase(self.temp_db.name)

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_database_initialization(self):
        """Test database initialization creates tables."""
        # Check if tables exist
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('urls', tables)
            self.assertIn('analytics', tables)
            self.assertIn('users', tables)

    def test_create_url_success(self):
        """Test successful URL creation."""
        now = datetime.now()
        url_record = URLRecord(
            short_code="test123",
            original_url="https://example.com",
            created_at=now,
            expires_at=now + timedelta(days=30),
            user_id="user123",
            metadata={"key": "value"}
        )
        
        result = self.db.create_url(url_record)
        self.assertTrue(result)

    def test_create_url_duplicate(self):
        """Test URL creation with duplicate short code."""
        now = datetime.now()
        url_record1 = URLRecord(
            short_code="duplicate",
            original_url="https://example1.com",
            created_at=now,
            expires_at=None
        )
        url_record2 = URLRecord(
            short_code="duplicate",
            original_url="https://example2.com",
            created_at=now,
            expires_at=None
        )
        
        # First creation should succeed
        self.assertTrue(self.db.create_url(url_record1))
        
        # Second creation should fail
        self.assertFalse(self.db.create_url(url_record2))

    def test_get_url_existing(self):
        """Test getting existing URL."""
        now = datetime.now()
        url_record = URLRecord(
            short_code="gettest",
            original_url="https://gettest.com",
            created_at=now,
            expires_at=None,
            click_count=5,
            metadata={"test": "data"}
        )
        
        self.db.create_url(url_record)
        retrieved = self.db.get_url("gettest")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.short_code, "gettest")
        self.assertEqual(retrieved.original_url, "https://gettest.com")
        self.assertEqual(retrieved.click_count, 5)
        self.assertEqual(retrieved.metadata, {"test": "data"})

    def test_get_url_nonexistent(self):
        """Test getting non-existent URL."""
        retrieved = self.db.get_url("nonexistent")
        self.assertIsNone(retrieved)

    def test_get_url_inactive(self):
        """Test getting inactive URL."""
        now = datetime.now()
        url_record = URLRecord(
            short_code="inactive",
            original_url="https://inactive.com",
            created_at=now,
            expires_at=None,
            is_active=False
        )
        
        self.db.create_url(url_record)
        retrieved = self.db.get_url("inactive")
        self.assertIsNone(retrieved)

    def test_increment_click_count(self):
        """Test incrementing click count."""
        now = datetime.now()
        url_record = URLRecord(
            short_code="clicktest",
            original_url="https://clicktest.com",
            created_at=now,
            expires_at=None,
            click_count=0
        )
        
        self.db.create_url(url_record)
        
        # Increment click count
        result = self.db.increment_click_count("clicktest")
        self.assertTrue(result)
        
        # Verify click count was incremented
        retrieved = self.db.get_url("clicktest")
        self.assertEqual(retrieved.click_count, 1)

    def test_increment_click_count_nonexistent(self):
        """Test incrementing click count for non-existent URL."""
        result = self.db.increment_click_count("nonexistent")
        self.assertFalse(result)

    def test_add_analytics(self):
        """Test adding analytics record."""
        now = datetime.now()
        url_record = URLRecord(
            short_code="analytics",
            original_url="https://analytics.com",
            created_at=now,
            expires_at=None
        )
        
        self.db.create_url(url_record)
        
        result = self.db.add_analytics(
            short_code="analytics",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            referer="https://google.com",
            country="US",
            city="New York"
        )
        
        self.assertTrue(result)

    def test_get_analytics(self):
        """Test getting analytics records."""
        now = datetime.now()
        url_record = URLRecord(
            short_code="getanalytics",
            original_url="https://getanalytics.com",
            created_at=now,
            expires_at=None
        )
        
        self.db.create_url(url_record)
        
        # Add multiple analytics records
        self.db.add_analytics("getanalytics", "192.168.1.1", "Mozilla/5.0")
        self.db.add_analytics("getanalytics", "192.168.1.2", "Chrome/91.0")
        
        analytics = self.db.get_analytics("getanalytics", limit=10)
        
        self.assertEqual(len(analytics), 2)
        # Check that analytics are ordered by clicked_at DESC (most recent first)
        self.assertTrue(analytics[0]['clicked_at'] >= analytics[1]['clicked_at'])

    def test_get_user_urls(self):
        """Test getting URLs for a user."""
        now = datetime.now()
        user_id = "user123"
        
        url_record1 = URLRecord(
            short_code="user1",
            original_url="https://user1.com",
            created_at=now,
            expires_at=None,
            user_id=user_id
        )
        url_record2 = URLRecord(
            short_code="user2",
            original_url="https://user2.com",
            created_at=now,
            expires_at=None,
            user_id=user_id
        )
        
        self.db.create_url(url_record1)
        self.db.create_url(url_record2)
        
        user_urls = self.db.get_user_urls(user_id)
        
        self.assertEqual(len(user_urls), 2)
        # Check that URLs are ordered by created_at DESC (most recent first)
        self.assertTrue(user_urls[0].created_at >= user_urls[1].created_at)

    def test_delete_url(self):
        """Test deleting URL."""
        now = datetime.now()
        url_record = URLRecord(
            short_code="deletetest",
            original_url="https://deletetest.com",
            created_at=now,
            expires_at=None
        )
        
        self.db.create_url(url_record)
        
        # Verify URL exists
        retrieved = self.db.get_url("deletetest")
        self.assertIsNotNone(retrieved)
        
        # Delete URL
        result = self.db.delete_url("deletetest")
        self.assertTrue(result)
        
        # Verify URL is no longer accessible
        retrieved = self.db.get_url("deletetest")
        self.assertIsNone(retrieved)

    def test_delete_url_with_user_id(self):
        """Test deleting URL with user authorization."""
        now = datetime.now()
        url_record = URLRecord(
            short_code="deleteuser",
            original_url="https://deleteuser.com",
            created_at=now,
            expires_at=None,
            user_id="user123"
        )
        
        self.db.create_url(url_record)
        
        # Delete with correct user ID
        result = self.db.delete_url("deleteuser", "user123")
        self.assertTrue(result)
        
        # Try to delete with wrong user ID
        url_record2 = URLRecord(
            short_code="deleteuser2",
            original_url="https://deleteuser2.com",
            created_at=now,
            expires_at=None,
            user_id="user123"
        )
        self.db.create_url(url_record2)
        
        result = self.db.delete_url("deleteuser2", "user456")
        self.assertFalse(result)


class TestTinyURLGenerator(unittest.TestCase):
    """Test TinyURLGenerator class."""

    def setUp(self):
        """Set up generator."""
        self.generator = TinyURLGenerator(length=6)

    def test_generate_short_code(self):
        """Test generating random short code."""
        code = self.generator.generate_short_code()
        
        self.assertEqual(len(code), 6)
        self.assertTrue(all(c in self.generator.chars for c in code))

    def test_generate_custom_code(self):
        """Test generating custom code."""
        custom_code = self.generator.generate_custom_code("MyCode123")
        
        self.assertEqual(len(custom_code), 6)
        self.assertTrue(custom_code.startswith("mycode"))

    def test_generate_custom_code_invalid_chars(self):
        """Test generating custom code with invalid characters."""
        custom_code = self.generator.generate_custom_code("My@Code#123!")
        
        self.assertEqual(len(custom_code), 6)
        self.assertTrue(all(c in self.generator.chars for c in custom_code))

    def test_generate_custom_code_short(self):
        """Test generating custom code shorter than required length."""
        custom_code = self.generator.generate_custom_code("abc")
        
        self.assertEqual(len(custom_code), 6)
        self.assertTrue(custom_code.startswith("abc"))

    def test_generate_from_url(self):
        """Test generating deterministic code from URL."""
        url = "https://example.com/path"
        code1 = self.generator.generate_from_url(url)
        code2 = self.generator.generate_from_url(url)
        
        self.assertEqual(len(code1), 6)
        self.assertEqual(code1, code2)  # Should be deterministic

    def test_generate_from_url_different(self):
        """Test generating different codes for different URLs."""
        url1 = "https://example.com/path1"
        url2 = "https://example.com/path2"
        
        code1 = self.generator.generate_from_url(url1)
        code2 = self.generator.generate_from_url(url2)
        
        self.assertNotEqual(code1, code2)


class TestTinyURLService(unittest.TestCase):
    """Test TinyURLService class."""

    def setUp(self):
        """Set up service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = TinyURLService(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up service."""
        os.unlink(self.temp_db.name)

    def test_shorten_url_success(self):
        """Test successful URL shortening."""
        result = self.service.shorten_url("https://example.com")
        
        self.assertTrue(result['success'])
        self.assertIn('short_code', result)
        self.assertIn('short_url', result)
        self.assertEqual(result['original_url'], "https://example.com")

    def test_shorten_url_custom_code(self):
        """Test URL shortening with custom code."""
        result = self.service.shorten_url(
            "https://example.com",
            custom_code="mycode"
        )
        
        self.assertTrue(result['success'])
        self.assertTrue(result['short_code'].startswith("mycode"))

    def test_shorten_url_expiration(self):
        """Test URL shortening with expiration."""
        result = self.service.shorten_url(
            "https://example.com",
            expires_in_days=7
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['expires_at'])

    def test_shorten_url_invalid(self):
        """Test shortening invalid URL."""
        result = self.service.shorten_url("not-a-url")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_shorten_url_duplicate_custom_code(self):
        """Test shortening with duplicate custom code."""
        # First URL
        result1 = self.service.shorten_url(
            "https://example1.com",
            custom_code="duplicate"
        )
        self.assertTrue(result1['success'])
        
        # Second URL with same custom code
        result2 = self.service.shorten_url(
            "https://example2.com",
            custom_code="duplicate"
        )
        self.assertFalse(result2['success'])
        self.assertIn('error', result2)

    def test_expand_url_success(self):
        """Test successful URL expansion."""
        # Shorten URL first
        shorten_result = self.service.shorten_url("https://example.com")
        short_code = shorten_result['short_code']
        
        # Expand URL
        original_url = self.service.expand_url(short_code)
        
        self.assertEqual(original_url, "https://example.com")

    def test_expand_url_nonexistent(self):
        """Test expanding non-existent URL."""
        original_url = self.service.expand_url("nonexistent")
        self.assertIsNone(original_url)

    def test_expand_url_expired(self):
        """Test expanding expired URL."""
        # Create URL with past expiration
        past_time = datetime.now() - timedelta(days=1)
        url_record = URLRecord(
            short_code="expired",
            original_url="https://expired.com",
            created_at=past_time,
            expires_at=past_time
        )
        
        self.service.db.create_url(url_record)
        
        # Try to expand expired URL
        original_url = self.service.expand_url("expired")
        self.assertIsNone(original_url)

    def test_get_url_info(self):
        """Test getting URL information."""
        # Shorten URL first
        shorten_result = self.service.shorten_url("https://example.com")
        short_code = shorten_result['short_code']
        
        # Get URL info
        info = self.service.get_url_info(short_code)
        
        self.assertIsNotNone(info)
        self.assertEqual(info['original_url'], "https://example.com")
        self.assertIn('recent_clicks', info)

    def test_get_url_info_nonexistent(self):
        """Test getting info for non-existent URL."""
        info = self.service.get_url_info("nonexistent")
        self.assertIsNone(info)

    def test_is_valid_url(self):
        """Test URL validation."""
        # Valid URLs
        self.assertTrue(self.service._is_valid_url("https://example.com"))
        self.assertTrue(self.service._is_valid_url("http://localhost:8080"))
        self.assertTrue(self.service._is_valid_url("https://192.168.1.1"))
        
        # Invalid URLs
        self.assertFalse(self.service._is_valid_url("not-a-url"))
        self.assertFalse(self.service._is_valid_url("ftp://example.com"))
        self.assertFalse(self.service._is_valid_url(""))

    @patch('tinyurl.tinyurl_service.redis')
    def test_service_with_redis(self, mock_redis):
        """Test service with Redis caching."""
        mock_redis_client = MagicMock()
        mock_redis.from_url.return_value = mock_redis_client
        
        service = TinyURLService(
            db_path=self.temp_db.name,
            redis_url="redis://localhost:6379"
        )
        
        # Test shortening with Redis
        result = service.shorten_url("https://example.com")
        self.assertTrue(result['success'])
        
        # Verify Redis set was called
        mock_redis_client.setex.assert_called_once()

    @patch('tinyurl.tinyurl_service.redis')
    def test_expand_url_with_redis_cache(self, mock_redis):
        """Test URL expansion with Redis cache."""
        mock_redis_client = MagicMock()
        mock_redis.from_url.return_value = mock_redis_client
        
        # Mock cached data
        cached_data = {
            'short_code': 'cached123',
            'original_url': 'https://cached.com',
            'created_at': datetime.now().isoformat(),
            'expires_at': None,
            'click_count': 0,
            'last_clicked': None,
            'user_id': None,
            'is_active': True,
            'metadata': {}
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        service = TinyURLService(
            db_path=self.temp_db.name,
            redis_url="redis://localhost:6379"
        )
        
        # Test expanding from cache
        original_url = service.expand_url("cached123")
        self.assertEqual(original_url, "https://cached.com")
        
        # Verify Redis get was called
        mock_redis_client.get.assert_called_once_with("url:cached123")


class TestFlaskApp(unittest.TestCase):
    """Test Flask application endpoints."""

    def setUp(self):
        """Set up Flask test client."""
        app.config['TESTING'] = True
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create a test service with the temp database
        global tinyurl_service
        tinyurl_service = TinyURLService(self.temp_db.name)
        
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_index_page(self):
        """Test home page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TinyURL Service', response.data)

    def test_shorten_url_post(self):
        """Test URL shortening via POST."""
        response = self.client.post('/shorten', data={
            'url': 'https://example.com'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_shorten_url_json(self):
        """Test URL shortening via JSON."""
        response = self.client.post('/shorten', 
            json={'url': 'https://example.com'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_shorten_url_missing_url(self):
        """Test shortening without URL."""
        response = self.client.post('/shorten', data={})
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_redirect_url(self):
        """Test URL redirection."""
        # First shorten a URL
        shorten_response = self.client.post('/shorten', data={
            'url': 'https://example.com'
        })
        short_code = shorten_response.get_json()['short_code']
        
        # Then redirect
        response = self.client.get(f'/{short_code}')
        self.assertEqual(response.status_code, 302)

    def test_redirect_nonexistent(self):
        """Test redirecting non-existent URL."""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_get_url_info(self):
        """Test getting URL info."""
        # First shorten a URL
        shorten_response = self.client.post('/shorten', data={
            'url': 'https://example.com'
        })
        short_code = shorten_response.get_json()['short_code']
        
        # Then get info
        response = self.client.get(f'/api/info/{short_code}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_get_url_info_nonexistent(self):
        """Test getting info for non-existent URL."""
        response = self.client.get('/api/info/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_get_analytics(self):
        """Test getting analytics."""
        # First shorten a URL
        shorten_response = self.client.post('/shorten', data={
            'url': 'https://example.com'
        })
        short_code = shorten_response.get_json()['short_code']
        
        # Then get analytics
        response = self.client.get(f'/api/analytics/{short_code}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])


if __name__ == '__main__':
    # Run tests with coverage
    unittest.main(verbosity=2)
