#!/usr/bin/env python3
"""
Newsfeed System - Content Aggregation and Distribution Service

This system provides:
- Real-time news aggregation from multiple sources
- Content filtering and categorization
- User personalization and recommendation engine
- Social features (likes, shares, comments)
- Content ranking algorithms
- API for content consumption
"""

import asyncio
import aiohttp
import json
import sqlite3
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import re
from collections import defaultdict, Counter
import threading
import queue


@dataclass
class NewsArticle:
    """Represents a news article."""
    id: str
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    category: str
    tags: List[str]
    author: str
    image_url: Optional[str] = None
    summary: Optional[str] = None
    language: str = "en"
    sentiment_score: float = 0.0
    engagement_score: float = 0.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'source': self.source,
            'published_at': self.published_at.isoformat(),
            'category': self.category,
            'tags': self.tags,
            'author': self.author,
            'image_url': self.image_url,
            'summary': self.summary,
            'language': self.language,
            'sentiment_score': self.sentiment_score,
            'engagement_score': self.engagement_score,
            'metadata': self.metadata
        }


@dataclass
class UserProfile:
    """Represents a user profile."""
    user_id: str
    username: str
    email: str
    preferences: Dict[str, Any]
    reading_history: List[str]
    liked_articles: List[str]
    shared_articles: List[str]
    followed_sources: List[str]
    followed_categories: List[str]
    created_at: datetime
    last_active: datetime

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.reading_history is None:
            self.reading_history = []
        if self.liked_articles is None:
            self.liked_articles = []
        if self.shared_articles is None:
            self.shared_articles = []
        if self.followed_sources is None:
            self.followed_sources = []
        if self.followed_categories is None:
            self.followed_categories = []

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'preferences': self.preferences,
            'reading_history': self.reading_history,
            'liked_articles': self.liked_articles,
            'shared_articles': self.shared_articles,
            'followed_sources': self.followed_sources,
            'followed_categories': self.followed_categories,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat()
        }


class NewsDatabase:
    """Database operations for news system."""

    def __init__(self, db_path: str = "newsfeed.db"):
        """Initialize database."""
        self.db_path = db_path
        self.init_database()

    def init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    published_at TIMESTAMP NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT,
                    author TEXT,
                    image_url TEXT,
                    summary TEXT,
                    language TEXT DEFAULT 'en',
                    sentiment_score REAL DEFAULT 0.0,
                    engagement_score REAL DEFAULT 0.0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    preferences TEXT,
                    reading_history TEXT,
                    liked_articles TEXT,
                    shared_articles TEXT,
                    followed_sources TEXT,
                    followed_categories TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    article_id TEXT NOT NULL,
                    interaction_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            ''')
            
            # Sources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    rss_url TEXT,
                    api_url TEXT,
                    category TEXT,
                    language TEXT DEFAULT 'en',
                    is_active BOOLEAN DEFAULT 1,
                    last_fetched TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def save_article(self, article: NewsArticle) -> bool:
        """Save article to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (id, title, content, url, source, published_at, category, tags,
                     author, image_url, summary, language, sentiment_score, 
                     engagement_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.id, article.title, article.content, article.url,
                    article.source, article.published_at.isoformat(),
                    article.category, json.dumps(article.tags), article.author,
                    article.image_url, article.summary, article.language,
                    article.sentiment_score, article.engagement_score,
                    json.dumps(article.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving article: {e}")
            return False

    def get_article(self, article_id: str) -> Optional[NewsArticle]:
        """Get article by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, content, url, source, published_at, category,
                           tags, author, image_url, summary, language, sentiment_score,
                           engagement_score, metadata
                    FROM articles WHERE id = ?
                ''', (article_id,))
                
                row = cursor.fetchone()
                if row:
                    return NewsArticle(
                        id=row[0], title=row[1], content=row[2], url=row[3],
                        source=row[4], published_at=datetime.fromisoformat(row[5]),
                        category=row[6], tags=json.loads(row[7]) if row[7] else [],
                        author=row[8], image_url=row[9], summary=row[10],
                        language=row[11], sentiment_score=row[12],
                        engagement_score=row[13],
                        metadata=json.loads(row[14]) if row[14] else {}
                    )
                return None
        except Exception as e:
            logging.error(f"Error getting article: {e}")
            return None

    def get_articles(self, limit: int = 50, offset: int = 0, 
                    category: str = None, source: str = None) -> List[NewsArticle]:
        """Get articles with filtering."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, title, content, url, source, published_at, category,
                           tags, author, image_url, summary, language, sentiment_score,
                           engagement_score, metadata
                    FROM articles
                '''
                params = []
                
                conditions = []
                if category:
                    conditions.append("category = ?")
                    params.append(category)
                if source:
                    conditions.append("source = ?")
                    params.append(source)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                articles = []
                for row in rows:
                    articles.append(NewsArticle(
                        id=row[0], title=row[1], content=row[2], url=row[3],
                        source=row[4], published_at=datetime.fromisoformat(row[5]),
                        category=row[6], tags=json.loads(row[7]) if row[7] else [],
                        author=row[8], image_url=row[9], summary=row[10],
                        language=row[11], sentiment_score=row[12],
                        engagement_score=row[13],
                        metadata=json.loads(row[14]) if row[14] else {}
                    ))
                
                return articles
        except Exception as e:
            logging.error(f"Error getting articles: {e}")
            return []

    def save_user(self, user: UserProfile) -> bool:
        """Save user profile."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, email, preferences, reading_history,
                     liked_articles, shared_articles, followed_sources,
                     followed_categories, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.user_id, user.username, user.email,
                    json.dumps(user.preferences), json.dumps(user.reading_history),
                    json.dumps(user.liked_articles), json.dumps(user.shared_articles),
                    json.dumps(user.followed_sources), json.dumps(user.followed_categories),
                    user.created_at.isoformat(), user.last_active.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving user: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, email, preferences, reading_history,
                           liked_articles, shared_articles, followed_sources,
                           followed_categories, created_at, last_active
                    FROM users WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return UserProfile(
                        user_id=row[0], username=row[1], email=row[2],
                        preferences=json.loads(row[3]) if row[3] else {},
                        reading_history=json.loads(row[4]) if row[4] else [],
                        liked_articles=json.loads(row[5]) if row[5] else [],
                        shared_articles=json.loads(row[6]) if row[6] else [],
                        followed_sources=json.loads(row[7]) if row[7] else [],
                        followed_categories=json.loads(row[8]) if row[8] else [],
                        created_at=datetime.fromisoformat(row[9]),
                        last_active=datetime.fromisoformat(row[10])
                    )
                return None
        except Exception as e:
            logging.error(f"Error getting user: {e}")
            return None

    def record_interaction(self, user_id: str, article_id: str, 
                          interaction_type: str) -> bool:
        """Record user interaction."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO interactions (user_id, article_id, interaction_type)
                    VALUES (?, ?, ?)
                ''', (user_id, article_id, interaction_type))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error recording interaction: {e}")
            return False

    def get_user_interactions(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get user interactions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT article_id, interaction_type, timestamp
                    FROM interactions 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                return [
                    {
                        'article_id': row[0],
                        'interaction_type': row[1],
                        'timestamp': row[2]
                    }
                    for row in rows
                ]
        except Exception as e:
            logging.error(f"Error getting interactions: {e}")
            return []


class NewsAggregator:
    """Aggregates news from multiple sources."""

    def __init__(self, db: NewsDatabase):
        """Initialize aggregator."""
        self.db = db
        self.sources = [
            {
                'name': 'TechCrunch',
                'url': 'https://techcrunch.com',
                'rss_url': 'https://techcrunch.com/feed/',
                'category': 'technology'
            },
            {
                'name': 'BBC News',
                'url': 'https://bbc.com/news',
                'rss_url': 'https://feeds.bbci.co.uk/news/rss.xml',
                'category': 'general'
            },
            {
                'name': 'Reuters',
                'url': 'https://reuters.com',
                'rss_url': 'https://feeds.reuters.com/reuters/topNews',
                'category': 'general'
            }
        ]

    async def fetch_rss_feed(self, rss_url: str) -> List[Dict]:
        """Fetch RSS feed."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(rss_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self.parse_rss_content(content)
                    else:
                        logging.error(f"Failed to fetch RSS: {response.status}")
                        return []
        except Exception as e:
            logging.error(f"Error fetching RSS: {e}")
            return []

    def parse_rss_content(self, content: str) -> List[Dict]:
        """Parse RSS content."""
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(content)
            items = []
            
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                
                if title is not None and link is not None:
                    items.append({
                        'title': title.text or '',
                        'url': link.text or '',
                        'content': description.text if description is not None else '',
                        'published_at': pub_date.text if pub_date is not None else '',
                        'source': 'RSS Feed'
                    })
            
            return items
        except Exception as e:
            logging.error(f"Error parsing RSS: {e}")
            return []

    async def aggregate_news(self) -> int:
        """Aggregate news from all sources."""
        total_articles = 0
        
        for source in self.sources:
            try:
                articles = await self.fetch_rss_feed(source['rss_url'])
                
                for article_data in articles:
                    article = NewsArticle(
                        id=self.generate_article_id(article_data['url']),
                        title=article_data['title'],
                        content=article_data['content'],
                        url=article_data['url'],
                        source=source['name'],
                        published_at=datetime.now(),
                        category=source['category'],
                        tags=self.extract_tags(article_data['title'] + ' ' + article_data['content']),
                        author='Unknown',
                        summary=self.generate_summary(article_data['content']),
                        sentiment_score=self.analyze_sentiment(article_data['content'])
                    )
                    
                    if self.db.save_article(article):
                        total_articles += 1
                
                logging.info(f"Aggregated {len(articles)} articles from {source['name']}")
                
            except Exception as e:
                logging.error(f"Error aggregating from {source['name']}: {e}")
        
        return total_articles

    def generate_article_id(self, url: str) -> str:
        """Generate unique article ID."""
        return hashlib.md5(url.encode()).hexdigest()

    def extract_tags(self, text: str) -> List[str]:
        """Extract tags from text."""
        # Simple keyword extraction
        keywords = [
            'technology', 'politics', 'sports', 'business', 'health',
            'science', 'entertainment', 'world', 'local', 'breaking'
        ]
        
        text_lower = text.lower()
        found_tags = []
        
        for keyword in keywords:
            if keyword in text_lower:
                found_tags.append(keyword)
        
        return found_tags

    def generate_summary(self, content: str) -> str:
        """Generate article summary."""
        if len(content) <= 200:
            return content
        
        # Simple summary: first 200 characters
        return content[:200] + "..."

    def analyze_sentiment(self, text: str) -> float:
        """Analyze text sentiment."""
        # Simple sentiment analysis based on keywords
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'positive']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'negative', 'worst']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment))


class RecommendationEngine:
    """Generates personalized recommendations."""

    def __init__(self, db: NewsDatabase):
        """Initialize recommendation engine."""
        self.db = db

    def get_recommendations(self, user_id: str, limit: int = 10) -> List[NewsArticle]:
        """Get personalized recommendations for user."""
        user = self.db.get_user(user_id)
        if not user:
            return []

        # Get user's reading history and preferences
        liked_categories = self.get_user_preferred_categories(user)
        liked_sources = user.followed_sources
        
        # Get articles from preferred categories and sources
        recommendations = []
        
        for category in liked_categories:
            articles = self.db.get_articles(limit=5, category=category)
            recommendations.extend(articles)
        
        for source in liked_sources:
            articles = self.db.get_articles(limit=5, source=source)
            recommendations.extend(articles)
        
        # Remove duplicates and articles user has already seen
        seen_articles = set(user.reading_history + user.liked_articles)
        unique_recommendations = []
        
        for article in recommendations:
            if article.id not in seen_articles and article not in unique_recommendations:
                unique_recommendations.append(article)
        
        # Sort by engagement score and recency
        unique_recommendations.sort(
            key=lambda x: (x.engagement_score, x.published_at),
            reverse=True
        )
        
        return unique_recommendations[:limit]

    def get_user_preferred_categories(self, user: UserProfile) -> List[str]:
        """Get user's preferred categories based on history."""
        category_counts = Counter()
        
        # Count categories from reading history
        for article_id in user.reading_history:
            article = self.db.get_article(article_id)
            if article:
                category_counts[article.category] += 1
        
        # Count categories from liked articles
        for article_id in user.liked_articles:
            article = self.db.get_article(article_id)
            if article:
                category_counts[article.category] += 2  # Weight likes higher
        
        # Return top categories
        return [category for category, count in category_counts.most_common(5)]


class NewsfeedService:
    """Main newsfeed service."""

    def __init__(self, db_path: str = "newsfeed.db"):
        """Initialize service."""
        self.db = NewsDatabase(db_path)
        self.aggregator = NewsAggregator(self.db)
        self.recommendation_engine = RecommendationEngine(self.db)
        self.running = False
        self.aggregation_thread = None

    def start_aggregation(self):
        """Start background news aggregation."""
        if not self.running:
            self.running = True
            self.aggregation_thread = threading.Thread(target=self._aggregation_loop)
            self.aggregation_thread.daemon = True
            self.aggregation_thread.start()

    def stop_aggregation(self):
        """Stop background news aggregation."""
        self.running = False
        if self.aggregation_thread:
            self.aggregation_thread.join()

    def _aggregation_loop(self):
        """Background aggregation loop."""
        while self.running:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                total_articles = loop.run_until_complete(self.aggregator.aggregate_news())
                loop.close()
                
                logging.info(f"Aggregated {total_articles} new articles")
                
                # Wait 5 minutes before next aggregation
                time.sleep(300)
            except Exception as e:
                logging.error(f"Error in aggregation loop: {e}")
                time.sleep(60)  # Wait 1 minute on error

    def get_newsfeed(self, user_id: str = None, limit: int = 50) -> List[Dict]:
        """Get newsfeed for user."""
        if user_id:
            # Get personalized recommendations
            recommendations = self.recommendation_engine.get_recommendations(user_id, limit)
            return [article.to_dict() for article in recommendations]
        else:
            # Get general newsfeed
            articles = self.db.get_articles(limit=limit)
            return [article.to_dict() for article in articles]

    def like_article(self, user_id: str, article_id: str) -> bool:
        """Like an article."""
        user = self.db.get_user(user_id)
        if user and article_id not in user.liked_articles:
            user.liked_articles.append(article_id)
            self.db.save_user(user)
            self.db.record_interaction(user_id, article_id, 'like')
            return True
        return False

    def share_article(self, user_id: str, article_id: str) -> bool:
        """Share an article."""
        user = self.db.get_user(user_id)
        if user and article_id not in user.shared_articles:
            user.shared_articles.append(article_id)
            self.db.save_user(user)
            self.db.record_interaction(user_id, article_id, 'share')
            return True
        return False

    def read_article(self, user_id: str, article_id: str) -> bool:
        """Record article read."""
        user = self.db.get_user(user_id)
        if user and article_id not in user.reading_history:
            user.reading_history.append(article_id)
            # Keep only last 100 articles in history
            if len(user.reading_history) > 100:
                user.reading_history = user.reading_history[-100:]
            self.db.save_user(user)
            self.db.record_interaction(user_id, article_id, 'read')
            return True
        return False


# Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'newsfeed_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize service
newsfeed_service = NewsfeedService()
newsfeed_service.start_aggregation()


@app.route('/')
def index():
    """Home page."""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Newsfeed Service</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .article { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px; }
            .article h2 { margin-top: 0; color: #333; }
            .article-meta { color: #666; font-size: 0.9em; margin-bottom: 10px; }
            .article-content { line-height: 1.6; }
            .article-actions { margin-top: 15px; }
            .btn { padding: 8px 16px; margin-right: 10px; border: none; border-radius: 4px; cursor: pointer; }
            .btn-like { background: #e74c3c; color: white; }
            .btn-share { background: #3498db; color: white; }
            .btn-read { background: #2ecc71; color: white; }
            .btn:hover { opacity: 0.8; }
        </style>
    </head>
    <body>
        <h1>Newsfeed Service</h1>
        <div id="newsfeed"></div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            
            // Load initial newsfeed
            fetch('/api/newsfeed')
                .then(response => response.json())
                .then(data => {
                    displayNewsfeed(data);
                });
            
            // Listen for new articles
            socket.on('new_article', function(article) {
                addArticleToFeed(article);
            });
            
            function displayNewsfeed(articles) {
                const newsfeed = document.getElementById('newsfeed');
                newsfeed.innerHTML = '';
                
                articles.forEach(article => {
                    addArticleToFeed(article);
                });
            }
            
            function addArticleToFeed(article) {
                const newsfeed = document.getElementById('newsfeed');
                const articleDiv = document.createElement('div');
                articleDiv.className = 'article';
                articleDiv.innerHTML = `
                    <h2>${article.title}</h2>
                    <div class="article-meta">
                        By ${article.author} | ${article.source} | ${new Date(article.published_at).toLocaleString()}
                    </div>
                    <div class="article-content">${article.content}</div>
                    <div class="article-actions">
                        <button class="btn btn-like" onclick="likeArticle('${article.id}')">Like</button>
                        <button class="btn btn-share" onclick="shareArticle('${article.id}')">Share</button>
                        <button class="btn btn-read" onclick="readArticle('${article.id}')">Mark as Read</button>
                    </div>
                `;
                newsfeed.insertBefore(articleDiv, newsfeed.firstChild);
            }
            
            function likeArticle(articleId) {
                fetch(`/api/like/${articleId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Article liked!');
                        }
                    });
            }
            
            function shareArticle(articleId) {
                fetch(`/api/share/${articleId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Article shared!');
                        }
                    });
            }
            
            function readArticle(articleId) {
                fetch(`/api/read/${articleId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Article marked as read!');
                        }
                    });
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)


@app.route('/api/newsfeed')
def get_newsfeed():
    """Get newsfeed API."""
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 50))
    
    newsfeed = newsfeed_service.get_newsfeed(user_id, limit)
    return jsonify({'success': True, 'data': newsfeed})


@app.route('/api/like/<article_id>', methods=['POST'])
def like_article(article_id):
    """Like article API."""
    user_id = request.json.get('user_id', 'anonymous')
    
    success = newsfeed_service.like_article(user_id, article_id)
    return jsonify({'success': success})


@app.route('/api/share/<article_id>', methods=['POST'])
def share_article(article_id):
    """Share article API."""
    user_id = request.json.get('user_id', 'anonymous')
    
    success = newsfeed_service.share_article(user_id, article_id)
    return jsonify({'success': success})


@app.route('/api/read/<article_id>', methods=['POST'])
def read_article(article_id):
    """Read article API."""
    user_id = request.json.get('user_id', 'anonymous')
    
    success = newsfeed_service.read_article(user_id, article_id)
    return jsonify({'success': success})


@app.route('/api/recommendations/<user_id>')
def get_recommendations(user_id):
    """Get recommendations API."""
    limit = int(request.args.get('limit', 10))
    
    recommendations = newsfeed_service.recommendation_engine.get_recommendations(user_id, limit)
    return jsonify({'success': True, 'data': [article.to_dict() for article in recommendations]})


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    emit('status', {'message': 'Connected to newsfeed'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5001)
    finally:
        newsfeed_service.stop_aggregation()
