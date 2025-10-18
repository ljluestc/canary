"""
Newsfeed System Implementation
High-performance social media newsfeed with real-time updates
"""

import time
import threading
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import heapq
import json
import redis
from enum import Enum
import statistics

class PostType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    POLL = "poll"

class FeedAlgorithm(Enum):
    CHRONOLOGICAL = "chronological"
    RELEVANCE = "relevance"
    ENGAGEMENT = "engagement"
    MIXED = "mixed"

@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    email: str
    created_at: datetime
    followers: Set[str] = field(default_factory=set)
    following: Set[str] = field(default_factory=set)
    interests: List[str] = field(default_factory=list)
    is_active: bool = True
    last_activity: Optional[datetime] = None

@dataclass
class Post:
    """Post data structure"""
    post_id: str
    user_id: str
    content: str
    post_type: PostType
    created_at: datetime
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    tags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    is_public: bool = True
    engagement_score: float = 0.0

@dataclass
class Comment:
    """Comment data structure"""
    comment_id: str
    post_id: str
    user_id: str
    content: str
    created_at: datetime
    likes: int = 0
    parent_comment_id: Optional[str] = None

@dataclass
class FeedItem:
    """Feed item for display"""
    post: Post
    score: float
    timestamp: datetime
    user: Optional[User] = None

class NewsfeedSystem:
    """High-performance newsfeed system"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Core data structures
        self.users = {}  # user_id -> User
        self.posts = {}  # post_id -> Post
        self.comments = {}  # comment_id -> Comment
        self.user_feeds = defaultdict(list)  # user_id -> List[FeedItem]
        self.user_timeline = defaultdict(deque)  # user_id -> Deque[Post]
        
        # Indexes for fast lookup
        self.posts_by_user = defaultdict(list)  # user_id -> List[post_id]
        self.comments_by_post = defaultdict(list)  # post_id -> List[comment_id]
        self.posts_by_tag = defaultdict(set)  # tag -> Set[post_id]
        self.trending_posts = []  # Heap of trending posts
        
        # Threading
        self.lock = threading.RLock()
        self.feed_update_thread = threading.Thread(target=self._update_feeds_continuously, daemon=True)
        self.feed_update_thread.start()
        
        # Configuration
        self.feed_size = 100
        self.trending_window = 3600  # 1 hour
        self.engagement_decay = 0.95
        self.update_interval = 60  # 1 minute
    
    def create_user(self, user_id: str, username: str, email: str, interests: List[str] = None) -> User:
        """Create a new user"""
        with self.lock:
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                created_at=datetime.now(),
                interests=interests or []
            )
            self.users[user_id] = user
            self._persist_user(user)
            return user
    
    def follow_user(self, follower_id: str, followee_id: str) -> bool:
        """Follow a user"""
        with self.lock:
            if follower_id not in self.users or followee_id not in self.users:
                return False
            
            self.users[follower_id].following.add(followee_id)
            self.users[followee_id].followers.add(follower_id)
            
            # Update follower's feed
            self._update_user_feed(follower_id)
            
            self._persist_user(self.users[follower_id])
            self._persist_user(self.users[followee_id])
            return True
    
    def unfollow_user(self, follower_id: str, followee_id: str) -> bool:
        """Unfollow a user"""
        with self.lock:
            if follower_id not in self.users or followee_id not in self.users:
                return False
            
            self.users[follower_id].following.discard(followee_id)
            self.users[followee_id].followers.discard(follower_id)
            
            # Update follower's feed
            self._update_user_feed(follower_id)
            
            self._persist_user(self.users[follower_id])
            self._persist_user(self.users[followee_id])
            return True
    
    def create_post(self, user_id: str, content: str, post_type: PostType = PostType.TEXT,
                   tags: List[str] = None, media_urls: List[str] = None, is_public: bool = True) -> Post:
        """Create a new post"""
        with self.lock:
            post = Post(
                post_id=f"post_{int(time.time() * 1000)}_{user_id}",
                user_id=user_id,
                content=content,
                post_type=post_type,
                created_at=datetime.now(),
                tags=tags or [],
                media_urls=media_urls or [],
                is_public=is_public
            )
            
            self.posts[post.post_id] = post
            self.posts_by_user[user_id].append(post.post_id)
            
            # Add to tag indexes
            for tag in post.tags:
                self.posts_by_tag[tag].add(post.post_id)
            
            # Update followers' feeds
            self._update_followers_feeds(user_id, post)
            
            # Update trending posts
            self._update_trending_posts(post)
            
            self._persist_post(post)
            return post
    
    def like_post(self, user_id: str, post_id: str) -> bool:
        """Like a post"""
        with self.lock:
            if post_id not in self.posts:
                return False
            
            post = self.posts[post_id]
            post.likes += 1
            post.engagement_score = self._calculate_engagement_score(post)
            
            # Update trending posts
            self._update_trending_posts(post)
            
            self._persist_post(post)
            return True
    
    def comment_on_post(self, user_id: str, post_id: str, content: str, parent_comment_id: str = None) -> Comment:
        """Add a comment to a post"""
        with self.lock:
            comment = Comment(
                comment_id=f"comment_{int(time.time() * 1000)}_{user_id}",
                post_id=post_id,
                user_id=user_id,
                content=content,
                created_at=datetime.now(),
                parent_comment_id=parent_comment_id
            )
            
            self.comments[comment.comment_id] = comment
            self.comments_by_post[post_id].append(comment.comment_id)
            
            # Update post comment count
            if post_id in self.posts:
                self.posts[post_id].comments += 1
                self.posts[post_id].engagement_score = self._calculate_engagement_score(self.posts[post_id])
                self._persist_post(self.posts[post_id])
            
            self._persist_comment(comment)
            return comment
    
    def share_post(self, user_id: str, post_id: str) -> bool:
        """Share a post"""
        with self.lock:
            if post_id not in self.posts:
                return False
            
            post = self.posts[post_id]
            post.shares += 1
            post.engagement_score = self._calculate_engagement_score(post)
            
            # Update trending posts
            self._update_trending_posts(post)
            
            self._persist_post(post)
            return True
    
    def get_user_feed(self, user_id: str, algorithm: FeedAlgorithm = FeedAlgorithm.RELEVANCE, 
                     limit: int = 50) -> List[FeedItem]:
        """Get user's personalized feed"""
        with self.lock:
            if user_id not in self.users:
                return []
            
            feed_items = self.user_feeds.get(user_id, [])
            
            if algorithm == FeedAlgorithm.CHRONOLOGICAL:
                # Sort by timestamp (newest first)
                feed_items.sort(key=lambda x: x.timestamp, reverse=True)
            elif algorithm == FeedAlgorithm.RELEVANCE:
                # Sort by relevance score
                feed_items.sort(key=lambda x: x.score, reverse=True)
            elif algorithm == FeedAlgorithm.ENGAGEMENT:
                # Sort by engagement score
                feed_items.sort(key=lambda x: x.post.engagement_score, reverse=True)
            elif algorithm == FeedAlgorithm.MIXED:
                # Mix of relevance and recency
                feed_items.sort(key=lambda x: (x.score * 0.7 + x.timestamp.timestamp() * 0.3), reverse=True)
            
            return feed_items[:limit]
    
    def get_trending_posts(self, limit: int = 20) -> List[Post]:
        """Get trending posts"""
        with self.lock:
            # Filter posts from the last hour
            cutoff_time = datetime.now() - timedelta(seconds=self.trending_window)
            trending = [post for post in self.trending_posts 
                       if post.created_at > cutoff_time]
            
            # Sort by engagement score
            trending.sort(key=lambda x: x.engagement_score, reverse=True)
            return trending[:limit]
    
    def search_posts(self, query: str, user_id: str = None, limit: int = 50) -> List[Post]:
        """Search posts by content or tags"""
        with self.lock:
            results = []
            query_lower = query.lower()
            
            for post in self.posts.values():
                # Check if user can see the post
                if not self._can_user_see_post(user_id, post):
                    continue
                
                # Search in content
                if query_lower in post.content.lower():
                    results.append(post)
                    continue
                
                # Search in tags
                if any(query_lower in tag.lower() for tag in post.tags):
                    results.append(post)
                    continue
            
            # Sort by recency
            results.sort(key=lambda x: x.created_at, reverse=True)
            return results[:limit]
    
    def get_user_posts(self, user_id: str, limit: int = 50) -> List[Post]:
        """Get posts by a specific user"""
        with self.lock:
            post_ids = self.posts_by_user.get(user_id, [])
            posts = [self.posts[post_id] for post_id in post_ids if post_id in self.posts]
            posts.sort(key=lambda x: x.created_at, reverse=True)
            return posts[:limit]
    
    def get_post_comments(self, post_id: str, limit: int = 50) -> List[Comment]:
        """Get comments for a post"""
        with self.lock:
            comment_ids = self.comments_by_post.get(post_id, [])
            comments = [self.comments[comment_id] for comment_id in comment_ids if comment_id in self.comments]
            comments.sort(key=lambda x: x.created_at, reverse=True)
            return comments[:limit]
    
    def _can_user_see_post(self, user_id: str, post: Post) -> bool:
        """Check if user can see a post"""
        if not post.is_public:
            return False
        
        if user_id is None:
            return post.is_public
        
        if user_id == post.user_id:
            return True
        
        # Check if user follows the post author
        if user_id in self.users and post.user_id in self.users[user_id].following:
            return True
        
        return post.is_public
    
    def _calculate_engagement_score(self, post: Post) -> float:
        """Calculate engagement score for a post"""
        # Weighted engagement score
        score = (post.likes * 1.0 + 
                post.comments * 2.0 + 
                post.shares * 3.0 + 
                post.views * 0.1)
        
        # Time decay
        age_hours = (datetime.now() - post.created_at).total_seconds() / 3600
        decay_factor = self.engagement_decay ** age_hours
        
        return score * decay_factor
    
    def _update_user_feed(self, user_id: str):
        """Update a user's feed"""
        if user_id not in self.users:
            return
        
        user = self.users[user_id]
        feed_items = []
        
        # Get posts from followed users
        for followee_id in user.following:
            if followee_id in self.posts_by_user:
                for post_id in self.posts_by_user[followee_id]:
                    if post_id in self.posts:
                        post = self.posts[post_id]
                        if self._can_user_see_post(user_id, post):
                            score = self._calculate_relevance_score(user, post)
                            feed_items.append(FeedItem(
                                post=post,
                                score=score,
                                timestamp=post.created_at,
                                user=self.users.get(followee_id)
                            ))
        
        # Sort by score and timestamp
        feed_items.sort(key=lambda x: (x.score, x.timestamp), reverse=True)
        self.user_feeds[user_id] = feed_items[:self.feed_size]
    
    def _update_followers_feeds(self, user_id: str, post: Post):
        """Update feeds of all followers"""
        if user_id not in self.users:
            return
        
        user = self.users[user_id]
        
        for follower_id in user.followers:
            if follower_id in self.users:
                self._update_user_feed(follower_id)
    
    def _calculate_relevance_score(self, user: User, post: Post) -> float:
        """Calculate relevance score for a post"""
        score = 0.0
        
        # Base score from engagement
        score += post.engagement_score * 0.4
        
        # Interest matching
        if user.interests:
            interest_matches = sum(1 for tag in post.tags if tag in user.interests)
            score += interest_matches * 0.3
        
        # Recency
        age_hours = (datetime.now() - post.created_at).total_seconds() / 3600
        recency_score = max(0, 1 - age_hours / 24)  # Decay over 24 hours
        score += recency_score * 0.3
        
        return score
    
    def _update_trending_posts(self, post: Post):
        """Update trending posts list"""
        # Add to trending posts
        self.trending_posts.append(post)
        
        # Keep only recent posts
        cutoff_time = datetime.now() - timedelta(seconds=self.trending_window)
        self.trending_posts = [p for p in self.trending_posts if p.created_at > cutoff_time]
        
        # Sort by engagement score
        self.trending_posts.sort(key=lambda x: x.engagement_score, reverse=True)
        
        # Keep only top posts
        self.trending_posts = self.trending_posts[:100]
    
    def _update_feeds_continuously(self):
        """Continuously update feeds in background"""
        while True:
            try:
                time.sleep(self.update_interval)
                
                with self.lock:
                    # Update all user feeds
                    for user_id in self.users:
                        self._update_user_feed(user_id)
                    
                    # Clean up old data
                    self._cleanup_old_data()
                
            except Exception as e:
                print(f"Error in feed update thread: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data to prevent memory issues"""
        # Remove old posts (older than 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        old_posts = [post_id for post_id, post in self.posts.items() 
                    if post.created_at < cutoff_date]
        
        for post_id in old_posts:
            self._delete_post(post_id)
    
    def _delete_post(self, post_id: str):
        """Delete a post and its associated data"""
        if post_id in self.posts:
            post = self.posts[post_id]
            
            # Remove from indexes
            if post.user_id in self.posts_by_user:
                self.posts_by_user[post.user_id].remove(post_id)
            
            for tag in post.tags:
                self.posts_by_tag[tag].discard(post_id)
            
            # Remove from trending
            self.trending_posts = [p for p in self.trending_posts if p.post_id != post_id]
            
            # Delete post
            del self.posts[post_id]
    
    def _persist_user(self, user: User):
        """Persist user to Redis"""
        user_data = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'followers': json.dumps(list(user.followers)),
            'following': json.dumps(list(user.following)),
            'interests': json.dumps(user.interests),
            'is_active': str(user.is_active),
            'last_activity': user.last_activity.isoformat() if user.last_activity else None
        }
        self.redis_client.hset(f"user:{user.user_id}", mapping=user_data)
    
    def _persist_post(self, post: Post):
        """Persist post to Redis"""
        post_data = {
            'post_id': post.post_id,
            'user_id': post.user_id,
            'content': post.content,
            'post_type': post.post_type.value,
            'created_at': post.created_at.isoformat(),
            'likes': str(post.likes),
            'comments': str(post.comments),
            'shares': str(post.shares),
            'views': str(post.views),
            'tags': json.dumps(post.tags),
            'media_urls': json.dumps(post.media_urls),
            'is_public': str(post.is_public),
            'engagement_score': str(post.engagement_score)
        }
        self.redis_client.hset(f"post:{post.post_id}", mapping=post_data)
    
    def _persist_comment(self, comment: Comment):
        """Persist comment to Redis"""
        comment_data = {
            'comment_id': comment.comment_id,
            'post_id': comment.post_id,
            'user_id': comment.user_id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'likes': str(comment.likes),
            'parent_comment_id': comment.parent_comment_id or ''
        }
        self.redis_client.hset(f"comment:{comment.comment_id}", mapping=comment_data)
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        with self.lock:
            return {
                'total_users': len(self.users),
                'total_posts': len(self.posts),
                'total_comments': len(self.comments),
                'total_follows': sum(len(user.following) for user in self.users.values()),
                'trending_posts_count': len(self.trending_posts),
                'average_posts_per_user': len(self.posts) / max(len(self.users), 1),
                'average_engagement': statistics.mean([post.engagement_score for post in self.posts.values()]) if self.posts else 0
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize system
    newsfeed = NewsfeedSystem()
    
    # Create users
    user1 = newsfeed.create_user("user1", "alice", "alice@example.com", ["tech", "programming"])
    user2 = newsfeed.create_user("user2", "bob", "bob@example.com", ["sports", "fitness"])
    user3 = newsfeed.create_user("user3", "charlie", "charlie@example.com", ["tech", "gaming"])
    
    # Follow users
    newsfeed.follow_user("user1", "user2")
    newsfeed.follow_user("user1", "user3")
    newsfeed.follow_user("user2", "user1")
    
    # Create posts
    post1 = newsfeed.create_post("user1", "Just learned Python!", PostType.TEXT, ["programming", "tech"])
    post2 = newsfeed.create_post("user2", "Great workout today!", PostType.TEXT, ["fitness", "sports"])
    post3 = newsfeed.create_post("user3", "New game release!", PostType.TEXT, ["gaming", "tech"])
    
    # Like and comment
    newsfeed.like_post("user2", post1.post_id)
    newsfeed.comment_on_post("user2", post1.post_id, "Great job!")
    newsfeed.share_post("user3", post1.post_id)
    
    # Get feeds
    feed1 = newsfeed.get_user_feed("user1")
    feed2 = newsfeed.get_user_feed("user2")
    
    print(f"User1 feed: {len(feed1)} items")
    print(f"User2 feed: {len(feed2)} items")
    
    # Get trending posts
    trending = newsfeed.get_trending_posts()
    print(f"Trending posts: {len(trending)}")
    
    # Get system stats
    stats = newsfeed.get_system_stats()
    print(f"System stats: {stats}")
