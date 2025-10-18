"""
Google Docs System Implementation
Real-time collaborative document editing with conflict resolution
"""

import time
import threading
import uuid
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json
import redis
from enum import Enum
import hashlib
import difflib

class OperationType(Enum):
    INSERT = "insert"
    DELETE = "delete"
    FORMAT = "format"
    CURSOR_MOVE = "cursor_move"
    SELECTION = "selection"

class TextFormat(Enum):
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    FONT_SIZE = "font_size"
    FONT_COLOR = "font_color"
    BACKGROUND_COLOR = "background_color"

@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    email: str
    created_at: datetime
    is_online: bool = False
    last_seen: Optional[datetime] = None

@dataclass
class Document:
    """Document data structure"""
    doc_id: str
    title: str
    content: str
    owner_id: str
    created_at: datetime
    modified_at: datetime
    version: int = 1
    collaborators: Set[str] = field(default_factory=set)
    is_public: bool = False
    permissions: Dict[str, str] = field(default_factory=dict)  # user_id -> permission

@dataclass
class Operation:
    """Operation data structure"""
    op_id: str
    doc_id: str
    user_id: str
    op_type: OperationType
    position: int
    content: str = ""
    length: int = 0
    format: Optional[TextFormat] = None
    format_value: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    version: int = 1

@dataclass
class Cursor:
    """Cursor position data structure"""
    user_id: str
    position: int
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DocumentSnapshot:
    """Document snapshot for version control"""
    doc_id: str
    content: str
    version: int
    timestamp: datetime
    operations: List[Operation] = field(default_factory=list)

class GoogleDocsSystem:
    """Real-time collaborative document editing system"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Core data structures
        self.users = {}  # user_id -> User
        self.documents = {}  # doc_id -> Document
        self.operations = defaultdict(list)  # doc_id -> List[Operation]
        self.cursors = defaultdict(dict)  # doc_id -> {user_id -> Cursor}
        self.document_snapshots = defaultdict(list)  # doc_id -> List[DocumentSnapshot]
        
        # Threading
        self.lock = threading.RLock()
        self.operation_processor = threading.Thread(target=self._process_operations, daemon=True)
        self.operation_processor.start()
        
        # Configuration
        self.max_operations_per_doc = 10000
        self.snapshot_interval = 100  # Create snapshot every 100 operations
        self.cursor_timeout = 30  # seconds
        self.conflict_resolution_strategy = "last_writer_wins"
    
    def create_user(self, user_id: str, username: str, email: str) -> User:
        """Create a new user"""
        with self.lock:
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                created_at=datetime.now()
            )
            self.users[user_id] = user
            self._persist_user(user)
            return user
    
    def create_document(self, user_id: str, title: str, content: str = "", is_public: bool = False) -> Document:
        """Create a new document"""
        with self.lock:
            doc_id = str(uuid.uuid4())
            document = Document(
                doc_id=doc_id,
                title=title,
                content=content,
                owner_id=user_id,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                is_public=is_public
            )
            
            # Add owner as collaborator
            document.collaborators.add(user_id)
            document.permissions[user_id] = "edit"
            
            self.documents[doc_id] = document
            self.operations[doc_id] = []
            
            # Create initial snapshot
            self._create_snapshot(doc_id)
            
            self._persist_document(document)
            return document
    
    def add_collaborator(self, doc_id: str, owner_id: str, collaborator_id: str, permission: str = "edit") -> bool:
        """Add a collaborator to a document"""
        with self.lock:
            if doc_id not in self.documents:
                return False
            
            document = self.documents[doc_id]
            if document.owner_id != owner_id:
                return False
            
            document.collaborators.add(collaborator_id)
            document.permissions[collaborator_id] = permission
            
            self._persist_document(document)
            return True
    
    def remove_collaborator(self, doc_id: str, owner_id: str, collaborator_id: str) -> bool:
        """Remove a collaborator from a document"""
        with self.lock:
            if doc_id not in self.documents:
                return False
            
            document = self.documents[doc_id]
            if document.owner_id != owner_id:
                return False
            
            document.collaborators.discard(collaborator_id)
            document.permissions.pop(collaborator_id, None)
            
            # Remove cursor if exists
            if doc_id in self.cursors and collaborator_id in self.cursors[doc_id]:
                del self.cursors[doc_id][collaborator_id]
            
            self._persist_document(document)
            return True
    
    def apply_operation(self, doc_id: str, user_id: str, op_type: OperationType, 
                       position: int, content: str = "", length: int = 0,
                       format: Optional[TextFormat] = None, format_value: Optional[str] = None) -> bool:
        """Apply an operation to a document"""
        with self.lock:
            if doc_id not in self.documents:
                return False
            
            document = self.documents[doc_id]
            if user_id not in document.collaborators:
                return False
            
            # Create operation
            operation = Operation(
                op_id=str(uuid.uuid4()),
                doc_id=doc_id,
                user_id=user_id,
                op_type=op_type,
                position=position,
                content=content,
                length=length,
                format=format,
                format_value=format_value,
                version=document.version + 1
            )
            
            # Apply operation to document
            success = self._apply_operation_to_document(document, operation)
            
            if success:
                # Store operation
                self.operations[doc_id].append(operation)
                document.version += 1
                document.modified_at = datetime.now()
                
                # Create snapshot if needed
                if len(self.operations[doc_id]) % self.snapshot_interval == 0:
                    self._create_snapshot(doc_id)
                
                # Persist changes
                self._persist_document(document)
                self._persist_operation(operation)
            
            return success
    
    def _apply_operation_to_document(self, document: Document, operation: Operation) -> bool:
        """Apply operation to document content"""
        try:
            if operation.op_type == OperationType.INSERT:
                # Insert text at position
                if operation.position > len(document.content):
                    return False
                
                document.content = (document.content[:operation.position] + 
                                  operation.content + 
                                  document.content[operation.position:])
                
            elif operation.op_type == OperationType.DELETE:
                # Delete text at position
                if operation.position + operation.length > len(document.content):
                    return False
                
                document.content = (document.content[:operation.position] + 
                                  document.content[operation.position + operation.length:])
                
            elif operation.op_type == OperationType.FORMAT:
                # Apply formatting (simplified - in real implementation would use rich text)
                # For now, just update the content
                pass
            
            return True
            
        except Exception as e:
            print(f"Error applying operation: {e}")
            return False
    
    def get_document(self, doc_id: str, user_id: str) -> Optional[Document]:
        """Get document if user has access"""
        with self.lock:
            if doc_id not in self.documents:
                return None
            
            document = self.documents[doc_id]
            if (user_id not in document.collaborators and 
                not document.is_public and 
                document.owner_id != user_id):
                return None
            
            return document
    
    def get_document_operations(self, doc_id: str, user_id: str, since_version: int = 0) -> List[Operation]:
        """Get operations since a specific version"""
        with self.lock:
            if doc_id not in self.documents:
                return []
            
            document = self.documents[doc_id]
            if user_id not in document.collaborators:
                return []
            
            operations = self.operations[doc_id]
            return [op for op in operations if op.version > since_version]
    
    def update_cursor(self, doc_id: str, user_id: str, position: int, 
                     selection_start: Optional[int] = None, selection_end: Optional[int] = None) -> bool:
        """Update user's cursor position"""
        with self.lock:
            if doc_id not in self.documents:
                return False
            
            document = self.documents[doc_id]
            if user_id not in document.collaborators:
                return False
            
            cursor = Cursor(
                user_id=user_id,
                position=position,
                selection_start=selection_start,
                selection_end=selection_end
            )
            
            self.cursors[doc_id][user_id] = cursor
            self._persist_cursor(doc_id, cursor)
            return True
    
    def get_document_cursors(self, doc_id: str, user_id: str) -> Dict[str, Cursor]:
        """Get all cursors for a document"""
        with self.lock:
            if doc_id not in self.documents:
                return {}
            
            document = self.documents[doc_id]
            if user_id not in document.collaborators:
                return {}
            
            # Filter out expired cursors
            current_time = datetime.now()
            active_cursors = {}
            
            for uid, cursor in self.cursors[doc_id].items():
                if uid != user_id:  # Don't return own cursor
                    time_diff = (current_time - cursor.timestamp).total_seconds()
                    if time_diff < self.cursor_timeout:
                        active_cursors[uid] = cursor
            
            return active_cursors
    
    def search_documents(self, user_id: str, query: str, limit: int = 50) -> List[Document]:
        """Search documents by content"""
        with self.lock:
            results = []
            query_lower = query.lower()
            
            for document in self.documents.values():
                # Check access
                if (user_id not in document.collaborators and 
                    not document.is_public and 
                    document.owner_id != user_id):
                    continue
                
                # Search in title and content
                if (query_lower in document.title.lower() or 
                    query_lower in document.content.lower()):
                    results.append(document)
            
            # Sort by modification time
            results.sort(key=lambda x: x.modified_at, reverse=True)
            return results[:limit]
    
    def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        with self.lock:
            results = []
            
            for document in self.documents.values():
                if (user_id in document.collaborators or 
                    document.owner_id == user_id):
                    results.append(document)
            
            # Sort by modification time
            results.sort(key=lambda x: x.modified_at, reverse=True)
            return results
    
    def get_document_history(self, doc_id: str, user_id: str) -> List[DocumentSnapshot]:
        """Get document version history"""
        with self.lock:
            if doc_id not in self.documents:
                return []
            
            document = self.documents[doc_id]
            if user_id not in document.collaborators:
                return []
            
            return self.document_snapshots[doc_id]
    
    def restore_document_version(self, doc_id: str, user_id: str, version: int) -> bool:
        """Restore document to a specific version"""
        with self.lock:
            if doc_id not in self.documents:
                return False
            
            document = self.documents[doc_id]
            if user_id != document.owner_id:
                return False
            
            # Find snapshot
            snapshot = None
            for snap in self.document_snapshots[doc_id]:
                if snap.version == version:
                    snapshot = snap
                    break
            
            if not snapshot:
                return False
            
            # Restore document
            document.content = snapshot.content
            document.version = version
            document.modified_at = datetime.now()
            
            # Remove operations after this version
            self.operations[doc_id] = [op for op in self.operations[doc_id] if op.version <= version]
            
            self._persist_document(document)
            return True
    
    def _create_snapshot(self, doc_id: str):
        """Create a document snapshot"""
        if doc_id not in self.documents:
            return
        
        document = self.documents[doc_id]
        operations = self.operations[doc_id]
        
        snapshot = DocumentSnapshot(
            doc_id=doc_id,
            content=document.content,
            version=document.version,
            timestamp=datetime.now(),
            operations=operations[-self.snapshot_interval:] if operations else []
        )
        
        self.document_snapshots[doc_id].append(snapshot)
        
        # Keep only recent snapshots
        if len(self.document_snapshots[doc_id]) > 100:
            self.document_snapshots[doc_id] = self.document_snapshots[doc_id][-100:]
    
    def _process_operations(self):
        """Process operations in background"""
        while True:
            try:
                time.sleep(1)  # Process every second
                
                with self.lock:
                    # Clean up expired cursors
                    current_time = datetime.now()
                    for doc_id in list(self.cursors.keys()):
                        expired_users = []
                        for user_id, cursor in self.cursors[doc_id].items():
                            time_diff = (current_time - cursor.timestamp).total_seconds()
                            if time_diff > self.cursor_timeout:
                                expired_users.append(user_id)
                        
                        for user_id in expired_users:
                            del self.cursors[doc_id][user_id]
                
            except Exception as e:
                print(f"Error in operation processor: {e}")
    
    def _persist_user(self, user: User):
        """Persist user to Redis"""
        user_data = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'is_online': str(user.is_online),
            'last_seen': user.last_seen.isoformat() if user.last_seen else None
        }
        self.redis_client.hset(f"user:{user.user_id}", mapping=user_data)
    
    def _persist_document(self, document: Document):
        """Persist document to Redis"""
        document_data = {
            'doc_id': document.doc_id,
            'title': document.title,
            'content': document.content,
            'owner_id': document.owner_id,
            'created_at': document.created_at.isoformat(),
            'modified_at': document.modified_at.isoformat(),
            'version': str(document.version),
            'collaborators': json.dumps(list(document.collaborators)),
            'is_public': str(document.is_public),
            'permissions': json.dumps(document.permissions)
        }
        self.redis_client.hset(f"document:{document.doc_id}", mapping=document_data)
    
    def _persist_operation(self, operation: Operation):
        """Persist operation to Redis"""
        operation_data = {
            'op_id': operation.op_id,
            'doc_id': operation.doc_id,
            'user_id': operation.user_id,
            'op_type': operation.op_type.value,
            'position': str(operation.position),
            'content': operation.content,
            'length': str(operation.length),
            'format': operation.format.value if operation.format else '',
            'format_value': operation.format_value or '',
            'timestamp': operation.timestamp.isoformat(),
            'version': str(operation.version)
        }
        self.redis_client.hset(f"operation:{operation.op_id}", mapping=operation_data)
    
    def _persist_cursor(self, doc_id: str, cursor: Cursor):
        """Persist cursor to Redis"""
        cursor_data = {
            'user_id': cursor.user_id,
            'position': str(cursor.position),
            'selection_start': str(cursor.selection_start) if cursor.selection_start else '',
            'selection_end': str(cursor.selection_end) if cursor.selection_end else '',
            'timestamp': cursor.timestamp.isoformat()
        }
        self.redis_client.hset(f"cursor:{doc_id}:{cursor.user_id}", mapping=cursor_data)
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        with self.lock:
            total_operations = sum(len(ops) for ops in self.operations.values())
            total_cursors = sum(len(cursors) for cursors in self.cursors.values())
            
            return {
                'total_users': len(self.users),
                'total_documents': len(self.documents),
                'total_operations': total_operations,
                'total_cursors': total_cursors,
                'average_operations_per_doc': total_operations / max(len(self.documents), 1),
                'documents_with_collaborators': len([doc for doc in self.documents.values() if len(doc.collaborators) > 1])
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize system
    docs_system = GoogleDocsSystem()
    
    # Create users
    user1 = docs_system.create_user("user1", "alice", "alice@example.com")
    user2 = docs_system.create_user("user2", "bob", "bob@example.com")
    
    # Create document
    doc = docs_system.create_document("user1", "My Document", "Hello, World!")
    
    # Add collaborator
    docs_system.add_collaborator(doc.doc_id, "user1", "user2", "edit")
    
    # Apply operations
    docs_system.apply_operation(doc.doc_id, "user1", OperationType.INSERT, 12, " This is a test.")
    docs_system.apply_operation(doc.doc_id, "user2", OperationType.INSERT, 0, "Collaborative editing: ")
    
    # Update cursors
    docs_system.update_cursor(doc.doc_id, "user1", 25)
    docs_system.update_cursor(doc.doc_id, "user2", 30)
    
    # Get document
    updated_doc = docs_system.get_document(doc.doc_id, "user1")
    print(f"Document content: {updated_doc.content}")
    
    # Get cursors
    cursors = docs_system.get_document_cursors(doc.doc_id, "user1")
    print(f"Active cursors: {len(cursors)}")
    
    # Get system stats
    stats = docs_system.get_system_stats()
    print(f"System stats: {stats}")
