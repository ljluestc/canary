#!/usr/bin/env python3
"""
Comprehensive test suite for Quora-like Q&A Platform Service.
"""

import unittest
import tempfile
import os
import sys
import time
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from quora_service import (
    User, Question, Answer, Comment, Vote, QuoraDatabase,
    QuoraService, app
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
            reputation=100,
            bio="Test bio",
            location="Test City",
            website="https://example.com",
            created_at=now,
            last_active=now,
            is_verified=True,
            profile_image="image.jpg"
        )
        
        self.assertEqual(user.user_id, "user123")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.reputation, 100)
        self.assertEqual(user.bio, "Test bio")
        self.assertEqual(user.location, "Test City")
        self.assertEqual(user.website, "https://example.com")
        self.assertEqual(user.is_verified, True)
        self.assertEqual(user.profile_image, "image.jpg")
    
    def test_user_defaults(self):
        """Test User with default values."""
        user = User(
            user_id="user456",
            username="defaultuser",
            email="default@example.com"
        )
        
        self.assertEqual(user.reputation, 0)
        self.assertEqual(user.bio, "")
        self.assertEqual(user.location, "")
        self.assertEqual(user.website, "")
        self.assertEqual(user.is_verified, False)
        self.assertEqual(user.profile_image, "")
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.last_active)

class TestQuestion(unittest.TestCase):
    """Test Question model."""
    
    def test_question_creation(self):
        """Test Question creation with all fields."""
        now = datetime.now()
        question = Question(
            question_id="q123",
            title="Test Question",
            content="This is a test question",
            author_id="user123",
            tags=["test", "question"],
            views=10,
            upvotes=5,
            downvotes=1,
            is_answered=True,
            created_at=now,
            updated_at=now,
            is_anonymous=False,
            is_public=True,
            category="general"
        )
        
        self.assertEqual(question.question_id, "q123")
        self.assertEqual(question.title, "Test Question")
        self.assertEqual(question.content, "This is a test question")
        self.assertEqual(question.author_id, "user123")
        self.assertEqual(question.tags, ["test", "question"])
        self.assertEqual(question.views, 10)
        self.assertEqual(question.upvotes, 5)
        self.assertEqual(question.downvotes, 1)
        self.assertEqual(question.is_answered, True)
        self.assertEqual(question.is_anonymous, False)
        self.assertEqual(question.is_public, True)
        self.assertEqual(question.category, "general")
    
    def test_question_defaults(self):
        """Test Question with default values."""
        question = Question(
            question_id="q456",
            title="Default Question",
            content="Default content",
            author_id="user456",
            tags=[]
        )
        
        self.assertEqual(question.tags, [])
        self.assertEqual(question.views, 0)
        self.assertEqual(question.upvotes, 0)
        self.assertEqual(question.downvotes, 0)
        self.assertEqual(question.is_answered, False)
        self.assertEqual(question.is_anonymous, False)
        self.assertEqual(question.is_public, True)
        self.assertEqual(question.category, "general")
        self.assertIsNotNone(question.created_at)
        self.assertIsNotNone(question.updated_at)

class TestAnswer(unittest.TestCase):
    """Test Answer model."""
    
    def test_answer_creation(self):
        """Test Answer creation with all fields."""
        now = datetime.now()
        answer = Answer(
            answer_id="a123",
            question_id="q123",
            content="This is a test answer",
            author_id="user123",
            upvotes=3,
            downvotes=0,
            is_accepted=True,
            created_at=now,
            updated_at=now,
            is_anonymous=False
        )
        
        self.assertEqual(answer.answer_id, "a123")
        self.assertEqual(answer.question_id, "q123")
        self.assertEqual(answer.content, "This is a test answer")
        self.assertEqual(answer.author_id, "user123")
        self.assertEqual(answer.upvotes, 3)
        self.assertEqual(answer.downvotes, 0)
        self.assertEqual(answer.is_accepted, True)
        self.assertEqual(answer.is_anonymous, False)
    
    def test_answer_defaults(self):
        """Test Answer with default values."""
        answer = Answer(
            answer_id="a456",
            question_id="q456",
            content="Default answer",
            author_id="user456"
        )
        
        self.assertEqual(answer.upvotes, 0)
        self.assertEqual(answer.downvotes, 0)
        self.assertEqual(answer.is_accepted, False)
        self.assertEqual(answer.is_anonymous, False)
        self.assertIsNotNone(answer.created_at)
        self.assertIsNotNone(answer.updated_at)

class TestComment(unittest.TestCase):
    """Test Comment model."""
    
    def test_comment_creation(self):
        """Test Comment creation with all fields."""
        now = datetime.now()
        comment = Comment(
            comment_id="c123",
            parent_id="q123",
            parent_type="question",
            content="This is a test comment",
            author_id="user123",
            upvotes=2,
            downvotes=0,
            created_at=now,
            is_anonymous=False
        )
        
        self.assertEqual(comment.comment_id, "c123")
        self.assertEqual(comment.parent_id, "q123")
        self.assertEqual(comment.parent_type, "question")
        self.assertEqual(comment.content, "This is a test comment")
        self.assertEqual(comment.author_id, "user123")
        self.assertEqual(comment.upvotes, 2)
        self.assertEqual(comment.downvotes, 0)
        self.assertEqual(comment.is_anonymous, False)
    
    def test_comment_defaults(self):
        """Test Comment with default values."""
        comment = Comment(
            comment_id="c456",
            parent_id="a456",
            parent_type="answer",
            content="Default comment",
            author_id="user456"
        )
        
        self.assertEqual(comment.upvotes, 0)
        self.assertEqual(comment.downvotes, 0)
        self.assertEqual(comment.is_anonymous, False)
        self.assertIsNotNone(comment.created_at)

class TestVote(unittest.TestCase):
    """Test Vote model."""
    
    def test_vote_creation(self):
        """Test Vote creation with all fields."""
        now = datetime.now()
        vote = Vote(
            vote_id="v123",
            user_id="user123",
            target_id="q123",
            target_type="question",
            vote_type="upvote",
            created_at=now
        )
        
        self.assertEqual(vote.vote_id, "v123")
        self.assertEqual(vote.user_id, "user123")
        self.assertEqual(vote.target_id, "q123")
        self.assertEqual(vote.target_type, "question")
        self.assertEqual(vote.vote_type, "upvote")
    
    def test_vote_defaults(self):
        """Test Vote with default values."""
        vote = Vote(
            vote_id="v456",
            user_id="user456",
            target_id="a456",
            target_type="answer",
            vote_type="downvote"
        )
        
        self.assertIsNotNone(vote.created_at)

class TestQuoraDatabase(unittest.TestCase):
    """Test QuoraDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = QuoraDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization creates tables."""
        # Database should be initialized in setUp
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_user_success(self):
        """Test successful user saving."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com"
        )
        
        result = self.db.save_user(user)
        self.assertTrue(result)
    
    def test_get_user_existing(self):
        """Test getting existing user."""
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
    
    def test_save_question_success(self):
        """Test successful question saving."""
        question = Question(
            question_id="q123",
            title="Test Question",
            content="Test content",
            author_id="user123",
            tags=["test"]
        )
        
        result = self.db.save_question(question)
        self.assertTrue(result)
    
    def test_get_question_existing(self):
        """Test getting existing question."""
        question = Question(
            question_id="q123",
            title="Test Question",
            content="Test content",
            author_id="user123",
            tags=["test"]
        )
        
        self.db.save_question(question)
        retrieved_question = self.db.get_question("q123")
        
        self.assertIsNotNone(retrieved_question)
        self.assertEqual(retrieved_question.question_id, "q123")
        self.assertEqual(retrieved_question.title, "Test Question")
        self.assertEqual(retrieved_question.tags, ["test"])
    
    def test_get_question_nonexistent(self):
        """Test getting non-existent question."""
        retrieved_question = self.db.get_question("nonexistent")
        self.assertIsNone(retrieved_question)
    
    def test_get_questions_with_filters(self):
        """Test getting questions with filters."""
        # Create test questions
        question1 = Question(
            question_id="q1",
            title="Question 1",
            content="Content 1",
            author_id="user1",
            tags=["tag1"],
            category="tech"
        )
        question2 = Question(
            question_id="q2",
            title="Question 2",
            content="Content 2",
            author_id="user2",
            tags=["tag2"],
            category="general"
        )
        
        self.db.save_question(question1)
        self.db.save_question(question2)
        
        # Test category filter
        tech_questions = self.db.get_questions(category="tech")
        self.assertEqual(len(tech_questions), 1)
        self.assertEqual(tech_questions[0].category, "tech")
        
        # Test tag filter
        tag1_questions = self.db.get_questions(tags=["tag1"])
        self.assertEqual(len(tag1_questions), 1)
        self.assertIn("tag1", tag1_questions[0].tags)
    
    def test_save_answer_success(self):
        """Test successful answer saving."""
        answer = Answer(
            answer_id="a123",
            question_id="q123",
            content="Test answer",
            author_id="user123"
        )
        
        result = self.db.save_answer(answer)
        self.assertTrue(result)
    
    def test_get_answers(self):
        """Test getting answers for a question."""
        # Create test answers
        answer1 = Answer(
            answer_id="a1",
            question_id="q1",
            content="Answer 1",
            author_id="user1",
            upvotes=5
        )
        answer2 = Answer(
            answer_id="a2",
            question_id="q1",
            content="Answer 2",
            author_id="user2",
            upvotes=3
        )
        
        self.db.save_answer(answer1)
        self.db.save_answer(answer2)
        
        answers = self.db.get_answers("q1")
        self.assertEqual(len(answers), 2)
        # Should be ordered by upvotes DESC
        self.assertEqual(answers[0].upvotes, 5)
        self.assertEqual(answers[1].upvotes, 3)
    
    def test_save_comment_success(self):
        """Test successful comment saving."""
        comment = Comment(
            comment_id="c123",
            parent_id="q123",
            parent_type="question",
            content="Test comment",
            author_id="user123"
        )
        
        result = self.db.save_comment(comment)
        self.assertTrue(result)
    
    def test_get_comments(self):
        """Test getting comments for a question."""
        comment = Comment(
            comment_id="c1",
            parent_id="q1",
            parent_type="question",
            content="Test comment",
            author_id="user1"
        )
        
        self.db.save_comment(comment)
        comments = self.db.get_comments("q1", "question")
        
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].content, "Test comment")
    
    def test_save_vote_success(self):
        """Test successful vote saving."""
        vote = Vote(
            vote_id="v123",
            user_id="user123",
            target_id="q123",
            target_type="question",
            vote_type="upvote"
        )
        
        result = self.db.save_vote(vote)
        self.assertTrue(result)
    
    def test_get_vote_existing(self):
        """Test getting existing vote."""
        vote = Vote(
            vote_id="v123",
            user_id="user123",
            target_id="q123",
            target_type="question",
            vote_type="upvote"
        )
        
        self.db.save_vote(vote)
        retrieved_vote = self.db.get_vote("user123", "q123", "question")
        
        self.assertIsNotNone(retrieved_vote)
        self.assertEqual(retrieved_vote.vote_type, "upvote")
    
    def test_get_vote_nonexistent(self):
        """Test getting non-existent vote."""
        retrieved_vote = self.db.get_vote("user123", "nonexistent", "question")
        self.assertIsNone(retrieved_vote)
    
    def test_update_vote_counts(self):
        """Test updating vote counts."""
        # Create a question first
        question = Question(
            question_id="q123",
            title="Test Question",
            content="Test content",
            author_id="user123",
            tags=[]
        )
        self.db.save_question(question)
        
        # Add some votes
        vote1 = Vote(
            vote_id="v1",
            user_id="user1",
            target_id="q123",
            target_type="question",
            vote_type="upvote"
        )
        vote2 = Vote(
            vote_id="v2",
            user_id="user2",
            target_id="q123",
            target_type="question",
            vote_type="upvote"
        )
        vote3 = Vote(
            vote_id="v3",
            user_id="user3",
            target_id="q123",
            target_type="question",
            vote_type="downvote"
        )
        
        self.db.save_vote(vote1)
        self.db.save_vote(vote2)
        self.db.save_vote(vote3)
        
        # Update vote counts
        result = self.db.update_vote_counts("q123", "question")
        self.assertTrue(result)
        
        # Check updated question
        updated_question = self.db.get_question("q123")
        self.assertEqual(updated_question.upvotes, 2)
        self.assertEqual(updated_question.downvotes, 1)

class TestQuoraService(unittest.TestCase):
    """Test QuoraService class."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = QuoraService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_create_user_success(self):
        """Test successful user creation."""
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            bio="Test bio"
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.bio, "Test bio")
    
    def test_get_user_existing(self):
        """Test getting existing user."""
        user = self.service.create_user("testuser", "test@example.com")
        retrieved_user = self.service.get_user(user.user_id)
        
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "testuser")
    
    def test_get_user_nonexistent(self):
        """Test getting non-existent user."""
        retrieved_user = self.service.get_user("nonexistent")
        self.assertIsNone(retrieved_user)
    
    def test_ask_question_success(self):
        """Test successful question asking."""
        user = self.service.create_user("testuser", "test@example.com")
        question = self.service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id,
            tags=["test"],
            category="tech"
        )
        
        self.assertIsNotNone(question)
        self.assertEqual(question.title, "Test Question")
        self.assertEqual(question.author_id, user.user_id)
        self.assertEqual(question.tags, ["test"])
        self.assertEqual(question.category, "tech")
    
    def test_get_questions_with_filters(self):
        """Test getting questions with filters."""
        user = self.service.create_user("testuser", "test@example.com")
        
        # Create test questions
        question1 = self.service.ask_question(
            title="Tech Question",
            content="Tech content",
            author_id=user.user_id,
            category="tech"
        )
        question2 = self.service.ask_question(
            title="General Question",
            content="General content",
            author_id=user.user_id,
            category="general"
        )
        
        # Test category filter
        tech_questions = self.service.get_questions(category="tech")
        self.assertEqual(len(tech_questions), 1)
        self.assertEqual(tech_questions[0].category, "tech")
        
        # Test all questions
        all_questions = self.service.get_questions()
        self.assertEqual(len(all_questions), 2)
    
    def test_answer_question_success(self):
        """Test successful question answering."""
        user = self.service.create_user("testuser", "test@example.com")
        question = self.service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        answer = self.service.answer_question(
            question_id=question.question_id,
            content="Test answer",
            author_id=user.user_id
        )
        
        self.assertIsNotNone(answer)
        self.assertEqual(answer.question_id, question.question_id)
        self.assertEqual(answer.content, "Test answer")
        self.assertEqual(answer.author_id, user.user_id)
    
    def test_get_answers(self):
        """Test getting answers for a question."""
        user = self.service.create_user("testuser", "test@example.com")
        question = self.service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        answer = self.service.answer_question(
            question_id=question.question_id,
            content="Test answer",
            author_id=user.user_id
        )
        
        answers = self.service.get_answers(question.question_id)
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0].content, "Test answer")
    
    def test_add_comment_success(self):
        """Test successful comment adding."""
        user = self.service.create_user("testuser", "test@example.com")
        question = self.service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        comment = self.service.add_comment(
            parent_id=question.question_id,
            parent_type="question",
            content="Test comment",
            author_id=user.user_id
        )
        
        self.assertIsNotNone(comment)
        self.assertEqual(comment.parent_id, question.question_id)
        self.assertEqual(comment.parent_type, "question")
        self.assertEqual(comment.content, "Test comment")
    
    def test_get_comments(self):
        """Test getting comments for a question."""
        user = self.service.create_user("testuser", "test@example.com")
        question = self.service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        comment = self.service.add_comment(
            parent_id=question.question_id,
            parent_type="question",
            content="Test comment",
            author_id=user.user_id
        )
        
        comments = self.service.get_comments(question.question_id, "question")
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].content, "Test comment")
    
    def test_vote_success(self):
        """Test successful voting."""
        user = self.service.create_user("testuser", "test@example.com")
        question = self.service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        result = self.service.vote(
            user_id=user.user_id,
            target_id=question.question_id,
            target_type="question",
            vote_type="upvote"
        )
        
        self.assertTrue(result)
    
    def test_search_questions(self):
        """Test searching questions."""
        user = self.service.create_user("testuser", "test@example.com")
        
        question1 = self.service.ask_question(
            title="Python Programming",
            content="How to learn Python?",
            author_id=user.user_id
        )
        question2 = self.service.ask_question(
            title="JavaScript Tips",
            content="Best JavaScript practices",
            author_id=user.user_id
        )
        
        # Search for Python
        results = self.service.search_questions("Python")
        self.assertEqual(len(results), 1)
        self.assertIn("Python", results[0].title)
        
        # Search for JavaScript
        results = self.service.search_questions("JavaScript")
        self.assertEqual(len(results), 1)
        self.assertIn("JavaScript", results[0].title)
    
    def test_increment_views(self):
        """Test incrementing question views."""
        user = self.service.create_user("testuser", "test@example.com")
        question = self.service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        initial_views = question.views
        result = self.service.increment_views(question.question_id)
        
        self.assertTrue(result)
        
        # Check if views were incremented
        updated_question = self.service.get_question(question.question_id)
        self.assertEqual(updated_question.views, initial_views + 1)

class TestFlaskApp(unittest.TestCase):
    """Test Flask application endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        app.config['TESTING'] = True
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create a test service with the temp database
        global quora_service
        quora_service = QuoraService(self.temp_db.name)
        
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_index_page(self):
        """Test home page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Quora-like Q&A Platform', response.data)
    
    def test_get_questions_api(self):
        """Test get questions API."""
        # Create a test question
        user = quora_service.create_user("testuser", "test@example.com")
        quora_service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        response = self.client.get('/api/questions')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['questions']), 0)
    
    def test_create_question_api(self):
        """Test create question API."""
        response = self.client.post('/api/questions', json={
            'title': 'API Test Question',
            'content': 'This is a test question via API',
            'author_id': 'testuser',
            'tags': ['test', 'api'],
            'category': 'tech'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['question']['title'], 'API Test Question')
    
    def test_create_question_missing_fields(self):
        """Test create question API with missing fields."""
        response = self.client.post('/api/questions', json={
            'title': 'Incomplete Question'
            # Missing content
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_get_question_api(self):
        """Test get specific question API."""
        # Create a test question using the global service
        from quora_service import quora_service
        user = quora_service.create_user("testuser", "test@example.com")
        question = quora_service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        response = self.client.get(f'/api/questions/{question.question_id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['question']['question_id'], question.question_id)
    
    def test_get_question_nonexistent(self):
        """Test get non-existent question API."""
        response = self.client.get('/api/questions/nonexistent')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_create_answer_api(self):
        """Test create answer API."""
        # Create a test question first
        user = quora_service.create_user("testuser", "test@example.com")
        question = quora_service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        response = self.client.post(f'/api/questions/{question.question_id}/answers', json={
            'content': 'This is a test answer via API',
            'author_id': 'testuser'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['answer']['content'], 'This is a test answer via API')
    
    def test_vote_api(self):
        """Test vote API."""
        # Create a test question first
        user = quora_service.create_user("testuser", "test@example.com")
        question = quora_service.ask_question(
            title="Test Question",
            content="Test content",
            author_id=user.user_id
        )
        
        response = self.client.post('/api/vote', json={
            'user_id': user.user_id,
            'target_id': question.question_id,
            'target_type': 'question',
            'vote_type': 'upvote'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
    
    def test_vote_missing_fields(self):
        """Test vote API with missing fields."""
        response = self.client.post('/api/vote', json={
            'user_id': 'testuser',
            'target_id': 'test123'
            # Missing target_type and vote_type
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_search_api(self):
        """Test search API."""
        # Create a test question using the global service
        from quora_service import quora_service
        user = quora_service.create_user("testuser", "test@example.com")
        quora_service.ask_question(
            title="Python Programming",
            content="How to learn Python?",
            author_id=user.user_id
        )
        
        response = self.client.get('/api/search?q=Python')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['query'], 'Python')
        self.assertGreater(len(data['questions']), 0)
    
    def test_search_missing_query(self):
        """Test search API without query parameter."""
        response = self.client.get('/api/search')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
