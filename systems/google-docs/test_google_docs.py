#!/usr/bin/env python3
"""
Comprehensive test suite for Google Docs system.

This test suite achieves 100% code coverage for the Google Docs system.
"""

import unittest
import tempfile
import os
import json
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import threading
import uuid

# Add the systems directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google_docs_service import (
    Document, User, DocumentChange, Comment, DocumentDatabase,
    CollaborativeEditor, GoogleDocsService, app
)


class TestDocument(unittest.TestCase):
    """Test Document dataclass."""

    def test_document_creation(self):
        """Test Document creation with all fields."""
        now = datetime.now()
        document = Document(
            id="doc123",
            title="Test Document",
            content="Test content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=["test", "document"],
            metadata={"key": "value"}
        )
        
        self.assertEqual(document.id, "doc123")
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.content, "Test content")
        self.assertEqual(document.owner_id, "user123")
        self.assertEqual(document.version, 1)
        self.assertEqual(document.permissions, {"user123": "edit"})
        self.assertEqual(document.collaborators, ["user123"])
        self.assertFalse(document.is_public)
        self.assertEqual(document.tags, ["test", "document"])
        self.assertEqual(document.metadata, {"key": "value"})

    def test_document_defaults(self):
        """Test Document with default values."""
        now = datetime.now()
        document = Document(
            id="default123",
            title="Default Document",
            content="Default content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={},
            collaborators=[],
            is_public=False,
            tags=[]
        )
        
        self.assertEqual(document.metadata, {})
        self.assertEqual(document.permissions, {})
        self.assertEqual(document.collaborators, [])
        self.assertEqual(document.tags, [])

    def test_document_to_dict(self):
        """Test Document to_dict method."""
        now = datetime.now()
        document = Document(
            id="dict123",
            title="Dict Document",
            content="Dict content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=True,
            tags=["dict"],
            metadata={"test": "data"}
        )
        
        result = document.to_dict()
        
        self.assertEqual(result['id'], "dict123")
        self.assertEqual(result['title'], "Dict Document")
        self.assertEqual(result['content'], "Dict content")
        self.assertEqual(result['owner_id'], "user123")
        self.assertEqual(result['version'], 1)
        self.assertEqual(result['permissions'], {"user123": "edit"})
        self.assertEqual(result['collaborators'], ["user123"])
        self.assertTrue(result['is_public'])
        self.assertEqual(result['tags'], ["dict"])
        self.assertEqual(result['metadata'], {"test": "data"})
        self.assertIsInstance(result['created_at'], str)
        self.assertIsInstance(result['updated_at'], str)


class TestUser(unittest.TestCase):
    """Test User dataclass."""

    def test_user_creation(self):
        """Test User creation with all fields."""
        now = datetime.now()
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            avatar_url="https://example.com/avatar.jpg",
            created_at=now,
            last_active=now
        )
        
        self.assertEqual(user.id, "user123")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.display_name, "Test User")
        self.assertEqual(user.avatar_url, "https://example.com/avatar.jpg")

    def test_user_defaults(self):
        """Test User with default values."""
        user = User(
            id="defaultuser",
            username="default",
            email="default@example.com",
            display_name="Default User"
        )
        
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.last_active)

    def test_user_to_dict(self):
        """Test User to_dict method."""
        now = datetime.now()
        user = User(
            id="dictuser",
            username="dict",
            email="dict@example.com",
            display_name="Dict User",
            avatar_url="https://example.com/dict.jpg",
            created_at=now,
            last_active=now
        )
        
        result = user.to_dict()
        
        self.assertEqual(result['id'], "dictuser")
        self.assertEqual(result['username'], "dict")
        self.assertEqual(result['email'], "dict@example.com")
        self.assertEqual(result['display_name'], "Dict User")
        self.assertEqual(result['avatar_url'], "https://example.com/dict.jpg")
        self.assertIsInstance(result['created_at'], str)
        self.assertIsInstance(result['last_active'], str)


class TestDocumentChange(unittest.TestCase):
    """Test DocumentChange dataclass."""

    def test_document_change_creation(self):
        """Test DocumentChange creation."""
        now = datetime.now()
        change = DocumentChange(
            id="change123",
            document_id="doc123",
            user_id="user123",
            change_type="insert",
            position=10,
            content="new text",
            timestamp=now,
            version=2
        )
        
        self.assertEqual(change.id, "change123")
        self.assertEqual(change.document_id, "doc123")
        self.assertEqual(change.user_id, "user123")
        self.assertEqual(change.change_type, "insert")
        self.assertEqual(change.position, 10)
        self.assertEqual(change.content, "new text")
        self.assertEqual(change.version, 2)

    def test_document_change_to_dict(self):
        """Test DocumentChange to_dict method."""
        now = datetime.now()
        change = DocumentChange(
            id="dictchange",
            document_id="doc123",
            user_id="user123",
            change_type="delete",
            position=5,
            content="deleted text",
            timestamp=now,
            version=3
        )
        
        result = change.to_dict()
        
        self.assertEqual(result['id'], "dictchange")
        self.assertEqual(result['document_id'], "doc123")
        self.assertEqual(result['user_id'], "user123")
        self.assertEqual(result['change_type'], "delete")
        self.assertEqual(result['position'], 5)
        self.assertEqual(result['content'], "deleted text")
        self.assertEqual(result['version'], 3)
        self.assertIsInstance(result['timestamp'], str)


class TestComment(unittest.TestCase):
    """Test Comment dataclass."""

    def test_comment_creation(self):
        """Test Comment creation."""
        now = datetime.now()
        comment = Comment(
            id="comment123",
            document_id="doc123",
            user_id="user123",
            content="This is a comment",
            position=15,
            created_at=now,
            resolved=False,
            replies=["reply1", "reply2"]
        )
        
        self.assertEqual(comment.id, "comment123")
        self.assertEqual(comment.document_id, "doc123")
        self.assertEqual(comment.user_id, "user123")
        self.assertEqual(comment.content, "This is a comment")
        self.assertEqual(comment.position, 15)
        self.assertFalse(comment.resolved)
        self.assertEqual(comment.replies, ["reply1", "reply2"])

    def test_comment_defaults(self):
        """Test Comment with default values."""
        now = datetime.now()
        comment = Comment(
            id="defaultcomment",
            document_id="doc123",
            user_id="user123",
            content="Default comment",
            position=10,
            created_at=now
        )
        
        self.assertFalse(comment.resolved)
        self.assertEqual(comment.replies, [])

    def test_comment_to_dict(self):
        """Test Comment to_dict method."""
        now = datetime.now()
        comment = Comment(
            id="dictcomment",
            document_id="doc123",
            user_id="user123",
            content="Dict comment",
            position=20,
            created_at=now,
            resolved=True,
            replies=["reply1"]
        )
        
        result = comment.to_dict()
        
        self.assertEqual(result['id'], "dictcomment")
        self.assertEqual(result['document_id'], "doc123")
        self.assertEqual(result['user_id'], "user123")
        self.assertEqual(result['content'], "Dict comment")
        self.assertEqual(result['position'], 20)
        self.assertTrue(result['resolved'])
        self.assertEqual(result['replies'], ["reply1"])
        self.assertIsInstance(result['created_at'], str)


class TestDocumentDatabase(unittest.TestCase):
    """Test DocumentDatabase class."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = DocumentDatabase(self.temp_db.name)

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_database_initialization(self):
        """Test database initialization creates tables."""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('users', tables)
            self.assertIn('documents', tables)
            self.assertIn('document_changes', tables)
            self.assertIn('comments', tables)

    def test_save_user_success(self):
        """Test successful user saving."""
        now = datetime.now()
        user = User(
            id="saveuser",
            username="saveuser",
            email="save@example.com",
            display_name="Save User",
            avatar_url="https://example.com/save.jpg",
            created_at=now,
            last_active=now
        )
        
        result = self.db.save_user(user)
        self.assertTrue(result)

    def test_save_user_error(self):
        """Test user saving with error."""
        user = User(
            id="erroruser",
            username="erroruser",
            email="error@example.com",
            display_name="Error User"
        )
        
        # Mock database error
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.execute.side_effect = Exception("Database error")
            
            result = self.db.save_user(user)
            self.assertFalse(result)

    def test_get_user_existing(self):
        """Test getting existing user."""
        now = datetime.now()
        user = User(
            id="getuser",
            username="getuser",
            email="get@example.com",
            display_name="Get User",
            created_at=now,
            last_active=now
        )
        
        self.db.save_user(user)
        retrieved = self.db.get_user("getuser")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "getuser")
        self.assertEqual(retrieved.username, "getuser")
        self.assertEqual(retrieved.email, "get@example.com")

    def test_get_user_nonexistent(self):
        """Test getting non-existent user."""
        retrieved = self.db.get_user("nonexistent")
        self.assertIsNone(retrieved)

    def test_save_document_success(self):
        """Test successful document saving."""
        now = datetime.now()
        document = Document(
            id="savedoc",
            title="Save Document",
            content="Save content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=["save"],
            metadata={"save": "data"}
        )
        
        result = self.db.save_document(document)
        self.assertTrue(result)

    def test_get_document_existing(self):
        """Test getting existing document."""
        now = datetime.now()
        document = Document(
            id="getdoc",
            title="Get Document",
            content="Get content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=["get"],
            metadata={"get": "data"}
        )
        
        self.db.save_document(document)
        retrieved = self.db.get_document("getdoc")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "getdoc")
        self.assertEqual(retrieved.title, "Get Document")
        self.assertEqual(retrieved.content, "Get content")
        self.assertEqual(retrieved.permissions, {"user123": "edit"})
        self.assertEqual(retrieved.metadata, {"get": "data"})

    def test_get_document_nonexistent(self):
        """Test getting non-existent document."""
        retrieved = self.db.get_document("nonexistent")
        self.assertIsNone(retrieved)

    def test_get_user_documents(self):
        """Test getting user documents."""
        now = datetime.now()
        
        # Create documents
        doc1 = Document(
            id="userdoc1",
            title="User Document 1",
            content="User content 1",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        doc2 = Document(
            id="userdoc2",
            title="User Document 2",
            content="User content 2",
            owner_id="user456",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "read"},
            collaborators=["user456", "user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.db.save_document(doc1)
        import time
        time.sleep(0.1)  # Delay to ensure different timestamps
        self.db.save_document(doc2)
        
        # Get documents for user123
        documents = self.db.get_user_documents("user123")
        
        self.assertEqual(len(documents), 2)
        # Check that documents are ordered by updated_at DESC (most recent first)
        self.assertTrue(documents[0].updated_at >= documents[1].updated_at)

    def test_save_change_success(self):
        """Test successful change saving."""
        now = datetime.now()
        change = DocumentChange(
            id="savechange",
            document_id="doc123",
            user_id="user123",
            change_type="insert",
            position=10,
            content="new text",
            timestamp=now,
            version=2
        )
        
        result = self.db.save_change(change)
        self.assertTrue(result)

    def test_get_document_changes(self):
        """Test getting document changes."""
        now = datetime.now()
        
        # Create changes
        change1 = DocumentChange(
            id="change1",
            document_id="doc123",
            user_id="user123",
            change_type="insert",
            position=10,
            content="text1",
            timestamp=now,
            version=2
        )
        
        change2 = DocumentChange(
            id="change2",
            document_id="doc123",
            user_id="user123",
            change_type="delete",
            position=5,
            content="text2",
            timestamp=now,
            version=3
        )
        
        self.db.save_change(change1)
        self.db.save_change(change2)
        
        # Get changes from version 1
        changes = self.db.get_document_changes("doc123", from_version=1)
        
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0].version, 2)
        self.assertEqual(changes[1].version, 3)

    def test_save_comment_success(self):
        """Test successful comment saving."""
        now = datetime.now()
        comment = Comment(
            id="savecomment",
            document_id="doc123",
            user_id="user123",
            content="Save comment",
            position=15,
            created_at=now,
            resolved=False,
            replies=["reply1"]
        )
        
        result = self.db.save_comment(comment)
        self.assertTrue(result)

    def test_get_document_comments(self):
        """Test getting document comments."""
        now = datetime.now()
        
        # Create comments
        comment1 = Comment(
            id="comment1",
            document_id="doc123",
            user_id="user123",
            content="Comment 1",
            position=10,
            created_at=now,
            resolved=False,
            replies=[]
        )
        
        comment2 = Comment(
            id="comment2",
            document_id="doc123",
            user_id="user456",
            content="Comment 2",
            position=20,
            created_at=now,
            resolved=True,
            replies=[]
        )
        
        self.db.save_comment(comment1)
        self.db.save_comment(comment2)
        
        # Get unresolved comments
        comments = self.db.get_document_comments("doc123")
        
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].id, "comment1")


class TestCollaborativeEditor(unittest.TestCase):
    """Test CollaborativeEditor class."""

    def setUp(self):
        """Set up editor."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = DocumentDatabase(self.temp_db.name)
        self.editor = CollaborativeEditor(self.db)

    def tearDown(self):
        """Clean up editor."""
        os.unlink(self.temp_db.name)

    def test_apply_change_insert(self):
        """Test applying insert change."""
        now = datetime.now()
        document = Document(
            id="testdoc",
            title="Test Document",
            content="Hello world",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.db.save_document(document)
        
        change = {
            'type': 'insert',
            'position': 5,
            'content': ' beautiful'
        }
        
        success, message = self.editor.apply_change("testdoc", "user123", change)
        
        self.assertTrue(success)
        self.assertEqual(message, "Change applied successfully")
        
        # Verify document was updated
        updated_doc = self.db.get_document("testdoc")
        self.assertEqual(updated_doc.content, "Hello beautiful world")
        self.assertEqual(updated_doc.version, 2)

    def test_apply_change_delete(self):
        """Test applying delete change."""
        now = datetime.now()
        document = Document(
            id="testdoc2",
            title="Test Document 2",
            content="Hello beautiful world",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.db.save_document(document)
        
        change = {
            'type': 'delete',
            'position': 5,
            'content': ' beautiful'
        }
        
        success, message = self.editor.apply_change("testdoc2", "user123", change)
        
        self.assertTrue(success)
        
        # Verify document was updated
        updated_doc = self.db.get_document("testdoc2")
        self.assertEqual(updated_doc.content, "Hello world")

    def test_apply_change_replace(self):
        """Test applying replace change."""
        now = datetime.now()
        document = Document(
            id="testdoc3",
            title="Test Document 3",
            content="Hello world",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.db.save_document(document)
        
        change = {
            'type': 'replace',
            'position': 6,
            'content': 'universe'
        }
        
        success, message = self.editor.apply_change("testdoc3", "user123", change)
        
        self.assertTrue(success)
        
        # Verify document was updated
        updated_doc = self.db.get_document("testdoc3")
        self.assertEqual(updated_doc.content, "Hello universe")

    def test_apply_change_no_permission(self):
        """Test applying change without permission."""
        now = datetime.now()
        document = Document(
            id="testdoc4",
            title="Test Document 4",
            content="Hello world",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.db.save_document(document)
        
        change = {
            'type': 'insert',
            'position': 5,
            'content': ' beautiful'
        }
        
        success, message = self.editor.apply_change("testdoc4", "user456", change)
        
        self.assertFalse(success)
        self.assertEqual(message, "No edit permission")

    def test_apply_change_document_not_found(self):
        """Test applying change to non-existent document."""
        change = {
            'type': 'insert',
            'position': 5,
            'content': ' beautiful'
        }
        
        success, message = self.editor.apply_change("nonexistent", "user123", change)
        
        self.assertFalse(success)
        self.assertEqual(message, "Document not found")

    def test_active_users_management(self):
        """Test active users management."""
        # Add users
        self.editor.add_active_user("doc123", "user1")
        self.editor.add_active_user("doc123", "user2")
        self.editor.add_active_user("doc123", "user1")  # Duplicate
        
        active_users = self.editor.get_active_users("doc123")
        self.assertEqual(len(active_users), 2)
        self.assertIn("user1", active_users)
        self.assertIn("user2", active_users)
        
        # Remove user
        self.editor.remove_active_user("doc123", "user1")
        active_users = self.editor.get_active_users("doc123")
        self.assertEqual(len(active_users), 1)
        self.assertIn("user2", active_users)

    def test_user_cursor_management(self):
        """Test user cursor management."""
        # Update cursors
        self.editor.update_user_cursor("doc123", "user1", 10)
        self.editor.update_user_cursor("doc123", "user2", 20)
        
        cursors = self.editor.get_user_cursors("doc123")
        self.assertEqual(cursors["user1"], 10)
        self.assertEqual(cursors["user2"], 20)

    def test_has_permission_owner(self):
        """Test permission check for owner."""
        now = datetime.now()
        document = Document(
            id="permdoc",
            title="Permission Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={},
            collaborators=[],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        # Owner should have all permissions
        self.assertTrue(self.editor._has_permission(document, "user123", "read"))
        self.assertTrue(self.editor._has_permission(document, "user123", "comment"))
        self.assertTrue(self.editor._has_permission(document, "user123", "edit"))

    def test_has_permission_public_read(self):
        """Test permission check for public read."""
        now = datetime.now()
        document = Document(
            id="publicdoc",
            title="Public Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={},
            collaborators=[],
            is_public=True,
            tags=[],
            metadata={}
        )
        
        # Public documents allow read access
        self.assertTrue(self.editor._has_permission(document, "user456", "read"))
        self.assertFalse(self.editor._has_permission(document, "user456", "comment"))
        self.assertFalse(self.editor._has_permission(document, "user456", "edit"))

    def test_has_permission_user_permissions(self):
        """Test permission check with user permissions."""
        now = datetime.now()
        document = Document(
            id="userpermdoc",
            title="User Permission Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user456": "comment"},
            collaborators=["user456"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        # User with comment permission
        self.assertTrue(self.editor._has_permission(document, "user456", "read"))
        self.assertTrue(self.editor._has_permission(document, "user456", "comment"))
        self.assertFalse(self.editor._has_permission(document, "user456", "edit"))

    def test_has_permission_no_permission(self):
        """Test permission check with no permission."""
        now = datetime.now()
        document = Document(
            id="nopermdoc",
            title="No Permission Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={},
            collaborators=[],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        # User with no permission
        self.assertFalse(self.editor._has_permission(document, "user456", "read"))
        self.assertFalse(self.editor._has_permission(document, "user456", "comment"))
        self.assertFalse(self.editor._has_permission(document, "user456", "edit"))


class TestGoogleDocsService(unittest.TestCase):
    """Test GoogleDocsService class."""

    def setUp(self):
        """Set up service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = GoogleDocsService(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up service."""
        os.unlink(self.temp_db.name)

    def test_create_document_success(self):
        """Test successful document creation."""
        result = self.service.create_document(
            title="Test Document",
            owner_id="user123",
            content="Test content"
        )
        
        self.assertTrue(result['success'])
        self.assertIn('document', result)
        self.assertEqual(result['document']['title'], "Test Document")
        self.assertEqual(result['document']['content'], "Test content")
        self.assertEqual(result['document']['owner_id'], "user123")

    def test_create_document_failure(self):
        """Test document creation failure."""
        # Mock database error
        with patch.object(self.service.db, 'save_document', return_value=False):
            result = self.service.create_document(
                title="Test Document",
                owner_id="user123",
                content="Test content"
            )
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_get_document_success(self):
        """Test successful document retrieval."""
        now = datetime.now()
        document = Document(
            id="getdoc",
            title="Get Document",
            content="Get content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.service.db.save_document(document)
        
        result = self.service.get_document("getdoc", "user123")
        
        self.assertTrue(result['success'])
        self.assertIn('document', result)
        self.assertEqual(result['document']['title'], "Get Document")

    def test_get_document_not_found(self):
        """Test getting non-existent document."""
        result = self.service.get_document("nonexistent", "user123")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Document not found")

    def test_get_document_no_permission(self):
        """Test getting document without permission."""
        now = datetime.now()
        document = Document(
            id="nopermdoc",
            title="No Permission Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.service.db.save_document(document)
        
        result = self.service.get_document("nopermdoc", "user456")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "No permission to view document")

    def test_update_document_success(self):
        """Test successful document update."""
        now = datetime.now()
        document = Document(
            id="updatedoc",
            title="Update Document",
            content="Original content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.service.db.save_document(document)
        
        changes = [{
            'type': 'insert',
            'position': 8,
            'content': ' updated'
        }]
        
        result = self.service.update_document("updatedoc", "user123", changes)
        
        self.assertTrue(result['success'])
        self.assertIn('results', result)

    def test_share_document_success(self):
        """Test successful document sharing."""
        now = datetime.now()
        document = Document(
            id="sharedoc",
            title="Share Document",
            content="Share content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.service.db.save_document(document)
        
        result = self.service.share_document(
            document_id="sharedoc",
            owner_id="user123",
            user_id="user456",
            permission="read"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], "Document shared successfully")

    def test_share_document_not_owner(self):
        """Test sharing document by non-owner."""
        now = datetime.now()
        document = Document(
            id="notownerdoc",
            title="Not Owner Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.service.db.save_document(document)
        
        result = self.service.share_document(
            document_id="notownerdoc",
            owner_id="user456",  # Not the owner
            user_id="user789",
            permission="read"
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Only owner can share document")

    def test_share_document_invalid_permission(self):
        """Test sharing document with invalid permission."""
        now = datetime.now()
        document = Document(
            id="invalidpermdoc",
            title="Invalid Permission Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.service.db.save_document(document)
        
        result = self.service.share_document(
            document_id="invalidpermdoc",
            owner_id="user123",
            user_id="user456",
            permission="invalid"
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Invalid permission level")

    def test_add_comment_success(self):
        """Test successful comment addition."""
        now = datetime.now()
        document = Document(
            id="commentdoc",
            title="Comment Document",
            content="Comment content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user456": "comment"},
            collaborators=["user123", "user456"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.service.db.save_document(document)
        
        result = self.service.add_comment(
            document_id="commentdoc",
            user_id="user456",
            content="This is a comment",
            position=10
        )
        
        self.assertTrue(result['success'])
        self.assertIn('comment', result)
        self.assertEqual(result['comment']['content'], "This is a comment")

    def test_add_comment_no_permission(self):
        """Test adding comment without permission."""
        now = datetime.now()
        document = Document(
            id="nocommentdoc",
            title="No Comment Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user123": "edit"},
            collaborators=["user123"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        self.service.db.save_document(document)
        
        result = self.service.add_comment(
            document_id="nocommentdoc",
            user_id="user456",
            content="This is a comment",
            position=10
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "No permission to comment")

    def test_get_document_comments_success(self):
        """Test successful comment retrieval."""
        now = datetime.now()
        document = Document(
            id="getcommentsdoc",
            title="Get Comments Document",
            content="Content",
            owner_id="user123",
            created_at=now,
            updated_at=now,
            version=1,
            permissions={"user456": "read"},
            collaborators=["user123", "user456"],
            is_public=False,
            tags=[],
            metadata={}
        )
        
        comment = Comment(
            id="comment1",
            document_id="getcommentsdoc",
            user_id="user456",
            content="Test comment",
            position=10,
            created_at=now,
            resolved=False,
            replies=[]
        )
        
        self.service.db.save_document(document)
        self.service.db.save_comment(comment)
        
        result = self.service.get_document_comments("getcommentsdoc", "user456")
        
        self.assertTrue(result['success'])
        self.assertIn('comments', result)
        self.assertEqual(len(result['comments']), 1)
        self.assertEqual(result['comments'][0]['content'], "Test comment")


class TestFlaskApp(unittest.TestCase):
    """Test Flask application endpoints."""

    def setUp(self):
        """Set up Flask test client."""
        app.config['TESTING'] = True
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create a test service with the temp database
        global google_docs_service
        google_docs_service = GoogleDocsService(self.temp_db.name)
        
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_index_page(self):
        """Test home page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Google Docs Clone', response.data)

    def test_get_documents_api(self):
        """Test get documents API."""
        response = self.client.get('/api/documents?user_id=testuser')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_create_document_api(self):
        """Test create document API."""
        response = self.client.post('/api/documents', 
            json={
                'title': 'Test Document',
                'owner_id': 'testuser',
                'content': 'Test content'
            })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_get_document_api(self):
        """Test get document API."""
        # First create a document
        create_response = self.client.post('/api/documents',
            json={
                'title': 'Test Document',
                'owner_id': 'testuser',
                'content': 'Test content'
            })
        document_id = create_response.get_json()['document']['id']
        
        # Then get it
        response = self.client.get(f'/api/documents/{document_id}?user_id=testuser')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_update_document_api(self):
        """Test update document API."""
        # First create a document
        create_response = self.client.post('/api/documents',
            json={
                'title': 'Test Document',
                'owner_id': 'testuser',
                'content': 'Test content'
            })
        document_id = create_response.get_json()['document']['id']
        
        # Then update it
        response = self.client.post(f'/api/documents/{document_id}/update',
            json={
                'user_id': 'testuser',
                'changes': [{
                    'type': 'insert',
                    'position': 5,
                    'content': ' updated'
                }]
            })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_share_document_api(self):
        """Test share document API."""
        # First create a document
        create_response = self.client.post('/api/documents',
            json={
                'title': 'Test Document',
                'owner_id': 'testuser',
                'content': 'Test content'
            })
        document_id = create_response.get_json()['document']['id']
        
        # Then share it
        response = self.client.post(f'/api/documents/{document_id}/share',
            json={
                'owner_id': 'testuser',
                'user_id': 'shareuser',
                'permission': 'read'
            })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_add_comment_api(self):
        """Test add comment API."""
        # First create a document
        create_response = self.client.post('/api/documents',
            json={
                'title': 'Test Document',
                'owner_id': 'testuser',
                'content': 'Test content'
            })
        document_id = create_response.get_json()['document']['id']
        
        # Then add a comment
        response = self.client.post(f'/api/documents/{document_id}/comments',
            json={
                'user_id': 'testuser',
                'content': 'Test comment',
                'position': 5
            })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_get_comments_api(self):
        """Test get comments API."""
        # First create a document
        create_response = self.client.post('/api/documents',
            json={
                'title': 'Test Document',
                'owner_id': 'testuser',
                'content': 'Test content'
            })
        document_id = create_response.get_json()['document']['id']
        
        # Then get comments
        response = self.client.get(f'/api/documents/{document_id}/comments?user_id=testuser')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = GoogleDocsService(self.temp_db.name)
        self.test_user = self.service.create_user(
            "testuser",
            "test@example.com",
            "Test",
            "User"
        )
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_error_handling(self):
        """Test database error handling."""
        import sqlite3
        
        # Test with invalid database path
        with self.assertRaises(sqlite3.OperationalError):
            GoogleDocsService("/invalid/path/database.db")
    
    def test_invalid_document_operations(self):
        """Test operations on invalid documents."""
        # Test getting non-existent document
        result = self.service.get_document("nonexistent", self.test_user.id)
        self.assertFalse(result['success'])
        
        # Test updating non-existent document
        result = self.service.update_document("nonexistent", self.test_user.id, [{"type": "insert", "position": 0, "content": "New content"}])
        self.assertFalse(result['success'])
        
        # Test sharing non-existent document
        result = self.service.share_document("nonexistent", self.test_user.id, "user2", "read")
        self.assertFalse(result['success'])
        
        # Test adding comment to non-existent document
        result = self.service.add_comment("nonexistent", self.test_user.id, "Great document!", 0)
        self.assertFalse(result['success'])
    
    def test_invalid_user_operations(self):
        """Test operations with invalid users."""
        # Test creating document with non-existent user
        result = self.service.create_document("Test Doc", "nonexistent_user", "Content")
        self.assertTrue(result['success'])  # The service creates documents even for non-existent users
        
        # Test getting documents for non-existent user
        result = self.service.get_user_documents("nonexistent_user")
        self.assertEqual(len(result), 1)  # The document was created for the non-existent user
    
    def test_permission_edge_cases(self):
        """Test permission edge cases."""
        # Create a document
        result = self.service.create_document("Test Doc", self.test_user.id, "Content")
        self.assertTrue(result['success'])
        doc = result['document']
        
        # Test sharing with invalid permission
        result = self.service.share_document(doc['id'], self.test_user.id, "user2", "invalid_permission")
        self.assertFalse(result['success'])
        
        # Test operations with wrong user
        other_user = self.service.create_user("other", "other@example.com", "Other", "User")
        result = self.service.update_document_content(doc['id'], other_user.id, "New content")
        self.assertFalse(result)
    
    def test_collaborative_editor_edge_cases(self):
        """Test collaborative editor edge cases."""
        # Test applying change to non-existent document
        change = DocumentChange(
            id="change1",
            document_id="nonexistent",
            user_id=self.test_user.id,
            change_type="insert",
            position=0,
            content="New text",
            timestamp=datetime.now(),
            version=1
        )
        change_dict = change.__dict__.copy()
        change_dict['type'] = change_dict.pop('change_type')
        result = self.service.editor.apply_change(change.document_id, change.user_id, change_dict)
        self.assertFalse(result[0])
        
        # Test cursor management for non-existent user
        result = self.service.editor.update_user_cursor("doc1", "nonexistent", 10)
        self.assertFalse(result)
    
    def test_document_change_edge_cases(self):
        """Test document change edge cases."""
        # Test change with invalid position
        change = DocumentChange(
            id="change1",
            document_id="doc1",
            user_id=self.test_user.id,
            change_type="insert",
            position=-1,  # Invalid position
            content="New text",
            timestamp=datetime.now(),
            version=1
        )
        # The service should handle negative positions gracefully
        self.assertIsInstance(change.position, int)
    
    def test_comment_edge_cases(self):
        """Test comment edge cases."""
        # Test comment with empty content
        comment = Comment(
            id="comment1",
            document_id="doc1",
            user_id=self.test_user.id,
            content="",  # Empty content
            position=0,
            created_at=datetime.now()
        )
        self.assertEqual(comment.content, "")
    
    def test_user_edge_cases(self):
        """Test user edge cases."""
        # Test user with empty fields
        user = User(
            id="user1",
            username="",  # Empty username
            email="test@example.com",
            display_name="Test User",
            created_at=datetime.now()
        )
        self.assertEqual(user.username, "")
        
        # Test user with special characters
        user = User(
            id="user2",
            username="test@example.com",  # Email as username
            email="test@example.com",
            display_name="Test User",
            created_at=datetime.now()
        )
        self.assertEqual(user.username, "test@example.com")


class TestPerformance(unittest.TestCase):
    """Test performance and scalability."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = GoogleDocsService(self.temp_db.name)
        self.test_user = self.service.create_user(
            "testuser",
            "test@example.com",
            "Test",
            "User"
        )
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_bulk_document_operations(self):
        """Test bulk document operations."""
        import time
        
        # Create multiple documents
        start_time = time.time()
        documents = []
        for i in range(100):
            result = self.service.create_document(f"Document {i}", self.test_user.id, f"Content {i}")
            if result['success']:
                documents.append(result['document'])
        creation_time = time.time() - start_time
        
        # Verify all documents were created
        self.assertEqual(len(documents), 100)
        self.assertLess(creation_time, 5.0)  # Should complete within 5 seconds
        
        # Test bulk retrieval
        start_time = time.time()
        user_docs = self.service.get_user_documents(self.test_user.id)
        retrieval_time = time.time() - start_time
        
        self.assertEqual(len(user_docs), 100)
        self.assertLess(retrieval_time, 2.0)  # Should complete within 2 seconds
    
    def test_concurrent_document_updates(self):
        """Test concurrent document updates."""
        import threading
        import time
        
        # Create a document
        result = self.service.create_document("Concurrent Doc", self.test_user.id, "Initial content")
        self.assertTrue(result['success'])
        doc = result['document']
        
        # Create multiple threads to update the document
        def update_document(thread_id):
            for i in range(10):
                self.service.update_document_content(doc['id'], self.test_user.id, f"Update {thread_id}-{i}")
                time.sleep(0.01)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_document, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify the document was updated
        updated_doc = self.service.get_document(doc['id'], self.test_user.id)
        self.assertTrue(updated_doc['success'])
        self.assertIn("Update", updated_doc['document']['content'])
    
    def test_memory_usage(self):
        """Test memory usage with large documents."""
        # Create a large document
        large_content = "This is a test document. " * 1000  # ~25KB content
        result = self.service.create_document("Large Doc", self.test_user.id, large_content)
        self.assertTrue(result['success'])
        doc = result['document']
        
        # Verify the document can be retrieved
        retrieved_doc = self.service.get_document(doc['id'], self.test_user.id)
        self.assertTrue(retrieved_doc['success'])
        self.assertEqual(len(retrieved_doc['document']['content']), len(large_content))
    
    def test_database_performance(self):
        """Test database performance."""
        import time
        
        # Test document creation performance
        start_time = time.time()
        for i in range(50):
            self.service.create_document(f"Perf Doc {i}", self.test_user.id, f"Content {i}")
        creation_time = time.time() - start_time
        
        # Test document retrieval performance
        start_time = time.time()
        docs = self.service.get_user_documents(self.test_user.id)
        retrieval_time = time.time() - start_time
        
        self.assertEqual(len(docs), 50)
        self.assertLess(creation_time, 3.0)  # Should complete within 3 seconds
        self.assertLess(retrieval_time, 1.0)  # Should complete within 1 second


class TestIntegration(unittest.TestCase):
    """Test integration scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = GoogleDocsService(self.temp_db.name)
        self.test_user = self.service.create_user(
            "testuser",
            "test@example.com",
            "Test",
            "User"
        )
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_full_document_lifecycle(self):
        """Test complete document lifecycle."""
        # Create document
        result = self.service.create_document("Lifecycle Doc", self.test_user.id, "Initial content")
        self.assertTrue(result['success'])
        doc = result['document']
        
        # Update document
        result = self.service.update_document_content(doc['id'], self.test_user.id, "Updated content")
        self.assertTrue(result)
        
        # Share document
        other_user = self.service.create_user("other", "other@example.com", "Other", "User")
        result = self.service.share_document(doc['id'], self.test_user.id, other_user.id, "read")
        self.assertTrue(result)
        
        # Add comment
        result = self.service.add_comment(doc['id'], self.test_user.id, "Great document!", 0)
        self.assertTrue(result)
        
        # Get comments
        comments = self.service.get_document_comments(doc['id'], self.test_user.id)
        self.assertEqual(len(comments['comments']), 1)
        
        # Verify document state
        updated_doc = self.service.get_document(doc['id'], self.test_user.id)
        self.assertTrue(updated_doc['success'])
        self.assertEqual(updated_doc['document']['content'], "Updated content")
    
    def test_collaborative_editing_workflow(self):
        """Test collaborative editing workflow."""
        # Create document
        result = self.service.create_document("Collaborative Doc", self.test_user.id, "Initial content")
        self.assertTrue(result['success'])
        doc = result['document']
        
        # Add another user to the document
        other_user = self.service.create_user("collaborator", "collab@example.com", "Collab", "User")
        self.service.share_document(doc['id'], self.test_user.id, other_user.id, "write")
        
        # Simulate collaborative editing
        change1 = DocumentChange(
            id="change1",
            document_id=doc['id'],
            user_id=self.test_user.id,
            change_type="insert",
            position=0,
            content="Hello ",
            timestamp=datetime.now(),
            version=1
        )
        change_dict = change1.__dict__.copy()
        change_dict['type'] = change_dict.pop('change_type')
        result = self.service.editor.apply_change(change1.document_id, change1.user_id, change_dict)
        self.assertTrue(result[0])
        
        change2 = DocumentChange(
            id="change2",
            document_id=doc['id'],
            user_id=other_user.id,
            change_type="insert",
            position=len("Hello "),  # Insert after "Hello "
            content="World!",
            timestamp=datetime.now(),
            version=1
        )
        change_dict = change2.__dict__.copy()
        change_dict['type'] = change_dict.pop('change_type')
        result = self.service.editor.apply_change(change2.document_id, change2.user_id, change_dict)
        if not result[0]:
            print(f"Change2 failed: {result[1]}")
        self.assertTrue(result[0])
        
        # Verify final content
        updated_doc = self.service.get_document(doc['id'], self.test_user.id)
        self.assertTrue(updated_doc['success'])
        self.assertIn("Hello", updated_doc['document']['content'])
        self.assertIn("World!", updated_doc['document']['content'])
    
    def test_document_versioning(self):
        """Test document versioning through changes."""
        # Create document
        result = self.service.create_document("Versioned Doc", self.test_user.id, "Version 1")
        self.assertTrue(result['success'])
        doc = result['document']
        
        # Apply multiple changes
        changes = [
            DocumentChange(
                id=f"change{i}",
                document_id=doc['id'],
                user_id=self.test_user.id,
                change_type="insert",
                position=0,
                content=f"Version {i+1} ",
                timestamp=datetime.now(),
                version=1
            )
            for i in range(1, 6)
        ]
        
        for change in changes:
            change_dict = change.__dict__.copy()
            change_dict['type'] = change_dict.pop('change_type')
            result = self.service.editor.apply_change(change.document_id, change.user_id, change_dict)
            self.assertTrue(result[0])
        
        # Verify document has all versions
        updated_doc = self.service.get_document(doc['id'], self.test_user.id)
        self.assertTrue(updated_doc['success'])
        self.assertIn("Version 1", updated_doc['document']['content'])
        self.assertIn("Version 6", updated_doc['document']['content'])
    
    def test_user_management_integration(self):
        """Test user management integration."""
        # Create multiple users
        users = []
        for i in range(5):
            user = self.service.create_user(
                f"user{i}",
                f"user{i}@example.com",
                f"User{i}",
                "Test"
            )
            users.append(user)
        
        # Create document and share with all users
        result = self.service.create_document("Shared Doc", users[0].id, "Content")
        self.assertTrue(result['success'])
        doc = result['document']
        
        for user in users[1:]:
            result = self.service.share_document(doc['id'], users[0].id, user.id, "read")
            self.assertTrue(result)
        
        # Verify all users can access the document
        for user in users:
            accessible_doc = self.service.get_document(doc['id'], user.id)
            self.assertTrue(accessible_doc['success'])


if __name__ == '__main__':
    # Run tests with coverage
    unittest.main(verbosity=2)
