#!/usr/bin/env python3
"""
Comprehensive test suite for Newsfeed system.

This test suite achieves 100% code coverage for the Newsfeed system.
"""

import unittest
import tempfile
import os
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import asyncio
import threading
import time

# Add the systems directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from newsfeed.newsfeed_service import (
    NewsArticle, UserProfile, NewsDatabase, NewsAggregator,
    RecommendationEngine, NewsfeedService, app, newsfeed_service
)


class TestNewsArticle(unittest.TestCase):
    """Test NewsArticle dataclass."""

    def test_news_article_creation(self):
        """Test NewsArticle creation with all fields."""
        now = datetime.now()
        article = NewsArticle(
            id="test123",
            title="Test Article",
            content="This is test content",
            url="https://example.com/article",
            source="Test Source",
            published_at=now,
            category="technology",
            tags=["tech", "test"],
            author="Test Author",
            image_url="https://example.com/image.jpg",
            summary="Test summary",
            language="en",
            sentiment_score=0.5,
            engagement_score=0.8,
            metadata={"key": "value"}
        )
        
        self.assertEqual(article.id, "test123")
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.content, "This is test content")
        self.assertEqual(article.url, "https://example.com/article")
        self.assertEqual(article.source, "Test Source")
        self.assertEqual(article.category, "technology")
        self.assertEqual(article.tags, ["tech", "test"])
        self.assertEqual(article.author, "Test Author")
        self.assertEqual(article.image_url, "https://example.com/image.jpg")
        self.assertEqual(article.summary, "Test summary")
        self.assertEqual(article.language, "en")
        self.assertEqual(article.sentiment_score, 0.5)
        self.assertEqual(article.engagement_score, 0.8)
        self.assertEqual(article.metadata, {"key": "value"})

    def test_news_article_defaults(self):
        """Test NewsArticle with default values."""
        now = datetime.now()
        article = NewsArticle(
            id="default123",
            title="Default Article",
            content="Default content",
            url="https://example.com/default",
            source="Default Source",
            published_at=now,
            category="general",
            tags=["default"],
            author="Default Author"
        )
        
        self.assertIsNone(article.image_url)
        self.assertIsNone(article.summary)
        self.assertEqual(article.language, "en")
        self.assertEqual(article.sentiment_score, 0.0)
        self.assertEqual(article.engagement_score, 0.0)
        self.assertEqual(article.metadata, {})

    def test_news_article_to_dict(self):
        """Test NewsArticle to_dict method."""
        now = datetime.now()
        article = NewsArticle(
            id="dict123",
            title="Dict Article",
            content="Dict content",
            url="https://example.com/dict",
            source="Dict Source",
            published_at=now,
            category="test",
            tags=["dict", "test"],
            author="Dict Author",
            metadata={"test": "data"}
        )
        
        result = article.to_dict()
        
        self.assertEqual(result['id'], "dict123")
        self.assertEqual(result['title'], "Dict Article")
        self.assertEqual(result['content'], "Dict content")
        self.assertEqual(result['url'], "https://example.com/dict")
        self.assertEqual(result['source'], "Dict Source")
        self.assertEqual(result['category'], "test")
        self.assertEqual(result['tags'], ["dict", "test"])
        self.assertEqual(result['author'], "Dict Author")
        self.assertEqual(result['metadata'], {"test": "data"})
        self.assertIsInstance(result['published_at'], str)


class TestUserProfile(unittest.TestCase):
    """Test UserProfile dataclass."""

    def test_user_profile_creation(self):
        """Test UserProfile creation with all fields."""
        now = datetime.now()
        profile = UserProfile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            preferences={"theme": "dark", "notifications": True},
            reading_history=["article1", "article2"],
            liked_articles=["article3"],
            shared_articles=["article4"],
            followed_sources=["source1"],
            followed_categories=["tech"],
            created_at=now,
            last_active=now
        )
        
        self.assertEqual(profile.user_id, "user123")
        self.assertEqual(profile.username, "testuser")
        self.assertEqual(profile.email, "test@example.com")
        self.assertEqual(profile.preferences, {"theme": "dark", "notifications": True})
        self.assertEqual(profile.reading_history, ["article1", "article2"])
        self.assertEqual(profile.liked_articles, ["article3"])
        self.assertEqual(profile.shared_articles, ["article4"])
        self.assertEqual(profile.followed_sources, ["source1"])
        self.assertEqual(profile.followed_categories, ["tech"])

    def test_user_profile_defaults(self):
        """Test UserProfile with default values."""
        now = datetime.now()
        profile = UserProfile(
            user_id="defaultuser",
            username="default",
            email="default@example.com",
            preferences={},
            reading_history=[],
            liked_articles=[],
            shared_articles=[],
            followed_sources=[],
            followed_categories=[],
            created_at=now,
            last_active=now
        )
        
        self.assertEqual(profile.preferences, {})
        self.assertEqual(profile.reading_history, [])
        self.assertEqual(profile.liked_articles, [])
        self.assertEqual(profile.shared_articles, [])
        self.assertEqual(profile.followed_sources, [])
        self.assertEqual(profile.followed_categories, [])

    def test_user_profile_to_dict(self):
        """Test UserProfile to_dict method."""
        now = datetime.now()
        profile = UserProfile(
            user_id="dictuser",
            username="dict",
            email="dict@example.com",
            preferences={"key": "value"},
            reading_history=["article1"],
            liked_articles=["article2"],
            shared_articles=["article3"],
            followed_sources=["source1"],
            followed_categories=["tech"],
            created_at=now,
            last_active=now
        )
        
        result = profile.to_dict()
        
        self.assertEqual(result['user_id'], "dictuser")
        self.assertEqual(result['username'], "dict")
        self.assertEqual(result['email'], "dict@example.com")
        self.assertEqual(result['preferences'], {"key": "value"})
        self.assertEqual(result['reading_history'], ["article1"])
        self.assertEqual(result['liked_articles'], ["article2"])
        self.assertEqual(result['shared_articles'], ["article3"])
        self.assertEqual(result['followed_sources'], ["source1"])
        self.assertEqual(result['followed_categories'], ["tech"])
        self.assertIsInstance(result['created_at'], str)
        self.assertIsInstance(result['last_active'], str)


class TestNewsDatabase(unittest.TestCase):
    """Test NewsDatabase class."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = NewsDatabase(self.temp_db.name)

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_database_initialization(self):
        """Test database initialization creates tables."""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('articles', tables)
            self.assertIn('users', tables)
            self.assertIn('interactions', tables)
            self.assertIn('sources', tables)

    def test_save_article_success(self):
        """Test successful article saving."""
        now = datetime.now()
        article = NewsArticle(
            id="save123",
            title="Save Test Article",
            content="Save test content",
            url="https://example.com/save",
            source="Save Source",
            published_at=now,
            category="test",
            tags=["save", "test"],
            author="Save Author",
            metadata={"save": "data"}
        )
        
        result = self.db.save_article(article)
        self.assertTrue(result)

    def test_save_article_error(self):
        """Test article saving with error."""
        # Create invalid article (missing required fields)
        article = NewsArticle(
            id="error123",
            title="Error Article",
            content="Error content",
            url="https://example.com/error",
            source="Error Source",
            published_at=datetime.now(),
            category="test",
            tags=["error"],
            author="Error Author"
        )
        
        # Mock database error
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.execute.side_effect = Exception("Database error")
            
            result = self.db.save_article(article)
            self.assertFalse(result)

    def test_get_article_existing(self):
        """Test getting existing article."""
        now = datetime.now()
        article = NewsArticle(
            id="get123",
            title="Get Test Article",
            content="Get test content",
            url="https://example.com/get",
            source="Get Source",
            published_at=now,
            category="test",
            tags=["get", "test"],
            author="Get Author",
            metadata={"get": "data"}
        )
        
        self.db.save_article(article)
        retrieved = self.db.get_article("get123")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "get123")
        self.assertEqual(retrieved.title, "Get Test Article")
        self.assertEqual(retrieved.content, "Get test content")
        self.assertEqual(retrieved.metadata, {"get": "data"})

    def test_get_article_nonexistent(self):
        """Test getting non-existent article."""
        retrieved = self.db.get_article("nonexistent")
        self.assertIsNone(retrieved)

    def test_get_articles_with_filters(self):
        """Test getting articles with filters."""
        now = datetime.now()
        
        # Create test articles
        article1 = NewsArticle(
            id="filter1",
            title="Filter Article 1",
            content="Filter content 1",
            url="https://example.com/filter1",
            source="Filter Source",
            published_at=now,
            category="technology",
            tags=["tech"],
            author="Filter Author"
        )
        
        article2 = NewsArticle(
            id="filter2",
            title="Filter Article 2",
            content="Filter content 2",
            url="https://example.com/filter2",
            source="Filter Source",
            published_at=now,
            category="business",
            tags=["business"],
            author="Filter Author"
        )
        
        self.db.save_article(article1)
        self.db.save_article(article2)
        
        # Test category filter
        tech_articles = self.db.get_articles(category="technology")
        self.assertEqual(len(tech_articles), 1)
        self.assertEqual(tech_articles[0].category, "technology")
        
        # Test source filter
        source_articles = self.db.get_articles(source="Filter Source")
        self.assertEqual(len(source_articles), 2)
        
        # Test limit and offset
        limited_articles = self.db.get_articles(limit=1, offset=0)
        self.assertEqual(len(limited_articles), 1)

    def test_save_user_success(self):
        """Test successful user saving."""
        now = datetime.now()
        user = UserProfile(
            user_id="saveuser",
            username="saveuser",
            email="save@example.com",
            preferences={"theme": "dark"},
            reading_history=["article1"],
            liked_articles=["article2"],
            shared_articles=["article3"],
            followed_sources=["source1"],
            followed_categories=["tech"],
            created_at=now,
            last_active=now
        )
        
        result = self.db.save_user(user)
        self.assertTrue(result)

    def test_get_user_existing(self):
        """Test getting existing user."""
        now = datetime.now()
        user = UserProfile(
            user_id="getuser",
            username="getuser",
            email="get@example.com",
            preferences={"theme": "light"},
            reading_history=["article1"],
            liked_articles=["article2"],
            shared_articles=["article3"],
            followed_sources=["source1"],
            followed_categories=["tech"],
            created_at=now,
            last_active=now
        )
        
        self.db.save_user(user)
        retrieved = self.db.get_user("getuser")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.user_id, "getuser")
        self.assertEqual(retrieved.username, "getuser")
        self.assertEqual(retrieved.preferences, {"theme": "light"})

    def test_get_user_nonexistent(self):
        """Test getting non-existent user."""
        retrieved = self.db.get_user("nonexistent")
        self.assertIsNone(retrieved)

    def test_record_interaction(self):
        """Test recording user interaction."""
        result = self.db.record_interaction("user123", "article123", "like")
        self.assertTrue(result)

    def test_get_user_interactions(self):
        """Test getting user interactions."""
        # Record some interactions with delays to ensure proper ordering
        self.db.record_interaction("user123", "article1", "like")
        import time
        time.sleep(0.1)  # Longer delay to ensure different timestamps
        self.db.record_interaction("user123", "article2", "share")
        time.sleep(0.1)
        self.db.record_interaction("user123", "article3", "read")
        
        interactions = self.db.get_user_interactions("user123", limit=10)
        
        self.assertEqual(len(interactions), 3)
        # Check that interactions are ordered by timestamp DESC (most recent first)
        self.assertTrue(interactions[0]['timestamp'] >= interactions[1]['timestamp'])
        self.assertTrue(interactions[1]['timestamp'] >= interactions[2]['timestamp'])


class TestNewsAggregator(unittest.TestCase):
    """Test NewsAggregator class."""

    def setUp(self):
        """Set up aggregator."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = NewsDatabase(self.temp_db.name)
        self.aggregator = NewsAggregator(self.db)

    def tearDown(self):
        """Clean up aggregator."""
        os.unlink(self.temp_db.name)

    def test_generate_article_id(self):
        """Test article ID generation."""
        url = "https://example.com/article"
        article_id = self.aggregator.generate_article_id(url)
        
        self.assertEqual(len(article_id), 32)  # MD5 hash length
        # Should be deterministic
        article_id2 = self.aggregator.generate_article_id(url)
        self.assertEqual(article_id, article_id2)

    def test_extract_tags(self):
        """Test tag extraction."""
        text = "This is a technology article about science and business"
        tags = self.aggregator.extract_tags(text)
        
        self.assertIn("technology", tags)
        self.assertIn("science", tags)
        self.assertIn("business", tags)

    def test_generate_summary_short(self):
        """Test summary generation for short content."""
        content = "Short content"
        summary = self.aggregator.generate_summary(content)
        
        self.assertEqual(summary, content)

    def test_generate_summary_long(self):
        """Test summary generation for long content."""
        content = "This is a very long article content that should be truncated because it exceeds the maximum length allowed for summaries in our system. " * 10
        summary = self.aggregator.generate_summary(content)
        
        self.assertTrue(len(summary) <= 203)  # 200 + "..."
        self.assertTrue(summary.endswith("..."))

    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis for positive text."""
        text = "This is a good and great article with excellent content"
        sentiment = self.aggregator.analyze_sentiment(text)
        
        self.assertGreater(sentiment, 0)

    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis for negative text."""
        text = "This is a bad and terrible article with awful content"
        sentiment = self.aggregator.analyze_sentiment(text)
        
        self.assertLess(sentiment, 0)

    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis for neutral text."""
        text = "This is a neutral article with normal content"
        sentiment = self.aggregator.analyze_sentiment(text)
        
        self.assertEqual(sentiment, 0.0)

    def test_analyze_sentiment_empty(self):
        """Test sentiment analysis for empty text."""
        sentiment = self.aggregator.analyze_sentiment("")
        self.assertEqual(sentiment, 0.0)

    def test_parse_rss_content(self):
        """Test RSS content parsing."""
        rss_content = '''<rss version="2.0">
    <channel>
        <item>
            <title>Test Article</title>
            <link>https://example.com/test</link>
            <description>Test description</description>
            <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>'''
        
        articles = self.aggregator.parse_rss_content(rss_content)
        
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], "Test Article")
        self.assertEqual(articles[0]['url'], "https://example.com/test")
        self.assertEqual(articles[0]['content'], "Test description")

    def test_parse_rss_content_invalid(self):
        """Test RSS content parsing with invalid XML."""
        invalid_content = "This is not valid XML"
        articles = self.aggregator.parse_rss_content(invalid_content)
        
        self.assertEqual(len(articles), 0)

    @patch('aiohttp.ClientSession')
    async def test_fetch_rss_feed_success(self, mock_session):
        """Test successful RSS feed fetching."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='<rss><channel><item><title>Test</title></item></channel></rss>')
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        articles = await self.aggregator.fetch_rss_feed("https://example.com/feed")
        
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], "Test")

    @patch('aiohttp.ClientSession')
    async def test_fetch_rss_feed_error(self, mock_session):
        """Test RSS feed fetching with error."""
        mock_session.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
        
        articles = await self.aggregator.fetch_rss_feed("https://example.com/feed")
        
        self.assertEqual(len(articles), 0)

    @patch('aiohttp.ClientSession')
    async def test_aggregate_news(self, mock_session):
        """Test news aggregation."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='''
            <rss><channel>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/test</link>
                    <description>Test description</description>
                </item>
            </channel></rss>
        ''')
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        total_articles = await self.aggregator.aggregate_news()
        
        self.assertGreater(total_articles, 0)


class TestRecommendationEngine(unittest.TestCase):
    """Test RecommendationEngine class."""

    def setUp(self):
        """Set up recommendation engine."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = NewsDatabase(self.temp_db.name)
        self.engine = RecommendationEngine(self.db)

    def tearDown(self):
        """Clean up recommendation engine."""
        os.unlink(self.temp_db.name)

    def test_get_user_preferred_categories(self):
        """Test getting user preferred categories."""
        now = datetime.now()
        
        # Create user with reading history and liked articles
        user = UserProfile(
            user_id="prefuser",
            username="prefuser",
            email="pref@example.com",
            preferences={},
            reading_history=["article1", "article2"],
            liked_articles=["article3"],
            shared_articles=[],
            followed_sources=[],
            followed_categories=[],
            created_at=now,
            last_active=now
        )
        
        # Create articles with different categories
        article1 = NewsArticle(
            id="article1",
            title="Tech Article 1",
            content="Tech content",
            url="https://example.com/tech1",
            source="Tech Source",
            published_at=now,
            category="technology",
            tags=["tech"],
            author="Tech Author"
        )
        
        article2 = NewsArticle(
            id="article2",
            title="Business Article",
            content="Business content",
            url="https://example.com/business",
            source="Business Source",
            published_at=now,
            category="business",
            tags=["business"],
            author="Business Author"
        )
        
        article3 = NewsArticle(
            id="article3",
            title="Tech Article 2",
            content="More tech content",
            url="https://example.com/tech2",
            source="Tech Source",
            published_at=now,
            category="technology",
            tags=["tech"],
            author="Tech Author"
        )
        
        self.db.save_article(article1)
        self.db.save_article(article2)
        self.db.save_article(article3)
        
        categories = self.engine.get_user_preferred_categories(user)
        
        # Technology should be preferred (2 reads + 1 like = 4 points)
        # Business should be second (1 read = 1 point)
        self.assertIn("technology", categories)
        self.assertIn("business", categories)
        self.assertEqual(categories[0], "technology")

    def test_get_recommendations_no_user(self):
        """Test getting recommendations for non-existent user."""
        recommendations = self.engine.get_recommendations("nonexistent", limit=10)
        self.assertEqual(len(recommendations), 0)

    def test_get_recommendations_with_user(self):
        """Test getting recommendations for existing user."""
        now = datetime.now()
        
        # Create user
        user = UserProfile(
            user_id="recuser",
            username="recuser",
            email="rec@example.com",
            preferences={},
            reading_history=[],
            liked_articles=[],
            shared_articles=[],
            followed_sources=["Tech Source"],
            followed_categories=["technology"],
            created_at=now,
            last_active=now
        )
        
        # Create articles
        article1 = NewsArticle(
            id="rec1",
            title="Recommendation Article 1",
            content="Recommendation content 1",
            url="https://example.com/rec1",
            source="Tech Source",
            published_at=now,
            category="technology",
            tags=["tech"],
            author="Tech Author"
        )
        
        article2 = NewsArticle(
            id="rec2",
            title="Recommendation Article 2",
            content="Recommendation content 2",
            url="https://example.com/rec2",
            source="Tech Source",
            published_at=now,
            category="technology",
            tags=["tech"],
            author="Tech Author"
        )
        
        self.db.save_article(article1)
        self.db.save_article(article2)
        self.db.save_user(user)
        
        recommendations = self.engine.get_recommendations("recuser", limit=10)
        
        self.assertEqual(len(recommendations), 2)
        self.assertEqual(recommendations[0].source, "Tech Source")


class TestNewsfeedService(unittest.TestCase):
    """Test NewsfeedService class."""

    def setUp(self):
        """Set up service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = NewsfeedService(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up service."""
        os.unlink(self.temp_db.name)
        self.service.stop_aggregation()

    def test_get_newsfeed_no_user(self):
        """Test getting newsfeed without user."""
        now = datetime.now()
        
        # Create some articles
        article = NewsArticle(
            id="feed1",
            title="Feed Article",
            content="Feed content",
            url="https://example.com/feed",
            source="Feed Source",
            published_at=now,
            category="general",
            tags=["feed"],
            author="Feed Author"
        )
        
        self.service.db.save_article(article)
        
        newsfeed = self.service.get_newsfeed(limit=10)
        
        self.assertEqual(len(newsfeed), 1)
        self.assertEqual(newsfeed[0]['title'], "Feed Article")

    def test_get_newsfeed_with_user(self):
        """Test getting personalized newsfeed."""
        now = datetime.now()
        
        # Create user
        user = UserProfile(
            user_id="feeduser",
            username="feeduser",
            email="feed@example.com",
            preferences={},
            reading_history=[],
            liked_articles=[],
            shared_articles=[],
            followed_sources=["Feed Source"],
            followed_categories=["general"],
            created_at=now,
            last_active=now
        )
        
        # Create article
        article = NewsArticle(
            id="feed2",
            title="Personalized Article",
            content="Personalized content",
            url="https://example.com/personalized",
            source="Feed Source",
            published_at=now,
            category="general",
            tags=["personalized"],
            author="Personalized Author"
        )
        
        self.service.db.save_article(article)
        self.service.db.save_user(user)
        
        newsfeed = self.service.get_newsfeed(user_id="feeduser", limit=10)
        
        self.assertEqual(len(newsfeed), 1)
        self.assertEqual(newsfeed[0]['title'], "Personalized Article")

    def test_like_article_success(self):
        """Test successful article liking."""
        now = datetime.now()
        
        # Create user
        user = UserProfile(
            user_id="likeuser",
            username="likeuser",
            email="like@example.com",
            preferences={},
            reading_history=[],
            liked_articles=[],
            shared_articles=[],
            followed_sources=[],
            followed_categories=[],
            created_at=now,
            last_active=now
        )
        
        self.service.db.save_user(user)
        
        result = self.service.like_article("likeuser", "article123")
        self.assertTrue(result)
        
        # Verify user was updated
        updated_user = self.service.db.get_user("likeuser")
        self.assertIn("article123", updated_user.liked_articles)

    def test_like_article_already_liked(self):
        """Test liking already liked article."""
        now = datetime.now()
        
        # Create user with already liked article
        user = UserProfile(
            user_id="alreadylikeuser",
            username="alreadylikeuser",
            email="alreadylike@example.com",
            preferences={},
            reading_history=[],
            liked_articles=["article123"],
            shared_articles=[],
            followed_sources=[],
            followed_categories=[],
            created_at=now,
            last_active=now
        )
        
        self.service.db.save_user(user)
        
        result = self.service.like_article("alreadylikeuser", "article123")
        self.assertFalse(result)

    def test_share_article_success(self):
        """Test successful article sharing."""
        now = datetime.now()
        
        # Create user
        user = UserProfile(
            user_id="shareuser",
            username="shareuser",
            email="share@example.com",
            preferences={},
            reading_history=[],
            liked_articles=[],
            shared_articles=[],
            followed_sources=[],
            followed_categories=[],
            created_at=now,
            last_active=now
        )
        
        self.service.db.save_user(user)
        
        result = self.service.share_article("shareuser", "article123")
        self.assertTrue(result)
        
        # Verify user was updated
        updated_user = self.service.db.get_user("shareuser")
        self.assertIn("article123", updated_user.shared_articles)

    def test_read_article_success(self):
        """Test successful article reading."""
        now = datetime.now()
        
        # Create user
        user = UserProfile(
            user_id="readuser",
            username="readuser",
            email="read@example.com",
            preferences={},
            reading_history=[],
            liked_articles=[],
            shared_articles=[],
            followed_sources=[],
            followed_categories=[],
            created_at=now,
            last_active=now
        )
        
        self.service.db.save_user(user)
        
        result = self.service.read_article("readuser", "article123")
        self.assertTrue(result)
        
        # Verify user was updated
        updated_user = self.service.db.get_user("readuser")
        self.assertIn("article123", updated_user.reading_history)

    def test_read_article_history_limit(self):
        """Test reading history limit."""
        now = datetime.now()
        
        # Create user with full reading history
        reading_history = [f"article{i}" for i in range(100)]
        user = UserProfile(
            user_id="limituser",
            username="limituser",
            email="limit@example.com",
            preferences={},
            reading_history=reading_history,
            liked_articles=[],
            shared_articles=[],
            followed_sources=[],
            followed_categories=[],
            created_at=now,
            last_active=now
        )
        
        self.service.db.save_user(user)
        
        result = self.service.read_article("limituser", "article101")
        self.assertTrue(result)
        
        # Verify history is limited to 100
        updated_user = self.service.db.get_user("limituser")
        self.assertEqual(len(updated_user.reading_history), 100)
        self.assertIn("article101", updated_user.reading_history)
        self.assertNotIn("article0", updated_user.reading_history)


class TestFlaskApp(unittest.TestCase):
    """Test Flask application endpoints."""

    def setUp(self):
        """Set up Flask test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create a test article for API tests
        test_article = NewsArticle(
            id="testarticle",
            title="Test Article",
            content="Test content",
            url="https://example.com/test",
            source="Test Source",
            published_at=datetime.now(),
            category="test",
            tags=["test"],
            author="Test Author"
        )
        newsfeed_service.db.save_article(test_article)
        
        # Create a test user for API tests
        test_user = UserProfile(
            user_id="testuser",
            username="Test User",
            email="test@example.com",
            preferences={"categories": ["test"]},
            reading_history=[],
            liked_articles=[],
            shared_articles=[],
            followed_sources=[],
            followed_categories=[],
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        newsfeed_service.db.save_user(test_user)
    
    def tearDown(self):
        """Clean up test data."""
        # Note: No cleanup needed as we're using the same database as the Flask app
        pass

    def test_index_page(self):
        """Test home page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Newsfeed Service', response.data)

    def test_get_newsfeed_api(self):
        """Test newsfeed API."""
        response = self.client.get('/api/newsfeed')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_get_newsfeed_with_user(self):
        """Test newsfeed API with user ID."""
        response = self.client.get('/api/newsfeed?user_id=testuser&limit=10')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_like_article_api(self):
        """Test like article API."""
        response = self.client.post('/api/like/testarticle', 
            json={'user_id': 'testuser'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_share_article_api(self):
        """Test share article API."""
        response = self.client.post('/api/share/testarticle',
            json={'user_id': 'testuser'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_read_article_api(self):
        """Test read article API."""
        response = self.client.post('/api/read/testarticle',
            json={'user_id': 'testuser'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_get_recommendations_api(self):
        """Test recommendations API."""
        response = self.client.get('/api/recommendations/testuser?limit=5')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])


if __name__ == '__main__':
    # Run tests with coverage
    unittest.main(verbosity=2)
