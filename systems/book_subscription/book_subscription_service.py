#!/usr/bin/env python3
"""
Book Subscription Service

A comprehensive book subscription and content management system for
digital libraries, subscription management, reading progress tracking,
and content recommendation with support for various subscription tiers
and payment processing.
"""

import sqlite3
import hashlib
import time
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SubscriptionStatus(Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class SubscriptionTier(Enum):
    """Subscription tier enumeration."""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    STUDENT = "student"

class BookStatus(Enum):
    """Book status enumeration."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"

class ReadingStatus(Enum):
    """Reading status enumeration."""
    NOT_STARTED = "not_started"
    READING = "reading"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"

@dataclass
class User:
    """User model."""
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True

@dataclass
class Book:
    """Book model."""
    book_id: str
    title: str
    author: str
    isbn: str
    description: str
    genre: str
    language: str = "en"
    page_count: int = 0
    publication_date: Optional[datetime] = None
    publisher: str = ""
    cover_image_url: str = ""
    book_file_url: str = ""
    status: BookStatus = BookStatus.AVAILABLE
    subscription_tier_required: SubscriptionTier = SubscriptionTier.BASIC
    price: float = 0.0
    rating: float = 0.0
    total_ratings: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Subscription:
    """Subscription model."""
    subscription_id: str
    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    price: float = 0.0
    payment_frequency: str = "monthly"  # monthly, yearly
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ReadingProgress:
    """Reading progress model."""
    progress_id: str
    user_id: str
    book_id: str
    status: ReadingStatus = ReadingStatus.NOT_STARTED
    current_page: int = 0
    total_pages: int = 0
    progress_percentage: float = 0.0
    time_spent_minutes: int = 0
    last_read: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class BookReview:
    """Book review model."""
    review_id: str
    user_id: str
    book_id: str
    rating: int  # 1-5 stars
    review_text: str
    is_verified_purchase: bool = False
    helpful_votes: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Payment:
    """Payment model."""
    payment_id: str
    subscription_id: str
    amount: float
    user_id: str = ""
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: str = "credit_card"
    transaction_id: str = ""
    payment_date: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)

class BookSubscriptionDatabase:
    """Database operations for book subscription service."""
    
    def __init__(self, db_path: str = "book_subscription.db"):
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
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TIMESTAMP,
                phone TEXT DEFAULT '',
                address TEXT DEFAULT '',
                city TEXT DEFAULT '',
                state TEXT DEFAULT '',
                zip_code TEXT DEFAULT '',
                country TEXT DEFAULT '',
                preferences TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Books table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                genre TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                page_count INTEGER DEFAULT 0,
                publication_date TIMESTAMP,
                publisher TEXT DEFAULT '',
                cover_image_url TEXT DEFAULT '',
                book_file_url TEXT DEFAULT '',
                status TEXT DEFAULT 'available',
                subscription_tier_required TEXT DEFAULT 'basic',
                price REAL DEFAULT 0.0,
                rating REAL DEFAULT 0.0,
                total_ratings INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                auto_renew BOOLEAN DEFAULT 1,
                price REAL DEFAULT 0.0,
                payment_frequency TEXT DEFAULT 'monthly',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Reading progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_progress (
                progress_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                book_id TEXT NOT NULL,
                status TEXT DEFAULT 'not_started',
                current_page INTEGER DEFAULT 0,
                total_pages INTEGER DEFAULT 0,
                progress_percentage REAL DEFAULT 0.0,
                time_spent_minutes INTEGER DEFAULT 0,
                last_read TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (book_id) REFERENCES books (book_id),
                UNIQUE(user_id, book_id)
            )
        ''')
        
        # Book reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_reviews (
                review_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                book_id TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                review_text TEXT NOT NULL,
                is_verified_purchase BOOLEAN DEFAULT 0,
                helpful_votes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (book_id) REFERENCES books (book_id)
            )
        ''')
        
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subscription_id TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'pending',
                payment_method TEXT DEFAULT 'credit_card',
                transaction_id TEXT DEFAULT '',
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (subscription_id)
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
                (user_id, username, email, first_name, last_name, date_of_birth,
                 phone, address, city, state, zip_code, country, preferences,
                 created_at, updated_at, last_login, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id, user.username, user.email, user.first_name, user.last_name,
                user.date_of_birth, user.phone, user.address, user.city, user.state,
                user.zip_code, user.country, json.dumps(user.preferences),
                user.created_at, user.updated_at, user.last_login, user.is_active
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
            
            if row:
                user = User(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    first_name=row[3],
                    last_name=row[4],
                    date_of_birth=datetime.fromisoformat(row[5]) if row[5] else None,
                    phone=row[6] or "",
                    address=row[7] or "",
                    city=row[8] or "",
                    state=row[9] or "",
                    zip_code=row[10] or "",
                    country=row[11] or "",
                    preferences=json.loads(row[12]) if row[12] else {},
                    created_at=datetime.fromisoformat(row[13]) if row[13] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now(),
                    last_login=datetime.fromisoformat(row[15]) if row[15] else None,
                    is_active=bool(row[16])
                )
                conn.close()
                return user
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def save_book(self, book: Book) -> bool:
        """Save book to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO books 
                (book_id, title, author, isbn, description, genre, language,
                 page_count, publication_date, publisher, cover_image_url,
                 book_file_url, status, subscription_tier_required, price,
                 rating, total_ratings, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                book.book_id, book.title, book.author, book.isbn, book.description,
                book.genre, book.language, book.page_count, book.publication_date,
                book.publisher, book.cover_image_url, book.book_file_url,
                book.status.value, book.subscription_tier_required.value,
                book.price, book.rating, book.total_ratings, book.created_at, book.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving book: {e}")
            return False
    
    def get_book(self, book_id: str) -> Optional[Book]:
        """Get book by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM books WHERE book_id = ?', (book_id,))
            row = cursor.fetchone()
            
            if row:
                book = Book(
                    book_id=row[0],
                    title=row[1],
                    author=row[2],
                    isbn=row[3],
                    description=row[4],
                    genre=row[5],
                    language=row[6] or "en",
                    page_count=row[7] or 0,
                    publication_date=datetime.fromisoformat(row[8]) if row[8] else None,
                    publisher=row[9] or "",
                    cover_image_url=row[10] or "",
                    book_file_url=row[11] or "",
                    status=BookStatus(row[12]),
                    subscription_tier_required=SubscriptionTier(row[13]),
                    price=row[14] or 0.0,
                    rating=row[15] or 0.0,
                    total_ratings=row[16] or 0,
                    created_at=datetime.fromisoformat(row[17]) if row[17] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[18]) if row[18] else datetime.now()
                )
                conn.close()
                return book
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting book: {e}")
            return None
    
    def search_books(self, query: str = "", genre: str = "", author: str = "", 
                    limit: int = 20, offset: int = 0) -> List[Book]:
        """Search books."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            where_conditions = ["status = 'available'"]
            params = []
            
            if query:
                where_conditions.append("(title LIKE ? OR description LIKE ? OR author LIKE ?)")
                params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
            
            if genre:
                where_conditions.append("genre = ?")
                params.append(genre)
            
            if author:
                where_conditions.append("author LIKE ?")
                params.append(f'%{author}%')
            
            where_clause = " AND ".join(where_conditions)
            params.extend([limit, offset])
            
            cursor.execute(f'''
                SELECT * FROM books 
                WHERE {where_clause}
                ORDER BY rating DESC, total_ratings DESC, created_at DESC
                LIMIT ? OFFSET ?
            ''', params)
            
            books = []
            for row in cursor.fetchall():
                book = Book(
                    book_id=row[0],
                    title=row[1],
                    author=row[2],
                    isbn=row[3],
                    description=row[4],
                    genre=row[5],
                    language=row[6] or "en",
                    page_count=row[7] or 0,
                    publication_date=datetime.fromisoformat(row[8]) if row[8] else None,
                    publisher=row[9] or "",
                    cover_image_url=row[10] or "",
                    book_file_url=row[11] or "",
                    status=BookStatus(row[12]),
                    subscription_tier_required=SubscriptionTier(row[13]),
                    price=row[14] or 0.0,
                    rating=row[15] or 0.0,
                    total_ratings=row[16] or 0,
                    created_at=datetime.fromisoformat(row[17]) if row[17] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[18]) if row[18] else datetime.now()
                )
                books.append(book)
            
            conn.close()
            return books
        except Exception as e:
            logger.error(f"Error searching books: {e}")
            return []
    
    def save_subscription(self, subscription: Subscription) -> bool:
        """Save subscription to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO subscriptions 
                (subscription_id, user_id, tier, status, start_date, end_date,
                 auto_renew, price, payment_frequency, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                subscription.subscription_id, subscription.user_id, subscription.tier.value,
                subscription.status.value, subscription.start_date, subscription.end_date,
                subscription.auto_renew, subscription.price, subscription.payment_frequency,
                subscription.created_at, subscription.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving subscription: {e}")
            return False
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                subscription = Subscription(
                    subscription_id=row[0],
                    user_id=row[1],
                    tier=SubscriptionTier(row[2]),
                    status=SubscriptionStatus(row[3]),
                    start_date=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                    end_date=datetime.fromisoformat(row[5]) if row[5] else None,
                    auto_renew=bool(row[6]),
                    price=row[7] or 0.0,
                    payment_frequency=row[8] or "monthly",
                    created_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now()
                )
                conn.close()
                return subscription
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting user subscription: {e}")
            return None
    
    def save_reading_progress(self, progress: ReadingProgress) -> bool:
        """Save reading progress to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO reading_progress 
                (progress_id, user_id, book_id, status, current_page, total_pages,
                 progress_percentage, time_spent_minutes, last_read, started_at,
                 completed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                progress.progress_id, progress.user_id, progress.book_id,
                progress.status.value, progress.current_page, progress.total_pages,
                progress.progress_percentage, progress.time_spent_minutes,
                progress.last_read, progress.started_at, progress.completed_at,
                progress.created_at, progress.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving reading progress: {e}")
            return False
    
    def get_reading_progress(self, user_id: str, book_id: str) -> Optional[ReadingProgress]:
        """Get reading progress for user and book."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM reading_progress 
                WHERE user_id = ? AND book_id = ?
            ''', (user_id, book_id))
            
            row = cursor.fetchone()
            if row:
                progress = ReadingProgress(
                    progress_id=row[0],
                    user_id=row[1],
                    book_id=row[2],
                    status=ReadingStatus(row[3]),
                    current_page=row[4] or 0,
                    total_pages=row[5] or 0,
                    progress_percentage=row[6] or 0.0,
                    time_spent_minutes=row[7] or 0,
                    last_read=datetime.fromisoformat(row[8]) if row[8] else None,
                    started_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    completed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                    created_at=datetime.fromisoformat(row[11]) if row[11] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[12]) if row[12] else datetime.now()
                )
                conn.close()
                return progress
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting reading progress: {e}")
            return None
    
    def save_book_review(self, review: BookReview) -> bool:
        """Save book review to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO book_reviews 
                (review_id, user_id, book_id, rating, review_text, is_verified_purchase,
                 helpful_votes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                review.review_id, review.user_id, review.book_id, review.rating,
                review.review_text, review.is_verified_purchase, review.helpful_votes,
                review.created_at, review.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving book review: {e}")
            return False
    
    def get_book_reviews(self, book_id: str, limit: int = 20) -> List[BookReview]:
        """Get reviews for a book."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM book_reviews 
                WHERE book_id = ?
                ORDER BY helpful_votes DESC, created_at DESC
                LIMIT ?
            ''', (book_id, limit))
            
            reviews = []
            for row in cursor.fetchall():
                review = BookReview(
                    review_id=row[0],
                    user_id=row[1],
                    book_id=row[2],
                    rating=row[3],
                    review_text=row[4],
                    is_verified_purchase=bool(row[5]),
                    helpful_votes=row[6] or 0,
                    created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now()
                )
                reviews.append(review)
            
            conn.close()
            return reviews
        except Exception as e:
            logger.error(f"Error getting book reviews: {e}")
            return []

    def save_book_payment(self, payment: Payment) -> bool:
        """Save a subscription payment to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO payments
                (payment_id, user_id, subscription_id, amount, currency, status,
                 payment_method, transaction_id, payment_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                payment.payment_id, payment.user_id, payment.subscription_id,
                payment.amount, payment.currency, payment.status.value,
                payment.payment_method, payment.transaction_id,
                payment.payment_date, payment.created_at
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving payment: {e}")
            return False

class BookSubscriptionService:
    """Book subscription service with content management and recommendations."""
    
    def __init__(self, db_path: str = "book_subscription.db"):
        self.db = BookSubscriptionDatabase(db_path)
        self.initialize_default_books()
    
    def initialize_default_books(self):
        """Initialize default books."""
        default_books = [
            Book(
                book_id="book_001",
                title="The Great Gatsby",
                author="F. Scott Fitzgerald",
                isbn="9780743273565",
                description="A classic American novel about the Jazz Age.",
                genre="Fiction",
                language="en",
                page_count=180,
                publication_date=datetime(1925, 4, 10),
                publisher="Scribner",
                subscription_tier_required=SubscriptionTier.BASIC,
                price=9.99,
                rating=4.2,
                total_ratings=1250
            ),
            Book(
                book_id="book_002",
                title="To Kill a Mockingbird",
                author="Harper Lee",
                isbn="9780061120084",
                description="A gripping tale of racial injustice and childhood innocence.",
                genre="Fiction",
                language="en",
                page_count=281,
                publication_date=datetime(1960, 7, 11),
                publisher="J.B. Lippincott & Co.",
                subscription_tier_required=SubscriptionTier.BASIC,
                price=12.99,
                rating=4.5,
                total_ratings=2100
            ),
            Book(
                book_id="book_003",
                title="1984",
                author="George Orwell",
                isbn="9780451524935",
                description="A dystopian social science fiction novel.",
                genre="Science Fiction",
                language="en",
                page_count=328,
                publication_date=datetime(1949, 6, 8),
                publisher="Secker & Warburg",
                subscription_tier_required=SubscriptionTier.PREMIUM,
                price=15.99,
                rating=4.3,
                total_ratings=1800
            )
        ]
        
        for book in default_books:
            self.db.save_book(book)
    
    def generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def create_user(self, username: str, email: str, first_name: str, last_name: str,
                   date_of_birth: datetime = None, phone: str = "", address: str = "",
                   city: str = "", state: str = "", zip_code: str = "", country: str = "") -> Optional[User]:
        """Create a new user."""
        user_id = self.generate_id("user")
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            country=country
        )
        
        try:
            if self.db.save_user(user):
                return user
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.get_user(user_id)
    
    def create_subscription(self, user_id: str, tier: SubscriptionTier, 
                           price: float, payment_frequency: str = "monthly") -> Optional[Subscription]:
        """Create a new subscription."""
        # Check if user exists
        user = self.db.get_user(user_id)
        if not user:
            return None
        
        subscription_id = self.generate_id("sub")
        
        # Calculate end date based on payment frequency
        start_date = datetime.now()
        if payment_frequency == "yearly":
            end_date = start_date + timedelta(days=365)
        else:  # monthly
            end_date = start_date + timedelta(days=30)
        
        subscription = Subscription(
            subscription_id=subscription_id,
            user_id=user_id,
            tier=tier,
            price=price,
            payment_frequency=payment_frequency,
            end_date=end_date
        )
        
        if self.db.save_subscription(subscription):
            return subscription
        return None
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription."""
        return self.db.get_user_subscription(user_id)
    
    def can_access_book(self, user_id: str, book_id: str) -> bool:
        """Check if user can access a book based on subscription tier."""
        user = self.db.get_user(user_id)
        book = self.db.get_book(book_id)
        
        if not user or not book:
            return False
        
        subscription = self.db.get_user_subscription(user_id)
        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            return False
        
        # Check if subscription tier allows access
        tier_hierarchy = {
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.STUDENT: 1,
            SubscriptionTier.PREMIUM: 2,
            SubscriptionTier.ENTERPRISE: 3
        }
        
        user_tier_level = tier_hierarchy.get(subscription.tier, 0)
        required_tier_level = tier_hierarchy.get(book.subscription_tier_required, 0)
        
        return user_tier_level >= required_tier_level
    
    def start_reading(self, user_id: str, book_id: str) -> Optional[ReadingProgress]:
        """Start reading a book."""
        if not self.can_access_book(user_id, book_id):
            return None
        
        book = self.db.get_book(book_id)
        if not book:
            return None
        
        # Check if already reading
        existing_progress = self.db.get_reading_progress(user_id, book_id)
        if existing_progress:
            return existing_progress
        
        progress_id = self.generate_id("progress")
        progress = ReadingProgress(
            progress_id=progress_id,
            user_id=user_id,
            book_id=book_id,
            status=ReadingStatus.READING,
            total_pages=book.page_count,
            started_at=datetime.now(),
            last_read=datetime.now()
        )
        
        if self.db.save_reading_progress(progress):
            return progress
        return None
    
    def update_reading_progress(self, user_id: str, book_id: str, current_page: int,
                               time_spent_minutes: int = 0) -> Optional[ReadingProgress]:
        """Update reading progress."""
        progress = self.db.get_reading_progress(user_id, book_id)
        if not progress:
            return None
        
        progress.current_page = current_page
        progress.time_spent_minutes += time_spent_minutes
        progress.last_read = datetime.now()
        
        if progress.total_pages > 0:
            progress.progress_percentage = (progress.current_page / progress.total_pages) * 100
            
            if progress.current_page >= progress.total_pages:
                progress.status = ReadingStatus.COMPLETED
                progress.completed_at = datetime.now()
                progress.progress_percentage = 100.0
        
        progress.updated_at = datetime.now()
        
        if self.db.save_reading_progress(progress):
            return progress
        return None
    
    def search_books(self, query: str = "", genre: str = "", author: str = "",
                    user_id: str = None, limit: int = 20, offset: int = 0) -> List[Book]:
        """Search books with access control."""
        books = self.db.search_books(query, genre, author, limit, offset)
        
        if user_id:
            # Filter books based on user's subscription
            accessible_books = []
            for book in books:
                if self.can_access_book(user_id, book.book_id):
                    accessible_books.append(book)
            return accessible_books
        
        return books
    
    def add_book_review(self, user_id: str, book_id: str, rating: int, 
                       review_text: str) -> Optional[BookReview]:
        """Add a book review."""
        if not (1 <= rating <= 5):
            return None
        
        # Check if user has access to the book
        if not self.can_access_book(user_id, book_id):
            return None
        
        review_id = self.generate_id("review")
        review = BookReview(
            review_id=review_id,
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            review_text=review_text,
            is_verified_purchase=True  # Assume verified if they can access
        )
        
        if self.db.save_book_review(review):
            # Update book rating
            self._update_book_rating(book_id)
            return review
        return None

    def create_book(self, title: str, author: str, isbn: str, description: str, genre: str,
                     language: str = "en", page_count: int = 0, price: float = 0.0,
                     subscription_tier_required: SubscriptionTier = SubscriptionTier.BASIC,
                     publication_date: Optional[datetime] = None, publisher: str = "",
                     cover_image_url: str = "", book_file_url: str = "") -> Optional[Book]:
        """Create and persist a new book."""
        book = Book(
            book_id=self.generate_id("book"),
            title=title,
            author=author,
            isbn=isbn,
            description=description,
            genre=genre,
            language=language,
            page_count=page_count,
            publication_date=publication_date,
            publisher=publisher,
            cover_image_url=cover_image_url,
            book_file_url=book_file_url,
            subscription_tier_required=subscription_tier_required,
            price=price,
        )
        if self.db.save_book(book):
            return book
        return None

    def process_payment(self, subscription_id: str, amount: float,
                        payment_method: str = "credit_card", currency: str = "USD",
                        user_id: Optional[str] = "") -> Optional[Payment]:
        """Process a payment for a subscription."""
        payment = Payment(
            payment_id=self.generate_id("pay"),
            user_id=user_id or "",
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PROCESSING,
            payment_method=payment_method,
        )
        if self.db.save_book_payment(payment):
            payment.status = PaymentStatus.COMPLETED
            return payment
        return None
    
    def _update_book_rating(self, book_id: str):
        """Update book's average rating."""
        reviews = self.db.get_book_reviews(book_id, limit=1000)  # Get all reviews
        
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            average_rating = total_rating / len(reviews)
            
            book = self.db.get_book(book_id)
            if book:
                book.rating = round(average_rating, 1)
                book.total_ratings = len(reviews)
                book.updated_at = datetime.now()
                self.db.save_book(book)
    
    def get_recommendations(self, user_id: str, limit: int = 10) -> List[Book]:
        """Get book recommendations for user."""
        # Simple recommendation based on reading history and ratings
        user_progress = self._get_user_reading_history(user_id)
        
        if not user_progress:
            # If no reading history, return popular books
            return self.db.search_books(limit=limit)
        
        # Get genres from reading history
        read_genres = set()
        for progress in user_progress:
            book = self.db.get_book(progress.book_id)
            if book:
                read_genres.add(book.genre)
        
        # Search for books in similar genres
        recommendations = []
        for genre in read_genres:
            books = self.db.search_books(genre=genre, limit=limit)
            for book in books:
                if book.book_id not in [p.book_id for p in user_progress]:
                    recommendations.append(book)
        
        # Sort by rating and return top recommendations
        recommendations.sort(key=lambda x: x.rating, reverse=True)
        return recommendations[:limit]
    
    def _get_user_reading_history(self, user_id: str) -> List[ReadingProgress]:
        """Get user's reading history."""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT progress_id, user_id, book_id, current_page, total_pages,
                       progress_percentage, status, last_read, completed_at,
                       time_spent_minutes, created_at, updated_at
                FROM reading_progress
                WHERE user_id = ?
                ORDER BY last_read DESC
            ''', (user_id,))

            progress_list = []
            for row in cursor.fetchall():
                progress = ReadingProgress(
                    progress_id=row[0],
                    user_id=row[1],
                    book_id=row[2],
                    current_page=row[3],
                    total_pages=row[4],
                    progress_percentage=row[5],
                    status=ReadingStatus(row[6]),
                    last_read=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                    completed_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    time_spent_minutes=row[9],
                    created_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[11]) if row[11] else datetime.now()
                )
                progress_list.append(progress)

            conn.close()
            return progress_list
        except Exception as e:
            logger.error(f"Error getting user reading history: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics."""
        # This would require more complex queries in a real implementation
        return {
            'books_read': 0,
            'total_reading_time': 0,
            'favorite_genre': 'Unknown',
            'current_books': 0
        }

# Global service instance
book_subscription_service = BookSubscriptionService()

# Flask app for API
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    """Index page."""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Book Subscription Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .book { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .book h3 { margin-top: 0; }
            .book-meta { color: #666; font-size: 14px; }
            .rating { color: #ffa500; font-weight: bold; }
            .tabs { border-bottom: 1px solid #ddd; margin-bottom: 20px; }
            .tab { display: inline-block; padding: 10px 20px; cursor: pointer; border-bottom: 2px solid transparent; }
            .tab.active { border-bottom-color: #007cba; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Book Subscription Service</h1>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('search')">Search Books</div>
                <div class="tab" onclick="showTab('user')">User Management</div>
                <div class="tab" onclick="showTab('subscription')">Subscription</div>
            </div>
            
            <div id="search" class="tab-content active">
                <h2>Search Books</h2>
                <form id="searchForm">
                    <div class="form-group">
                        <input type="text" id="search_query" name="query" placeholder="Search books...">
                    </div>
                    <div class="form-group">
                        <select id="genre_filter" name="genre">
                            <option value="">All Genres</option>
                            <option value="Fiction">Fiction</option>
                            <option value="Science Fiction">Science Fiction</option>
                            <option value="Mystery">Mystery</option>
                            <option value="Romance">Romance</option>
                            <option value="Non-Fiction">Non-Fiction</option>
                        </select>
                    </div>
                    <button type="submit">Search</button>
                </form>
                <div id="searchResults"></div>
            </div>
            
            <div id="user" class="tab-content">
                <h2>Create User Account</h2>
                <form id="userForm">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="first_name">First Name:</label>
                        <input type="text" id="first_name" name="first_name" required>
                    </div>
                    <div class="form-group">
                        <label for="last_name">Last Name:</label>
                        <input type="text" id="last_name" name="last_name" required>
                    </div>
                    <div class="form-group">
                        <label for="date_of_birth">Date of Birth:</label>
                        <input type="date" id="date_of_birth" name="date_of_birth">
                    </div>
                    <button type="submit">Create Account</button>
                </form>
            </div>
            
            <div id="subscription" class="tab-content">
                <h2>Subscription Management</h2>
                <form id="subscriptionForm">
                    <div class="form-group">
                        <label for="user_id">User ID:</label>
                        <input type="text" id="user_id" name="user_id" required>
                    </div>
                    <div class="form-group">
                        <label for="tier">Subscription Tier:</label>
                        <select id="tier" name="tier" required>
                            <option value="basic">Basic ($9.99/month)</option>
                            <option value="premium">Premium ($19.99/month)</option>
                            <option value="enterprise">Enterprise ($49.99/month)</option>
                            <option value="student">Student ($4.99/month)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="payment_frequency">Payment Frequency:</label>
                        <select id="payment_frequency" name="payment_frequency">
                            <option value="monthly">Monthly</option>
                            <option value="yearly">Yearly (20% discount)</option>
                        </select>
                    </div>
                    <button type="submit">Create Subscription</button>
                </form>
            </div>
        </div>
        
        <script>
            function showTab(tabName) {
                // Hide all tab contents
                const contents = document.querySelectorAll('.tab-content');
                contents.forEach(content => content.classList.remove('active'));
                
                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked tab
                event.target.classList.add('active');
            }
            
            document.getElementById('searchForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const query = document.getElementById('search_query').value;
                const genre = document.getElementById('genre_filter').value;
                
                try {
                    const response = await fetch(`/api/books?query=${encodeURIComponent(query)}&genre=${encodeURIComponent(genre)}`);
                    const books = await response.json();
                    
                    const resultsDiv = document.getElementById('searchResults');
                    resultsDiv.innerHTML = '<h3>Search Results</h3>';
                    
                    if (books.length === 0) {
                        resultsDiv.innerHTML += '<p>No books found.</p>';
                        return;
                    }
                    
                    books.forEach(book => {
                        resultsDiv.innerHTML += `
                            <div class="book">
                                <h3>${book.title}</h3>
                                <div class="book-meta">
                                    <p><strong>Author:</strong> ${book.author}</p>
                                    <p><strong>Genre:</strong> ${book.genre}</p>
                                    <p><strong>Pages:</strong> ${book.page_count}</p>
                                    <p><strong>Rating:</strong> <span class="rating">${book.rating}/5</span> (${book.total_ratings} reviews)</p>
                                    <p><strong>Price:</strong> $${book.price}</p>
                                    <p><strong>Description:</strong> ${book.description}</p>
                                </div>
                            </div>
                        `;
                    });
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            document.getElementById('userForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                data.date_of_birth = data.date_of_birth ? new Date(data.date_of_birth).toISOString() : null;
                
                try {
                    const response = await fetch('/api/users', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    alert(result.success ? 'User created successfully! ID: ' + result.user_id : 'Error: ' + result.error);
                    if (result.success) {
                        e.target.reset();
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            document.getElementById('subscriptionForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                // Calculate price based on tier and frequency
                const tierPrices = {
                    'basic': 9.99,
                    'premium': 19.99,
                    'enterprise': 49.99,
                    'student': 4.99
                };
                
                let price = tierPrices[data.tier];
                if (data.payment_frequency === 'yearly') {
                    price *= 12 * 0.8; // 20% discount for yearly
                }
                
                data.price = price;
                
                try {
                    const response = await fetch('/api/subscriptions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    alert(result.success ? 'Subscription created successfully!' : 'Error: ' + result.error);
                    if (result.success) {
                        e.target.reset();
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user."""
    data = request.get_json()
    
    required_fields = ['username', 'email', 'first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        user = book_subscription_service.create_user(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            date_of_birth=datetime.fromisoformat(data['date_of_birth']) if data.get('date_of_birth') else None,
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            zip_code=data.get('zip_code', ''),
            country=data.get('country', '')
        )
        
        if user:
            return jsonify({'success': True, 'user_id': user.user_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to create user'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/books')
def search_books():
    """Search books."""
    query = request.args.get('query', '')
    genre = request.args.get('genre', '')
    author = request.args.get('author', '')
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    books = book_subscription_service.search_books(
        query=query, genre=genre, author=author, 
        user_id=user_id, limit=limit, offset=offset
    )
    
    results = []
    for book in books:
        results.append({
            'book_id': book.book_id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'description': book.description,
            'genre': book.genre,
            'language': book.language,
            'page_count': book.page_count,
            'publication_date': book.publication_date.isoformat() if book.publication_date else None,
            'publisher': book.publisher,
            'cover_image_url': book.cover_image_url,
            'status': book.status.value,
            'subscription_tier_required': book.subscription_tier_required.value,
            'price': book.price,
            'rating': book.rating,
            'total_ratings': book.total_ratings
        })
    
    return jsonify(results)

@app.route('/api/books', methods=['POST'])
def create_book_api():
    """Create a new book."""
    data = request.get_json()
    required = ['title', 'author', 'isbn', 'description', 'genre']
    for f in required:
        if not data.get(f):
            return jsonify({'success': False, 'error': f'{f} is required'})
    try:
        tier_value = data.get('subscription_tier_required', 'basic')
        tier = SubscriptionTier(tier_value)
        book = book_subscription_service.create_book(
            title=data['title'],
            author=data['author'],
            isbn=data['isbn'],
            description=data['description'],
            genre=data['genre'],
            language=data.get('language', 'en'),
            page_count=int(data.get('page_count', 0)),
            price=float(data.get('price', 0.0)),
            subscription_tier_required=tier,
            publisher=data.get('publisher', ''),
            cover_image_url=data.get('cover_image_url', ''),
            book_file_url=data.get('book_file_url', ''),
        )
        if book:
            return jsonify({'success': True, 'book_id': book.book_id})
        return jsonify({'success': False, 'error': 'Failed to create book'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    """Create a new subscription."""
    data = request.get_json()
    
    required_fields = ['user_id', 'tier']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        tier = SubscriptionTier(data['tier'])
        price = float(data.get('price', 0))
        payment_frequency = data.get('payment_frequency', 'monthly')
        
        subscription = book_subscription_service.create_subscription(
            user_id=data['user_id'],
            tier=tier,
            price=price,
            payment_frequency=payment_frequency
        )
        
        if subscription:
            return jsonify({'success': True, 'subscription_id': subscription.subscription_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to create subscription'})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid subscription tier'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/books/<book_id>/start-reading', methods=['POST'])
def start_reading(book_id):
    """Start reading a book."""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'user_id is required'})
    
    progress = book_subscription_service.start_reading(user_id, book_id)
    
    if progress:
        return jsonify({
            'success': True,
            'progress_id': progress.progress_id,
            'status': progress.status.value,
            'current_page': progress.current_page,
            'total_pages': progress.total_pages,
            'progress_percentage': progress.progress_percentage
        })
    else:
        return jsonify({'success': False, 'error': 'Cannot access this book or book not found'})

@app.route('/api/books/<book_id>/reviews', methods=['POST'])
def add_review(book_id):
    """Add a book review."""
    data = request.get_json()
    
    required_fields = ['user_id', 'rating', 'review_text']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        review = book_subscription_service.add_book_review(
            user_id=data['user_id'],
            book_id=book_id,
            rating=int(data['rating']),
            review_text=data['review_text']
        )
        
        if review:
            return jsonify({'success': True, 'review_id': review.review_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to add review'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'book_subscription'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
