#!/usr/bin/env python3
"""
Google Docs-like Collaborative Document System

This system provides:
- Real-time collaborative document editing
- Version control and change tracking
- User permissions and access control
- Document sharing and commenting
- Rich text editing with formatting
- Document templates and organization
- Conflict resolution for simultaneous edits
"""

import json
import sqlite3
import uuid
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
from collections import defaultdict
import difflib
import re


@dataclass
class Document:
    """Represents a collaborative document."""
    id: str
    title: str
    content: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    version: int
    permissions: Dict[str, str]  # user_id -> permission level
    collaborators: List[str]
    is_public: bool
    tags: List[str]
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.permissions is None:
            self.permissions = {}
        if self.collaborators is None:
            self.collaborators = []
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version,
            'permissions': self.permissions,
            'collaborators': self.collaborators,
            'is_public': self.is_public,
            'tags': self.tags,
            'metadata': self.metadata
        }


@dataclass
class User:
    """Represents a user in the system."""
    id: str
    username: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    created_at: datetime = None
    last_active: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat()
        }


@dataclass
class DocumentChange:
    """Represents a change to a document."""
    id: str
    document_id: str
    user_id: str
    change_type: str  # 'insert', 'delete', 'format'
    position: int
    content: str
    timestamp: datetime
    version: int

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'change_type': self.change_type,
            'position': self.position,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version
        }


@dataclass
class Comment:
    """Represents a comment on a document."""
    id: str
    document_id: str
    user_id: str
    content: str
    position: int
    created_at: datetime
    resolved: bool = False
    replies: List[str] = None

    def __post_init__(self):
        if self.replies is None:
            self.replies = []

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'content': self.content,
            'position': self.position,
            'created_at': self.created_at.isoformat(),
            'resolved': self.resolved,
            'replies': self.replies
        }


class DocumentDatabase:
    """Database operations for document system."""

    def __init__(self, db_path: str = "google_docs.db"):
        """Initialize database."""
        self.db_path = db_path
        self.init_database()

    def init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    avatar_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    permissions TEXT,
                    collaborators TEXT,
                    is_public BOOLEAN DEFAULT 0,
                    tags TEXT,
                    metadata TEXT,
                    FOREIGN KEY (owner_id) REFERENCES users (id)
                )
            ''')
            
            # Document changes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_changes (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Comments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT 0,
                    replies TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()

    def save_user(self, user: User) -> bool:
        """Save user to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (id, username, email, display_name, avatar_url, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.id, user.username, user.email, user.display_name,
                    user.avatar_url, user.created_at.isoformat(),
                    user.last_active.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving user: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, email, display_name, avatar_url, created_at, last_active
                    FROM users WHERE id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return User(
                        id=row[0], username=row[1], email=row[2],
                        display_name=row[3], avatar_url=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        last_active=datetime.fromisoformat(row[6])
                    )
                return None
        except Exception as e:
            logging.error(f"Error getting user: {e}")
            return None

    def save_document(self, document: Document) -> bool:
        """Save document to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO documents 
                    (id, title, content, owner_id, created_at, updated_at, version,
                     permissions, collaborators, is_public, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document.id, document.title, document.content, document.owner_id,
                    document.created_at.isoformat(), document.updated_at.isoformat(),
                    document.version, json.dumps(document.permissions),
                    json.dumps(document.collaborators), document.is_public,
                    json.dumps(document.tags), json.dumps(document.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving document: {e}")
            return False

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, content, owner_id, created_at, updated_at, version,
                           permissions, collaborators, is_public, tags, metadata
                    FROM documents WHERE id = ?
                ''', (document_id,))
                
                row = cursor.fetchone()
                if row:
                    return Document(
                        id=row[0], title=row[1], content=row[2], owner_id=row[3],
                        created_at=datetime.fromisoformat(row[4]),
                        updated_at=datetime.fromisoformat(row[5]),
                        version=row[6], permissions=json.loads(row[7]) if row[7] else {},
                        collaborators=json.loads(row[8]) if row[8] else [],
                        is_public=bool(row[9]), tags=json.loads(row[10]) if row[10] else [],
                        metadata=json.loads(row[11]) if row[11] else {}
                    )
                return None
        except Exception as e:
            logging.error(f"Error getting document: {e}")
            return None

    def get_user_documents(self, user_id: str) -> List[Document]:
        """Get documents for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, content, owner_id, created_at, updated_at, version,
                           permissions, collaborators, is_public, tags, metadata
                    FROM documents 
                    WHERE owner_id = ? OR ? IN (SELECT value FROM json_each(collaborators))
                    ORDER BY updated_at DESC
                ''', (user_id, user_id))
                
                rows = cursor.fetchall()
                documents = []
                for row in rows:
                    documents.append(Document(
                        id=row[0], title=row[1], content=row[2], owner_id=row[3],
                        created_at=datetime.fromisoformat(row[4]),
                        updated_at=datetime.fromisoformat(row[5]),
                        version=row[6], permissions=json.loads(row[7]) if row[7] else {},
                        collaborators=json.loads(row[8]) if row[8] else [],
                        is_public=bool(row[9]), tags=json.loads(row[10]) if row[10] else [],
                        metadata=json.loads(row[11]) if row[11] else {}
                    ))
                
                return documents
        except Exception as e:
            logging.error(f"Error getting user documents: {e}")
            return []

    def save_change(self, change: DocumentChange) -> bool:
        """Save document change."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO document_changes 
                    (id, document_id, user_id, change_type, position, content, timestamp, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    change.id, change.document_id, change.user_id, change.change_type,
                    change.position, change.content, change.timestamp.isoformat(),
                    change.version
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving change: {e}")
            return False

    def get_document_changes(self, document_id: str, from_version: int = 0) -> List[DocumentChange]:
        """Get document changes from a specific version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, document_id, user_id, change_type, position, content, timestamp, version
                    FROM document_changes 
                    WHERE document_id = ? AND version > ?
                    ORDER BY version, timestamp
                ''', (document_id, from_version))
                
                rows = cursor.fetchall()
                changes = []
                for row in rows:
                    changes.append(DocumentChange(
                        id=row[0], document_id=row[1], user_id=row[2],
                        change_type=row[3], position=row[4], content=row[5],
                        timestamp=datetime.fromisoformat(row[6]), version=row[7]
                    ))
                
                return changes
        except Exception as e:
            logging.error(f"Error getting document changes: {e}")
            return []

    def save_comment(self, comment: Comment) -> bool:
        """Save comment."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO comments 
                    (id, document_id, user_id, content, position, created_at, resolved, replies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    comment.id, comment.document_id, comment.user_id,
                    comment.content, comment.position, comment.created_at.isoformat(),
                    comment.resolved, json.dumps(comment.replies)
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving comment: {e}")
            return False

    def get_document_comments(self, document_id: str) -> List[Comment]:
        """Get comments for a document."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, document_id, user_id, content, position, created_at, resolved, replies
                    FROM comments 
                    WHERE document_id = ? AND resolved = 0
                    ORDER BY created_at
                ''', (document_id,))
                
                rows = cursor.fetchall()
                comments = []
                for row in rows:
                    comments.append(Comment(
                        id=row[0], document_id=row[1], user_id=row[2],
                        content=row[3], position=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        resolved=bool(row[6]), replies=json.loads(row[7]) if row[7] else []
                    ))
                
                return comments
        except Exception as e:
            logging.error(f"Error getting comments: {e}")
            return []


class CollaborativeEditor:
    """Handles real-time collaborative editing."""

    def __init__(self, db: DocumentDatabase):
        """Initialize editor."""
        self.db = db
        self.active_users: Dict[str, List[str]] = defaultdict(list)  # document_id -> [user_ids]
        self.user_cursors: Dict[str, Dict[str, int]] = defaultdict(dict)  # document_id -> {user_id: position}
        self.lock = threading.Lock()

    def apply_change(self, document_id: str, user_id: str, change: Dict) -> Tuple[bool, str]:
        """Apply a change to a document."""
        with self.lock:
            document = self.db.get_document(document_id)
            if not document:
                return False, "Document not found"

            # Check permissions
            if not self._has_permission(document, user_id, 'edit'):
                return False, "No edit permission"

            # Apply change to content
            new_content = self._apply_change_to_content(document.content, change)
            
            # Create change record
            change_record = DocumentChange(
                id=str(uuid.uuid4()),
                document_id=document_id,
                user_id=user_id,
                change_type=change['type'],
                position=change['position'],
                content=change['content'],
                timestamp=datetime.now(),
                version=document.version + 1
            )

            # Update document
            document.content = new_content
            document.version += 1
            document.updated_at = datetime.now()

            # Save to database
            if self.db.save_document(document) and self.db.save_change(change_record):
                return True, "Change applied successfully"
            else:
                return False, "Failed to save change"

    def _apply_change_to_content(self, content: str, change: Dict) -> str:
        """Apply a change to document content."""
        position = change['position']
        change_type = change['type']
        change_content = change['content']

        if change_type == 'insert':
            return content[:position] + change_content + content[position:]
        elif change_type == 'delete':
            end_position = position + len(change_content)
            return content[:position] + content[end_position:]
        elif change_type == 'replace':
            end_position = position + len(change_content)
            return content[:position] + change_content + content[end_position:]
        
        return content

    def _has_permission(self, document: Document, user_id: str, permission: str) -> bool:
        """Check if user has permission for document."""
        if document.owner_id == user_id:
            return True
        
        if document.is_public and permission == 'read':
            return True
        
        user_permission = document.permissions.get(user_id, 'none')
        
        if permission == 'read':
            return user_permission in ['read', 'comment', 'edit']
        elif permission == 'comment':
            return user_permission in ['comment', 'edit']
        elif permission == 'edit':
            return user_permission == 'edit'
        
        return False

    def add_active_user(self, document_id: str, user_id: str):
        """Add user to active users list."""
        with self.lock:
            if user_id not in self.active_users[document_id]:
                self.active_users[document_id].append(user_id)

    def remove_active_user(self, document_id: str, user_id: str):
        """Remove user from active users list."""
        with self.lock:
            if user_id in self.active_users[document_id]:
                self.active_users[document_id].remove(user_id)

    def get_active_users(self, document_id: str) -> List[str]:
        """Get active users for document."""
        with self.lock:
            return self.active_users[document_id].copy()

    def update_user_cursor(self, document_id: str, user_id: str, position: int):
        """Update user cursor position."""
        with self.lock:
            self.user_cursors[document_id][user_id] = position

    def get_user_cursors(self, document_id: str) -> Dict[str, int]:
        """Get user cursor positions."""
        with self.lock:
            return self.user_cursors[document_id].copy()


class GoogleDocsService:
    """Main Google Docs service."""

    def __init__(self, db_path: str = "google_docs.db"):
        """Initialize service."""
        self.db = DocumentDatabase(db_path)
        self.editor = CollaborativeEditor(self.db)
    
    def create_user(self, username: str, email: str, first_name: str, last_name: str) -> Optional[User]:
        """Create a new user."""
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            display_name=f"{first_name} {last_name}",
            created_at=datetime.now()
        )
        
        if self.db.save_user(user):
            return user
        return None

    def create_document(self, title: str, owner_id: str, content: str = "") -> Dict:
        """Create a new document."""
        document = Document(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            owner_id=owner_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
            permissions={owner_id: 'edit'},
            collaborators=[owner_id],
            is_public=False,
            tags=[],
            metadata={}
        )

        if self.db.save_document(document):
            return {'success': True, 'document': document.to_dict()}
        else:
            return {'success': False, 'error': 'Failed to create document'}

    def get_document(self, document_id: str, user_id: str) -> Dict:
        """Get document with permission check."""
        document = self.db.get_document(document_id)
        if not document:
            return {'success': False, 'error': 'Document not found'}

        if not self.editor._has_permission(document, user_id, 'read'):
            return {'success': False, 'error': 'No permission to view document'}

        return {'success': True, 'document': document.to_dict()}

    def update_document(self, document_id: str, user_id: str, changes: List[Dict]) -> Dict:
        """Update document with changes."""
        results = []
        for change in changes:
            success, message = self.editor.apply_change(document_id, user_id, change)
            results.append({'success': success, 'message': message})
        
        return {'success': all(r['success'] for r in results), 'results': results}
    
    def update_document_content(self, document_id: str, user_id: str, content: str) -> bool:
        """Update document content directly."""
        document = self.db.get_document(document_id)
        if not document:
            return False
        
        if not self.editor._has_permission(document, user_id, 'edit'):
            return False
        
        # Update the document content
        document.content = content
        document.updated_at = datetime.now()
        document.version += 1
        
        return self.db.save_document(document)
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        """Get all documents for a user."""
        documents = self.db.get_user_documents(user_id)
        return [doc.to_dict() for doc in documents]

    def share_document(self, document_id: str, owner_id: str, 
                      user_id: str, permission: str) -> Dict:
        """Share document with user."""
        document = self.db.get_document(document_id)
        if not document:
            return {'success': False, 'error': 'Document not found'}

        if document.owner_id != owner_id:
            return {'success': False, 'error': 'Only owner can share document'}

        if permission not in ['read', 'comment', 'edit']:
            return {'success': False, 'error': 'Invalid permission level'}

        document.permissions[user_id] = permission
        if user_id not in document.collaborators:
            document.collaborators.append(user_id)

        if self.db.save_document(document):
            return {'success': True, 'message': 'Document shared successfully'}
        else:
            return {'success': False, 'error': 'Failed to share document'}

    def add_comment(self, document_id: str, user_id: str, 
                   content: str, position: int) -> Dict:
        """Add comment to document."""
        document = self.db.get_document(document_id)
        if not document:
            return {'success': False, 'error': 'Document not found'}

        if not self.editor._has_permission(document, user_id, 'comment'):
            return {'success': False, 'error': 'No permission to comment'}

        comment = Comment(
            id=str(uuid.uuid4()),
            document_id=document_id,
            user_id=user_id,
            content=content,
            position=position,
            created_at=datetime.now()
        )

        if self.db.save_comment(comment):
            return {'success': True, 'comment': comment.to_dict()}
        else:
            return {'success': False, 'error': 'Failed to add comment'}

    def get_document_comments(self, document_id: str, user_id: str) -> Dict:
        """Get comments for document."""
        document = self.db.get_document(document_id)
        if not document:
            return {'success': False, 'error': 'Document not found'}

        if not self.editor._has_permission(document, user_id, 'read'):
            return {'success': False, 'error': 'No permission to view comments'}

        comments = self.db.get_document_comments(document_id)
        return {'success': True, 'comments': [comment.to_dict() for comment in comments]}


# Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'google_docs_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize service
google_docs_service = GoogleDocsService()


@app.route('/')
def index():
    """Home page."""
    html_template = '''
    <!DOCTYPE html>
    <head>
        <title>Google Docs Clone</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
            .document-list { border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
            .document-item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; }
            .document-item:hover { background: #f5f5f5; }
            .editor-container { display: none; margin-top: 20px; }
            .editor { border: 1px solid #ddd; border-radius: 8px; padding: 20px; min-height: 400px; }
            .editor:focus { outline: none; }
            .toolbar { margin-bottom: 10px; }
            .btn { padding: 8px 16px; margin-right: 10px; border: none; border-radius: 4px; cursor: pointer; }
            .btn-primary { background: #4285f4; color: white; }
            .btn-secondary { background: #f1f3f4; color: #5f6368; }
            .collaborators { margin-top: 10px; }
            .collaborator { display: inline-block; margin-right: 10px; padding: 4px 8px; background: #e8f0fe; border-radius: 4px; }
            .comments-panel { position: fixed; right: 0; top: 0; width: 300px; height: 100%; background: white; border-left: 1px solid #ddd; padding: 20px; overflow-y: auto; }
            .comment { margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Google Docs Clone</h1>
                <div>
                    <button class="btn btn-primary" onclick="createDocument()">New Document</button>
                    <button class="btn btn-secondary" onclick="showDocumentList()">My Documents</button>
                </div>
            </div>
            
            <div id="document-list" class="document-list">
                <h3>My Documents</h3>
                <div id="documents"></div>
            </div>
            
            <div id="editor-container" class="editor-container">
                <div class="toolbar">
                    <button class="btn btn-primary" onclick="saveDocument()">Save</button>
                    <button class="btn btn-secondary" onclick="shareDocument()">Share</button>
                    <button class="btn btn-secondary" onclick="addComment()">Add Comment</button>
                    <button class="btn btn-secondary" onclick="showDocumentList()">Back to List</button>
                </div>
                <div id="collaborators" class="collaborators"></div>
                <div id="editor" class="editor" contenteditable="true" spellcheck="false"></div>
            </div>
        </div>
        
        <div id="comments-panel" class="comments-panel" style="display: none;">
            <h3>Comments</h3>
            <div id="comments"></div>
        </div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            let currentDocument = null;
            let currentUser = 'user_' + Math.random().toString(36).substr(2, 9);
            
            // Load documents on page load
            loadDocuments();
            
            // Socket event handlers
            socket.on('document_updated', function(data) {
                if (data.document_id === currentDocument?.id) {
                    applyChanges(data.changes);
                }
            });
            
            socket.on('user_joined', function(data) {
                updateCollaborators(data.users);
            });
            
            socket.on('user_left', function(data) {
                updateCollaborators(data.users);
            });
            
            socket.on('cursor_moved', function(data) {
                updateUserCursors(data.cursors);
            });
            
            function loadDocuments() {
                fetch('/api/documents?user_id=' + currentUser)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            displayDocuments(data.documents);
                        }
                    });
            }
            
            function displayDocuments(documents) {
                const container = document.getElementById('documents');
                container.innerHTML = '';
                
                documents.forEach(doc => {
                    const div = document.createElement('div');
                    div.className = 'document-item';
                    div.innerHTML = `
                        <h4>${doc.title}</h4>
                        <p>Last updated: ${new Date(doc.updated_at).toLocaleString()}</p>
                        <p>Version: ${doc.version}</p>
                    `;
                    div.onclick = () => openDocument(doc.id);
                    container.appendChild(div);
                });
            }
            
            function openDocument(documentId) {
                fetch('/api/documents/' + documentId + '?user_id=' + currentUser)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            currentDocument = data.document;
                            showEditor();
                            loadDocumentContent();
                            joinDocumentRoom(documentId);
                        } else {
                            alert('Error: ' + data.error);
                        }
                    });
            }
            
            function showEditor() {
                document.getElementById('document-list').style.display = 'none';
                document.getElementById('editor-container').style.display = 'block';
            }
            
            function showDocumentList() {
                document.getElementById('document-list').style.display = 'block';
                document.getElementById('editor-container').style.display = 'none';
                if (currentDocument) {
                    leaveDocumentRoom(currentDocument.id);
                }
                currentDocument = null;
                loadDocuments();
            }
            
            function loadDocumentContent() {
                const editor = document.getElementById('editor');
                editor.innerHTML = currentDocument.content;
            }
            
            function joinDocumentRoom(documentId) {
                socket.emit('join_document', {document_id: documentId, user_id: currentUser});
            }
            
            function leaveDocumentRoom(documentId) {
                socket.emit('leave_document', {document_id: documentId, user_id: currentUser});
            }
            
            function createDocument() {
                const title = prompt('Enter document title:');
                if (title) {
                    fetch('/api/documents', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            title: title,
                            owner_id: currentUser,
                            content: ''
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            loadDocuments();
                        } else {
                            alert('Error: ' + data.error);
                        }
                    });
                }
            }
            
            function saveDocument() {
                if (!currentDocument) return;
                
                const editor = document.getElementById('editor');
                const content = editor.innerHTML;
                
                // Detect changes
                const changes = detectChanges(currentDocument.content, content);
                
                if (changes.length > 0) {
                    fetch('/api/documents/' + currentDocument.id + '/update', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            user_id: currentUser,
                            changes: changes
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            currentDocument.content = content;
                            currentDocument.version++;
                            socket.emit('document_change', {
                                document_id: currentDocument.id,
                                changes: changes,
                                user_id: currentUser
                            });
                        }
                    });
                }
            }
            
            function detectChanges(oldContent, newContent) {
                // Simple change detection - in production, use operational transforms
                const changes = [];
                
                if (oldContent !== newContent) {
                    changes.push({
                        type: 'replace',
                        position: 0,
                        content: newContent
                    });
                }
                
                return changes;
            }
            
            function applyChanges(changes) {
                const editor = document.getElementById('editor');
                // Apply changes to editor content
                // This is simplified - real implementation would use operational transforms
                editor.innerHTML = changes[changes.length - 1].content;
            }
            
            function updateCollaborators(users) {
                const container = document.getElementById('collaborators');
                container.innerHTML = '';
                
                users.forEach(userId => {
                    const div = document.createElement('span');
                    div.className = 'collaborator';
                    div.textContent = userId;
                    container.appendChild(div);
                });
            }
            
            function updateUserCursors(cursors) {
                // Update cursor positions in editor
                // Implementation would show other users' cursors
            }
            
            function shareDocument() {
                if (!currentDocument) return;
                
                const userId = prompt('Enter user ID to share with:');
                const permission = prompt('Enter permission (read/comment/edit):');
                
                if (userId && permission) {
                    fetch('/api/documents/' + currentDocument.id + '/share', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            owner_id: currentDocument.owner_id,
                            user_id: userId,
                            permission: permission
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Document shared successfully!');
                        } else {
                            alert('Error: ' + data.error);
                        }
                    });
                }
            }
            
            function addComment() {
                if (!currentDocument) return;
                
                const content = prompt('Enter comment:');
                if (content) {
                    const selection = window.getSelection();
                    const position = selection.anchorOffset;
                    
                    fetch('/api/documents/' + currentDocument.id + '/comments', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            user_id: currentUser,
                            content: content,
                            position: position
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            loadComments();
                        } else {
                            alert('Error: ' + data.error);
                        }
                    });
                }
            }
            
            function loadComments() {
                fetch('/api/documents/' + currentDocument.id + '/comments?user_id=' + currentUser)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            displayComments(data.comments);
                        }
                    });
            }
            
            function displayComments(comments) {
                const container = document.getElementById('comments');
                container.innerHTML = '';
                
                comments.forEach(comment => {
                    const div = document.createElement('div');
                    div.className = 'comment';
                    div.innerHTML = `
                        <strong>${comment.user_id}</strong>
                        <p>${comment.content}</p>
                        <small>${new Date(comment.created_at).toLocaleString()}</small>
                    `;
                    container.appendChild(div);
                });
            }
            
            // Auto-save every 30 seconds
            setInterval(saveDocument, 30000);
            
            // Track cursor movement
            document.getElementById('editor').addEventListener('keyup', function() {
                const selection = window.getSelection();
                const position = selection.anchorOffset;
                socket.emit('cursor_move', {
                    document_id: currentDocument?.id,
                    user_id: currentUser,
                    position: position
                });
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)


@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get user documents."""
    user_id = request.args.get('user_id')
    documents = google_docs_service.db.get_user_documents(user_id)
    return jsonify({'success': True, 'documents': [doc.to_dict() for doc in documents]})


@app.route('/api/documents', methods=['POST'])
def create_document():
    """Create new document."""
    data = request.get_json()
    result = google_docs_service.create_document(
        title=data['title'],
        owner_id=data['owner_id'],
        content=data.get('content', '')
    )
    return jsonify(result)


@app.route('/api/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    """Get document."""
    user_id = request.args.get('user_id')
    result = google_docs_service.get_document(document_id, user_id)
    return jsonify(result)


@app.route('/api/documents/<document_id>/update', methods=['POST'])
def update_document(document_id):
    """Update document."""
    data = request.get_json()
    result = google_docs_service.update_document(
        document_id=document_id,
        user_id=data['user_id'],
        changes=data['changes']
    )
    return jsonify(result)


@app.route('/api/documents/<document_id>/share', methods=['POST'])
def share_document(document_id):
    """Share document."""
    data = request.get_json()
    result = google_docs_service.share_document(
        document_id=document_id,
        owner_id=data['owner_id'],
        user_id=data['user_id'],
        permission=data['permission']
    )
    return jsonify(result)


@app.route('/api/documents/<document_id>/comments', methods=['GET'])
def get_comments(document_id):
    """Get document comments."""
    user_id = request.args.get('user_id')
    result = google_docs_service.get_document_comments(document_id, user_id)
    return jsonify(result)


@app.route('/api/documents/<document_id>/comments', methods=['POST'])
def add_comment(document_id):
    """Add comment to document."""
    data = request.get_json()
    result = google_docs_service.add_comment(
        document_id=document_id,
        user_id=data['user_id'],
        content=data['content'],
        position=data['position']
    )
    return jsonify(result)


@socketio.on('join_document')
def handle_join_document(data):
    """Handle user joining document."""
    document_id = data['document_id']
    user_id = data['user_id']
    
    google_docs_service.editor.add_active_user(document_id, user_id)
    join_room(document_id)
    
    active_users = google_docs_service.editor.get_active_users(document_id)
    emit('user_joined', {'users': active_users}, room=document_id)


@socketio.on('leave_document')
def handle_leave_document(data):
    """Handle user leaving document."""
    document_id = data['document_id']
    user_id = data['user_id']
    
    google_docs_service.editor.remove_active_user(document_id, user_id)
    leave_room(document_id)
    
    active_users = google_docs_service.editor.get_active_users(document_id)
    emit('user_left', {'users': active_users}, room=document_id)


@socketio.on('document_change')
def handle_document_change(data):
    """Handle document change."""
    document_id = data['document_id']
    changes = data['changes']
    user_id = data['user_id']
    
    emit('document_updated', {
        'document_id': document_id,
        'changes': changes,
        'user_id': user_id
    }, room=document_id, include_self=False)


@socketio.on('cursor_move')
def handle_cursor_move(data):
    """Handle cursor movement."""
    document_id = data['document_id']
    user_id = data['user_id']
    position = data['position']
    
    google_docs_service.editor.update_user_cursor(document_id, user_id, position)
    
    cursors = google_docs_service.editor.get_user_cursors(document_id)
    emit('cursor_moved', {'cursors': cursors}, room=document_id, include_self=False)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    socketio.run(app, debug=True, host='0.0.0.0', port=5002)
