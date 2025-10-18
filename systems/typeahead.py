"""
Typeahead System Implementation
High-performance autocomplete and search suggestions
"""

import time
import threading
import json
import redis
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import heapq
import re
from collections import Counter

class SuggestionType(Enum):
    TEXT = "text"
    URL = "url"
    QUERY = "query"
    USER = "user"
    HASHTAG = "hashtag"
    MENTION = "mention"

class RankingAlgorithm(Enum):
    FREQUENCY = "frequency"
    RECENCY = "recency"
    RELEVANCE = "relevance"
    POPULARITY = "popularity"
    MIXED = "mixed"

@dataclass
class Suggestion:
    """Suggestion data structure"""
    suggestion_id: str
    text: str
    suggestion_type: SuggestionType
    frequency: int = 1
    last_used: datetime = field(default_factory=datetime.now)
    popularity_score: float = 0.0
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

@dataclass
class SearchQuery:
    """Search query data structure"""
    query_id: str
    query_text: str
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    result_count: int = 0
    clicked_suggestion: Optional[str] = None

@dataclass
class TrieNode:
    """Trie node data structure"""
    char: str
    children: Dict[str, 'TrieNode'] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    is_end: bool = False
    frequency: int = 0

class TypeaheadSystem:
    """High-performance typeahead and autocomplete system"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Core data structures
        self.suggestions = {}  # suggestion_id -> Suggestion
        self.search_queries = deque(maxlen=10000)  # Recent search queries
        self.user_queries = defaultdict(list)  # user_id -> List[query_id]
        
        # Trie for fast prefix matching
        self.trie_root = TrieNode("")
        
        # Indexes for different suggestion types
        self.suggestions_by_type = defaultdict(list)  # type -> List[suggestion_id]
        self.suggestions_by_tag = defaultdict(set)  # tag -> Set[suggestion_id]
        self.suggestions_by_user = defaultdict(set)  # user_id -> Set[suggestion_id]
        
        # Popular suggestions cache
        self.popular_suggestions = {}  # type -> List[suggestion_id]
        self.trending_suggestions = {}  # type -> List[suggestion_id]
        
        # Threading
        self.lock = threading.RLock()
        self.analytics_thread = threading.Thread(target=self._analytics_loop, daemon=True)
        self.analytics_thread.start()
        self.cache_update_thread = threading.Thread(target=self._cache_update_loop, daemon=True)
        self.cache_update_thread.start()
        
        # Configuration
        self.max_suggestions = 10
        self.max_query_length = 100
        self.min_query_length = 1
        self.analytics_interval = 300  # 5 minutes
        self.cache_update_interval = 600  # 10 minutes
        self.trending_window = 3600  # 1 hour
        self.frequency_decay = 0.95  # Decay factor for frequency over time
        
        # Ranking weights
        self.ranking_weights = {
            'frequency': 0.3,
            'recency': 0.2,
            'relevance': 0.3,
            'popularity': 0.2
        }
    
    def add_suggestion(self, text: str, suggestion_type: SuggestionType = SuggestionType.TEXT,
                      user_id: Optional[str] = None, tags: List[str] = None,
                      metadata: Dict[str, Any] = None) -> str:
        """Add a suggestion to the system"""
        with self.lock:
            # Normalize text
            normalized_text = self._normalize_text(text)
            if not normalized_text or len(normalized_text) < self.min_query_length:
                return None
            
            # Check if suggestion already exists
            existing_id = self._find_existing_suggestion(normalized_text, suggestion_type)
            if existing_id:
                # Update existing suggestion
                suggestion = self.suggestions[existing_id]
                suggestion.frequency += 1
                suggestion.last_used = datetime.now()
                
                # Update tags and metadata
                if tags:
                    suggestion.tags.extend(tags)
                    suggestion.tags = list(set(suggestion.tags))  # Remove duplicates
                
                if metadata:
                    suggestion.metadata.update(metadata)
                
                self._update_trie_suggestion(existing_id, suggestion)
                return existing_id
            
            # Create new suggestion
            suggestion_id = f"suggestion_{int(time.time() * 1000)}_{hash(normalized_text)}"
            suggestion = Suggestion(
                suggestion_id=suggestion_id,
                text=normalized_text,
                suggestion_type=suggestion_type,
                user_id=user_id,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self.suggestions[suggestion_id] = suggestion
            self.suggestions_by_type[suggestion_type].append(suggestion_id)
            
            # Add to tag indexes
            for tag in suggestion.tags:
                self.suggestions_by_tag[tag].add(suggestion_id)
            
            # Add to user index
            if user_id:
                self.suggestions_by_user[user_id].add(suggestion_id)
            
            # Add to trie
            self._add_to_trie(suggestion_id, suggestion)
            
            # Persist to Redis
            self._persist_suggestion(suggestion)
            
            return suggestion_id
    
    def get_suggestions(self, query: str, suggestion_type: Optional[SuggestionType] = None,
                       user_id: Optional[str] = None, limit: int = None,
                       ranking_algorithm: RankingAlgorithm = RankingAlgorithm.MIXED) -> List[Suggestion]:
        """Get suggestions for a query"""
        with self.lock:
            if not query or len(query) < self.min_query_length:
                return []
            
            normalized_query = self._normalize_text(query)
            limit = limit or self.max_suggestions
            
            # Get candidate suggestions from trie
            candidate_ids = self._get_trie_suggestions(normalized_query)
            
            # Filter by type if specified
            if suggestion_type:
                candidate_ids = [sid for sid in candidate_ids 
                               if self.suggestions[sid].suggestion_type == suggestion_type]
            
            # Filter by user if specified
            if user_id:
                user_suggestions = self.suggestions_by_user[user_id]
                candidate_ids = [sid for sid in candidate_ids if sid in user_suggestions]
            
            # Rank suggestions
            ranked_suggestions = self._rank_suggestions(candidate_ids, normalized_query, 
                                                      ranking_algorithm, user_id)
            
            # Return top suggestions
            return ranked_suggestions[:limit]
    
    def search(self, query: str, user_id: Optional[str] = None, 
              suggestion_type: Optional[SuggestionType] = None) -> List[Suggestion]:
        """Search for suggestions (alias for get_suggestions)"""
        return self.get_suggestions(query, suggestion_type, user_id)
    
    def record_query(self, query_text: str, user_id: Optional[str] = None,
                    clicked_suggestion: Optional[str] = None) -> str:
        """Record a search query"""
        with self.lock:
            query_id = f"query_{int(time.time() * 1000)}_{hash(query_text)}"
            
            query = SearchQuery(
                query_id=query_id,
                query_text=query_text,
                user_id=user_id,
                clicked_suggestion=clicked_suggestion
            )
            
            self.search_queries.append(query)
            
            if user_id:
                self.user_queries[user_id].append(query_id)
            
            # Update suggestion frequency if clicked
            if clicked_suggestion and clicked_suggestion in self.suggestions:
                suggestion = self.suggestions[clicked_suggestion]
                suggestion.frequency += 1
                suggestion.last_used = datetime.now()
                self._update_trie_suggestion(clicked_suggestion, suggestion)
            
            # Persist query
            self._persist_query(query)
            
            return query_id
    
    def get_popular_suggestions(self, suggestion_type: Optional[SuggestionType] = None,
                               limit: int = 20) -> List[Suggestion]:
        """Get popular suggestions"""
        with self.lock:
            if suggestion_type:
                suggestion_ids = self.popular_suggestions.get(suggestion_type, [])
            else:
                # Get popular suggestions across all types
                all_popular = []
                for type_suggestions in self.popular_suggestions.values():
                    all_popular.extend(type_suggestions)
                suggestion_ids = all_popular
            
            suggestions = [self.suggestions[sid] for sid in suggestion_ids if sid in self.suggestions]
            return suggestions[:limit]
    
    def get_trending_suggestions(self, suggestion_type: Optional[SuggestionType] = None,
                                limit: int = 20) -> List[Suggestion]:
        """Get trending suggestions"""
        with self.lock:
            if suggestion_type:
                suggestion_ids = self.trending_suggestions.get(suggestion_type, [])
            else:
                # Get trending suggestions across all types
                all_trending = []
                for type_suggestions in self.trending_suggestions.values():
                    all_trending.extend(type_suggestions)
                suggestion_ids = all_trending
            
            suggestions = [self.suggestions[sid] for sid in suggestion_ids if sid in self.suggestions]
            return suggestions[:limit]
    
    def get_user_suggestions(self, user_id: str, limit: int = 20) -> List[Suggestion]:
        """Get suggestions for a specific user"""
        with self.lock:
            if user_id not in self.user_queries:
                return []
            
            # Get user's recent queries
            recent_queries = self.user_queries[user_id][-100:]  # Last 100 queries
            
            # Extract suggestions from queries
            suggestion_ids = set()
            for query_id in recent_queries:
                # Find queries that match this query_id
                for query in self.search_queries:
                    if query.query_id == query_id and query.clicked_suggestion:
                        suggestion_ids.add(query.clicked_suggestion)
            
            suggestions = [self.suggestions[sid] for sid in suggestion_ids if sid in self.suggestions]
            
            # Sort by frequency and recency
            suggestions.sort(key=lambda x: (x.frequency, x.last_used), reverse=True)
            
            return suggestions[:limit]
    
    def get_similar_suggestions(self, suggestion_id: str, limit: int = 10) -> List[Suggestion]:
        """Get suggestions similar to a given suggestion"""
        with self.lock:
            if suggestion_id not in self.suggestions:
                return []
            
            target_suggestion = self.suggestions[suggestion_id]
            similar_suggestions = []
            
            # Find suggestions with similar tags
            for tag in target_suggestion.tags:
                for similar_id in self.suggestions_by_tag[tag]:
                    if similar_id != suggestion_id:
                        similar_suggestions.append(self.suggestions[similar_id])
            
            # Remove duplicates and sort by similarity score
            unique_suggestions = list(set(similar_suggestions))
            unique_suggestions.sort(key=lambda x: self._calculate_similarity_score(target_suggestion, x), reverse=True)
            
            return unique_suggestions[:limit]
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for indexing"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove special characters (keep alphanumeric and spaces)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized
    
    def _find_existing_suggestion(self, text: str, suggestion_type: SuggestionType) -> Optional[str]:
        """Find existing suggestion by text and type"""
        for suggestion in self.suggestions.values():
            if (suggestion.text == text and 
                suggestion.suggestion_type == suggestion_type):
                return suggestion.suggestion_id
        return None
    
    def _add_to_trie(self, suggestion_id: str, suggestion: Suggestion):
        """Add suggestion to trie"""
        current = self.trie_root
        
        for char in suggestion.text:
            if char not in current.children:
                current.children[char] = TrieNode(char)
            current = current.children[char]
        
        current.is_end = True
        current.suggestions.append(suggestion_id)
        current.frequency += 1
    
    def _update_trie_suggestion(self, suggestion_id: str, suggestion: Suggestion):
        """Update suggestion in trie"""
        # Remove old suggestion
        self._remove_from_trie(suggestion_id)
        
        # Add updated suggestion
        self._add_to_trie(suggestion_id, suggestion)
    
    def _remove_from_trie(self, suggestion_id: str):
        """Remove suggestion from trie"""
        # This is a simplified implementation
        # In production, you'd need to properly clean up the trie
        pass
    
    def _get_trie_suggestions(self, query: str) -> List[str]:
        """Get suggestions from trie for a query"""
        current = self.trie_root
        
        # Traverse to the query prefix
        for char in query:
            if char not in current.children:
                return []
            current = current.children[char]
        
        # Collect all suggestions from this node and its children
        suggestions = []
        self._collect_suggestions(current, suggestions)
        
        return suggestions
    
    def _collect_suggestions(self, node: TrieNode, suggestions: List[str]):
        """Collect suggestions from a trie node and its children"""
        if node.is_end:
            suggestions.extend(node.suggestions)
        
        for child in node.children.values():
            self._collect_suggestions(child, suggestions)
    
    def _rank_suggestions(self, candidate_ids: List[str], query: str,
                         algorithm: RankingAlgorithm, user_id: Optional[str] = None) -> List[Suggestion]:
        """Rank suggestions based on the specified algorithm"""
        if not candidate_ids:
            return []
        
        suggestions = [self.suggestions[sid] for sid in candidate_ids if sid in self.suggestions]
        
        if algorithm == RankingAlgorithm.FREQUENCY:
            suggestions.sort(key=lambda x: x.frequency, reverse=True)
        elif algorithm == RankingAlgorithm.RECENCY:
            suggestions.sort(key=lambda x: x.last_used, reverse=True)
        elif algorithm == RankingAlgorithm.RELEVANCE:
            suggestions.sort(key=lambda x: self._calculate_relevance_score(x, query), reverse=True)
        elif algorithm == RankingAlgorithm.POPULARITY:
            suggestions.sort(key=lambda x: x.popularity_score, reverse=True)
        elif algorithm == RankingAlgorithm.MIXED:
            suggestions.sort(key=lambda x: self._calculate_mixed_score(x, query, user_id), reverse=True)
        
        return suggestions
    
    def _calculate_relevance_score(self, suggestion: Suggestion, query: str) -> float:
        """Calculate relevance score for a suggestion"""
        score = 0.0
        
        # Exact match bonus
        if suggestion.text == query:
            score += 100.0
        elif suggestion.text.startswith(query):
            score += 50.0
        elif query in suggestion.text:
            score += 25.0
        
        # Length penalty (shorter suggestions are better for exact matches)
        if suggestion.text.startswith(query):
            score += (len(query) / len(suggestion.text)) * 10.0
        
        return score
    
    def _calculate_mixed_score(self, suggestion: Suggestion, query: str, user_id: Optional[str] = None) -> float:
        """Calculate mixed score for ranking"""
        frequency_score = min(suggestion.frequency / 100.0, 1.0)  # Normalize to 0-1
        recency_score = self._calculate_recency_score(suggestion)
        relevance_score = min(self._calculate_relevance_score(suggestion, query) / 100.0, 1.0)
        popularity_score = min(suggestion.popularity_score, 1.0)
        
        # User personalization
        user_score = 0.0
        if user_id and suggestion.suggestion_id in self.suggestions_by_user.get(user_id, set()):
            user_score = 0.1
        
        # Calculate weighted score
        mixed_score = (
            frequency_score * self.ranking_weights['frequency'] +
            recency_score * self.ranking_weights['recency'] +
            relevance_score * self.ranking_weights['relevance'] +
            popularity_score * self.ranking_weights['popularity'] +
            user_score
        )
        
        return mixed_score
    
    def _calculate_recency_score(self, suggestion: Suggestion) -> float:
        """Calculate recency score for a suggestion"""
        age_hours = (datetime.now() - suggestion.last_used).total_seconds() / 3600
        return max(0, 1 - age_hours / 24)  # Decay over 24 hours
    
    def _calculate_similarity_score(self, suggestion1: Suggestion, suggestion2: Suggestion) -> float:
        """Calculate similarity score between two suggestions"""
        score = 0.0
        
        # Text similarity
        if suggestion1.text == suggestion2.text:
            score += 100.0
        elif suggestion1.text in suggestion2.text or suggestion2.text in suggestion1.text:
            score += 50.0
        
        # Tag similarity
        common_tags = set(suggestion1.tags) & set(suggestion2.tags)
        if common_tags:
            score += len(common_tags) * 10.0
        
        # Type similarity
        if suggestion1.suggestion_type == suggestion2.suggestion_type:
            score += 20.0
        
        return score
    
    def _analytics_loop(self):
        """Analytics processing loop"""
        while True:
            try:
                time.sleep(self.analytics_interval)
                
                with self.lock:
                    # Update suggestion frequencies with decay
                    self._update_frequency_decay()
                    
                    # Update popularity scores
                    self._update_popularity_scores()
                    
                    # Update trending suggestions
                    self._update_trending_suggestions()
                
            except Exception as e:
                print(f"Error in analytics loop: {e}")
    
    def _cache_update_loop(self):
        """Cache update loop"""
        while True:
            try:
                time.sleep(self.cache_update_interval)
                
                with self.lock:
                    # Update popular suggestions cache
                    self._update_popular_suggestions_cache()
                    
                    # Update trending suggestions cache
                    self._update_trending_suggestions_cache()
                
            except Exception as e:
                print(f"Error in cache update loop: {e}")
    
    def _update_frequency_decay(self):
        """Update suggestion frequencies with decay"""
        for suggestion in self.suggestions.values():
            # Apply frequency decay
            suggestion.frequency = max(1, int(suggestion.frequency * self.frequency_decay))
    
    def _update_popularity_scores(self):
        """Update popularity scores for suggestions"""
        for suggestion in self.suggestions.values():
            # Calculate popularity based on frequency and recency
            frequency_score = min(suggestion.frequency / 100.0, 1.0)
            recency_score = self._calculate_recency_score(suggestion)
            
            suggestion.popularity_score = (frequency_score + recency_score) / 2.0
    
    def _update_trending_suggestions(self):
        """Update trending suggestions"""
        # Get suggestions used in the last hour
        cutoff_time = datetime.now() - timedelta(seconds=self.trending_window)
        
        trending_by_type = defaultdict(list)
        
        for query in self.search_queries:
            if query.timestamp > cutoff_time and query.clicked_suggestion:
                suggestion = self.suggestions.get(query.clicked_suggestion)
                if suggestion:
                    trending_by_type[suggestion.suggestion_type].append(suggestion.suggestion_id)
        
        # Sort by frequency and update cache
        for suggestion_type, suggestion_ids in trending_by_type.items():
            # Count frequencies
            frequency_count = Counter(suggestion_ids)
            
            # Sort by frequency
            sorted_suggestions = sorted(frequency_count.items(), key=lambda x: x[1], reverse=True)
            
            # Update trending cache
            self.trending_suggestions[suggestion_type] = [sid for sid, _ in sorted_suggestions[:50]]
    
    def _update_popular_suggestions_cache(self):
        """Update popular suggestions cache"""
        for suggestion_type in SuggestionType:
            type_suggestions = [
                (sid, suggestion) for sid, suggestion in self.suggestions.items()
                if suggestion.suggestion_type == suggestion_type
            ]
            
            # Sort by popularity score
            type_suggestions.sort(key=lambda x: x[1].popularity_score, reverse=True)
            
            # Update cache
            self.popular_suggestions[suggestion_type] = [sid for sid, _ in type_suggestions[:100]]
    
    def _update_trending_suggestions_cache(self):
        """Update trending suggestions cache"""
        # This is called by the analytics loop
        pass
    
    def _persist_suggestion(self, suggestion: Suggestion):
        """Persist suggestion to Redis"""
        suggestion_data = {
            "suggestion_id": suggestion.suggestion_id,
            "text": suggestion.text,
            "suggestion_type": suggestion.suggestion_type.value,
            "frequency": str(suggestion.frequency),
            "last_used": suggestion.last_used.isoformat(),
            "popularity_score": str(suggestion.popularity_score),
            "relevance_score": str(suggestion.relevance_score),
            "metadata": json.dumps(suggestion.metadata),
            "tags": json.dumps(suggestion.tags)
        }
        
        self.redis_client.hset(f"suggestion:{suggestion.suggestion_id}", mapping=suggestion_data)
    
    def _persist_query(self, query: SearchQuery):
        """Persist query to Redis"""
        query_data = {
            "query_id": query.query_id,
            "query_text": query.query_text,
            "user_id": query.user_id or "",
            "timestamp": query.timestamp.isoformat(),
            "result_count": str(query.result_count),
            "clicked_suggestion": query.clicked_suggestion or ""
        }
        
        self.redis_client.hset(f"query:{query.query_id}", mapping=query_data)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        with self.lock:
            return {
                "total_suggestions": len(self.suggestions),
                "total_queries": len(self.search_queries),
                "suggestions_by_type": {t.value: len(sids) for t, sids in self.suggestions_by_type.items()},
                "total_tags": len(self.suggestions_by_tag),
                "total_users": len(self.user_queries),
                "popular_suggestions_cached": sum(len(sids) for sids in self.popular_suggestions.values()),
                "trending_suggestions_cached": sum(len(sids) for sids in self.trending_suggestions.values()),
                "trie_nodes": self._count_trie_nodes(self.trie_root)
            }
    
    def _count_trie_nodes(self, node: TrieNode) -> int:
        """Count total nodes in trie"""
        count = 1
        for child in node.children.values():
            count += self._count_trie_nodes(child)
        return count


# Example usage and testing
if __name__ == "__main__":
    # Initialize typeahead system
    typeahead = TypeaheadSystem()
    
    # Add suggestions
    typeahead.add_suggestion("python programming", SuggestionType.TEXT, tags=["programming", "python"])
    typeahead.add_suggestion("python tutorial", SuggestionType.TEXT, tags=["programming", "python", "tutorial"])
    typeahead.add_suggestion("javascript", SuggestionType.TEXT, tags=["programming", "javascript"])
    typeahead.add_suggestion("machine learning", SuggestionType.TEXT, tags=["ai", "ml"])
    typeahead.add_suggestion("data science", SuggestionType.TEXT, tags=["data", "analytics"])
    
    # Add URLs
    typeahead.add_suggestion("https://python.org", SuggestionType.URL, tags=["programming", "python"])
    typeahead.add_suggestion("https://github.com", SuggestionType.URL, tags=["development", "git"])
    
    # Add users
    typeahead.add_suggestion("@john_doe", SuggestionType.USER, tags=["user"])
    typeahead.add_suggestion("@jane_smith", SuggestionType.USER, tags=["user"])
    
    # Record queries
    typeahead.record_query("python", user_id="user1")
    typeahead.record_query("javascript", user_id="user1")
    typeahead.record_query("machine learning", user_id="user2")
    
    # Get suggestions
    suggestions = typeahead.get_suggestions("python", limit=5)
    print(f"Suggestions for 'python': {[s.text for s in suggestions]}")
    
    # Get popular suggestions
    popular = typeahead.get_popular_suggestions(limit=5)
    print(f"Popular suggestions: {[s.text for s in popular]}")
    
    # Get user suggestions
    user_suggestions = typeahead.get_user_suggestions("user1", limit=5)
    print(f"User suggestions: {[s.text for s in user_suggestions]}")
    
    # Get system stats
    stats = typeahead.get_system_stats()
    print(f"System stats: {stats}")
