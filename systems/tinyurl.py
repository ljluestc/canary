"""
TinyURL System Implementation
High-performance URL shortening service with analytics
"""

import hashlib
import base64
import time
import threading
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import redis
from collections import defaultdict, deque
import statistics

@dataclass
class URLData:
    """URL data structure"""
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime]
    click_count: int = 0
    last_accessed: Optional[datetime] = None
    user_id: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class Analytics:
    """Analytics data structure"""
    total_clicks: int
    unique_clicks: int
    click_timestamps: List[datetime]
    referrers: Dict[str, int]
    countries: Dict[str, int]
    devices: Dict[str, int]
    browsers: Dict[str, int]
    
    def __post_init__(self):
        if self.click_timestamps is None:
            self.click_timestamps = []
        if self.referrers is None:
            self.referrers = {}
        if self.countries is None:
            self.countries = {}
        if self.devices is None:
            self.devices = {}
        if self.browsers is None:
            self.browsers = {}

class TinyURLSystem:
    """High-performance TinyURL system"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        self.url_storage = {}  # In-memory storage for fast access
        self.analytics_storage = {}  # Analytics storage
        self.custom_codes = set()  # Custom short codes
        self.lock = threading.RLock()
        
        # Configuration
        self.base_url = "https://tiny.url/"
        self.short_code_length = 6
        self.max_retries = 10
        self.cleanup_interval = 3600  # 1 hour
        self.max_url_length = 2048
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_urls, daemon=True)
        self.cleanup_thread.start()
    
    def _generate_short_code(self, url: str, custom_code: Optional[str] = None) -> str:
        """Generate short code for URL"""
        if custom_code:
            if self._is_code_available(custom_code):
                return custom_code
            else:
                raise ValueError("Custom code already exists")
        
        # Generate hash-based code
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Try different approaches to generate unique code
        for i in range(self.max_retries):
            if i == 0:
                # Use first N characters of hash
                code = url_hash[:self.short_code_length]
            else:
                # Add timestamp and counter for uniqueness
                timestamp = str(int(time.time()))[-4:]
                counter = str(i).zfill(2)
                combined = url_hash + timestamp + counter
                code = base64.urlsafe_b64encode(combined.encode())[:self.short_code_length].decode()
            
            if self._is_code_available(code):
                return code
        
        raise RuntimeError("Unable to generate unique short code")
    
    def _is_code_available(self, code: str) -> bool:
        """Check if short code is available"""
        with self.lock:
            return code not in self.url_storage and code not in self.custom_codes
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url or len(url) > self.max_url_length:
            return False
        
        # Basic URL validation
        return url.startswith(('http://', 'https://', 'ftp://'))
    
    def create_short_url(self, 
                        original_url: str, 
                        custom_code: Optional[str] = None,
                        expires_in: Optional[int] = None,
                        user_id: Optional[str] = None,
                        tags: Optional[List[str]] = None) -> str:
        """Create short URL"""
        if not self._validate_url(original_url):
            raise ValueError("Invalid URL format")
        
        with self.lock:
            # Check if URL already exists
            existing_code = self._find_existing_url(original_url)
            if existing_code:
                return self.base_url + existing_code
            
            # Generate short code
            short_code = self._generate_short_code(original_url, custom_code)
            
            # Calculate expiration
            expires_at = None
            if expires_in:
                expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Create URL data
            url_data = URLData(
                original_url=original_url,
                short_code=short_code,
                created_at=datetime.now(),
                expires_at=expires_at,
                user_id=user_id,
                tags=tags or []
            )
            
            # Store URL data
            self.url_storage[short_code] = url_data
            self.analytics_storage[short_code] = Analytics(
                total_clicks=0,
                unique_clicks=0,
                click_timestamps=[],
                referrers={},
                countries={},
                devices={},
                browsers={}
            )
            
            if custom_code:
                self.custom_codes.add(custom_code)
            
            # Persist to Redis
            self._persist_to_redis(short_code, url_data)
            
            return self.base_url + short_code
    
    def _find_existing_url(self, original_url: str) -> Optional[str]:
        """Find existing short code for URL"""
        for code, url_data in self.url_storage.items():
            if url_data.original_url == original_url:
                return code
        return None
    
    def get_original_url(self, short_code: str) -> Optional[str]:
        """Get original URL from short code"""
        with self.lock:
            if short_code in self.url_storage:
                url_data = self.url_storage[short_code]
                
                # Check expiration
                if url_data.expires_at and datetime.now() > url_data.expires_at:
                    self._delete_url(short_code)
                    return None
                
                # Update access info
                url_data.click_count += 1
                url_data.last_accessed = datetime.now()
                
                return url_data.original_url
        
        return None
    
    def _delete_url(self, short_code: str):
        """Delete URL and its analytics"""
        if short_code in self.url_storage:
            del self.url_storage[short_code]
        
        if short_code in self.analytics_storage:
            del self.analytics_storage[short_code]
        
        if short_code in self.custom_codes:
            self.custom_codes.remove(short_code)
        
        # Remove from Redis
        self.redis_client.delete(f"url:{short_code}")
        self.redis_client.delete(f"analytics:{short_code}")
    
    def _persist_to_redis(self, short_code: str, url_data: URLData):
        """Persist URL data to Redis"""
        url_dict = {
            'original_url': url_data.original_url,
            'short_code': url_data.short_code,
            'created_at': url_data.created_at.isoformat(),
            'expires_at': url_data.expires_at.isoformat() if url_data.expires_at else None,
            'click_count': url_data.click_count,
            'last_accessed': url_data.last_accessed.isoformat() if url_data.last_accessed else None,
            'user_id': url_data.user_id,
            'tags': json.dumps(url_data.tags)
        }
        
        self.redis_client.hset(f"url:{short_code}", mapping=url_dict)
    
    def _cleanup_expired_urls(self):
        """Clean up expired URLs"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                
                with self.lock:
                    expired_codes = []
                    for code, url_data in self.url_storage.items():
                        if url_data.expires_at and datetime.now() > url_data.expires_at:
                            expired_codes.append(code)
                    
                    for code in expired_codes:
                        self._delete_url(code)
                
            except Exception as e:
                print(f"Error in cleanup thread: {e}")
    
    def track_click(self, short_code: str, 
                   referrer: Optional[str] = None,
                   country: Optional[str] = None,
                   device: Optional[str] = None,
                   browser: Optional[str] = None,
                   user_agent: Optional[str] = None):
        """Track click analytics"""
        if short_code not in self.analytics_storage:
            return
        
        analytics = self.analytics_storage[short_code]
        now = datetime.now()
        
        analytics.total_clicks += 1
        analytics.click_timestamps.append(now)
        
        # Track referrer
        if referrer:
            analytics.referrers[referrer] = analytics.referrers.get(referrer, 0) + 1
        
        # Track country
        if country:
            analytics.countries[country] = analytics.countries.get(country, 0) + 1
        
        # Track device
        if device:
            analytics.devices[device] = analytics.devices.get(device, 0) + 1
        
        # Track browser
        if browser:
            analytics.browsers[browser] = analytics.browsers.get(browser, 0) + 1
        
        # Calculate unique clicks (simplified)
        analytics.unique_clicks = len(set(analytics.click_timestamps))
    
    def get_analytics(self, short_code: str) -> Optional[Analytics]:
        """Get analytics for short code"""
        return self.analytics_storage.get(short_code)
    
    def get_url_info(self, short_code: str) -> Optional[URLData]:
        """Get URL information"""
        return self.url_storage.get(short_code)
    
    def get_user_urls(self, user_id: str) -> List[URLData]:
        """Get all URLs for a user"""
        with self.lock:
            return [url_data for url_data in self.url_storage.values() 
                   if url_data.user_id == user_id]
    
    def search_urls(self, query: str) -> List[URLData]:
        """Search URLs by query"""
        with self.lock:
            results = []
            query_lower = query.lower()
            
            for url_data in self.url_storage.values():
                if (query_lower in url_data.original_url.lower() or
                    query_lower in url_data.short_code.lower() or
                    any(query_lower in tag.lower() for tag in url_data.tags)):
                    results.append(url_data)
            
            return results
    
    def get_top_urls(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top URLs by click count"""
        with self.lock:
            url_counts = [(code, url_data.click_count) 
                         for code, url_data in self.url_storage.items()]
            url_counts.sort(key=lambda x: x[1], reverse=True)
            return url_counts[:limit]
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        with self.lock:
            total_urls = len(self.url_storage)
            total_clicks = sum(url_data.click_count for url_data in self.url_storage.values())
            total_analytics = sum(analytics.total_clicks for analytics in self.analytics_storage.values())
            
            return {
                'total_urls': total_urls,
                'total_clicks': total_clicks,
                'total_analytics': total_analytics,
                'custom_codes': len(self.custom_codes),
                'active_urls': len([url for url in self.url_storage.values() 
                                  if not url.expires_at or url.expires_at > datetime.now()])
            }
    
    def bulk_create_urls(self, url_data_list: List[Dict]) -> List[str]:
        """Bulk create URLs"""
        results = []
        
        with self.lock:
            for data in url_data_list:
                try:
                    short_url = self.create_short_url(
                        original_url=data['original_url'],
                        custom_code=data.get('custom_code'),
                        expires_in=data.get('expires_in'),
                        user_id=data.get('user_id'),
                        tags=data.get('tags')
                    )
                    results.append(short_url)
                except Exception as e:
                    results.append(f"Error: {str(e)}")
        
        return results
    
    def export_analytics(self, short_code: str) -> Dict:
        """Export analytics data"""
        analytics = self.get_analytics(short_code)
        if not analytics:
            return {}
        
        return {
            'short_code': short_code,
            'total_clicks': analytics.total_clicks,
            'unique_clicks': analytics.unique_clicks,
            'click_timestamps': [ts.isoformat() for ts in analytics.click_timestamps],
            'referrers': analytics.referrers,
            'countries': analytics.countries,
            'devices': analytics.devices,
            'browsers': analytics.browsers,
            'exported_at': datetime.now().isoformat()
        }
    
    def get_click_timeline(self, short_code: str, days: int = 30) -> Dict:
        """Get click timeline for the last N days"""
        analytics = self.get_analytics(short_code)
        if not analytics:
            return {}
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        timeline = defaultdict(int)
        for timestamp in analytics.click_timestamps:
            if start_date <= timestamp <= end_date:
                date_key = timestamp.date().isoformat()
                timeline[date_key] += 1
        
        return dict(timeline)
    
    def cleanup_old_analytics(self, days: int = 90):
        """Clean up old analytics data"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            for analytics in self.analytics_storage.values():
                analytics.click_timestamps = [
                    ts for ts in analytics.click_timestamps 
                    if ts > cutoff_date
                ]
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        with self.lock:
            if not self.url_storage:
                return {}
            
            click_counts = [url_data.click_count for url_data in self.url_storage.values()]
            
            return {
                'average_clicks_per_url': statistics.mean(click_counts),
                'median_clicks_per_url': statistics.median(click_counts),
                'max_clicks_per_url': max(click_counts),
                'min_clicks_per_url': min(click_counts),
                'total_storage_size': len(self.url_storage),
                'memory_usage_estimate': len(str(self.url_storage)) + len(str(self.analytics_storage))
            }


class TinyURLAPI:
    """REST API for TinyURL system"""
    
    def __init__(self, tinyurl_system: TinyURLSystem):
        self.system = tinyurl_system
    
    def create_short_url(self, request_data: Dict) -> Dict:
        """API endpoint to create short URL"""
        try:
            short_url = self.system.create_short_url(
                original_url=request_data['url'],
                custom_code=request_data.get('custom_code'),
                expires_in=request_data.get('expires_in'),
                user_id=request_data.get('user_id'),
                tags=request_data.get('tags')
            )
            
            return {
                'success': True,
                'short_url': short_url,
                'original_url': request_data['url']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_original_url(self, short_code: str) -> Dict:
        """API endpoint to get original URL"""
        original_url = self.system.get_original_url(short_code)
        
        if original_url:
            return {
                'success': True,
                'original_url': original_url
            }
        else:
            return {
                'success': False,
                'error': 'URL not found or expired'
            }
    
    def get_analytics(self, short_code: str) -> Dict:
        """API endpoint to get analytics"""
        analytics = self.system.get_analytics(short_code)
        
        if analytics:
            return {
                'success': True,
                'analytics': {
                    'total_clicks': analytics.total_clicks,
                    'unique_clicks': analytics.unique_clicks,
                    'referrers': analytics.referrers,
                    'countries': analytics.countries,
                    'devices': analytics.devices,
                    'browsers': analytics.browsers
                }
            }
        else:
            return {
                'success': False,
                'error': 'Analytics not found'
            }
    
    def get_system_stats(self) -> Dict:
        """API endpoint to get system statistics"""
        stats = self.system.get_system_stats()
        return {
            'success': True,
            'stats': stats
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize system
    tinyurl = TinyURLSystem()
    
    # Create short URLs
    url1 = tinyurl.create_short_url("https://www.google.com", custom_code="google")
    url2 = tinyurl.create_short_url("https://www.github.com", expires_in=3600)
    url3 = tinyurl.create_short_url("https://www.stackoverflow.com", tags=["programming", "help"])
    
    print(f"Created URLs: {url1}, {url2}, {url3}")
    
    # Test URL resolution
    original1 = tinyurl.get_original_url("google")
    print(f"Original URL for 'google': {original1}")
    
    # Track clicks
    tinyurl.track_click("google", referrer="search", country="US", device="desktop", browser="chrome")
    tinyurl.track_click("google", referrer="social", country="CA", device="mobile", browser="safari")
    
    # Get analytics
    analytics = tinyurl.get_analytics("google")
    print(f"Analytics for 'google': {analytics}")
    
    # Get system stats
    stats = tinyurl.get_system_stats()
    print(f"System stats: {stats}")
