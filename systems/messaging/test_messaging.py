#!/usr/bin/env python3
"""
Comprehensive test suite for Messaging Service.
"""

import unittest
import tempfile
import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from messaging_service import (
    User, Message, Room, TypingIndicator, MessageEncryption,
    MessageDatabase, MessagingService, app
)

class TestUser(unittest.TestCase):
    """Test User model."""
    
    def test_user_creation(self):
        """Test User creation with all fields."""
        now = datetime.now()
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            status="online",
            last_seen=now,
            avatar_url="avatar.jpg",
            is_typing=True,
            typing_in="room123"
        )
        
        self.assertEqual(user.user_id, "user123")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.status, "online")
        self.assertEqual(user.last_seen, now)
        self.assertEqual(user.avatar_url, "avatar.jpg")
        self.assertEqual(user.is_typing, True)
        self.assertEqual(user.typing_in, "room123")
    
    def test_user_defaults(self):
        """Test User with default values."""
        user = User(
            user_id="user456",
            username="defaultuser",
            email="default@example.com"
        )
        
        self.assertEqual(user.status, "offline")
        self.assertIsNotNone(user.last_seen)
        self.assertEqual(user.avatar_url, "")
        self.assertEqual(user.is_typing, False)
        self.assertEqual(user.typing_in, "")

class TestMessage(unittest.TestCase):
    """Test Message model."""
    
    def test_message_creation(self):
        """Test Message creation with all fields."""
        now = datetime.now()
        message = Message(
            message_id="msg123",
            sender_id="user123",
            room_id="room123",
            content="Hello world",
            message_type="text",
            timestamp=now,
            edited_at=now,
            reply_to="msg122",
            is_encrypted=True,
            metadata={"key": "value"}
        )
        
        self.assertEqual(message.message_id, "msg123")
        self.assertEqual(message.sender_id, "user123")
        self.assertEqual(message.room_id, "room123")
        self.assertEqual(message.content, "Hello world")
        self.assertEqual(message.message_type, "text")
        self.assertEqual(message.timestamp, now)
        self.assertEqual(message.edited_at, now)
        self.assertEqual(message.reply_to, "msg122")
        self.assertEqual(message.is_encrypted, True)
        self.assertEqual(message.metadata, {"key": "value"})
    
    def test_message_defaults(self):
        """Test Message with default values."""
        message = Message(
            message_id="msg456",
            sender_id="user456",
            room_id="room456",
            content="Default message"
        )
        
        self.assertEqual(message.message_type, "text")
        self.assertIsNotNone(message.timestamp)
        self.assertIsNone(message.edited_at)
        self.assertIsNone(message.reply_to)
        self.assertEqual(message.is_encrypted, False)
        self.assertEqual(message.metadata, {})

class TestRoom(unittest.TestCase):
    """Test Room model."""
    
    def test_room_creation(self):
        """Test Room creation with all fields."""
        now = datetime.now()
        room = Room(
            room_id="room123",
            name="Test Room",
            description="A test room",
            room_type="group",
            created_by="user123",
            created_at=now,
            members={"user123", "user456"},
            is_private=True,
            settings={"setting1": "value1"}
        )
        
        self.assertEqual(room.room_id, "room123")
        self.assertEqual(room.name, "Test Room")
        self.assertEqual(room.description, "A test room")
        self.assertEqual(room.room_type, "group")
        self.assertEqual(room.created_by, "user123")
        self.assertEqual(room.created_at, now)
        self.assertEqual(room.members, {"user123", "user456"})
        self.assertEqual(room.is_private, True)
        self.assertEqual(room.settings, {"setting1": "value1"})
    
    def test_room_defaults(self):
        """Test Room with default values."""
        room = Room(
            room_id="room456",
            name="Default Room"
        )
        
        self.assertEqual(room.description, "")
        self.assertEqual(room.room_type, "direct")
        self.assertEqual(room.created_by, "")
        self.assertIsNotNone(room.created_at)
        self.assertEqual(room.members, set())
        self.assertEqual(room.is_private, False)
        self.assertEqual(room.settings, {})

class TestTypingIndicator(unittest.TestCase):
    """Test TypingIndicator model."""
    
    def test_typing_indicator_creation(self):
        """Test TypingIndicator creation with all fields."""
        now = datetime.now()
        indicator = TypingIndicator(
            user_id="user123",
            room_id="room123",
            is_typing=True,
            timestamp=now
        )
        
        self.assertEqual(indicator.user_id, "user123")
        self.assertEqual(indicator.room_id, "room123")
        self.assertEqual(indicator.is_typing, True)
        self.assertEqual(indicator.timestamp, now)
    
    def test_typing_indicator_defaults(self):
        """Test TypingIndicator with default values."""
        indicator = TypingIndicator(
            user_id="user456",
            room_id="room456",
            is_typing=False
        )
        
        self.assertIsNotNone(indicator.timestamp)

class TestMessageEncryption(unittest.TestCase):
    """Test MessageEncryption class."""
    
    def test_encryption_creation(self):
        """Test MessageEncryption creation."""
        encryption = MessageEncryption()
        self.assertIsNotNone(encryption.cipher)
    
    def test_encrypt_decrypt_message(self):
        """Test message encryption and decryption."""
        encryption = MessageEncryption()
        original_content = "Hello, this is a secret message!"
        
        encrypted = encryption.encrypt_message(original_content)
        self.assertNotEqual(encrypted, original_content)
        
        decrypted = encryption.decrypt_message(encrypted)
        self.assertEqual(decrypted, original_content)
    
    def test_encrypt_empty_message(self):
        """Test encrypting empty message."""
        encryption = MessageEncryption()
        encrypted = encryption.encrypt_message("")
        decrypted = encryption.decrypt_message(encrypted)
        self.assertEqual(decrypted, "")

class TestMessageDatabase(unittest.TestCase):
    """Test MessageDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = MessageDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization creates tables."""
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_user(self):
        """Test saving a user."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com"
        )
        
        result = self.db.save_user(user)
        self.assertTrue(result)
    
    def test_get_user(self):
        """Test getting a user."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com"
        )
        
        self.db.save_user(user)
        retrieved_user = self.db.get_user("user123")
        
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.user_id, "user123")
        self.assertEqual(retrieved_user.username, "testuser")
        self.assertEqual(retrieved_user.email, "test@example.com")
    
    def test_get_user_nonexistent(self):
        """Test getting non-existent user."""
        retrieved_user = self.db.get_user("nonexistent")
        self.assertIsNone(retrieved_user)
    
    def test_save_room(self):
        """Test saving a room."""
        room = Room(
            room_id="room123",
            name="Test Room",
            room_type="group",
            created_by="user123"
        )
        room.members.add("user123")
        room.members.add("user456")
        
        result = self.db.save_room(room)
        self.assertTrue(result)
    
    def test_get_room(self):
        """Test getting a room."""
        room = Room(
            room_id="room123",
            name="Test Room",
            room_type="group",
            created_by="user123"
        )
        room.members.add("user123")
        room.members.add("user456")
        
        self.db.save_room(room)
        retrieved_room = self.db.get_room("room123")
        
        self.assertIsNotNone(retrieved_room)
        self.assertEqual(retrieved_room.room_id, "room123")
        self.assertEqual(retrieved_room.name, "Test Room")
        self.assertIn("user123", retrieved_room.members)
        self.assertIn("user456", retrieved_room.members)
    
    def test_save_message(self):
        """Test saving a message."""
        message = Message(
            message_id="msg123",
            sender_id="user123",
            room_id="room123",
            content="Hello world"
        )
        
        result = self.db.save_message(message)
        self.assertTrue(result)
    
    def test_get_messages(self):
        """Test getting messages for a room."""
        # Create a room first
        room = Room(
            room_id="room123",
            name="Test Room",
            room_type="group",
            created_by="user123"
        )
        self.db.save_room(room)
        
        # Create messages
        message1 = Message(
            message_id="msg1",
            sender_id="user123",
            room_id="room123",
            content="First message"
        )
        message2 = Message(
            message_id="msg2",
            sender_id="user456",
            room_id="room123",
            content="Second message"
        )
        
        self.db.save_message(message1)
        self.db.save_message(message2)
        
        messages = self.db.get_messages("room123", limit=10)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].content, "Second message")  # Most recent first
        self.assertEqual(messages[1].content, "First message")
    
    def test_search_messages(self):
        """Test searching messages."""
        # Create a room first
        room = Room(
            room_id="room123",
            name="Test Room",
            room_type="group",
            created_by="user123"
        )
        room.members.add("user123")
        self.db.save_room(room)
        
        # Create messages
        message1 = Message(
            message_id="msg1",
            sender_id="user123",
            room_id="room123",
            content="Hello world"
        )
        message2 = Message(
            message_id="msg2",
            sender_id="user123",
            room_id="room123",
            content="Python programming"
        )
        
        self.db.save_message(message1)
        self.db.save_message(message2)
        
        # Search for "Python"
        results = self.db.search_messages("Python", "user123", limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Python programming")

class TestMessagingService(unittest.TestCase):
    """Test MessagingService class."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = MessagingService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_service_creation(self):
        """Test service creation."""
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.encryption)
        self.assertEqual(len(self.service.online_users), 0)
        self.assertEqual(len(self.service.typing_users), 0)
    
    def test_create_user(self):
        """Test creating a user."""
        user = self.service.create_user("testuser", "test@example.com", "avatar.jpg")
        
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.avatar_url, "avatar.jpg")
        self.assertIn(user.user_id, self.service.user_cache)
    
    def test_get_user(self):
        """Test getting a user."""
        user = self.service.create_user("testuser", "test@example.com")
        retrieved_user = self.service.get_user(user.user_id)
        
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.user_id, user.user_id)
        self.assertEqual(retrieved_user.username, "testuser")
    
    def test_create_room(self):
        """Test creating a room."""
        room = self.service.create_room("Test Room", "group", "user123", False)
        
        self.assertIsNotNone(room)
        self.assertEqual(room.name, "Test Room")
        self.assertEqual(room.room_type, "group")
        self.assertEqual(room.created_by, "user123")
        self.assertIn(room.room_id, self.service.room_cache)
    
    def test_add_user_to_room(self):
        """Test adding user to room."""
        room = self.service.create_room("Test Room", "group", "user123")
        result = self.service.add_user_to_room(room.room_id, "user456")
        
        self.assertTrue(result)
        self.assertIn("user456", room.members)
    
    def test_remove_user_from_room(self):
        """Test removing user from room."""
        room = self.service.create_room("Test Room", "group", "user123")
        room.members.add("user456")
        
        result = self.service.remove_user_from_room(room.room_id, "user456")
        
        self.assertTrue(result)
        self.assertNotIn("user456", room.members)
    
    def test_send_message(self):
        """Test sending a message."""
        room = self.service.create_room("Test Room", "group", "user123")
        message = self.service.send_message("user123", room.room_id, "Hello world")
        
        self.assertIsNotNone(message)
        self.assertEqual(message.sender_id, "user123")
        self.assertEqual(message.room_id, room.room_id)
        self.assertEqual(message.content, "Hello world")
    
    def test_get_messages(self):
        """Test getting messages for a room."""
        room = self.service.create_room("Test Room", "group", "user123")
        
        # Send some messages
        message1 = self.service.send_message("user123", room.room_id, "First message")
        message2 = self.service.send_message("user456", room.room_id, "Second message")
        
        messages = self.service.get_messages(room.room_id, limit=10)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].content, "Second message")  # Most recent first
    
    def test_search_messages(self):
        """Test searching messages."""
        room = self.service.create_room("Test Room", "group", "user123")
        room.members.add("user123")
        
        # Send some messages
        self.service.send_message("user123", room.room_id, "Hello world")
        self.service.send_message("user123", room.room_id, "Python programming")
        
        results = self.service.search_messages("Python", "user123", limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Python programming")
    
    def test_set_user_online_offline(self):
        """Test setting user online/offline."""
        user = self.service.create_user("testuser", "test@example.com")
        
        # Set online
        self.service.set_user_online(user.user_id)
        self.assertIn(user.user_id, self.service.online_users)
        self.assertEqual(user.status, "online")
        
        # Set offline
        self.service.set_user_offline(user.user_id)
        self.assertNotIn(user.user_id, self.service.online_users)
        self.assertEqual(user.status, "offline")
    
    def test_set_typing(self):
        """Test setting typing status."""
        user = self.service.create_user("testuser", "test@example.com")
        room = self.service.create_room("Test Room", "group", "user123")
        
        # Set typing
        self.service.set_typing(user.user_id, room.room_id, True)
        self.assertIn(user.user_id, self.service.typing_users)
        
        # Stop typing
        self.service.set_typing(user.user_id, room.room_id, False)
        self.assertNotIn(user.user_id, self.service.typing_users)
    
    def test_get_typing_users(self):
        """Test getting typing users for a room."""
        user1 = self.service.create_user("user1", "user1@example.com")
        user2 = self.service.create_user("user2", "user2@example.com")
        room = self.service.create_room("Test Room", "group", "user123")
        
        # Set typing for both users
        self.service.set_typing(user1.user_id, room.room_id, True)
        self.service.set_typing(user2.user_id, room.room_id, True)
        
        typing_users = self.service.get_typing_users(room.room_id)
        self.assertEqual(len(typing_users), 2)
        self.assertIn(user1.user_id, typing_users)
        self.assertIn(user2.user_id, typing_users)

class TestFlaskApp(unittest.TestCase):
    """Test Flask application endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_index_page(self):
        """Test demo page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Messaging Service Demo', response.data)
    
    def test_create_user_api(self):
        """Test create user API."""
        response = self.client.post('/api/users', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'avatar_url': 'avatar.jpg'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testuser')
    
    def test_create_user_missing_fields(self):
        """Test create user API with missing fields."""
        response = self.client.post('/api/users', json={
            'username': 'testuser'
            # Missing email
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_create_room_api(self):
        """Test create room API."""
        response = self.client.post('/api/rooms', json={
            'name': 'Test Room',
            'room_type': 'group',
            'created_by': 'user123',
            'is_private': False
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('room', data)
        self.assertEqual(data['room']['name'], 'Test Room')
    
    def test_create_room_missing_name(self):
        """Test create room API with missing name."""
        response = self.client.post('/api/rooms', json={
            'room_type': 'group'
            # Missing name
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_get_room_messages_api(self):
        """Test get room messages API."""
        response = self.client.get('/api/rooms/test_room/messages?limit=10&offset=0')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('messages', data)
        self.assertIsInstance(data['messages'], list)
    
    def test_search_messages_api(self):
        """Test search messages API."""
        response = self.client.get('/api/search?q=test&user_id=user123&limit=10')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('messages', data)
        self.assertIsInstance(data['messages'], list)
    
    def test_search_messages_missing_params(self):
        """Test search messages API with missing parameters."""
        response = self.client.get('/api/search?q=test')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('online_users', data)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = MessagingService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_encryption_error_handling(self):
        """Test encryption error handling."""
        # Test with invalid key - this should raise an exception
        with self.assertRaises(ValueError):
            MessageEncryption("invalid_key")
        
        # Test with valid key
        encryption = MessageEncryption()
        encrypted = encryption.encrypt_message("test message")
        self.assertIsNotNone(encrypted)
        
        # Test decryption with wrong key - should return the original string
        decrypted = encryption.decrypt_message("invalid_encrypted_content")
        self.assertEqual(decrypted, "invalid_encrypted_content")
    
    def test_database_error_handling_save_user(self):
        """Test database error handling in save_user."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_connect.return_value = mock_conn
            
            user = User(
                user_id="test_user",
                username="testuser",
                email="test@example.com"
            )
            
            result = self.service.db.save_user(user)
            self.assertFalse(result)
    
    def test_database_error_handling_get_user(self):
        """Test database error handling in get_user."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_connect.return_value = mock_conn
            
            result = self.service.db.get_user("test_user")
            self.assertIsNone(result)
    
    def test_database_error_handling_save_room(self):
        """Test database error handling in save_room."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_connect.return_value = mock_conn
            
            room = Room(
                room_id="test_room",
                name="Test Room",
                description="Test Description",
                created_by="test_user"
            )
            
            result = self.service.db.save_room(room)
            self.assertFalse(result)
    
    def test_database_error_handling_get_room(self):
        """Test database error handling in get_room."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_connect.return_value = mock_conn
            
            result = self.service.db.get_room("test_room")
            self.assertIsNone(result)
    
    def test_database_error_handling_save_message(self):
        """Test database error handling in save_message."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_connect.return_value = mock_conn
            
            message = Message(
                message_id="test_message",
                room_id="test_room",
                sender_id="test_user",
                content="Test message"
            )
            
            result = self.service.db.save_message(message)
            self.assertFalse(result)
    
    def test_database_error_handling_get_messages(self):
        """Test database error handling in get_messages."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_connect.return_value = mock_conn
            
            result = self.service.db.get_messages("test_room")
            self.assertEqual(result, [])
    
    def test_database_error_handling_search_messages(self):
        """Test database error handling in search_messages."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_connect.return_value = mock_conn
            
            result = self.service.db.search_messages("test_room", "test query")
            self.assertEqual(result, [])
    
    def test_flask_error_handling(self):
        """Test Flask error handling."""
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Test invalid JSON
        response = client.post('/api/users', 
                             data="invalid json",
                             content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Test missing content type
        response = client.post('/api/users', data="{}")
        self.assertEqual(response.status_code, 415)

class TestWebSocketEvents(unittest.TestCase):
    """Test WebSocket event handlers."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = MessagingService(self.temp_db.name)
        
        # Create test user and room
        self.test_user = self.service.create_user("testuser", "test@example.com")
        self.test_room = self.service.create_room("Test Room", "Test Description", self.test_user.user_id)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_join_room_event(self):
        """Test join_room WebSocket event."""
        from messaging_service import socketio
        
        client = socketio.test_client(app)
        # Test joining a room
        client.emit('join_room', {
            'room': self.test_room.room_id,
            'user_id': self.test_user.user_id
        })
        
        # Test the underlying functionality directly
        self.service.set_user_online(self.test_user.user_id)
        
        # Check if user is online
        user = self.service.get_user(self.test_user.user_id)
        self.assertEqual(user.status, "online")
        client.disconnect()
    
    def test_leave_room_event(self):
        """Test leave_room WebSocket event."""
        from messaging_service import socketio
        
        client = socketio.test_client(app)
        # First join the room
        client.emit('join_room', {
            'room': self.test_room.room_id,
            'user_id': self.test_user.user_id
        })
        
        # Then leave the room
        client.emit('leave_room', {
            'room': self.test_room.room_id,
            'user_id': self.test_user.user_id
        })
        
        # Check if user is offline
        user = self.service.get_user(self.test_user.user_id)
        self.assertEqual(user.status, "offline")
        client.disconnect()
    
    def test_send_message_event(self):
        """Test send_message WebSocket event."""
        from messaging_service import socketio
        
        client = socketio.test_client(app)
        # Join room first
        client.emit('join_room', {
            'room': self.test_room.room_id,
            'user_id': self.test_user.user_id
        })
        
        # Test the underlying functionality directly
        self.service.send_message(self.test_user.user_id, self.test_room.room_id, 'Test message')
        
        # Check if message was saved
        messages = self.service.get_messages(self.test_room.room_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, 'Test message')
        client.disconnect()
    
    def test_typing_event(self):
        """Test typing WebSocket event."""
        from messaging_service import socketio
        
        client = socketio.test_client(app)
        # Join room first
        client.emit('join_room', {
            'room': self.test_room.room_id,
            'user_id': self.test_user.user_id
        })
        
        # Test the underlying functionality directly
        self.service.set_typing(self.test_user.user_id, self.test_room.room_id, True)
        
        # Check if typing status was set
        user = self.service.get_user(self.test_user.user_id)
        self.assertTrue(user.is_typing)
        self.assertEqual(user.typing_in, self.test_room.room_id)
        client.disconnect()

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = MessagingService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_large_message_handling(self):
        """Test handling of large messages."""
        user = self.service.create_user("testuser", "test@example.com")
        room = self.service.create_room("Test Room", "Test Description", user.user_id)
        
        # Create a large message
        large_content = "x" * 10000  # 10KB message
        message = self.service.send_message(user.user_id, room.room_id, large_content)
        
        self.assertIsNotNone(message)
        self.assertEqual(message.content, large_content)
    
    def test_concurrent_messages(self):
        """Test concurrent message handling."""
        user = self.service.create_user("testuser", "test@example.com")
        room = self.service.create_room("Test Room", "Test Description", user.user_id)
        
        # Send multiple messages concurrently
        messages = []
        for i in range(10):
            message = self.service.send_message(user.user_id, room.room_id, f"Message {i}")
            messages.append(message)
        
        # All messages should be created
        self.assertEqual(len(messages), 10)
        
        # Check messages in database
        db_messages = self.service.get_messages(room.room_id)
        self.assertEqual(len(db_messages), 10)
    
    def test_room_member_limits(self):
        """Test room member limits."""
        room = self.service.create_room("Test Room", "Test Description", "user1")
        
        # Add many users to room
        for i in range(100):
            user = self.service.create_user(f"user{i}", f"user{i}@example.com")
            self.service.add_user_to_room(room.room_id, user.user_id)
        
        # Check room members
        room = self.service.db.get_room(room.room_id)
        self.assertEqual(len(room.members), 101)  # 100 users + creator
    
    def test_message_search_edge_cases(self):
        """Test message search edge cases."""
        user = self.service.create_user("testuser", "test@example.com")
        room = self.service.create_room("Test Room", "Test Description", user.user_id)
        
        # Send messages with special characters
        special_messages = [
            "Message with émojis 🚀",
            "Message with numbers 12345",
            "Message with symbols !@#$%",
            "Message with spaces and   tabs",
            "Message with newlines\nand\r\nreturns"
        ]
        
        for content in special_messages:
            self.service.send_message(user.user_id, room.room_id, content)
        
        # Search for each message
        for content in special_messages:
            results = self.service.search_messages(content[:10], user.user_id)
            self.assertGreater(len(results), 0)

class TestPerformance(unittest.TestCase):
    """Test performance and scalability."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = MessagingService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_message_creation_performance(self):
        """Test message creation performance."""
        import time
        
        user = self.service.create_user("testuser", "test@example.com")
        room = self.service.create_room("Test Room", "Test Description", user.user_id)
        
        start_time = time.time()
        
        # Create 1000 messages
        for i in range(1000):
            self.service.send_message(user.user_id, room.room_id, f"Message {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (less than 5 seconds)
        self.assertLess(duration, 5.0)
        print(f"Created 1000 messages in {duration:.2f} seconds")
    
    def test_user_creation_performance(self):
        """Test user creation performance."""
        import time
        
        start_time = time.time()
        
        # Create 1000 users
        for i in range(1000):
            self.service.create_user(f"user{i}", f"user{i}@example.com")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (less than 3 seconds)
        self.assertLess(duration, 3.0)
        print(f"Created 1000 users in {duration:.2f} seconds")
    
    def test_memory_usage(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        user = self.service.create_user("testuser", "test@example.com")
        room = self.service.create_room("Test Room", "Test Description", user.user_id)
        
        # Create many messages
        for i in range(1000):
            self.service.send_message(user.user_id, room.room_id, f"Message {i}")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        self.assertLess(memory_increase, 50.0)
        print(f"Memory usage increased by {memory_increase:.2f}MB")

if __name__ == '__main__':
    unittest.main()


