#!/usr/bin/env python3
"""
Typeahead Service

A comprehensive typeahead/autocomplete system with features like:
- Real-time search suggestions
- Fuzzy matching algorithms
- Trie data structure for efficient prefix matching
- Caching and performance optimization
- Multiple data sources support
- Ranking and scoring algorithms
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, render_template_string
import re
from collections import defaultdict, Counter
import heapq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Suggestion:
    """Suggestion model."""
    text: str
    score: float = 1.0
    category: str = "general"
    metadata: Dict[str, Any] = None
    frequency: int = 1
    last_used: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_used is None:
            self.last_used = datetime.now()

class TrieNode:
    """Trie node for efficient prefix matching."""
    
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.suggestions = []
        self.frequency = 0

class Trie:
    """Trie data structure for typeahead suggestions."""
    
    def __init__(self):
        self.root = TrieNode()
        self.total_words = 0
    
    def insert(self, word: str, suggestion: Suggestion):
        """Insert a word into the trie."""
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end = True
        node.suggestions.append(suggestion)
        node.frequency += 1
        self.total_words += 1
    
    def search(self, prefix: str, limit: int = 10) -> List[Suggestion]:
        """Search for suggestions with given prefix."""
        node = self.root
        
        # Navigate to the prefix node
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Collect all suggestions from this node and its children
        suggestions = []
        self._collect_suggestions(node, suggestions, limit)
        
        # Sort by score and frequency
        suggestions.sort(key=lambda x: (x.score, x.frequency), reverse=True)
        return suggestions[:limit]
    
    def _collect_suggestions(self, node: TrieNode, suggestions: List[Suggestion], limit: int):
        """Recursively collect suggestions from trie nodes."""
        if node.is_end:
            suggestions.extend(node.suggestions)
        
        for child in node.children.values():
            if len(suggestions) >= limit:
                break
            self._collect_suggestions(child, suggestions, limit)

class FuzzyMatcher:
    """Fuzzy matching for typeahead suggestions."""
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return FuzzyMatcher.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def fuzzy_score(query: str, text: str) -> float:
        """Calculate fuzzy matching score between query and text."""
        if not query or not text:
            return 0.0
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Exact match gets highest score
        if query_lower == text_lower:
            return 1.0
        
        # Prefix match gets high score
        if text_lower.startswith(query_lower):
            return 0.9
        
        # Substring match gets medium score
        if query_lower in text_lower:
            return 0.7
        
        # Fuzzy match based on Levenshtein distance
        distance = FuzzyMatcher.levenshtein_distance(query_lower, text_lower)
        max_len = max(len(query_lower), len(text_lower))
        similarity = 1.0 - (distance / max_len)
        
        return max(0.0, similarity * 0.5)  # Cap fuzzy matches at 0.5

class RankingEngine:
    """Ranking engine for typeahead suggestions."""
    
    def __init__(self):
        self.weights = {
            'exact_match': 1.0,
            'prefix_match': 0.9,
            'substring_match': 0.7,
            'fuzzy_match': 0.5,
            'frequency': 0.3,
            'recency': 0.2,
            'category_boost': 0.1
        }
    
    def calculate_score(self, query: str, suggestion: Suggestion) -> float:
        """Calculate ranking score for a suggestion."""
        text = suggestion.text.lower()
        query_lower = query.lower()
        
        # Base score from fuzzy matching
        base_score = FuzzyMatcher.fuzzy_score(query, suggestion.text)
        
        # Apply weights based on match type
        if query_lower == text:
            match_weight = self.weights['exact_match']
        elif text.startswith(query_lower):
            match_weight = self.weights['prefix_match']
        elif query_lower in text:
            match_weight = self.weights['substring_match']
        else:
            match_weight = self.weights['fuzzy_match']
        
        # Frequency weight
        frequency_weight = min(1.0, suggestion.frequency / 100.0) * self.weights['frequency']
        
        # Recency weight
        recency_weight = 0.0
        if suggestion.last_used:
            days_ago = (datetime.now() - suggestion.last_used).days
            recency_weight = max(0.0, 1.0 - (days_ago / 30.0)) * self.weights['recency']
        
        # Category boost
        category_boost = 0.0
        if suggestion.category in ['popular', 'trending']:
            category_boost = self.weights['category_boost']
        
        # Calculate final score
        final_score = (base_score * match_weight) + frequency_weight + recency_weight + category_boost
        
        return min(1.0, final_score)

class TypeaheadCache:
    """Cache for typeahead suggestions."""
    
    def __init__(self, max_size: int = 10000, ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_times = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[List[Suggestion]]:
        """Get suggestions from cache."""
        with self.lock:
            if key in self.cache:
                # Check TTL
                if time.time() - self.access_times[key] < self.ttl:
                    self.access_times[key] = time.time()
                    return self.cache[key]
                else:
                    # Expired, remove from cache
                    del self.cache[key]
                    del self.access_times[key]
            return None
    
    def set(self, key: str, suggestions: List[Suggestion]):
        """Set suggestions in cache."""
        with self.lock:
            # Remove oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = suggestions
            self.access_times[key] = time.time()
    
    def clear(self):
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()

class TypeaheadService:
    """Main typeahead service."""
    
    def __init__(self):
        self.trie = Trie()
        self.ranking_engine = RankingEngine()
        self.cache = TypeaheadCache()
        self.suggestions_count = 0
        self.popular_queries = Counter()
        
        # Load initial data
        self._load_initial_data()
    
    def _load_initial_data(self):
        """Load initial suggestion data."""
        # Common words and phrases
        common_suggestions = [
            "python programming",
            "javascript development",
            "machine learning",
            "web development",
            "data science",
            "artificial intelligence",
            "cloud computing",
            "cybersecurity",
            "mobile app development",
            "database design",
            "software engineering",
            "user interface design",
            "project management",
            "agile methodology",
            "version control",
            "testing strategies",
            "performance optimization",
            "code review",
            "documentation",
            "deployment"
        ]
        
        for i, text in enumerate(common_suggestions):
            suggestion = Suggestion(
                text=text,
                score=1.0 - (i * 0.01),  # Decreasing score
                category="general",
                frequency=100 - i,
                metadata={"source": "common"}
            )
            self.add_suggestion(suggestion)
    
    def add_suggestion(self, suggestion: Suggestion):
        """Add a suggestion to the typeahead system."""
        self.trie.insert(suggestion.text, suggestion)
        self.suggestions_count += 1
        
        # Update popular queries
        self.popular_queries[suggestion.text] += 1
    
    def search(self, query: str, limit: int = 10, category: str = None) -> List[Suggestion]:
        """Search for suggestions matching the query."""
        if not query or len(query) < 1:
            return []
        
        # Check cache first
        cache_key = f"{query}:{limit}:{category}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Get raw suggestions from trie
        raw_suggestions = self.trie.search(query, limit * 2)
        
        # Filter by category if specified
        if category:
            raw_suggestions = [s for s in raw_suggestions if s.category == category]
        
        # Calculate scores and rank
        scored_suggestions = []
        for suggestion in raw_suggestions:
            score = self.ranking_engine.calculate_score(query, suggestion)
            suggestion.score = score
            scored_suggestions.append(suggestion)
        
        # Sort by score
        scored_suggestions.sort(key=lambda x: x.score, reverse=True)
        
        # Take top results
        result = scored_suggestions[:limit]
        
        # Cache the result
        self.cache.set(cache_key, result)
        
        return result
    
    def get_popular_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular queries."""
        return self.popular_queries.most_common(limit)
    
    def update_suggestion_frequency(self, text: str):
        """Update frequency of a suggestion when used."""
        # This would require a more sophisticated data structure
        # For now, we'll just update the popular queries counter
        self.popular_queries[text] += 1
    
    def get_suggestions_by_category(self, category: str, limit: int = 10) -> List[Suggestion]:
        """Get suggestions by category."""
        # This would require indexing by category
        # For now, return empty list
        return []
    
    def clear_cache(self):
        """Clear the suggestion cache."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get typeahead service statistics."""
        return {
            'total_suggestions': self.suggestions_count,
            'cache_size': len(self.cache.cache),
            'popular_queries': dict(self.popular_queries.most_common(10)),
            'trie_words': self.trie.total_words
        }

# Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'typeahead-secret-key'

# Initialize service
typeahead_service = TypeaheadService()

@app.route('/')
def index():
    """Typeahead demo page."""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Typeahead Service Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .search-container { margin: 20px 0; }
            .search-input { 
                width: 300px; 
                padding: 10px; 
                font-size: 16px; 
                border: 2px solid #ddd; 
                border-radius: 5px; 
            }
            .suggestions { 
                border: 1px solid #ddd; 
                border-top: none; 
                max-height: 200px; 
                overflow-y: auto; 
                background: white; 
                position: absolute; 
                width: 300px; 
                z-index: 1000; 
            }
            .suggestion { 
                padding: 10px; 
                cursor: pointer; 
                border-bottom: 1px solid #eee; 
            }
            .suggestion:hover { background: #f5f5f5; }
            .suggestion.selected { background: #e3f2fd; }
            .suggestion-text { font-weight: bold; }
            .suggestion-category { color: #666; font-size: 0.9em; }
            .suggestion-score { color: #999; font-size: 0.8em; }
            .stats { background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Typeahead Service Demo</h1>
        
        <div class="search-container">
            <input type="text" id="searchInput" class="search-input" placeholder="Type to search..." autocomplete="off">
            <div id="suggestions" class="suggestions" style="display: none;"></div>
        </div>
        
        <div class="stats">
            <h3>Service Statistics</h3>
            <div id="stats">Loading...</div>
        </div>
        
        <script>
            let selectedIndex = -1;
            let suggestions = [];
            
            const searchInput = document.getElementById('searchInput');
            const suggestionsDiv = document.getElementById('suggestions');
            const statsDiv = document.getElementById('stats');
            
            // Load stats
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statsDiv.innerHTML = `
                            <strong>Total Suggestions:</strong> ${data.stats.total_suggestions}<br>
                            <strong>Cache Size:</strong> ${data.stats.cache_size}<br>
                            <strong>Trie Words:</strong> ${data.stats.trie_words}<br>
                            <strong>Popular Queries:</strong> ${Object.keys(data.stats.popular_queries).join(', ')}
                        `;
                    }
                });
            
            searchInput.addEventListener('input', function() {
                const query = this.value;
                if (query.length < 1) {
                    suggestionsDiv.style.display = 'none';
                    return;
                }
                
                fetch(`/api/suggestions?q=${encodeURIComponent(query)}&limit=10`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            suggestions = data.suggestions;
                            displaySuggestions(suggestions);
                        }
                    });
            });
            
            searchInput.addEventListener('keydown', function(e) {
                if (suggestions.length === 0) return;
                
                switch(e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1);
                        updateSelection();
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        selectedIndex = Math.max(selectedIndex - 1, -1);
                        updateSelection();
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (selectedIndex >= 0) {
                            selectSuggestion(suggestions[selectedIndex]);
                        }
                        break;
                    case 'Escape':
                        suggestionsDiv.style.display = 'none';
                        selectedIndex = -1;
                        break;
                }
            });
            
            function displaySuggestions(suggestions) {
                if (suggestions.length === 0) {
                    suggestionsDiv.style.display = 'none';
                    return;
                }
                
                suggestionsDiv.innerHTML = suggestions.map((suggestion, index) => `
                    <div class="suggestion" data-index="${index}">
                        <div class="suggestion-text">${suggestion.text}</div>
                        <div class="suggestion-category">${suggestion.category}</div>
                        <div class="suggestion-score">Score: ${suggestion.score.toFixed(3)}</div>
                    </div>
                `).join('');
                
                suggestionsDiv.style.display = 'block';
                selectedIndex = -1;
            }
            
            function updateSelection() {
                const suggestionElements = suggestionsDiv.querySelectorAll('.suggestion');
                suggestionElements.forEach((el, index) => {
                    el.classList.toggle('selected', index === selectedIndex);
                });
            }
            
            function selectSuggestion(suggestion) {
                searchInput.value = suggestion.text;
                suggestionsDiv.style.display = 'none';
                selectedIndex = -1;
                
                // Update frequency
                fetch('/api/update-frequency', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: suggestion.text})
                });
            }
            
            // Hide suggestions when clicking outside
            document.addEventListener('click', function(e) {
                if (!searchInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
                    suggestionsDiv.style.display = 'none';
                }
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/api/suggestions')
def get_suggestions():
    """Get typeahead suggestions API."""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    category = request.args.get('category')
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter is required'})
    
    suggestions = typeahead_service.search(query, limit, category)
    
    return jsonify({
        'success': True,
        'suggestions': [asdict(s) for s in suggestions],
        'query': query,
        'count': len(suggestions)
    })

@app.route('/api/suggestions', methods=['POST'])
def add_suggestion():
    """Add a new suggestion API."""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({'success': False, 'error': 'Text is required'})
    
    suggestion = Suggestion(
        text=data['text'],
        score=data.get('score', 1.0),
        category=data.get('category', 'general'),
        frequency=data.get('frequency', 1),
        metadata=data.get('metadata', {})
    )
    
    typeahead_service.add_suggestion(suggestion)
    
    return jsonify({
        'success': True,
        'message': 'Suggestion added successfully'
    })

@app.route('/api/popular')
def get_popular_queries():
    """Get popular queries API."""
    limit = request.args.get('limit', 10, type=int)
    popular = typeahead_service.get_popular_queries(limit)
    
    return jsonify({
        'success': True,
        'popular_queries': popular
    })

@app.route('/api/update-frequency', methods=['POST'])
def update_frequency():
    """Update suggestion frequency API."""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({'success': False, 'error': 'Text is required'})
    
    typeahead_service.update_suggestion_frequency(data['text'])
    
    return jsonify({
        'success': True,
        'message': 'Frequency updated successfully'
    })

@app.route('/api/stats')
def get_stats():
    """Get service statistics API."""
    stats = typeahead_service.get_stats()
    
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear suggestion cache API."""
    typeahead_service.clear_cache()
    
    return jsonify({
        'success': True,
        'message': 'Cache cleared successfully'
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'suggestions_count': typeahead_service.suggestions_count
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
