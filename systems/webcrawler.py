"""
Web Crawler System Implementation
High-performance web crawling with content extraction and indexing
"""

import time
import threading
import requests
import json
import redis
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import hashlib
import urllib.parse
import re
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import logging
from pathlib import Path
import gzip
import pickle

class CrawlStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class ContentType(Enum):
    HTML = "html"
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    JSON = "json"
    XML = "xml"
    OTHER = "other"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class URL:
    """URL data structure"""
    url: str
    domain: str
    path: str
    query: str
    fragment: str
    normalized_url: str
    depth: int = 0
    priority: Priority = Priority.MEDIUM
    last_crawled: Optional[datetime] = None
    crawl_count: int = 0
    status: CrawlStatus = CrawlStatus.PENDING
    error_message: Optional[str] = None

@dataclass
class WebPage:
    """Web page data structure"""
    url: str
    title: str
    content: str
    content_type: ContentType
    content_length: int
    status_code: int
    headers: Dict[str, str]
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    crawled_at: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0

@dataclass
class CrawlJob:
    """Crawl job data structure"""
    job_id: str
    name: str
    start_urls: List[str]
    max_depth: int = 3
    max_pages: int = 1000
    delay: float = 1.0
    respect_robots: bool = True
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    allowed_paths: List[str] = field(default_factory=list)
    blocked_paths: List[str] = field(default_factory=list)
    user_agent: str = "WebCrawler/1.0"
    created_at: datetime = field(default_factory=datetime.now)
    status: CrawlStatus = CrawlStatus.PENDING
    pages_crawled: int = 0
    pages_failed: int = 0

@dataclass
class CrawlStats:
    """Crawl statistics"""
    total_urls: int = 0
    crawled_urls: int = 0
    failed_urls: int = 0
    blocked_urls: int = 0
    total_pages: int = 0
    total_content_size: int = 0
    average_response_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class WebCrawler:
    """High-performance web crawler system"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Core data structures
        self.urls = {}  # url -> URL
        self.pages = {}  # url -> WebPage
        self.crawl_jobs = {}  # job_id -> CrawlJob
        self.robots_cache = {}  # domain -> RobotFileParser
        
        # Crawl queues
        self.pending_urls = deque()  # Queue of URLs to crawl
        self.failed_urls = deque()  # Queue of failed URLs for retry
        self.blocked_urls = set()  # Set of blocked URLs
        
        # Indexes
        self.domain_urls = defaultdict(list)  # domain -> List[url]
        self.job_urls = defaultdict(list)  # job_id -> List[url]
        self.content_index = defaultdict(list)  # word -> List[url]
        
        # Threading
        self.lock = threading.RLock()
        self.crawler_threads = []
        self.max_workers = 5
        self.crawl_delay = 1.0
        
        # Configuration
        self.max_content_size = 10 * 1024 * 1024  # 10MB
        self.timeout = 30  # seconds
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        self.cleanup_interval = 3600  # 1 hour
        
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Start crawler threads
        self._start_crawler_threads()
    
    def create_crawl_job(self, name: str, start_urls: List[str], max_depth: int = 3,
                        max_pages: int = 1000, delay: float = 1.0,
                        respect_robots: bool = True, user_agent: str = "WebCrawler/1.0",
                        allowed_domains: List[str] = None, blocked_domains: List[str] = None) -> str:
        """Create a new crawl job"""
        with self.lock:
            job_id = f"job_{int(time.time() * 1000)}"
            
            job = CrawlJob(
                job_id=job_id,
                name=name,
                start_urls=start_urls,
                max_depth=max_depth,
                max_pages=max_pages,
                delay=delay,
                respect_robots=respect_robots,
                user_agent=user_agent,
                allowed_domains=allowed_domains or [],
                blocked_domains=blocked_domains or []
            )
            
            self.crawl_jobs[job_id] = job
            
            # Add start URLs to crawl queue
            for url in start_urls:
                self._add_url_to_crawl(url, job_id, 0)
            
            self._persist_crawl_job(job)
            return job_id
    
    def start_crawl_job(self, job_id: str) -> bool:
        """Start a crawl job"""
        with self.lock:
            if job_id not in self.crawl_jobs:
                return False
            
            job = self.crawl_jobs[job_id]
            if job.status != CrawlStatus.PENDING:
                return False
            
            job.status = CrawlStatus.IN_PROGRESS
            job.created_at = datetime.now()
            
            self._persist_crawl_job(job)
            return True
    
    def stop_crawl_job(self, job_id: str) -> bool:
        """Stop a crawl job"""
        with self.lock:
            if job_id not in self.crawl_jobs:
                return False
            
            job = self.crawl_jobs[job_id]
            job.status = CrawlStatus.COMPLETED
            job.end_time = datetime.now()
            
            self._persist_crawl_job(job)
            return True
    
    def get_crawl_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get crawl job status"""
        with self.lock:
            if job_id not in self.crawl_jobs:
                return None
            
            job = self.crawl_jobs[job_id]
            return {
                "job_id": job.job_id,
                "name": job.name,
                "status": job.status.value,
                "pages_crawled": job.pages_crawled,
                "pages_failed": job.pages_failed,
                "created_at": job.created_at.isoformat(),
                "progress": job.pages_crawled / max(job.max_pages, 1) * 100
            }
    
    def get_crawled_pages(self, job_id: str, limit: int = 100) -> List[WebPage]:
        """Get crawled pages for a job"""
        with self.lock:
            if job_id not in self.job_urls:
                return []
            
            urls = self.job_urls[job_id]
            pages = [self.pages[url] for url in urls if url in self.pages]
            
            # Sort by crawl time
            pages.sort(key=lambda x: x.crawled_at, reverse=True)
            
            return pages[:limit]
    
    def search_content(self, query: str, job_id: Optional[str] = None, limit: int = 50) -> List[WebPage]:
        """Search crawled content"""
        with self.lock:
            query_words = self._extract_words(query.lower())
            if not query_words:
                return []
            
            # Find URLs containing query words
            matching_urls = set()
            for word in query_words:
                if word in self.content_index:
                    matching_urls.update(self.content_index[word])
            
            # Filter by job if specified
            if job_id and job_id in self.job_urls:
                job_urls = set(self.job_urls[job_id])
                matching_urls = matching_urls & job_urls
            
            # Get pages and rank by relevance
            pages = [self.pages[url] for url in matching_urls if url in self.pages]
            pages.sort(key=lambda x: self._calculate_relevance_score(x, query_words), reverse=True)
            
            return pages[:limit]
    
    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a domain"""
        with self.lock:
            if domain not in self.domain_urls:
                return {}
            
            urls = self.domain_urls[domain]
            pages = [self.pages[url] for url in urls if url in self.pages]
            
            if not pages:
                return {}
            
            total_content_size = sum(page.content_length for page in pages)
            response_times = [page.processing_time for page in pages if page.processing_time > 0]
            
            return {
                "domain": domain,
                "total_urls": len(urls),
                "crawled_pages": len(pages),
                "total_content_size": total_content_size,
                "average_content_size": total_content_size / len(pages) if pages else 0,
                "average_response_time": statistics.mean(response_times) if response_times else 0,
                "last_crawled": max(page.crawled_at for page in pages).isoformat() if pages else None
            }
    
    def _add_url_to_crawl(self, url: str, job_id: str, depth: int, priority: Priority = Priority.MEDIUM):
        """Add URL to crawl queue"""
        normalized_url = self._normalize_url(url)
        if not normalized_url:
            return
        
        # Check if URL already exists
        if normalized_url in self.urls:
            existing_url = self.urls[normalized_url]
            if existing_url.depth > depth:
                existing_url.depth = depth
                existing_url.priority = priority
        else:
            # Create new URL
            parsed_url = urllib.parse.urlparse(normalized_url)
            url_obj = URL(
                url=normalized_url,
                domain=parsed_url.netloc,
                path=parsed_url.path,
                query=parsed_url.query,
                fragment=parsed_url.fragment,
                normalized_url=normalized_url,
                depth=depth,
                priority=priority
            )
            
            self.urls[normalized_url] = url_obj
            self.domain_urls[parsed_url.netloc].append(normalized_url)
            self.job_urls[job_id].append(normalized_url)
        
        # Add to pending queue
        self.pending_urls.append((normalized_url, job_id))
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize URL"""
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme:
                url = "http://" + url
                parsed = urllib.parse.urlparse(url)
            
            # Remove fragment
            normalized = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, parsed.query, ""
            ))
            
            # Remove trailing slash for consistency
            if normalized.endswith('/') and len(parsed.path) > 1:
                normalized = normalized[:-1]
            
            return normalized
        except:
            return None
    
    def _start_crawler_threads(self):
        """Start crawler worker threads"""
        for i in range(self.max_workers):
            thread = threading.Thread(target=self._crawler_worker, daemon=True)
            thread.start()
            self.crawler_threads.append(thread)
    
    def _crawler_worker(self):
        """Crawler worker thread"""
        while True:
            try:
                # Get next URL to crawl
                url, job_id = self._get_next_url()
                if not url:
                    time.sleep(1)
                    continue
                
                # Crawl the URL
                self._crawl_url(url, job_id)
                
                # Respect crawl delay
                time.sleep(self.crawl_delay)
                
            except Exception as e:
                self.logger.error(f"Error in crawler worker: {e}")
                time.sleep(5)
    
    def _get_next_url(self) -> Tuple[Optional[str], Optional[str]]:
        """Get next URL to crawl"""
        with self.lock:
            if not self.pending_urls:
                return None, None
            
            return self.pending_urls.popleft()
    
    def _crawl_url(self, url: str, job_id: str):
        """Crawl a single URL"""
        if url not in self.urls or job_id not in self.crawl_jobs:
            return
        
        url_obj = self.urls[url]
        job = self.crawl_jobs[job_id]
        
        # Check if URL should be crawled
        if not self._should_crawl_url(url_obj, job):
            url_obj.status = CrawlStatus.BLOCKED
            self.blocked_urls.add(url)
            return
        
        # Check robots.txt
        if job.respect_robots and not self._check_robots_txt(url_obj):
            url_obj.status = CrawlStatus.BLOCKED
            self.blocked_urls.add(url)
            return
        
        # Update URL status
        url_obj.status = CrawlStatus.IN_PROGRESS
        url_obj.crawl_count += 1
        
        start_time = time.time()
        
        try:
            # Make HTTP request
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": job.user_agent},
                allow_redirects=True
            )
            
            # Process response
            page = self._process_response(url, response, job)
            if page:
                self.pages[url] = page
                self._index_content(page)
                
                # Extract links
                self._extract_links(page, job)
                
                # Update job stats
                job.pages_crawled += 1
                url_obj.status = CrawlStatus.COMPLETED
            else:
                url_obj.status = CrawlStatus.FAILED
                job.pages_failed += 1
            
        except Exception as e:
            url_obj.status = CrawlStatus.FAILED
            url_obj.error_message = str(e)
            job.pages_failed += 1
            self.logger.error(f"Error crawling {url}: {e}")
        
        finally:
            url_obj.last_crawled = datetime.now()
            url_obj.processing_time = time.time() - start_time
            
            # Persist URL and job
            self._persist_url(url_obj)
            self._persist_crawl_job(job)
    
    def _should_crawl_url(self, url_obj: URL, job: CrawlJob) -> bool:
        """Check if URL should be crawled"""
        # Check depth
        if url_obj.depth > job.max_depth:
            return False
        
        # Check if max pages reached
        if job.pages_crawled >= job.max_pages:
            return False
        
        # Check allowed domains
        if job.allowed_domains and url_obj.domain not in job.allowed_domains:
            return False
        
        # Check blocked domains
        if url_obj.domain in job.blocked_domains:
            return False
        
        # Check allowed paths
        if job.allowed_paths:
            if not any(url_obj.path.startswith(path) for path in job.allowed_paths):
                return False
        
        # Check blocked paths
        if job.blocked_paths:
            if any(url_obj.path.startswith(path) for path in job.blocked_paths):
                return False
        
        return True
    
    def _check_robots_txt(self, url_obj: URL) -> bool:
        """Check robots.txt for URL"""
        domain = url_obj.domain
        
        if domain not in self.robots_cache:
            try:
                robots_url = f"http://{domain}/robots.txt"
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[domain] = rp
            except:
                self.robots_cache[domain] = None
        
        rp = self.robots_cache[domain]
        if not rp:
            return True
        
        return rp.can_fetch("*", url_obj.url)
    
    def _process_response(self, url: str, response: requests.Response, job: CrawlJob) -> Optional[WebPage]:
        """Process HTTP response"""
        if response.status_code != 200:
            return None
        
        # Check content type
        content_type = self._get_content_type(response)
        if content_type == ContentType.OTHER:
            return None
        
        # Check content size
        content_length = len(response.content)
        if content_length > self.max_content_size:
            return None
        
        # Extract content
        content = self._extract_content(response, content_type)
        if not content:
            return None
        
        # Extract title
        title = self._extract_title(response, content, content_type)
        
        # Create page object
        page = WebPage(
            url=url,
            title=title,
            content=content,
            content_type=content_type,
            content_length=content_length,
            status_code=response.status_code,
            headers=dict(response.headers),
            crawled_at=datetime.now()
        )
        
        return page
    
    def _get_content_type(self, response: requests.Response) -> ContentType:
        """Get content type from response"""
        content_type = response.headers.get('content-type', '').lower()
        
        if 'text/html' in content_type:
            return ContentType.HTML
        elif 'application/pdf' in content_type:
            return ContentType.PDF
        elif 'image/' in content_type:
            return ContentType.IMAGE
        elif 'text/plain' in content_type:
            return ContentType.TEXT
        elif 'application/json' in content_type:
            return ContentType.JSON
        elif 'application/xml' in content_type or 'text/xml' in content_type:
            return ContentType.XML
        else:
            return ContentType.OTHER
    
    def _extract_content(self, response: requests.Response, content_type: ContentType) -> str:
        """Extract content from response"""
        if content_type == ContentType.HTML:
            return self._extract_html_content(response.text)
        elif content_type == ContentType.TEXT:
            return response.text
        elif content_type == ContentType.JSON:
            try:
                data = response.json()
                return json.dumps(data, indent=2)
            except:
                return response.text
        else:
            return response.text
    
    def _extract_html_content(self, html: str) -> str:
        """Extract text content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except:
            return html
    
    def _extract_title(self, response: requests.Response, content: str, content_type: ContentType) -> str:
        """Extract title from response"""
        if content_type == ContentType.HTML:
            try:
                soup = BeautifulSoup(content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    return title_tag.get_text().strip()
            except:
                pass
        
        # Fallback to URL
        return urllib.parse.urlparse(response.url).path
    
    def _extract_links(self, page: WebPage, job: CrawlJob):
        """Extract links from page"""
        if page.content_type != ContentType.HTML:
            return
        
        try:
            soup = BeautifulSoup(page.content, 'html.parser')
            
            # Extract links
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urllib.parse.urljoin(page.url, href)
                normalized_url = self._normalize_url(absolute_url)
                
                if normalized_url and normalized_url != page.url:
                    page.links.append(normalized_url)
                    
                    # Add to crawl queue if within depth limit
                    if page.url in self.urls:
                        current_depth = self.urls[page.url].depth
                        if current_depth < job.max_depth:
                            self._add_url_to_crawl(normalized_url, job.job_id, current_depth + 1)
            
            # Extract images
            for img in soup.find_all('img', src=True):
                src = img['src']
                absolute_url = urllib.parse.urljoin(page.url, src)
                page.images.append(absolute_url)
        
        except Exception as e:
            self.logger.error(f"Error extracting links from {page.url}: {e}")
    
    def _index_content(self, page: WebPage):
        """Index page content for search"""
        words = self._extract_words(page.content)
        for word in words:
            self.content_index[word].append(page.url)
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text"""
        # Simple word extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return list(set(words))  # Remove duplicates
    
    def _calculate_relevance_score(self, page: WebPage, query_words: List[str]) -> float:
        """Calculate relevance score for search"""
        content_words = self._extract_words(page.content)
        title_words = self._extract_words(page.title)
        
        score = 0.0
        
        # Count word matches in content
        for word in query_words:
            score += content_words.count(word)
        
        # Boost score for title matches
        for word in query_words:
            if word in title_words:
                score += 5.0
        
        return score
    
    def _persist_url(self, url_obj: URL):
        """Persist URL to Redis"""
        url_data = {
            "url": url_obj.url,
            "domain": url_obj.domain,
            "path": url_obj.path,
            "query": url_obj.query,
            "fragment": url_obj.fragment,
            "normalized_url": url_obj.normalized_url,
            "depth": str(url_obj.depth),
            "priority": url_obj.priority.value,
            "last_crawled": url_obj.last_crawled.isoformat() if url_obj.last_crawled else None,
            "crawl_count": str(url_obj.crawl_count),
            "status": url_obj.status.value,
            "error_message": url_obj.error_message or ""
        }
        self.redis_client.hset(f"url:{url_obj.normalized_url}", mapping=url_data)
    
    def _persist_crawl_job(self, job: CrawlJob):
        """Persist crawl job to Redis"""
        job_data = {
            "job_id": job.job_id,
            "name": job.name,
            "start_urls": json.dumps(job.start_urls),
            "max_depth": str(job.max_depth),
            "max_pages": str(job.max_pages),
            "delay": str(job.delay),
            "respect_robots": str(job.respect_robots),
            "allowed_domains": json.dumps(job.allowed_domains),
            "blocked_domains": json.dumps(job.blocked_domains),
            "user_agent": job.user_agent,
            "created_at": job.created_at.isoformat(),
            "status": job.status.value,
            "pages_crawled": str(job.pages_crawled),
            "pages_failed": str(job.pages_failed)
        }
        self.redis_client.hset(f"crawl_job:{job.job_id}", mapping=job_data)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        with self.lock:
            return {
                "total_urls": len(self.urls),
                "total_pages": len(self.pages),
                "total_jobs": len(self.crawl_jobs),
                "pending_urls": len(self.pending_urls),
                "failed_urls": len(self.failed_urls),
                "blocked_urls": len(self.blocked_urls),
                "active_jobs": len([job for job in self.crawl_jobs.values() if job.status == CrawlStatus.IN_PROGRESS]),
                "total_content_size": sum(page.content_length for page in self.pages.values()),
                "average_content_size": statistics.mean([page.content_length for page in self.pages.values()]) if self.pages else 0,
                "crawler_threads": len(self.crawler_threads)
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize web crawler
    crawler = WebCrawler()
    
    # Create crawl job
    job_id = crawler.create_crawl_job(
        name="Example Crawl",
        start_urls=["https://example.com"],
        max_depth=2,
        max_pages=100,
        delay=1.0,
        respect_robots=True
    )
    
    # Start crawl job
    crawler.start_crawl_job(job_id)
    
    # Wait for some crawling to happen
    time.sleep(10)
    
    # Get job status
    status = crawler.get_crawl_job_status(job_id)
    print(f"Job status: {status}")
    
    # Get crawled pages
    pages = crawler.get_crawled_pages(job_id, limit=10)
    print(f"Crawled pages: {len(pages)}")
    
    # Search content
    search_results = crawler.search_content("example", job_id, limit=5)
    print(f"Search results: {len(search_results)}")
    
    # Get system stats
    stats = crawler.get_system_stats()
    print(f"System stats: {stats}")
