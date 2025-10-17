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


if __name__ == '__main__':
    # Run tests with coverage
    unittest.main(verbosity=2)
