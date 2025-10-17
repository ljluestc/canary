#!/usr/bin/env python3
"""
Quora-like Q&A Platform Service

A comprehensive question and answer platform with features like:
- Question posting and management
- Answer submission and voting
- User reputation system
- Topic categorization
- Search and filtering
- Real-time notifications
"""

import os
import sqlite3
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, render_template_string
import re
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class User:
    """User model for the Q&A platform."""
    user_id: str
    username: str
    email: str
    reputation: int = 0
    bio: str = ""
    location: str = ""
    website: str = ""
    created_at: datetime = None
    last_active: datetime = None
    is_verified: bool = False
    profile_image: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()

@dataclass
class Question:
    """Question model."""
    question_id: str
    title: str
    content: str
    author_id: str
    tags: List[str]
    views: int = 0
    upvotes: int = 0
    downvotes: int = 0
    is_answered: bool = False
    created_at: datetime = None
    updated_at: datetime = None
    is_anonymous: bool = False
    is_public: bool = True
    category: str = "general"
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Answer:
    """Answer model."""
    answer_id: str
    question_id: str
    content: str
    author_id: str
    upvotes: int = 0
    downvotes: int = 0
    is_accepted: bool = False
    created_at: datetime = None
    updated_at: datetime = None
    is_anonymous: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Comment:
    """Comment model for questions and answers."""
    comment_id: str
    parent_id: str  # question_id or answer_id
    parent_type: str  # "question" or "answer"
    content: str
    author_id: str
    upvotes: int = 0
    downvotes: int = 0
    created_at: datetime = None
    is_anonymous: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Vote:
    """Vote model for questions, answers, and comments."""
    vote_id: str
    user_id: str
    target_id: str  # question_id, answer_id, or comment_id
    target_type: str  # "question", "answer", or "comment"
    vote_type: str  # "upvote" or "downvote"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class QuoraDatabase:
    """Database operations for the Q&A platform."""
    
    def __init__(self, db_path: str = "quora.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        reputation INTEGER DEFAULT 0,
                        bio TEXT DEFAULT '',
                        location TEXT DEFAULT '',
                        website TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_verified BOOLEAN DEFAULT 0,
                        profile_image TEXT DEFAULT ''
                    )
                ''')
                
                # Questions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS questions (
                        question_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        author_id TEXT NOT NULL,
                        tags TEXT DEFAULT '[]',
                        views INTEGER DEFAULT 0,
                        upvotes INTEGER DEFAULT 0,
                        downvotes INTEGER DEFAULT 0,
                        is_answered BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_anonymous BOOLEAN DEFAULT 0,
                        is_public BOOLEAN DEFAULT 1,
                        category TEXT DEFAULT 'general',
                        FOREIGN KEY (author_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Answers table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS answers (
                        answer_id TEXT PRIMARY KEY,
                        question_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        author_id TEXT NOT NULL,
                        upvotes INTEGER DEFAULT 0,
                        downvotes INTEGER DEFAULT 0,
                        is_accepted BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_anonymous BOOLEAN DEFAULT 0,
                        FOREIGN KEY (question_id) REFERENCES questions (question_id),
                        FOREIGN KEY (author_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Comments table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        comment_id TEXT PRIMARY KEY,
                        parent_id TEXT NOT NULL,
                        parent_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        author_id TEXT NOT NULL,
                        upvotes INTEGER DEFAULT 0,
                        downvotes INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_anonymous BOOLEAN DEFAULT 0,
                        FOREIGN KEY (author_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Votes table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS votes (
                        vote_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        target_type TEXT NOT NULL,
                        vote_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, target_id, target_type),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Topics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS topics (
                        topic_id TEXT PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT DEFAULT '',
                        followers_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def save_user(self, user: User) -> bool:
        """Save user to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, email, reputation, bio, location, website, 
                     created_at, last_active, is_verified, profile_image)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.user_id, user.username, user.email, user.reputation,
                    user.bio, user.location, user.website, user.created_at,
                    user.last_active, user.is_verified, user.profile_image
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return User(
                        user_id=row[0], username=row[1], email=row[2],
                        reputation=row[3], bio=row[4], location=row[5],
                        website=row[6], created_at=row[7], last_active=row[8],
                        is_verified=bool(row[9]), profile_image=row[10]
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def save_question(self, question: Question) -> bool:
        """Save question to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO questions 
                    (question_id, title, content, author_id, tags, views, upvotes, 
                     downvotes, is_answered, created_at, updated_at, is_anonymous, 
                     is_public, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question.question_id, question.title, question.content,
                    question.author_id, json.dumps(question.tags), question.views,
                    question.upvotes, question.downvotes, question.is_answered,
                    question.created_at, question.updated_at, question.is_anonymous,
                    question.is_public, question.category
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving question: {e}")
            return False
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get question by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM questions WHERE question_id = ?', (question_id,))
                row = cursor.fetchone()
                
                if row:
                    return Question(
                        question_id=row[0], title=row[1], content=row[2],
                        author_id=row[3], tags=json.loads(row[4]), views=row[5],
                        upvotes=row[6], downvotes=row[7], is_answered=bool(row[8]),
                        created_at=row[9], updated_at=row[10], is_anonymous=bool(row[11]),
                        is_public=bool(row[12]), category=row[13]
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting question: {e}")
            return None
    
    def get_questions(self, limit: int = 50, offset: int = 0, 
                     category: str = None, tags: List[str] = None,
                     sort_by: str = "created_at") -> List[Question]:
        """Get questions with filtering and sorting."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM questions WHERE is_public = 1"
                params = []
                
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                if tags:
                    for tag in tags:
                        query += " AND tags LIKE ?"
                        params.append(f'%"{tag}"%')
                
                if sort_by == "created_at":
                    query += " ORDER BY created_at DESC"
                elif sort_by == "views":
                    query += " ORDER BY views DESC"
                elif sort_by == "upvotes":
                    query += " ORDER BY upvotes DESC"
                
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                questions = []
                for row in rows:
                    questions.append(Question(
                        question_id=row[0], title=row[1], content=row[2],
                        author_id=row[3], tags=json.loads(row[4]), views=row[5],
                        upvotes=row[6], downvotes=row[7], is_answered=bool(row[8]),
                        created_at=row[9], updated_at=row[10], is_anonymous=bool(row[11]),
                        is_public=bool(row[12]), category=row[13]
                    ))
                
                return questions
        except Exception as e:
            logger.error(f"Error getting questions: {e}")
            return []
    
    def save_answer(self, answer: Answer) -> bool:
        """Save answer to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO answers 
                    (answer_id, question_id, content, author_id, upvotes, 
                     downvotes, is_accepted, created_at, updated_at, is_anonymous)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    answer.answer_id, answer.question_id, answer.content,
                    answer.author_id, answer.upvotes, answer.downvotes,
                    answer.is_accepted, answer.created_at, answer.updated_at,
                    answer.is_anonymous
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving answer: {e}")
            return False
    
    def get_answers(self, question_id: str, limit: int = 50) -> List[Answer]:
        """Get answers for a question."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM answers 
                    WHERE question_id = ? 
                    ORDER BY upvotes DESC, created_at ASC 
                    LIMIT ?
                ''', (question_id, limit))
                rows = cursor.fetchall()
                
                answers = []
                for row in rows:
                    answers.append(Answer(
                        answer_id=row[0], question_id=row[1], content=row[2],
                        author_id=row[3], upvotes=row[4], downvotes=row[5],
                        is_accepted=bool(row[6]), created_at=row[7], updated_at=row[8],
                        is_anonymous=bool(row[9])
                    ))
                
                return answers
        except Exception as e:
            logger.error(f"Error getting answers: {e}")
            return []
    
    def save_comment(self, comment: Comment) -> bool:
        """Save comment to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO comments 
                    (comment_id, parent_id, parent_type, content, author_id, 
                     upvotes, downvotes, created_at, is_anonymous)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    comment.comment_id, comment.parent_id, comment.parent_type,
                    comment.content, comment.author_id, comment.upvotes,
                    comment.downvotes, comment.created_at, comment.is_anonymous
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving comment: {e}")
            return False
    
    def get_comments(self, parent_id: str, parent_type: str) -> List[Comment]:
        """Get comments for a question or answer."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM comments 
                    WHERE parent_id = ? AND parent_type = ? 
                    ORDER BY created_at ASC
                ''', (parent_id, parent_type))
                rows = cursor.fetchall()
                
                comments = []
                for row in rows:
                    comments.append(Comment(
                        comment_id=row[0], parent_id=row[1], parent_type=row[2],
                        content=row[3], author_id=row[4], upvotes=row[5],
                        downvotes=row[6], created_at=row[7], is_anonymous=bool(row[8])
                    ))
                
                return comments
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []
    
    def save_vote(self, vote: Vote) -> bool:
        """Save vote to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO votes 
                    (vote_id, user_id, target_id, target_type, vote_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    vote.vote_id, vote.user_id, vote.target_id, vote.target_type,
                    vote.vote_type, vote.created_at
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving vote: {e}")
            return False
    
    def get_vote(self, user_id: str, target_id: str, target_type: str) -> Optional[Vote]:
        """Get user's vote for a target."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM votes 
                    WHERE user_id = ? AND target_id = ? AND target_type = ?
                ''', (user_id, target_id, target_type))
                row = cursor.fetchone()
                
                if row:
                    return Vote(
                        vote_id=row[0], user_id=row[1], target_id=row[2],
                        target_type=row[3], vote_type=row[4], created_at=row[5]
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting vote: {e}")
            return None
    
    def update_vote_counts(self, target_id: str, target_type: str) -> bool:
        """Update vote counts for a target."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count upvotes and downvotes
                cursor.execute('''
                    SELECT COUNT(*) FROM votes 
                    WHERE target_id = ? AND target_type = ? AND vote_type = 'upvote'
                ''', (target_id, target_type))
                upvotes = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM votes 
                    WHERE target_id = ? AND target_type = ? AND vote_type = 'downvote'
                ''', (target_id, target_type))
                downvotes = cursor.fetchone()[0]
                
                # Update the target table
                if target_type == "question":
                    cursor.execute('''
                        UPDATE questions SET upvotes = ?, downvotes = ? 
                        WHERE question_id = ?
                    ''', (upvotes, downvotes, target_id))
                elif target_type == "answer":
                    cursor.execute('''
                        UPDATE answers SET upvotes = ?, downvotes = ? 
                        WHERE answer_id = ?
                    ''', (upvotes, downvotes, target_id))
                elif target_type == "comment":
                    cursor.execute('''
                        UPDATE comments SET upvotes = ?, downvotes = ? 
                        WHERE comment_id = ?
                    ''', (upvotes, downvotes, target_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating vote counts: {e}")
            return False

class QuoraService:
    """Main service class for the Q&A platform."""
    
    def __init__(self, db_path: str = "quora.db"):
        """Initialize the service."""
        self.db = QuoraDatabase(db_path)
    
    def create_user(self, username: str, email: str, **kwargs) -> Optional[User]:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            **kwargs
        )
        
        if self.db.save_user(user):
            return user
        return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.get_user(user_id)
    
    def ask_question(self, title: str, content: str, author_id: str, 
                    tags: List[str] = None, category: str = "general",
                    is_anonymous: bool = False) -> Optional[Question]:
        """Ask a new question."""
        question_id = str(uuid.uuid4())
        question = Question(
            question_id=question_id,
            title=title,
            content=content,
            author_id=author_id,
            tags=tags or [],
            category=category,
            is_anonymous=is_anonymous
        )
        
        if self.db.save_question(question):
            return question
        return None
    
    def get_questions(self, limit: int = 50, offset: int = 0, 
                     category: str = None, tags: List[str] = None,
                     sort_by: str = "created_at") -> List[Question]:
        """Get questions with filtering."""
        return self.db.get_questions(limit, offset, category, tags, sort_by)
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get question by ID."""
        return self.db.get_question(question_id)
    
    def answer_question(self, question_id: str, content: str, author_id: str,
                       is_anonymous: bool = False) -> Optional[Answer]:
        """Answer a question."""
        answer_id = str(uuid.uuid4())
        answer = Answer(
            answer_id=answer_id,
            question_id=question_id,
            content=content,
            author_id=author_id,
            is_anonymous=is_anonymous
        )
        
        if self.db.save_answer(answer):
            return answer
        return None
    
    def get_answers(self, question_id: str) -> List[Answer]:
        """Get answers for a question."""
        return self.db.get_answers(question_id)
    
    def add_comment(self, parent_id: str, parent_type: str, content: str,
                   author_id: str, is_anonymous: bool = False) -> Optional[Comment]:
        """Add a comment to a question or answer."""
        comment_id = str(uuid.uuid4())
        comment = Comment(
            comment_id=comment_id,
            parent_id=parent_id,
            parent_type=parent_type,
            content=content,
            author_id=author_id,
            is_anonymous=is_anonymous
        )
        
        if self.db.save_comment(comment):
            return comment
        return None
    
    def get_comments(self, parent_id: str, parent_type: str) -> List[Comment]:
        """Get comments for a question or answer."""
        return self.db.get_comments(parent_id, parent_type)
    
    def vote(self, user_id: str, target_id: str, target_type: str, 
             vote_type: str) -> bool:
        """Vote on a question, answer, or comment."""
        # Check if user already voted
        existing_vote = self.db.get_vote(user_id, target_id, target_type)
        
        if existing_vote and existing_vote.vote_type == vote_type:
            # User is trying to vote the same way, remove the vote
            vote_id = str(uuid.uuid4())
            vote = Vote(
                vote_id=vote_id,
                user_id=user_id,
                target_id=target_id,
                target_type=target_type,
                vote_type="none"  # Special type to indicate removal
            )
        else:
            vote_id = str(uuid.uuid4())
            vote = Vote(
                vote_id=vote_id,
                user_id=user_id,
                target_id=target_id,
                target_type=target_type,
                vote_type=vote_type
            )
        
        if self.db.save_vote(vote):
            # Update vote counts
            self.db.update_vote_counts(target_id, target_type)
            return True
        return False
    
    def search_questions(self, query: str, limit: int = 20) -> List[Question]:
        """Search questions by title and content."""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM questions 
                    WHERE is_public = 1 AND (
                        title LIKE ? OR content LIKE ?
                    )
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', limit))
                rows = cursor.fetchall()
                
                questions = []
                for row in rows:
                    questions.append(Question(
                        question_id=row[0], title=row[1], content=row[2],
                        author_id=row[3], tags=json.loads(row[4]), views=row[5],
                        upvotes=row[6], downvotes=row[7], is_answered=bool(row[8]),
                        created_at=row[9], updated_at=row[10], is_anonymous=bool(row[11]),
                        is_public=bool(row[12]), category=row[13]
                    ))
                
                return questions
        except Exception as e:
            logger.error(f"Error searching questions: {e}")
            return []
    
    def increment_views(self, question_id: str) -> bool:
        """Increment view count for a question."""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE questions SET views = views + 1 
                    WHERE question_id = ?
                ''', (question_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error incrementing views: {e}")
            return False

# Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize service
quora_service = QuoraService()

@app.route('/')
def index():
    """Home page."""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quora-like Q&A Platform</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .question { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px; }
            .question h3 { color: #333; margin-top: 0; }
            .question-meta { color: #666; font-size: 0.9em; }
            .tags { margin-top: 10px; }
            .tag { background: #e1ecf4; color: #39739d; padding: 2px 6px; margin: 2px; border-radius: 3px; font-size: 0.8em; }
        </style>
    </head>
    <body>
        <h1>Quora-like Q&A Platform</h1>
        <p>Ask questions, get answers, and share knowledge!</p>
        
        <h2>Recent Questions</h2>
        <div id="questions">
            <p>Loading questions...</p>
        </div>
        
        <script>
            fetch('/api/questions')
                .then(response => response.json())
                .then(data => {
                    const questionsDiv = document.getElementById('questions');
                    if (data.questions && data.questions.length > 0) {
                        questionsDiv.innerHTML = data.questions.map(q => `
                            <div class="question">
                                <h3><a href="/question/${q.question_id}">${q.title}</a></h3>
                                <p>${q.content.substring(0, 200)}...</p>
                                <div class="question-meta">
                                    Asked by ${q.is_anonymous ? 'Anonymous' : q.author_id} • 
                                    ${q.views} views • ${q.upvotes} upvotes
                                </div>
                                <div class="tags">
                                    ${q.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                                </div>
                            </div>
                        `).join('');
                    } else {
                        questionsDiv.innerHTML = '<p>No questions found.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('questions').innerHTML = '<p>Error loading questions.</p>';
                });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """Get questions API."""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    category = request.args.get('category')
    sort_by = request.args.get('sort_by', 'created_at')
    
    questions = quora_service.get_questions(limit, offset, category, None, sort_by)
    
    return jsonify({
        'success': True,
        'questions': [asdict(q) for q in questions],
        'total': len(questions)
    })

@app.route('/api/questions', methods=['POST'])
def create_question():
    """Create question API."""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'success': False, 'error': 'Title and content are required'})
    
    question = quora_service.ask_question(
        title=data['title'],
        content=data['content'],
        author_id=data.get('author_id', 'anonymous'),
        tags=data.get('tags', []),
        category=data.get('category', 'general'),
        is_anonymous=data.get('is_anonymous', False)
    )
    
    if question:
        return jsonify({'success': True, 'question': asdict(question)})
    else:
        return jsonify({'success': False, 'error': 'Failed to create question'})

@app.route('/api/questions/<question_id>', methods=['GET'])
def get_question(question_id):
    """Get specific question API."""
    question = quora_service.get_question(question_id)
    
    if question:
        # Increment view count
        quora_service.increment_views(question_id)
        
        # Get answers
        answers = quora_service.get_answers(question_id)
        
        return jsonify({
            'success': True,
            'question': asdict(question),
            'answers': [asdict(a) for a in answers]
        })
    else:
        return jsonify({'success': False, 'error': 'Question not found'})

@app.route('/api/questions/<question_id>/answers', methods=['POST'])
def create_answer(question_id):
    """Create answer API."""
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'Content is required'})
    
    answer = quora_service.answer_question(
        question_id=question_id,
        content=data['content'],
        author_id=data.get('author_id', 'anonymous'),
        is_anonymous=data.get('is_anonymous', False)
    )
    
    if answer:
        return jsonify({'success': True, 'answer': asdict(answer)})
    else:
        return jsonify({'success': False, 'error': 'Failed to create answer'})

@app.route('/api/vote', methods=['POST'])
def vote():
    """Vote API."""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['user_id', 'target_id', 'target_type', 'vote_type']):
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    success = quora_service.vote(
        user_id=data['user_id'],
        target_id=data['target_id'],
        target_type=data['target_type'],
        vote_type=data['vote_type']
    )
    
    return jsonify({'success': success})

@app.route('/api/search', methods=['GET'])
def search():
    """Search questions API."""
    query = request.args.get('q')
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter is required'})
    
    limit = request.args.get('limit', 20, type=int)
    questions = quora_service.search_questions(query, limit)
    
    return jsonify({
        'success': True,
        'questions': [asdict(q) for q in questions],
        'query': query
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
