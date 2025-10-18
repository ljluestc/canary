"""
Messaging System Implementation
Real-time messaging with group chats, file sharing, and notifications
"""

import time
import threading
import uuid
import json
import redis
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import hashlib
import base64
import os
from pathlib import Path

class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VIDEO = "video"
    AUDIO = "audio"
    LOCATION = "location"
    SYSTEM = "system"

class MessageStatus(Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class ChatType(Enum):
    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"

class UserStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"

@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    status: UserStatus = UserStatus.OFFLINE
    last_seen: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class Chat:
    """Chat data structure"""
    chat_id: str
    chat_type: ChatType
    name: str
    description: Optional[str] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    members: Set[str] = field(default_factory=set)
    admins: Set[str] = field(default_factory=set)
    is_active: bool = True
    last_message_time: Optional[datetime] = None
    last_message_id: Optional[str] = None

@dataclass
class Message:
    """Message data structure"""
    message_id: str
    chat_id: str
    sender_id: str
    message_type: MessageType
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    edited_at: Optional[datetime] = None
    reply_to: Optional[str] = None
    status: MessageStatus = MessageStatus.SENT
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)
    reactions: Dict[str, Set[str]] = field(default_factory=dict)  # emoji -> Set[user_ids]

@dataclass
class MessageRead:
    """Message read status data structure"""
    message_id: str
    user_id: str
    read_at: datetime = field(default_factory=datetime.now)

@dataclass
class Notification:
    """Notification data structure"""
    notification_id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class MessagingSystem:
    """Real-time messaging system"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Core data structures
        self.users = {}  # user_id -> User
        self.chats = {}  # chat_id -> Chat
        self.messages = {}  # message_id -> Message
        self.message_reads = {}  # message_id -> Set[user_id]
        self.notifications = {}  # notification_id -> Notification
        
        # Indexes for fast lookup
        self.user_chats = defaultdict(set)  # user_id -> Set[chat_id]
        self.chat_messages = defaultdict(list)  # chat_id -> List[message_id]
        self.user_notifications = defaultdict(list)  # user_id -> List[notification_id]
        self.user_status = {}  # user_id -> UserStatus
        
        # Real-time features
        self.online_users = set()  # Set of online user IDs
        self.user_connections = defaultdict(set)  # user_id -> Set[connection_id]
        self.typing_users = defaultdict(set)  # chat_id -> Set[user_id]
        
        # File storage
        self.file_storage_path = Path("uploads")
        self.file_storage_path.mkdir(exist_ok=True)
        
        # Threading
        self.lock = threading.RLock()
        self.notification_thread = threading.Thread(target=self._notification_loop, daemon=True)
        self.notification_thread.start()
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        # Configuration
        self.max_message_length = 4000
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.message_retention_days = 30
        self.typing_timeout = 10  # seconds
        self.notification_interval = 60  # seconds
        self.cleanup_interval = 3600  # 1 hour
    
    def create_user(self, user_id: str, username: str, email: str, 
                   display_name: str, avatar_url: Optional[str] = None) -> User:
        """Create a new user"""
        with self.lock:
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                display_name=display_name,
                avatar_url=avatar_url
            )
            
            self.users[user_id] = user
            self.user_status[user_id] = UserStatus.OFFLINE
            
            self._persist_user(user)
            return user
    
    def create_direct_chat(self, user1_id: str, user2_id: str) -> Chat:
        """Create a direct chat between two users"""
        with self.lock:
            # Check if direct chat already exists
            existing_chat = self._find_direct_chat(user1_id, user2_id)
            if existing_chat:
                return existing_chat
            
            chat_id = f"direct_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
            
            chat = Chat(
                chat_id=chat_id,
                chat_type=ChatType.DIRECT,
                name=f"Direct Chat",
                created_by=user1_id,
                members={user1_id, user2_id}
            )
            
            self.chats[chat_id] = chat
            self.user_chats[user1_id].add(chat_id)
            self.user_chats[user2_id].add(chat_id)
            
            self._persist_chat(chat)
            return chat
    
    def create_group_chat(self, name: str, description: str, created_by: str, 
                         member_ids: List[str]) -> Chat:
        """Create a group chat"""
        with self.lock:
            chat_id = str(uuid.uuid4())
            
            chat = Chat(
                chat_id=chat_id,
                chat_type=ChatType.GROUP,
                name=name,
                description=description,
                created_by=created_by,
                members=set(member_ids + [created_by]),
                admins={created_by}
            )
            
            self.chats[chat_id] = chat
            
            # Add to user chats
            for user_id in chat.members:
                self.user_chats[user_id].add(chat_id)
            
            self._persist_chat(chat)
            return chat
    
    def create_channel(self, name: str, description: str, created_by: str, 
                      member_ids: List[str]) -> Chat:
        """Create a channel"""
        with self.lock:
            chat_id = str(uuid.uuid4())
            
            chat = Chat(
                chat_id=chat_id,
                chat_type=ChatType.CHANNEL,
                name=name,
                description=description,
                created_by=created_by,
                members=set(member_ids + [created_by]),
                admins={created_by}
            )
            
            self.chats[chat_id] = chat
            
            # Add to user chats
            for user_id in chat.members:
                self.user_chats[user_id].add(chat_id)
            
            self._persist_chat(chat)
            return chat
    
    def send_message(self, chat_id: str, sender_id: str, content: str,
                    message_type: MessageType = MessageType.TEXT,
                    reply_to: Optional[str] = None,
                    attachments: List[str] = None) -> Message:
        """Send a message to a chat"""
        with self.lock:
            if chat_id not in self.chats:
                raise ValueError("Chat not found")
            
            chat = self.chats[chat_id]
            if sender_id not in chat.members:
                raise ValueError("User not a member of this chat")
            
            # Validate message content
            if not content and message_type == MessageType.TEXT:
                raise ValueError("Message content cannot be empty")
            
            if len(content) > self.max_message_length:
                raise ValueError("Message too long")
            
            # Create message
            message = Message(
                message_id=str(uuid.uuid4()),
                chat_id=chat_id,
                sender_id=sender_id,
                message_type=message_type,
                content=content,
                reply_to=reply_to,
                attachments=attachments or []
            )
            
            self.messages[message.message_id] = message
            self.chat_messages[chat_id].append(message.message_id)
            
            # Update chat last message
            chat.last_message_time = message.created_at
            chat.last_message_id = message.message_id
            
            # Create read status for sender
            self.message_reads[message.message_id] = {sender_id}
            
            # Send notifications to other members
            self._send_message_notifications(chat, message, sender_id)
            
            # Persist message
            self._persist_message(message)
            self._persist_chat(chat)
            
            return message
    
    def edit_message(self, message_id: str, user_id: str, new_content: str) -> bool:
        """Edit a message"""
        with self.lock:
            if message_id not in self.messages:
                return False
            
            message = self.messages[message_id]
            if message.sender_id != user_id:
                return False
            
            # Check if message is too old to edit (e.g., 15 minutes)
            if (datetime.now() - message.created_at).total_seconds() > 900:
                return False
            
            message.content = new_content
            message.edited_at = datetime.now()
            
            self._persist_message(message)
            return True
    
    def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message"""
        with self.lock:
            if message_id not in self.messages:
                return False
            
            message = self.messages[message_id]
            if message.sender_id != user_id:
                return False
            
            # Mark as deleted (soft delete)
            message.content = "[Message deleted]"
            message.metadata["deleted"] = True
            message.metadata["deleted_by"] = user_id
            message.metadata["deleted_at"] = datetime.now().isoformat()
            
            self._persist_message(message)
            return True
    
    def add_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """Add a reaction to a message"""
        with self.lock:
            if message_id not in self.messages:
                return False
            
            message = self.messages[message_id]
            if user_id not in self.chats[message.chat_id].members:
                return False
            
            if emoji not in message.reactions:
                message.reactions[emoji] = set()
            
            message.reactions[emoji].add(user_id)
            self._persist_message(message)
            return True
    
    def remove_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """Remove a reaction from a message"""
        with self.lock:
            if message_id not in self.messages:
                return False
            
            message = self.messages[message_id]
            if emoji in message.reactions:
                message.reactions[emoji].discard(user_id)
                if not message.reactions[emoji]:
                    del message.reactions[emoji]
            
            self._persist_message(message)
            return True
    
    def mark_message_as_read(self, message_id: str, user_id: str) -> bool:
        """Mark a message as read"""
        with self.lock:
            if message_id not in self.messages:
                return False
            
            message = self.messages[message_id]
            if user_id not in self.chats[message.chat_id].members:
                return False
            
            if message_id not in self.message_reads:
                self.message_reads[message_id] = set()
            
            self.message_reads[message_id].add(user_id)
            
            # Update message status if all members have read it
            chat = self.chats[message.chat_id]
            if len(self.message_reads[message_id]) == len(chat.members):
                message.status = MessageStatus.READ
            
            self._persist_message(message)
            return True
    
    def get_chat_messages(self, chat_id: str, user_id: str, limit: int = 50,
                         offset: int = 0) -> List[Message]:
        """Get messages from a chat"""
        with self.lock:
            if chat_id not in self.chats:
                return []
            
            chat = self.chats[chat_id]
            if user_id not in chat.members:
                return []
            
            message_ids = self.chat_messages[chat_id]
            messages = [self.messages[mid] for mid in message_ids if mid in self.messages]
            
            # Sort by creation time (newest first)
            messages.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply pagination
            start = offset
            end = offset + limit
            return messages[start:end]
    
    def get_user_chats(self, user_id: str) -> List[Chat]:
        """Get all chats for a user"""
        with self.lock:
            if user_id not in self.user_chats:
                return []
            
            chat_ids = self.user_chats[user_id]
            chats = [self.chats[cid] for cid in chat_ids if cid in self.chats]
            
            # Sort by last message time
            chats.sort(key=lambda x: x.last_message_time or x.created_at, reverse=True)
            
            return chats
    
    def search_messages(self, user_id: str, query: str, chat_id: Optional[str] = None,
                       limit: int = 50) -> List[Message]:
        """Search messages"""
        with self.lock:
            results = []
            query_lower = query.lower()
            
            # Get chats user has access to
            if chat_id:
                if chat_id in self.chats and user_id in self.chats[chat_id].members:
                    chat_ids = [chat_id]
                else:
                    return []
            else:
                chat_ids = list(self.user_chats[user_id])
            
            # Search in messages
            for cid in chat_ids:
                if cid in self.chat_messages:
                    for message_id in self.chat_messages[cid]:
                        if message_id in self.messages:
                            message = self.messages[message_id]
                            if query_lower in message.content.lower():
                                results.append(message)
            
            # Sort by creation time
            results.sort(key=lambda x: x.created_at, reverse=True)
            return results[:limit]
    
    def set_user_status(self, user_id: str, status: UserStatus) -> bool:
        """Set user status"""
        with self.lock:
            if user_id not in self.users:
                return False
            
            self.user_status[user_id] = status
            self.users[user_id].status = status
            self.users[user_id].last_seen = datetime.now()
            
            if status == UserStatus.ONLINE:
                self.online_users.add(user_id)
            else:
                self.online_users.discard(user_id)
            
            self._persist_user(self.users[user_id])
            return True
    
    def start_typing(self, chat_id: str, user_id: str) -> bool:
        """Start typing indicator"""
        with self.lock:
            if chat_id not in self.chats or user_id not in self.chats[chat_id].members:
                return False
            
            self.typing_users[chat_id].add(user_id)
            return True
    
    def stop_typing(self, chat_id: str, user_id: str) -> bool:
        """Stop typing indicator"""
        with self.lock:
            if chat_id in self.typing_users:
                self.typing_users[chat_id].discard(user_id)
            return True
    
    def get_typing_users(self, chat_id: str) -> List[str]:
        """Get users currently typing in a chat"""
        with self.lock:
            return list(self.typing_users.get(chat_id, set()))
    
    def upload_file(self, user_id: str, file_data: bytes, filename: str,
                   content_type: str) -> str:
        """Upload a file"""
        if len(file_data) > self.max_file_size:
            raise ValueError("File too large")
        
        # Generate unique filename
        file_hash = hashlib.md5(file_data).hexdigest()
        file_extension = Path(filename).suffix
        unique_filename = f"{file_hash}{file_extension}"
        
        # Save file
        file_path = self.file_storage_path / unique_filename
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return str(file_path)
    
    def create_notification(self, user_id: str, title: str, message: str,
                          notification_type: str, metadata: Dict[str, Any] = None) -> Notification:
        """Create a notification"""
        with self.lock:
            notification = Notification(
                notification_id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                metadata=metadata or {}
            )
            
            self.notifications[notification.notification_id] = notification
            self.user_notifications[user_id].append(notification.notification_id)
            
            self._persist_notification(notification)
            return notification
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Notification]:
        """Get notifications for a user"""
        with self.lock:
            if user_id not in self.user_notifications:
                return []
            
            notification_ids = self.user_notifications[user_id]
            notifications = [self.notifications[nid] for nid in notification_ids if nid in self.notifications]
            
            # Sort by creation time (newest first)
            notifications.sort(key=lambda x: x.created_at, reverse=True)
            
            return notifications[:limit]
    
    def mark_notification_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        with self.lock:
            if notification_id not in self.notifications:
                return False
            
            notification = self.notifications[notification_id]
            if notification.user_id != user_id:
                return False
            
            notification.is_read = True
            self._persist_notification(notification)
            return True
    
    def _find_direct_chat(self, user1_id: str, user2_id: str) -> Optional[Chat]:
        """Find existing direct chat between two users"""
        for chat in self.chats.values():
            if (chat.chat_type == ChatType.DIRECT and 
                user1_id in chat.members and 
                user2_id in chat.members):
                return chat
        return None
    
    def _send_message_notifications(self, chat: Chat, message: Message, sender_id: str):
        """Send notifications for a new message"""
        for user_id in chat.members:
            if user_id != sender_id:
                # Create notification
                notification = self.create_notification(
                    user_id=user_id,
                    title=f"New message in {chat.name}",
                    message=message.content[:100] + "..." if len(message.content) > 100 else message.content,
                    notification_type="message",
                    metadata={
                        "chat_id": chat.chat_id,
                        "message_id": message.message_id,
                        "sender_id": sender_id
                    }
                )
    
    def _notification_loop(self):
        """Notification processing loop"""
        while True:
            try:
                time.sleep(self.notification_interval)
                
                with self.lock:
                    # Clean up old notifications
                    self._cleanup_old_notifications()
                
            except Exception as e:
                print(f"Error in notification loop: {e}")
    
    def _cleanup_loop(self):
        """Cleanup loop"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                
                with self.lock:
                    # Clean up old messages
                    self._cleanup_old_messages()
                    
                    # Clean up old typing indicators
                    self._cleanup_typing_indicators()
                
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
    
    def _cleanup_old_notifications(self):
        """Clean up old notifications"""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        old_notifications = [
            nid for nid, notification in self.notifications.items()
            if notification.created_at < cutoff_time
        ]
        
        for nid in old_notifications:
            notification = self.notifications[nid]
            if notification.user_id in self.user_notifications:
                self.user_notifications[notification.user_id].remove(nid)
            del self.notifications[nid]
    
    def _cleanup_old_messages(self):
        """Clean up old messages"""
        cutoff_time = datetime.now() - timedelta(days=self.message_retention_days)
        
        old_messages = [
            mid for mid, message in self.messages.items()
            if message.created_at < cutoff_time
        ]
        
        for mid in old_messages:
            message = self.messages[mid]
            if message.chat_id in self.chat_messages:
                self.chat_messages[message.chat_id].remove(mid)
            del self.messages[mid]
    
    def _cleanup_typing_indicators(self):
        """Clean up old typing indicators"""
        current_time = time.time()
        
        for chat_id in list(self.typing_users.keys()):
            # Remove typing indicators older than timeout
            self.typing_users[chat_id] = {
                user_id for user_id in self.typing_users[chat_id]
                # In a real implementation, you'd track when typing started
            }
    
    def _persist_user(self, user: User):
        """Persist user to Redis"""
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url or "",
            "status": user.status.value,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
            "created_at": user.created_at.isoformat(),
            "is_active": str(user.is_active)
        }
        self.redis_client.hset(f"user:{user.user_id}", mapping=user_data)
    
    def _persist_chat(self, chat: Chat):
        """Persist chat to Redis"""
        chat_data = {
            "chat_id": chat.chat_id,
            "chat_type": chat.chat_type.value,
            "name": chat.name,
            "description": chat.description or "",
            "created_by": chat.created_by,
            "created_at": chat.created_at.isoformat(),
            "members": json.dumps(list(chat.members)),
            "admins": json.dumps(list(chat.admins)),
            "is_active": str(chat.is_active),
            "last_message_time": chat.last_message_time.isoformat() if chat.last_message_time else None,
            "last_message_id": chat.last_message_id or ""
        }
        self.redis_client.hset(f"chat:{chat.chat_id}", mapping=chat_data)
    
    def _persist_message(self, message: Message):
        """Persist message to Redis"""
        message_data = {
            "message_id": message.message_id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "message_type": message.message_type.value,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "edited_at": message.edited_at.isoformat() if message.edited_at else None,
            "reply_to": message.reply_to or "",
            "status": message.status.value,
            "metadata": json.dumps(message.metadata),
            "attachments": json.dumps(message.attachments),
            "reactions": json.dumps({k: list(v) for k, v in message.reactions.items()})
        }
        self.redis_client.hset(f"message:{message.message_id}", mapping=message_data)
    
    def _persist_notification(self, notification: Notification):
        """Persist notification to Redis"""
        notification_data = {
            "notification_id": notification.notification_id,
            "user_id": notification.user_id,
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "created_at": notification.created_at.isoformat(),
            "is_read": str(notification.is_read),
            "metadata": json.dumps(notification.metadata)
        }
        self.redis_client.hset(f"notification:{notification.notification_id}", mapping=notification_data)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        with self.lock:
            return {
                "total_users": len(self.users),
                "total_chats": len(self.chats),
                "total_messages": len(self.messages),
                "total_notifications": len(self.notifications),
                "online_users": len(self.online_users),
                "direct_chats": len([c for c in self.chats.values() if c.chat_type == ChatType.DIRECT]),
                "group_chats": len([c for c in self.chats.values() if c.chat_type == ChatType.GROUP]),
                "channels": len([c for c in self.chats.values() if c.chat_type == ChatType.CHANNEL]),
                "typing_users": sum(len(users) for users in self.typing_users.values()),
                "average_messages_per_chat": len(self.messages) / max(len(self.chats), 1)
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize messaging system
    messaging = MessagingSystem()
    
    # Create users
    user1 = messaging.create_user("user1", "alice", "alice@example.com", "Alice")
    user2 = messaging.create_user("user2", "bob", "bob@example.com", "Bob")
    user3 = messaging.create_user("user3", "charlie", "charlie@example.com", "Charlie")
    
    # Set users online
    messaging.set_user_status("user1", UserStatus.ONLINE)
    messaging.set_user_status("user2", UserStatus.ONLINE)
    
    # Create direct chat
    direct_chat = messaging.create_direct_chat("user1", "user2")
    
    # Create group chat
    group_chat = messaging.create_group_chat("Project Team", "Team chat for project", "user1", ["user2", "user3"])
    
    # Send messages
    message1 = messaging.send_message(direct_chat.chat_id, "user1", "Hello Bob!")
    message2 = messaging.send_message(direct_chat.chat_id, "user2", "Hi Alice!")
    message3 = messaging.send_message(group_chat.chat_id, "user1", "Welcome to the team chat!")
    
    # Add reactions
    messaging.add_reaction(message1.message_id, "user2", "👍")
    messaging.add_reaction(message2.message_id, "user1", "😊")
    
    # Mark messages as read
    messaging.mark_message_as_read(message1.message_id, "user2")
    messaging.mark_message_as_read(message2.message_id, "user1")
    
    # Get chat messages
    direct_messages = messaging.get_chat_messages(direct_chat.chat_id, "user1")
    print(f"Direct chat messages: {len(direct_messages)}")
    
    # Get user chats
    user1_chats = messaging.get_user_chats("user1")
    print(f"User1 chats: {len(user1_chats)}")
    
    # Search messages
    search_results = messaging.search_messages("user1", "Hello")
    print(f"Search results: {len(search_results)}")
    
    # Get system stats
    stats = messaging.get_system_stats()
    print(f"System stats: {stats}")
