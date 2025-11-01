#!/usr/bin/env python3
"""
Comprehensive tests for Book Subscription Service.

Tests all functionality including user management, subscription handling,
book search, reading progress tracking, reviews, and recommendations.
"""

import unittest
import tempfile
import os
import sys
import time
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from book_subscription_service import (
    BookSubscriptionService, BookSubscriptionDatabase,
    User, Book, Subscription, ReadingProgress, BookReview, Payment,
    SubscriptionStatus, PaymentStatus, SubscriptionTier, BookStatus, ReadingStatus
)

class TestBookSubscriptionDatabase(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = BookSubscriptionDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_save_and_get_user(self):
        """Test saving and retrieving user."""
        user = User(
            user_id="user_001",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Save user
        self.assertTrue(self.db.save_user(user))
        
        # Retrieve user
        retrieved_user = self.db.get_user("user_001")
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "testuser")
        self.assertEqual(retrieved_user.email, "test@example.com")
    
    def test_save_and_get_book(self):
        """Test saving and retrieving book."""
        book = Book(
            book_id="book_001",
            title="Test Book",
            author="Test Author",
            isbn="1234567890",
            description="A test book",
            genre="Fiction"
        )
        
        # Save book
        self.assertTrue(self.db.save_book(book))
        
        # Retrieve book
        retrieved_book = self.db.get_book("book_001")
        self.assertIsNotNone(retrieved_book)
        self.assertEqual(retrieved_book.title, "Test Book")
        self.assertEqual(retrieved_book.author, "Test Author")
    
    def test_search_books(self):
        """Test book search functionality."""
        # Add test books
        books = [
            Book(
                book_id="book_001",
                title="Python Programming",
                author="John Doe",
                isbn="1234567890",
                description="Learn Python programming",
                genre="Programming"
            ),
            Book(
                book_id="book_002",
                title="Java Programming",
                author="Jane Smith",
                isbn="0987654321",
                description="Learn Java programming",
                genre="Programming"
            ),
            Book(
                book_id="book_003",
                title="Fiction Novel",
                author="John Doe",
                isbn="1122334455",
                description="A great fiction story",
                genre="Fiction"
            )
        ]
        
        for book in books:
            self.db.save_book(book)
        
        # Search by query
        results = self.db.search_books(query="Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Python Programming")
        
        # Search by genre
        results = self.db.search_books(genre="Programming")
        self.assertEqual(len(results), 2)
        
        # Search by author
        results = self.db.search_books(author="John Doe")
        self.assertEqual(len(results), 2)
    
    def test_subscription_operations(self):
        """Test subscription operations."""
        # Create user first
        user = User(
            user_id="user_001",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        self.db.save_user(user)
        
        # Create subscription
        subscription = Subscription(
            subscription_id="sub_001",
            user_id="user_001",
            tier=SubscriptionTier.PREMIUM,
            price=19.99,
            payment_frequency="monthly"
        )
        
        # Save subscription
        self.assertTrue(self.db.save_subscription(subscription))
        
        # Get user subscription
        retrieved_subscription = self.db.get_user_subscription("user_001")
        self.assertIsNotNone(retrieved_subscription)
        self.assertEqual(retrieved_subscription.tier, SubscriptionTier.PREMIUM)
        self.assertEqual(retrieved_subscription.price, 19.99)
    
    def test_reading_progress_operations(self):
        """Test reading progress operations."""
        # Create user and book first
        user = User(
            user_id="user_001",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        self.db.save_user(user)
        
        book = Book(
            book_id="book_001",
            title="Test Book",
            author="Test Author",
            isbn="1234567890",
            description="A test book",
            genre="Fiction",
            page_count=100
        )
        self.db.save_book(book)
        
        # Create reading progress
        progress = ReadingProgress(
            progress_id="progress_001",
            user_id="user_001",
            book_id="book_001",
            status=ReadingStatus.READING,
            current_page=25,
            total_pages=100,
            progress_percentage=25.0,
            time_spent_minutes=60
        )
        
        # Save progress
        self.assertTrue(self.db.save_reading_progress(progress))
        
        # Get progress
        retrieved_progress = self.db.get_reading_progress("user_001", "book_001")
        self.assertIsNotNone(retrieved_progress)
        self.assertEqual(retrieved_progress.current_page, 25)
        self.assertEqual(retrieved_progress.progress_percentage, 25.0)
    
    def test_book_review_operations(self):
        """Test book review operations."""
        # Create user and book first
        user = User(
            user_id="user_001",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        self.db.save_user(user)
        
        book = Book(
            book_id="book_001",
            title="Test Book",
            author="Test Author",
            isbn="1234567890",
            description="A test book",
            genre="Fiction"
        )
        self.db.save_book(book)
        
        # Create review
        review = BookReview(
            review_id="review_001",
            user_id="user_001",
            book_id="book_001",
            rating=5,
            review_text="Great book!",
            is_verified_purchase=True
        )
        
        # Save review
        self.assertTrue(self.db.save_book_review(review))
        
        # Get reviews
        reviews = self.db.get_book_reviews("book_001")
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].rating, 5)
        self.assertEqual(reviews[0].review_text, "Great book!")

class TestBookSubscriptionService(unittest.TestCase):
    """Test book subscription service."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = BookSubscriptionService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_create_user(self):
        """Test user creation."""
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.user_id.startswith("user_"))
    
    def test_get_user(self):
        """Test user retrieval."""
        # Create user
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Retrieve user
        retrieved_user = self.service.get_user(user.user_id)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "testuser")
    
    def test_create_subscription(self):
        """Test subscription creation."""
        # Create user first
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Create subscription
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.PREMIUM,
            price=19.99,
            payment_frequency="monthly"
        )
        
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription.tier, SubscriptionTier.PREMIUM)
        self.assertEqual(subscription.price, 19.99)
        self.assertEqual(subscription.user_id, user.user_id)
    
    def test_get_user_subscription(self):
        """Test user subscription retrieval."""
        # Create user and subscription
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.PREMIUM,
            price=19.99
        )
        
        # Get subscription
        retrieved_subscription = self.service.get_user_subscription(user.user_id)
        self.assertIsNotNone(retrieved_subscription)
        self.assertEqual(retrieved_subscription.tier, SubscriptionTier.PREMIUM)
    
    def test_can_access_book(self):
        """Test book access control."""
        # Create user with basic subscription
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        # Test access to basic book
        self.assertTrue(self.service.can_access_book(user.user_id, "book_001"))
        
        # Test access to premium book (should fail)
        self.assertFalse(self.service.can_access_book(user.user_id, "book_003"))
    
    def test_start_reading(self):
        """Test starting to read a book."""
        # Create user with subscription
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        # Start reading
        progress = self.service.start_reading(user.user_id, "book_001")
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress.status, ReadingStatus.READING)
        self.assertEqual(progress.user_id, user.user_id)
        self.assertEqual(progress.book_id, "book_001")
    
    def test_update_reading_progress(self):
        """Test updating reading progress."""
        # Create user with subscription
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        # Start reading
        self.service.start_reading(user.user_id, "book_001")
        
        # Update progress
        progress = self.service.update_reading_progress(
            user_id=user.user_id,
            book_id="book_001",
            current_page=50,
            time_spent_minutes=30
        )
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress.current_page, 50)
        self.assertEqual(progress.time_spent_minutes, 30)
        # The book has 180 pages, so 50 pages = 27.78%
        self.assertAlmostEqual(progress.progress_percentage, 27.78, places=1)
    
    def test_search_books(self):
        """Test book search."""
        # Search without user (should return all books)
        books = self.service.search_books(query="Gatsby")
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].title, "The Great Gatsby")
        
        # Search with user (should filter by access)
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        books = self.service.search_books(query="Gatsby", user_id=user.user_id)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].title, "The Great Gatsby")
    
    def test_add_book_review(self):
        """Test adding book review."""
        # Create user with subscription
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        # Add review
        review = self.service.add_book_review(
            user_id=user.user_id,
            book_id="book_001",
            rating=5,
            review_text="Excellent book!"
        )
        
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.review_text, "Excellent book!")
        self.assertEqual(review.user_id, user.user_id)
        self.assertEqual(review.book_id, "book_001")
    
    def test_add_book_review_invalid_rating(self):
        """Test adding book review with invalid rating."""
        # Create user with subscription
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        # Add review with invalid rating
        review = self.service.add_book_review(
            user_id=user.user_id,
            book_id="book_001",
            rating=6,  # Invalid rating
            review_text="Excellent book!"
        )
        
        self.assertIsNone(review)
    
    def test_get_recommendations(self):
        """Test getting book recommendations."""
        # Create user
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Get recommendations (should return popular books)
        recommendations = self.service.get_recommendations(user.user_id)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_get_user_stats(self):
        """Test getting user statistics."""
        # Create user
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Get stats
        stats = self.service.get_user_stats(user.user_id)
        self.assertIsInstance(stats, dict)
        self.assertIn('books_read', stats)
        self.assertIn('total_reading_time', stats)
        self.assertIn('favorite_genre', stats)
        self.assertIn('current_books', stats)

class TestFlaskApp(unittest.TestCase):
    """Test Flask API endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create service with temp database
        self.service = BookSubscriptionService(self.temp_db.name)
        
        # Import and configure Flask app
        from book_subscription_service import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create test user
        self.test_user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Replace the global service instance used by Flask with our test service
        from book_subscription_service import book_subscription_service
        book_subscription_service.db = self.service.db
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_create_user_api(self):
        """Test create user API endpoint."""
        data = {
            'username': 'apiuser',
            'email': 'api@example.com',
            'first_name': 'API',
            'last_name': 'User'
        }
        
        response = self.client.post('/api/users', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('user_id', result)
    
    def test_create_user_api_missing_fields(self):
        """Test create user API with missing fields."""
        data = {
            'username': 'apiuser',
            'email': 'api@example.com'
            # Missing first_name and last_name
        }
        
        response = self.client.post('/api/users', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_search_books_api(self):
        """Test search books API endpoint."""
        response = self.client.get('/api/books?query=Gatsby')
        self.assertEqual(response.status_code, 200)
        
        books = response.get_json()
        self.assertIsInstance(books, list)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]['title'], 'The Great Gatsby')
    
    def test_search_books_api_with_genre(self):
        """Test search books API with genre filter."""
        response = self.client.get('/api/books?genre=Fiction')
        self.assertEqual(response.status_code, 200)
        
        books = response.get_json()
        self.assertIsInstance(books, list)
        self.assertGreater(len(books), 0)
        
        for book in books:
            self.assertEqual(book['genre'], 'Fiction')
    
    def test_create_subscription_api(self):
        """Test create subscription API endpoint."""
        data = {
            'user_id': self.test_user.user_id,
            'tier': 'premium',
            'price': 19.99,
            'payment_frequency': 'monthly'
        }
        
        response = self.client.post('/api/subscriptions', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('subscription_id', result)
    
    def test_create_subscription_api_invalid_tier(self):
        """Test create subscription API with invalid tier."""
        data = {
            'user_id': self.test_user.user_id,
            'tier': 'invalid_tier',
            'price': 19.99
        }
        
        response = self.client.post('/api/subscriptions', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_start_reading_api(self):
        """Test start reading API endpoint."""
        # Create subscription first
        self.service.create_subscription(
            user_id=self.test_user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        data = {'user_id': self.test_user.user_id}
        response = self.client.post('/api/books/book_001/start-reading', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('progress_id', result)
        self.assertEqual(result['status'], 'reading')
    
    def test_start_reading_api_no_access(self):
        """Test start reading API without access."""
        data = {'user_id': self.test_user.user_id}
        response = self.client.post('/api/books/book_003/start-reading', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_add_review_api(self):
        """Test add review API endpoint."""
        # Create subscription first
        self.service.create_subscription(
            user_id=self.test_user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        data = {
            'user_id': self.test_user.user_id,
            'rating': 5,
            'review_text': 'Great book!'
        }
        
        response = self.client.post('/api/books/book_001/reviews', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('review_id', result)
    
    def test_add_review_api_invalid_rating(self):
        """Test add review API with invalid rating."""
        # Create subscription first
        self.service.create_subscription(
            user_id=self.test_user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        data = {
            'user_id': self.test_user.user_id,
            'rating': 6,  # Invalid rating
            'review_text': 'Great book!'
        }
        
        response = self.client.post('/api/books/book_001/reviews', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_health_check_api(self):
        """Test health check API endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['service'], 'book_subscription')

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = BookSubscriptionService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_get_nonexistent_user(self):
        """Test getting non-existent user."""
        user = self.service.get_user("nonexistent_user")
        self.assertIsNone(user)
    
    def test_get_nonexistent_book(self):
        """Test getting non-existent book."""
        book = self.service.db.get_book("nonexistent_book")
        self.assertIsNone(book)
    
    def test_create_subscription_nonexistent_user(self):
        """Test creating subscription for non-existent user."""
        subscription = self.service.create_subscription(
            user_id="nonexistent_user",
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        self.assertIsNone(subscription)
    
    def test_start_reading_nonexistent_user(self):
        """Test starting reading for non-existent user."""
        progress = self.service.start_reading("nonexistent_user", "book_001")
        self.assertIsNone(progress)
    
    def test_start_reading_nonexistent_book(self):
        """Test starting reading for non-existent book."""
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        progress = self.service.start_reading(user.user_id, "nonexistent_book")
        self.assertIsNone(progress)
    
    def test_update_progress_nonexistent_progress(self):
        """Test updating non-existent reading progress."""
        progress = self.service.update_reading_progress(
            user_id="nonexistent_user",
            book_id="book_001",
            current_page=50
        )
        self.assertIsNone(progress)
    
    def test_add_review_nonexistent_user(self):
        """Test adding review for non-existent user."""
        review = self.service.add_book_review(
            user_id="nonexistent_user",
            book_id="book_001",
            rating=5,
            review_text="Great book!"
        )
        self.assertIsNone(review)
    
    def test_add_review_nonexistent_book(self):
        """Test adding review for non-existent book."""
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        
        review = self.service.add_book_review(
            user_id=user.user_id,
            book_id="nonexistent_book",
            rating=5,
            review_text="Great book!"
        )
        self.assertIsNone(review)
    
    def test_search_books_empty_query(self):
        """Test searching books with empty query."""
        books = self.service.search_books(query="")
        self.assertIsInstance(books, list)
        self.assertGreater(len(books), 0)  # Should return all books
    
    def test_search_books_nonexistent_genre(self):
        """Test searching books with non-existent genre."""
        books = self.service.search_books(genre="NonexistentGenre")
        self.assertEqual(len(books), 0)
    
    def test_get_recommendations_nonexistent_user(self):
        """Test getting recommendations for non-existent user."""
        recommendations = self.service.get_recommendations("nonexistent_user")
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)  # Should return popular books
    
    def test_get_user_stats_nonexistent_user(self):
        """Test getting stats for non-existent user."""
        stats = self.service.get_user_stats("nonexistent_user")
        self.assertIsInstance(stats, dict)
        self.assertIn('books_read', stats)

class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = BookSubscriptionService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_create_multiple_users_performance(self):
        """Test creating multiple users performance."""
        start_time = time.time()
        
        for i in range(100):
            self.service.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(duration, 5.0)  # 5 seconds for 100 users
    
    def test_search_books_performance(self):
        """Test book search performance."""
        # Add more test books
        for i in range(50):
            book = Book(
                book_id=f"book_{i:03d}",
                title=f"Book {i}",
                author=f"Author {i}",
                isbn=f"123456789{i:01d}",
                description=f"Description for book {i}",
                genre="Test" if i % 2 == 0 else "Fiction"
            )
            self.service.db.save_book(book)
        
        start_time = time.time()
        
        # Perform multiple searches
        for i in range(10):
            self.service.search_books(query=f"Book {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 2.0)  # 2 seconds for 10 searches

class TestBookSubscriptionErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = BookSubscriptionService(self.temp_db.name)

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_database_error_handling_save_user(self):
        """Test database error handling when saving user."""
        # Mock database error
        with patch.object(self.service.db, 'save_user', return_value=False):
            result = self.service.create_user(
                username="erroruser",
                email="error@error.com",
                first_name="Error",
                last_name="User"
            )
            self.assertIsNone(result)

    def test_database_error_handling_save_subscription(self):
        """Test database error handling when saving subscription."""
        # Create user first
        user = self.service.create_user(
            username="testuser",
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )

        # Mock database error
        with patch.object(self.service.db, 'save_subscription', return_value=False):
            result = self.service.create_subscription(
                user_id=user.user_id,
                tier=SubscriptionTier.PREMIUM,
                price=29.99,
                payment_frequency="monthly"
            )
            self.assertIsNone(result)

    def test_database_error_handling_save_reading_progress(self):
        """Test database error handling when saving reading progress."""
        # Create user first
        user = self.service.create_user(
            username="testuser",
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )

        # Mock database error
        with patch.object(self.service.db, 'save_reading_progress', return_value=False):
            result = self.service.start_reading(
                user_id=user.user_id,
                book_id="book_001"
            )
            self.assertIsNone(result)

    def test_database_error_handling_save_review(self):
        """Test database error handling when saving review."""
        # Create user first
        user = self.service.create_user(
            username="testuser",
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )

        # Mock database error
        with patch.object(self.service.db, 'save_book_review', return_value=False):
            result = self.service.add_book_review(
                user_id=user.user_id,
                book_id="book_001",
                rating=5,
                review_text="Great book!"
            )
            self.assertIsNone(result)

    def test_search_error_handling(self):
        """Test search error handling."""
        # Mock database error in search - exception will propagate
        with patch.object(self.service.db, 'search_books', side_effect=Exception("Database error")):
            with self.assertRaises(Exception):
                self.service.search_books("test query")

    def test_recommendation_error_handling(self):
        """Test recommendation error handling."""
        # When user reading history is empty, returns popular books (not empty list)
        result = self.service.get_recommendations("non_existent_user")
        # Should return some books from database (popular books)
        self.assertIsInstance(result, list)

class TestCoverageImprovements(unittest.TestCase):
    """Tests to improve code coverage to 95%+."""

    def setUp(self):
        """Set up test database and Flask app."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = BookSubscriptionService(self.temp_db.name)

        from book_subscription_service import app
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_database_connection_errors(self):
        """Test database connection error handling."""
        db = BookSubscriptionDatabase(":memory:")
        user = User(
            user_id="test_user",
            username="test",
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )
        # Patch connection after database is initialized
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.save_user(user)
            self.assertFalse(result)

    def test_create_subscription_nonexistent_user(self):
        """Test creating subscription for non-existent user."""
        result = self.service.create_subscription(
            user_id="nonexistent",
            tier=SubscriptionTier.BASIC,
            price=9.99,
            payment_frequency="monthly"
        )
        self.assertIsNone(result)

    def test_start_reading_nonexistent_book(self):
        """Test starting to read non-existent book."""
        user = self.service.create_user(
            username="testuser",
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )
        result = self.service.start_reading(
            user_id=user.user_id,
            book_id="nonexistent_book"
        )
        self.assertIsNone(result)

    def test_update_reading_progress_nonexistent_user(self):
        """Test updating reading progress for non-existent user."""
        result = self.service.update_reading_progress(
            user_id="nonexistent",
            book_id="book_001",
            current_page=50
        )
        self.assertIsNone(result)

    def test_add_review_invalid_rating_range(self):
        """Test adding review with invalid rating."""
        user = self.service.create_user(
            username="testuser",
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )

        # Test rating < 1
        result = self.service.add_book_review(
            user_id=user.user_id,
            book_id="book_001",
            rating=0,
            review_text="Test"
        )
        self.assertIsNone(result)

        # Test rating > 5
        result = self.service.add_book_review(
            user_id=user.user_id,
            book_id="book_001",
            rating=6,
            review_text="Test"
        )
        self.assertIsNone(result)

    def test_get_user_stats_nonexistent(self):
        """Test get user stats for non-existent user."""
        result = self.service.get_user_stats("nonexistent")
        # Service returns default stats regardless of user existence
        self.assertEqual(result, {
            'books_read': 0,
            'total_reading_time': 0,
            'favorite_genre': 'Unknown',
            'current_books': 0
        })

class TestCoverageImprovements(unittest.TestCase):
    """Tests to improve code coverage to 95%+."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = BookSubscriptionService(self.temp_db.name)

        # Set up Flask test client and update global service
        import book_subscription_service as bss
        bss.book_subscription_service = self.service
        app = bss.app
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_database_get_user_error(self):
        """Test database get_user with connection error."""
        db = BookSubscriptionDatabase(":memory:")
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.get_user("user_test")
            self.assertIsNone(result)

    def test_database_save_book_error(self):
        """Test database save_book with connection error."""
        db = BookSubscriptionDatabase(":memory:")
        book = Book(
            book_id="book_test",
            title="Test Book",
            author="Test Author",
            isbn="123-456",
            description="Test description",
            genre="Fiction"
        )
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.save_book(book)
            self.assertFalse(result)

    def test_database_save_subscription_error(self):
        """Test database save_subscription with connection error."""
        db = BookSubscriptionDatabase(":memory:")
        subscription = Subscription(
            subscription_id="sub_test",
            user_id="user_test",
            tier=SubscriptionTier.BASIC,
            price=9.99,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.save_subscription(subscription)
            self.assertFalse(result)

    def test_database_save_reading_progress_error(self):
        """Test database save_reading_progress with connection error."""
        db = BookSubscriptionDatabase(":memory:")
        progress = ReadingProgress(
            progress_id="prog_test",
            user_id="user_test",
            book_id="book_test",
            current_page=50,
            total_pages=200
        )
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.save_reading_progress(progress)
            self.assertFalse(result)

    def test_database_save_review_error(self):
        """Test database save_book_review with connection error."""
        db = BookSubscriptionDatabase(":memory:")
        review = BookReview(
            review_id="rev_test",
            user_id="user_test",
            book_id="book_test",
            rating=5,
            review_text="Great book!"
        )
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.save_book_review(review)
            self.assertFalse(result)

    def test_database_save_payment_error(self):
        """Test database save_book_payment with connection error."""
        db = BookSubscriptionDatabase(":memory:")
        payment = Payment(
            payment_id="pay_test",
            subscription_id="sub_test",
            amount=9.99,
            payment_method="credit_card"
        )
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.save_book_payment(payment)
            self.assertFalse(result)

    def test_service_create_user_error(self):
        """Test service create_user with database error."""
        with patch.object(self.service.db, 'save_user', side_effect=Exception("DB error")):
            result = self.service.create_user(
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User"
            )
            self.assertIsNone(result)

    def test_service_create_subscription_yearly(self):
        """Test creating a yearly subscription."""
        # Create user first
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

        # Create yearly subscription
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.PREMIUM,
            price=99.99,
            payment_frequency="yearly"
        )

        self.assertIsNotNone(subscription)
        # Check end date is approximately 365 days from now
        days_diff = (subscription.end_date - subscription.start_date).days
        self.assertGreaterEqual(days_diff, 364)
        self.assertLessEqual(days_diff, 366)

    def test_service_create_book_error(self):
        """Test service create_book with database error."""
        with patch.object(self.service.db, 'save_book', return_value=False):
            result = self.service.create_book(
                title="Test Book",
                author="Test Author",
                isbn="123-456",
                description="Test description",
                genre="Fiction"
            )
            self.assertIsNone(result)

    def test_service_create_subscription_error(self):
        """Test service create_subscription with database error."""
        # Create user first
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

        with patch.object(self.service.db, 'save_subscription', return_value=False):
            result = self.service.create_subscription(
                user_id=user.user_id,
                tier=SubscriptionTier.BASIC,
                price=9.99
            )
            self.assertIsNone(result)

    def test_service_process_payment_error(self):
        """Test service process_payment with database error."""
        with patch.object(self.service.db, 'save_book_payment', return_value=False):
            result = self.service.process_payment(
                subscription_id="sub_test",
                amount=9.99,
                payment_method="credit_card"
            )
            self.assertIsNone(result)

    def test_flask_create_user_database_error(self):
        """Test Flask create_user with database error."""
        from book_subscription_service import book_subscription_service as global_service

        with patch.object(global_service.db, 'save_user', return_value=False):
            data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
            response = self.client.post('/api/users', json=data)
            result = response.get_json()
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_flask_create_subscription_database_error(self):
        """Test Flask create_subscription with database error."""
        from book_subscription_service import book_subscription_service as global_service

        # Create user first
        user = self.service.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

        with patch.object(global_service.db, 'save_subscription', return_value=False):
            data = {
                'user_id': user.user_id,
                'tier': 'basic',
                'price': 9.99,
                'payment_frequency': 'monthly'
            }
            response = self.client.post('/api/subscriptions', json=data)
            result = response.get_json()
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_flask_create_book_database_error(self):
        """Test Flask create_book with database error."""
        from book_subscription_service import book_subscription_service as global_service

        with patch.object(global_service.db, 'save_book', return_value=False):
            data = {
                'title': 'Test Book',
                'author': 'Test Author',
                'isbn': '123-456',
                'description': 'Test description',
                'genre': 'Fiction'
            }
            response = self.client.post('/api/books', json=data)
            result = response.get_json()
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_flask_exception_handlers(self):
        """Test Flask exception handlers."""
        from book_subscription_service import book_subscription_service as global_service

        # Test create_user exception
        with patch.object(global_service, 'create_user', side_effect=Exception("Test error")):
            data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
            response = self.client.post('/api/users', json=data)
            result = response.get_json()
            self.assertFalse(result['success'])
            self.assertIn('error', result)

        # Test create_subscription exception
        with patch.object(global_service, 'create_subscription', side_effect=Exception("Test error")):
            data = {
                'user_id': 'user_test',
                'tier': 'basic',
                'price': 9.99
            }
            response = self.client.post('/api/subscriptions', json=data)
            result = response.get_json()
            self.assertFalse(result['success'])
            self.assertIn('error', result)

        # Test create_book exception
        with patch.object(global_service, 'create_book', side_effect=Exception("Test error")):
            data = {
                'title': 'Test Book',
                'author': 'Test Author',
                'isbn': '123-456',
                'description': 'Test description',
                'genre': 'Fiction'
            }
            response = self.client.post('/api/books', json=data)
            result = response.get_json()
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_start_reading_existing_progress(self):
        """Test start_reading when progress already exists."""
        # Create user, subscription, and book
        user = self.service.create_user(
            username="reader", email="reader@test.com",
            first_name="Test", last_name="Reader"
        )
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.PREMIUM,
            price=29.99
        )
        book = self.service.create_book(
            title="Test Book", author="Test Author", isbn="123",
            description="Test", genre="Fiction"
        )

        # Start reading first time
        progress1 = self.service.start_reading(user.user_id, book.book_id)
        self.assertIsNotNone(progress1)

        # Start reading again - should return existing progress
        progress2 = self.service.start_reading(user.user_id, book.book_id)
        self.assertEqual(progress1.progress_id, progress2.progress_id)

    def test_start_reading_nonexistent_book(self):
        """Test start_reading with non-existent book."""
        user = self.service.create_user(
            username="reader", email="reader@test.com",
            first_name="Test", last_name="Reader"
        )
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.PREMIUM,
            price=29.99
        )

        result = self.service.start_reading(user.user_id, "nonexistent")
        self.assertIsNone(result)

    def test_start_reading_database_error(self):
        """Test start_reading with database error."""
        user = self.service.create_user(
            username="reader", email="reader@test.com",
            first_name="Test", last_name="Reader"
        )
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.PREMIUM,
            price=29.99
        )
        book = self.service.create_book(
            title="Test Book", author="Test Author", isbn="123",
            description="Test", genre="Fiction"
        )

        with patch.object(self.service.db, 'save_reading_progress', return_value=False):
            result = self.service.start_reading(user.user_id, book.book_id)
            self.assertIsNone(result)

    def test_get_book_recommendations(self):
        """Test book recommendations based on reading history."""
        # Create user and subscription
        user = self.service.create_user(
            username="reader", email="reader@test.com",
            first_name="Test", last_name="Reader"
        )
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.PREMIUM,
            price=29.99
        )

        # Create fiction books
        book1 = self.service.create_book(
            title="Fiction 1", author="Author 1", isbn="001",
            description="Test", genre="Fiction"
        )
        book2 = self.service.create_book(
            title="Fiction 2", author="Author 2", isbn="002",
            description="Test", genre="Fiction"
        )

        # Start reading book1
        self.service.start_reading(user.user_id, book1.book_id)

        # Get recommendations (should include book2 from same genre)
        recommendations = self.service.get_recommendations(user.user_id, limit=5)
        book_ids = [b.book_id for b in recommendations]
        self.assertIn(book2.book_id, book_ids)
        self.assertNotIn(book1.book_id, book_ids)  # Should not recommend currently reading book

    def test_flask_create_book_missing_field(self):
        """Test Flask create_book with missing required field."""
        data = {
            'title': 'Test Book',
            'author': 'Test Author'
            # Missing isbn, description, genre
        }
        response = self.client.post('/api/books', json=data)
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_flask_create_book_success(self):
        """Test Flask create_book successful creation."""
        data = {
            'title': 'New Book',
            'author': 'New Author',
            'isbn': '999-888',
            'description': 'Great book',
            'genre': 'Mystery'
        }
        response = self.client.post('/api/books', json=data)
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('book_id', result)

    def test_save_book_payment(self):
        """Test saving a book payment."""
        from book_subscription_service import Payment, PaymentStatus
        # Use self.service.db which has the payments table properly initialized
        payment = Payment(
            payment_id="pay_test",
            user_id="user_test",
            subscription_id="sub_test",
            amount=29.99,
            currency="USD",
            status=PaymentStatus.COMPLETED,
            payment_method="credit_card",
            transaction_id="txn_123",
            payment_date=datetime.now(),
            created_at=datetime.now()
        )

        result = self.service.db.save_book_payment(payment)
        self.assertTrue(result)

    def test_save_book_payment_error(self):
        """Test save_book_payment with database error."""
        from book_subscription_service import Payment, PaymentStatus
        db = BookSubscriptionDatabase(":memory:")

        payment = Payment(
            payment_id="pay_test",
            user_id="user_test",
            subscription_id="sub_test",
            amount=29.99,
            currency="USD",
            status=PaymentStatus.COMPLETED,
            payment_method="credit_card",
            transaction_id="txn_123",
            payment_date=datetime.now(),
            created_at=datetime.now()
        )

        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.save_book_payment(payment)
            self.assertFalse(result)

    def test_get_book_reviews_error(self):
        """Test get_book_reviews with database error."""
        db = BookSubscriptionDatabase(":memory:")
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.get_book_reviews("book_test")
            self.assertEqual(result, [])

    def test_search_books_error(self):
        """Test search_books with database error."""
        db = BookSubscriptionDatabase(":memory:")
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.search_books(query="test")
            self.assertEqual(result, [])

    def test_get_user_subscription_error(self):
        """Test get_user_subscription with database error."""
        db = BookSubscriptionDatabase(":memory:")
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.get_user_subscription("user_test")
            self.assertIsNone(result)

    def test_get_book_error(self):
        """Test get_book with database error."""
        db = BookSubscriptionDatabase(":memory:")
        with patch('sqlite3.connect', side_effect=Exception("Connection error")):
            result = db.get_book("book_test")
            self.assertIsNone(result)

    def test_get_recommendations_with_reading_history(self):
        """Test book recommendations with user reading history."""
        # Create user
        user = self.service.create_user(
            username="testuser",
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )

        # Create subscription
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.PREMIUM,
            price=29.99,
            payment_frequency="monthly"
        )

        # Create multiple books in same genre
        book1 = self.service.create_book(
            title="Mystery Book 1",
            author="Author 1",
            isbn="111-111",
            description="First mystery",
            genre="Mystery"
        )

        book2 = self.service.create_book(
            title="Mystery Book 2",
            author="Author 2",
            isbn="222-222",
            description="Second mystery",
            genre="Mystery"
        )

        book3 = self.service.create_book(
            title="Sci-Fi Book",
            author="Author 3",
            isbn="333-333",
            description="Sci-fi story",
            genre="Sci-Fi"
        )

        # Mock reading history to trigger recommendation logic
        from book_subscription_service import ReadingProgress, ReadingStatus
        mock_progress = [
            ReadingProgress(
                progress_id="prog_1",
                user_id=user.user_id,
                book_id=book1.book_id,
                status=ReadingStatus.COMPLETED,
                current_page=100,
                total_pages=200,
                started_at=datetime.now(),
                last_read=datetime.now()
            )
        ]

        with patch.object(self.service, '_get_user_reading_history', return_value=mock_progress):
            recommendations = self.service.get_recommendations(user.user_id, limit=5)
            # Should return recommendations based on reading history
            self.assertIsInstance(recommendations, list)

    def test_process_payment_success(self):
        """Test successful payment processing."""
        user = self.service.create_user(
            username="payuser", email="pay@test.com",
            first_name="Pay", last_name="User"
        )
        subscription = self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )

        payment = self.service.process_payment(
            subscription_id=subscription.subscription_id,
            amount=9.99,
            payment_method="credit_card"
        )
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, PaymentStatus.COMPLETED)

    def test_update_reading_progress_complete_book(self):
        """Test completing a book."""
        user = self.service.create_user(
            username="completereader", email="complete@test.com",
            first_name="Complete", last_name="Reader"
        )
        # Create subscription so user can access books
        self.service.create_subscription(
            user_id=user.user_id,
            tier=SubscriptionTier.BASIC,
            price=9.99
        )
        book = self.service.create_book(
            title="Short Book", author="Test Author", isbn="456-short",
            description="Test", genre="Fiction", page_count=100
        )

        # Start reading
        self.service.start_reading(user.user_id, book.book_id)

        # Complete the book
        updated = self.service.update_reading_progress(
            user.user_id, book.book_id, current_page=100
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated.status, ReadingStatus.COMPLETED)
        self.assertEqual(updated.progress_percentage, 100.0)

    def test_update_reading_progress_save_failure(self):
        """Test update_reading_progress when save fails."""
        user = self.service.create_user(
            username="failreader", email="fail@test.com",
            first_name="Fail", last_name="Reader"
        )
        book = self.service.create_book(
            title="Fail Book", author="Test Author", isbn="789-fail",
            description="Test", genre="Fiction", page_count=200
        )

        # Start reading
        self.service.start_reading(user.user_id, book.book_id)

        # Mock save to fail
        with patch.object(self.service.db, 'save_reading_progress', return_value=False):
            result = self.service.update_reading_progress(
                user.user_id, book.book_id, current_page=50
            )
            self.assertIsNone(result)

    def test_add_book_review_save_failure(self):
        """Test add_book_review when save fails."""
        user = self.service.create_user(
            username="failreviewer", email="failrev@test.com",
            first_name="Fail", last_name="Reviewer"
        )
        book = self.service.create_book(
            title="Review Fail Book", author="Test Author", isbn="111-fail",
            description="Test", genre="Fiction"
        )

        # Start reading to get access
        self.service.start_reading(user.user_id, book.book_id)

        # Mock save to fail
        with patch.object(self.service.db, 'save_book_review', return_value=False):
            result = self.service.add_book_review(
                user_id=user.user_id,
                book_id=book.book_id,
                rating=5,
                review_text="Great!"
            )
            self.assertIsNone(result)

    def test_start_reading_nonexistent_book_returns_none(self):
        """Test start_reading with non-existent book returns None."""
        user = self.service.create_user(
            username="nonereader", email="none@test.com",
            first_name="None", last_name="Reader"
        )

        result = self.service.start_reading(user.user_id, "nonexistent_book_id")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
