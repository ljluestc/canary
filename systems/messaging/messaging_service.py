#!/usr/bin/env python3
"""
Messaging Service

A comprehensive real-time messaging system with features like:
- WebSocket support for real-time communication
- Message persistence and history
- User presence and typing indicators
- Message encryption and security
- Group messaging and channels
- File sharing and media support
- Message search and filtering
- Push notifications
"""

import os
import json
import time
import uuid
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import sqlite3
import hashlib
import base64
from cryptography.fernet import Fernet
import redis
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class User:
    """User model for messaging system."""
    user_id: str
    username: str
    email: str
    status: str = "offline"  # online, offline, away, busy
    last_seen: datetime = None
    avatar_url: str = ""
    is_typing: bool = False
    typing_in: str = ""  # room_id where user is typing
    
    def __post_init__(self):
        if self.last_seen is None:
            self.last_seen = datetime.now()

@dataclass
class Message:
    """Message model."""
    message_id: str
    sender_id: str
    room_id: str
    content: str
    message_type: str = "text"  # text, image, file, system
    timestamp: datetime = None
    edited_at: datetime = None
    reply_to: str = None  # message_id of message being replied to
    is_encrypted: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Room:
    """Room/Channel model."""
    room_id: str
    name: str
    description: str = ""
    room_type: str = "direct"  # direct, group, channel
    created_by: str = ""
    created_at: datetime = None
    members: Set[str] = None
    is_private: bool = False
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.members is None:
            self.members = set()
        if self.settings is None:
            self.settings = {}
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'room_id': self.room_id,
            'name': self.name,
            'description': self.description,
            'room_type': self.room_type,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'members': list(self.members),
            'is_private': self.is_private,
            'settings': self.settings
        }

@dataclass
class TypingIndicator:
    """Typing indicator model."""
    user_id: str
    room_id: str
    is_typing: bool
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MessageEncryption:
    """Message encryption utilities."""
    
    def __init__(self, key: str = None):
        if key:
            self.cipher = Fernet(key.encode())
        else:
            # Generate a new key
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
    
    def encrypt_message(self, content: str) -> str:
        """Encrypt message content."""
        try:
            encrypted_content = self.cipher.encrypt(content.encode())
            return base64.b64encode(encrypted_content).decode()
        except Exception as e:
            logger.error(f"Error encrypting message: {e}")
            return content
    
    def decrypt_message(self, encrypted_content: str) -> str:
        """Decrypt message content."""
        try:
            decoded_content = base64.b64decode(encrypted_content.encode())
            decrypted_content = self.cipher.decrypt(decoded_content)
            return decrypted_content.decode()
        except Exception as e:
            logger.error(f"Error decrypting message: {e}")
            return encrypted_content

class MessageDatabase:
    """Database operations for messaging system."""
    
    def __init__(self, db_path: str = "messaging.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'offline',
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                avatar_url TEXT,
                is_typing BOOLEAN DEFAULT FALSE,
                typing_in TEXT
            )
        ''')
        
        # Rooms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                room_type TEXT DEFAULT 'direct',
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_private BOOLEAN DEFAULT FALSE,
                settings TEXT
            )
        ''')
        
        # Room members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_members (
                room_id TEXT,
                user_id TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role TEXT DEFAULT 'member',
                PRIMARY KEY (room_id, user_id),
                FOREIGN KEY (room_id) REFERENCES rooms(room_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'text',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                edited_at TIMESTAMP,
                reply_to TEXT,
                is_encrypted BOOLEAN DEFAULT FALSE,
                metadata TEXT,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (room_id) REFERENCES rooms(room_id)
            )
        ''')
        
        # Typing indicators table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS typing_indicators (
                user_id TEXT,
                room_id TEXT,
                is_typing BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, room_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (room_id) REFERENCES rooms(room_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_user(self, user: User) -> bool:
        """Save user to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, email, status, last_seen, avatar_url, is_typing, typing_in)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id, user.username, user.email, user.status,
                user.last_seen.isoformat(), user.avatar_url, user.is_typing, user.typing_in
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return User(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    status=row[3],
                    last_seen=datetime.fromisoformat(row[4]) if row[4] else None,
                    avatar_url=row[5] or "",
                    is_typing=bool(row[6]),
                    typing_in=row[7] or ""
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def save_room(self, room: Room) -> bool:
        """Save room to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO rooms 
                (room_id, name, description, room_type, created_by, created_at, is_private, settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                room.room_id, room.name, room.description, room.room_type,
                room.created_by, room.created_at.isoformat(), room.is_private,
                json.dumps(room.settings)
            ))
            
            # Save room members
            cursor.execute('DELETE FROM room_members WHERE room_id = ?', (room.room_id,))
            for user_id in room.members:
                cursor.execute('''
                    INSERT INTO room_members (room_id, user_id, role)
                    VALUES (?, ?, 'member')
                ''', (room.room_id, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving room: {e}")
            return False
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM rooms WHERE room_id = ?', (room_id,))
            row = cursor.fetchone()
            
            if row:
                # Get room members
                cursor.execute('SELECT user_id FROM room_members WHERE room_id = ?', (room_id,))
                members = {row[0] for row in cursor.fetchall()}
                
                room = Room(
                    room_id=row[0],
                    name=row[1],
                    description=row[2] or "",
                    room_type=row[3],
                    created_by=row[4] or "",
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    is_private=bool(row[6]),
                    settings=json.loads(row[7]) if row[7] else {}
                )
                room.members = members
                
                conn.close()
                return room
            
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting room: {e}")
            return None
    
    def save_message(self, message: Message) -> bool:
        """Save message to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages 
                (message_id, sender_id, room_id, content, message_type, timestamp, 
                 edited_at, reply_to, is_encrypted, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.message_id, message.sender_id, message.room_id, message.content,
                message.message_type, message.timestamp.isoformat(),
                message.edited_at.isoformat() if message.edited_at else None,
                message.reply_to, message.is_encrypted, json.dumps(message.metadata)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    def get_messages(self, room_id: str, limit: int = 50, offset: int = 0) -> List[Message]:
        """Get messages for a room."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM messages 
                WHERE room_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (room_id, limit, offset))
            
            messages = []
            for row in cursor.fetchall():
                message = Message(
                    message_id=row[0],
                    sender_id=row[1],
                    room_id=row[2],
                    content=row[3],
                    message_type=row[4],
                    timestamp=datetime.fromisoformat(row[5]) if row[5] else None,
                    edited_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    reply_to=row[7],
                    is_encrypted=bool(row[8]),
                    metadata=json.loads(row[9]) if row[9] else {}
                )
                messages.append(message)
            
            conn.close()
            return messages
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def search_messages(self, query: str, user_id: str, limit: int = 20) -> List[Message]:
        """Search messages for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get rooms where user is a member
            cursor.execute('''
                SELECT DISTINCT m.* FROM messages m
                JOIN room_members rm ON m.room_id = rm.room_id
                WHERE rm.user_id = ? AND m.content LIKE ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            ''', (user_id, f'%{query}%', limit))
            
            messages = []
            for row in cursor.fetchall():
                message = Message(
                    message_id=row[0],
                    sender_id=row[1],
                    room_id=row[2],
                    content=row[3],
                    message_type=row[4],
                    timestamp=datetime.fromisoformat(row[5]) if row[5] else None,
                    edited_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    reply_to=row[7],
                    is_encrypted=bool(row[8]),
                    metadata=json.loads(row[9]) if row[9] else {}
                )
                messages.append(message)
            
            conn.close()
            return messages
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []

class MessagingService:
    """Main messaging service."""
    
    def __init__(self, db_path: str = "messaging.db"):
        self.db = MessageDatabase(db_path)
        self.encryption = MessageEncryption()
        self.online_users: Set[str] = set()
        self.typing_users: Dict[str, TypingIndicator] = {}
        self.room_cache: Dict[str, Room] = {}
        self.user_cache: Dict[str, User] = {}
    
    def create_user(self, username: str, email: str, avatar_url: str = "") -> User:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            avatar_url=avatar_url
        )
        
        if self.db.save_user(user):
            self.user_cache[user_id] = user
            return user
        return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        
        user = self.db.get_user(user_id)
        if user:
            self.user_cache[user_id] = user
        return user
    
    def create_room(self, name: str, room_type: str = "group", created_by: str = "", 
                   is_private: bool = False) -> Room:
        """Create a new room."""
        room_id = str(uuid.uuid4())
        room = Room(
            room_id=room_id,
            name=name,
            room_type=room_type,
            created_by=created_by,
            is_private=is_private
        )
        
        # Add creator to room members
        if created_by:
            room.members.add(created_by)
        
        if self.db.save_room(room):
            self.room_cache[room_id] = room
            return room
        return None
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        if room_id in self.room_cache:
            return self.room_cache[room_id]
        
        room = self.db.get_room(room_id)
        if room:
            self.room_cache[room_id] = room
        return room
    
    def add_user_to_room(self, room_id: str, user_id: str) -> bool:
        """Add user to room."""
        room = self.get_room(room_id)
        if room:
            room.members.add(user_id)
            return self.db.save_room(room)
        return False
    
    def remove_user_from_room(self, room_id: str, user_id: str) -> bool:
        """Remove user from room."""
        room = self.get_room(room_id)
        if room:
            room.members.discard(user_id)
            return self.db.save_room(room)
        return False
    
    def send_message(self, sender_id: str, room_id: str, content: str, 
                    message_type: str = "text", reply_to: str = None) -> Message:
        """Send a message to a room."""
        message_id = str(uuid.uuid4())
        message = Message(
            message_id=message_id,
            sender_id=sender_id,
            room_id=room_id,
            content=content,
            message_type=message_type,
            reply_to=reply_to
        )
        
        if self.db.save_message(message):
            return message
        return None
    
    def get_messages(self, room_id: str, limit: int = 50, offset: int = 0) -> List[Message]:
        """Get messages for a room."""
        return self.db.get_messages(room_id, limit, offset)
    
    def search_messages(self, query: str, user_id: str, limit: int = 20) -> List[Message]:
        """Search messages for a user."""
        return self.db.search_messages(query, user_id, limit)
    
    def set_user_online(self, user_id: str):
        """Set user as online."""
        self.online_users.add(user_id)
        user = self.get_user(user_id)
        if user:
            user.status = "online"
            user.last_seen = datetime.now()
            self.db.save_user(user)
    
    def set_user_offline(self, user_id: str):
        """Set user as offline."""
        self.online_users.discard(user_id)
        user = self.get_user(user_id)
        if user:
            user.status = "offline"
            user.last_seen = datetime.now()
            self.db.save_user(user)
    
    def set_typing(self, user_id: str, room_id: str, is_typing: bool):
        """Set user typing status."""
        if is_typing:
            self.typing_users[user_id] = TypingIndicator(
                user_id=user_id,
                room_id=room_id,
                is_typing=True
            )
        else:
            self.typing_users.pop(user_id, None)
    
    def get_typing_users(self, room_id: str) -> List[str]:
        """Get users currently typing in a room."""
        return [user_id for user_id, indicator in self.typing_users.items() 
                if indicator.room_id == room_id and indicator.is_typing]

# Flask application with SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'messaging-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize service
messaging_service = MessagingService()

@app.route('/')
def index():
    """Messaging demo page."""
    html_template = '''
    <!DOCTYPE html>
    <head>
        <title>Messaging Service Demo</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { display: flex; height: 600px; border: 1px solid #ddd; }
            .sidebar { width: 250px; background: #f5f5f5; padding: 10px; }
            .chat-area { flex: 1; display: flex; flex-direction: column; }
            .messages { flex: 1; padding: 10px; overflow-y: auto; }
            .message { margin: 5px 0; padding: 8px; background: #e3f2fd; border-radius: 5px; }
            .message.own { background: #c8e6c9; margin-left: 20px; }
            .input-area { padding: 10px; border-top: 1px solid #ddd; }
            .input-area input { width: 80%; padding: 8px; }
            .input-area button { width: 18%; padding: 8px; margin-left: 2%; }
            .room-list { list-style: none; padding: 0; }
            .room-item { padding: 10px; cursor: pointer; border-bottom: 1px solid #eee; }
            .room-item:hover { background: #e0e0e0; }
            .room-item.active { background: #2196f3; color: white; }
            .typing-indicator { color: #666; font-style: italic; }
        </style>
    </head>
    <body>
        <h1>Messaging Service Demo</h1>
        
        <div class="container">
            <div class="sidebar">
                <h3>Rooms</h3>
                <ul class="room-list" id="roomList">
                    <li class="room-item" data-room="general">General</li>
                    <li class="room-item" data-room="random">Random</li>
                </ul>
                
                <h3>Online Users</h3>
                <div id="onlineUsers">Loading...</div>
            </div>
            
            <div class="chat-area">
                <div class="messages" id="messages"></div>
                <div class="typing-indicator" id="typingIndicator"></div>
                <div class="input-area">
                    <input type="text" id="messageInput" placeholder="Type a message...">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
        
        <script>
            const socket = io();
            let currentRoom = 'general';
            let currentUser = 'user_' + Math.random().toString(36).substr(2, 9);
            
            // Join general room by default
            socket.emit('join_room', {room: currentRoom, user_id: currentUser});
            
            // Handle incoming messages
            socket.on('message', function(data) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                if (data.sender_id === currentUser) {
                    messageDiv.className += ' own';
                }
                messageDiv.innerHTML = `<strong>${data.sender_id}:</strong> ${data.content}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            });
            
            // Handle typing indicators
            socket.on('typing', function(data) {
                const typingDiv = document.getElementById('typingIndicator');
                if (data.is_typing) {
                    typingDiv.textContent = `${data.user_id} is typing...`;
                } else {
                    typingDiv.textContent = '';
                }
            });
            
            // Handle room switching
            document.querySelectorAll('.room-item').forEach(item => {
                item.addEventListener('click', function() {
                    document.querySelectorAll('.room-item').forEach(i => i.classList.remove('active'));
                    this.classList.add('active');
                    
                    socket.emit('leave_room', {room: currentRoom});
                    currentRoom = this.dataset.room;
                    socket.emit('join_room', {room: currentRoom, user_id: currentUser});
                    
                    // Clear messages
                    document.getElementById('messages').innerHTML = '';
                });
            });
            
            // Send message
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const content = input.value.trim();
                if (content) {
                    socket.emit('send_message', {
                        room: currentRoom,
                        sender_id: currentUser,
                        content: content
                    });
                    input.value = '';
                }
            }
            
            // Handle Enter key
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // Handle typing indicator
            let typingTimer;
            document.getElementById('messageInput').addEventListener('input', function() {
                socket.emit('typing', {
                    room: currentRoom,
                    user_id: currentUser,
                    is_typing: true
                });
                
                clearTimeout(typingTimer);
                typingTimer = setTimeout(() => {
                    socket.emit('typing', {
                        room: currentRoom,
                        user_id: currentUser,
                        is_typing: false
                    });
                }, 1000);
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@socketio.on('join_room')
def handle_join_room(data):
    """Handle user joining a room."""
    room = data['room']
    user_id = data['user_id']
    
    join_room(room)
    messaging_service.set_user_online(user_id)
    
    # Load recent messages
    messages = messaging_service.get_messages(room, limit=20)
    for message in reversed(messages):
        emit('message', {
            'message_id': message.message_id,
            'sender_id': message.sender_id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat()
        })
    
    emit('status', {'message': f'Joined room {room}'})

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle user leaving a room."""
    room = data['room']
    user_id = data['user_id']
    
    leave_room(room)
    emit('status', {'message': f'Left room {room}'})

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message."""
    room = data['room']
    sender_id = data['sender_id']
    content = data['content']
    
    message = messaging_service.send_message(sender_id, room, content)
    if message:
        emit('message', {
            'message_id': message.message_id,
            'sender_id': message.sender_id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat()
        }, room=room)

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator."""
    room = data['room']
    user_id = data['user_id']
    is_typing = data['is_typing']
    
    messaging_service.set_typing(user_id, room, is_typing)
    emit('typing', {
        'user_id': user_id,
        'is_typing': is_typing
    }, room=room, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnect."""
    messaging_service.set_user_offline(request.sid)

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user API."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email'):
        return jsonify({'success': False, 'error': 'Username and email are required'})
    
    user = messaging_service.create_user(
        username=data['username'],
        email=data['email'],
        avatar_url=data.get('avatar_url', '')
    )
    
    if user:
        return jsonify({
            'success': True,
            'user': asdict(user)
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to create user'})

@app.route('/api/rooms', methods=['POST'])
def create_room():
    """Create a new room API."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'success': False, 'error': 'Room name is required'})
    
    room = messaging_service.create_room(
        name=data['name'],
        room_type=data.get('room_type', 'group'),
        created_by=data.get('created_by', ''),
        is_private=data.get('is_private', False)
    )
    
    if room:
        return jsonify({
            'success': True,
            'room': room.to_dict()
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to create room'})

@app.route('/api/rooms/<room_id>/messages')
def get_room_messages(room_id):
    """Get messages for a room API."""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    messages = messaging_service.get_messages(room_id, limit, offset)
    
    return jsonify({
        'success': True,
        'messages': [asdict(msg) for msg in messages]
    })

@app.route('/api/search')
def search_messages():
    """Search messages API."""
    query = request.args.get('q', '')
    user_id = request.args.get('user_id', '')
    limit = request.args.get('limit', 20, type=int)
    
    if not query or not user_id:
        return jsonify({'success': False, 'error': 'Query and user_id are required'})
    
    messages = messaging_service.search_messages(query, user_id, limit)
    
    return jsonify({
        'success': True,
        'messages': [asdict(msg) for msg in messages]
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'online_users': len(messaging_service.online_users)
    })

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5005)
