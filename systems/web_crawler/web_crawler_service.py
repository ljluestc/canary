#!/usr/bin/env python3
"""
Web Crawler Service

A comprehensive web crawler system for content indexing, URL discovery,
and data extraction with support for robots.txt compliance, rate limiting,
and content analysis.
"""

import asyncio
import aiohttp
import sqlite3
import hashlib
import time
import re
import urllib.parse
import urllib.robotparser
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CrawlJob:
    """Crawl job configuration."""
    job_id: str
    name: str
    start_urls: List[str]
    max_pages: int = 1000
    max_depth: int = 5
    delay: float = 1.0  # Delay between requests in seconds
    respect_robots: bool = True
    follow_external: bool = False
    content_filters: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed, paused
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pages_crawled: int = 0
    pages_failed: int = 0
    error_message: Optional[str] = None

@dataclass
class WebPage:
    """Web page data model."""
    url: str
    title: str = ""
    content: str = ""
    html_content: str = ""
    meta_description: str = ""
    meta_keywords: str = ""
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    status_code: int = 0
    content_type: str = ""
    content_length: int = 0
    last_modified: Optional[datetime] = None
    crawl_timestamp: datetime = field(default_factory=datetime.now)
    depth: int = 0
    parent_url: Optional[str] = None
    page_hash: str = ""
    is_duplicate: bool = False

@dataclass
class CrawlStats:
    """Crawl statistics."""
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    duplicate_pages: int = 0
    external_pages: int = 0
    blocked_pages: int = 0
    total_size: int = 0
    average_response_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class WebCrawlerDatabase:
    """Database operations for web crawler."""
    
    def __init__(self, db_path: str = "web_crawler.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crawl jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_jobs (
                job_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                start_urls TEXT NOT NULL,
                max_pages INTEGER DEFAULT 1000,
                max_depth INTEGER DEFAULT 5,
                delay REAL DEFAULT 1.0,
                respect_robots BOOLEAN DEFAULT 1,
                follow_external BOOLEAN DEFAULT 0,
                content_filters TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                pages_crawled INTEGER DEFAULT 0,
                pages_failed INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')
        
        # Web pages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_pages (
                url TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                html_content TEXT,
                meta_description TEXT,
                meta_keywords TEXT,
                links TEXT DEFAULT '[]',
                images TEXT DEFAULT '[]',
                status_code INTEGER,
                content_type TEXT,
                content_length INTEGER,
                last_modified TIMESTAMP,
                crawl_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                depth INTEGER DEFAULT 0,
                parent_url TEXT,
                page_hash TEXT,
                is_duplicate BOOLEAN DEFAULT 0
            )
        ''')
        
        # Crawl queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_queue (
                url TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                depth INTEGER DEFAULT 0,
                parent_url TEXT,
                priority INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Robots.txt cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS robots_cache (
                domain TEXT PRIMARY KEY,
                robots_content TEXT,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_crawl_job(self, job: CrawlJob) -> bool:
        """Save crawl job to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO crawl_jobs 
                (job_id, name, start_urls, max_pages, max_depth, delay, 
                 respect_robots, follow_external, content_filters, status, 
                 created_at, started_at, completed_at, pages_crawled, 
                 pages_failed, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.job_id, job.name, json.dumps(job.start_urls), 
                job.max_pages, job.max_depth, job.delay,
                job.respect_robots, job.follow_external, 
                json.dumps(job.content_filters), job.status,
                job.created_at, job.started_at, job.completed_at,
                job.pages_crawled, job.pages_failed, job.error_message
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving crawl job: {e}")
            return False
    
    def get_crawl_job(self, job_id: str) -> Optional[CrawlJob]:
        """Get crawl job by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM crawl_jobs WHERE job_id = ?', (job_id,))
            row = cursor.fetchone()
            
            if row:
                job = CrawlJob(
                    job_id=row[0],
                    name=row[1],
                    start_urls=json.loads(row[2]),
                    max_pages=row[3],
                    max_depth=row[4],
                    delay=row[5],
                    respect_robots=bool(row[6]),
                    follow_external=bool(row[7]),
                    content_filters=json.loads(row[8]),
                    status=row[9],
                    created_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
                    started_at=datetime.fromisoformat(row[11]) if row[11] else None,
                    completed_at=datetime.fromisoformat(row[12]) if row[12] else None,
                    pages_crawled=row[13],
                    pages_failed=row[14],
                    error_message=row[15]
                )
                conn.close()
                return job
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting crawl job: {e}")
            return None
    
    def save_web_page(self, page: WebPage) -> bool:
        """Save web page to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO web_pages 
                (url, title, content, html_content, meta_description, meta_keywords,
                 links, images, status_code, content_type, content_length, 
                 last_modified, crawl_timestamp, depth, parent_url, page_hash, is_duplicate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                page.url, page.title, page.content, page.html_content,
                page.meta_description, page.meta_keywords,
                json.dumps(page.links), json.dumps(page.images),
                page.status_code, page.content_type, page.content_length,
                page.last_modified, page.crawl_timestamp, page.depth,
                page.parent_url, page.page_hash, page.is_duplicate
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving web page: {e}")
            return False
    
    def get_web_page(self, url: str) -> Optional[WebPage]:
        """Get web page by URL."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM web_pages WHERE url = ?', (url,))
            row = cursor.fetchone()
            
            if row:
                page = WebPage(
                    url=row[0],
                    title=row[1] or "",
                    content=row[2] or "",
                    html_content=row[3] or "",
                    meta_description=row[4] or "",
                    meta_keywords=row[5] or "",
                    links=json.loads(row[6]) if row[6] else [],
                    images=json.loads(row[7]) if row[7] else [],
                    status_code=row[8] or 0,
                    content_type=row[9] or "",
                    content_length=row[10] or 0,
                    last_modified=datetime.fromisoformat(row[11]) if row[11] else None,
                    crawl_timestamp=datetime.fromisoformat(row[12]) if row[12] else datetime.now(),
                    depth=row[13] or 0,
                    parent_url=row[14],
                    page_hash=row[15] or "",
                    is_duplicate=bool(row[16])
                )
                conn.close()
                return page
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting web page: {e}")
            return None
    
    def add_to_crawl_queue(self, url: str, job_id: str, depth: int = 0, 
                          parent_url: str = None, priority: int = 0) -> bool:
        """Add URL to crawl queue."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO crawl_queue 
                (url, job_id, depth, parent_url, priority, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (url, job_id, depth, parent_url, priority))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding to crawl queue: {e}")
            return False
    
    def get_next_crawl_url(self, job_id: str) -> Optional[tuple]:
        """Get next URL from crawl queue."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT url, depth, parent_url FROM crawl_queue 
                WHERE job_id = ? AND status = 'pending' 
                ORDER BY priority DESC, added_at ASC 
                LIMIT 1
            ''', (job_id,))
            
            result = cursor.fetchone()
            if result:
                # Mark as processing
                cursor.execute('''
                    UPDATE crawl_queue SET status = 'processing' 
                    WHERE url = ? AND job_id = ?
                ''', (result[0], job_id))
                conn.commit()
            
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error getting next crawl URL: {e}")
            return None
    
    def mark_url_completed(self, url: str, job_id: str) -> bool:
        """Mark URL as completed in crawl queue."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE crawl_queue SET status = 'completed' 
                WHERE url = ? AND job_id = ?
            ''', (url, job_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error marking URL completed: {e}")
            return False
    
    def get_crawl_stats(self, job_id: str) -> CrawlStats:
        """Get crawl statistics for a job."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get job info
            cursor.execute('''
                SELECT started_at, completed_at FROM crawl_jobs WHERE job_id = ?
            ''', (job_id,))
            job_row = cursor.fetchone()
            
            # Get page counts
            cursor.execute('''
                SELECT COUNT(*) FROM web_pages WHERE url IN (
                    SELECT url FROM crawl_queue WHERE job_id = ?
                )
            ''', (job_id,))
            total_pages = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM web_pages 
                WHERE url IN (SELECT url FROM crawl_queue WHERE job_id = ?)
                AND status_code >= 200 AND status_code < 400
            ''', (job_id,))
            successful_pages = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM web_pages 
                WHERE url IN (SELECT url FROM crawl_queue WHERE job_id = ?)
                AND status_code >= 400
            ''', (job_id,))
            failed_pages = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM web_pages 
                WHERE url IN (SELECT url FROM crawl_queue WHERE job_id = ?)
                AND is_duplicate = 1
            ''', (job_id,))
            duplicate_pages = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT SUM(content_length) FROM web_pages 
                WHERE url IN (SELECT url FROM crawl_queue WHERE job_id = ?)
            ''', (job_id,))
            total_size = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return CrawlStats(
                total_pages=total_pages,
                successful_pages=successful_pages,
                failed_pages=failed_pages,
                duplicate_pages=duplicate_pages,
                start_time=datetime.fromisoformat(job_row[0]) if job_row and job_row[0] else None,
                end_time=datetime.fromisoformat(job_row[1]) if job_row and job_row[1] else None,
                total_size=total_size
            )
        except Exception as e:
            logger.error(f"Error getting crawl stats: {e}")
            return CrawlStats()

class WebCrawlerService:
    """Web crawler service with async crawling capabilities."""
    
    def __init__(self, db_path: str = "web_crawler.db"):
        self.db = WebCrawlerDatabase(db_path)
        self.session: Optional[aiohttp.ClientSession] = None
        self.robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self.crawl_tasks: Dict[str, asyncio.Task] = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'WebCrawler/1.0 (+https://example.com/bot)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def create_crawl_job(self, name: str, start_urls: List[str], 
                        max_pages: int = 1000, max_depth: int = 5,
                        delay: float = 1.0, respect_robots: bool = True,
                        follow_external: bool = False) -> CrawlJob:
        """Create a new crawl job."""
        job_id = hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:12]
        
        job = CrawlJob(
            job_id=job_id,
            name=name,
            start_urls=start_urls,
            max_pages=max_pages,
            max_depth=max_depth,
            delay=delay,
            respect_robots=respect_robots,
            follow_external=follow_external
        )
        
        if self.db.save_crawl_job(job):
            # Add start URLs to crawl queue
            for url in start_urls:
                self.db.add_to_crawl_queue(url, job_id, depth=0, priority=10)
            
            return job
        return None
    
    async def check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if domain in self.robots_cache:
                rp = self.robots_cache[domain]
            else:
                rp = urllib.robotparser.RobotFileParser()
                robots_url = urljoin(domain, '/robots.txt')
                
                try:
                    async with self.session.get(robots_url) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                            # Create a mock response for the robot parser
                            import io
                            from urllib.request import Request, urlopen
                            
                            # Use a simple approach - just check for Disallow patterns
                            if 'Disallow: /' in robots_content:
                                return False  # Disallow all
                            elif 'Allow: /' in robots_content:
                                return True   # Allow all
                            else:
                                return True   # Default to allow
                        else:
                            return True  # No robots.txt, allow crawling
                except:
                    return True  # Error fetching robots.txt, allow crawling
                
                self.robots_cache[domain] = rp
            
            return rp.can_fetch('*', url)
        except Exception as e:
            logger.error(f"Error checking robots.txt: {e}")
            return True  # Allow crawling on error
    
    def calculate_page_hash(self, content: str) -> str:
        """Calculate hash of page content for duplicate detection."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def extract_content(self, html: str) -> Dict[str, Any]:
        """Extract content from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract meta description
            meta_description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_description = meta_desc.get('content', '').strip()
            
            # Extract meta keywords
            meta_keywords = ""
            meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords_tag:
                meta_keywords = meta_keywords_tag.get('content', '').strip()
            
            # Extract text content
            text_content = soup.get_text()
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') or href.startswith('/'):
                    links.append(href)
            
            # Extract images
            images = []
            for img in soup.find_all('img', src=True):
                src = img['src']
                if src.startswith('http') or src.startswith('/'):
                    images.append(src)
            
            return {
                'title': title,
                'content': text_content,
                'meta_description': meta_description,
                'meta_keywords': meta_keywords,
                'links': links,
                'images': images
            }
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return {
                'title': '',
                'content': '',
                'meta_description': '',
                'meta_keywords': '',
                'links': [],
                'images': []
            }
    
    async def crawl_page(self, url: str, job: CrawlJob, depth: int = 0, 
                        parent_url: str = None) -> Optional[WebPage]:
        """Crawl a single page."""
        try:
            # Check if already crawled
            existing_page = self.db.get_web_page(url)
            if existing_page:
                return existing_page
            
            # Check robots.txt if enabled
            if job.respect_robots and not await self.check_robots_txt(url):
                logger.info(f"Blocked by robots.txt: {url}")
                return None
            
            # Fetch page
            async with self.session.get(url) as response:
                status_code = response.status
                content_type = response.headers.get('content-type', '')
                content_length = int(response.headers.get('content-length', 0))
                
                # Only process HTML content
                if 'text/html' not in content_type:
                    logger.info(f"Skipping non-HTML content: {url}")
                    return None
                
                html_content = await response.text()
                
                # Extract content
                extracted = self.extract_content(html_content)
                
                # Calculate page hash
                page_hash = self.calculate_page_hash(extracted['content'])
                
                # Check for duplicates
                is_duplicate = False
                if existing_page and existing_page.page_hash == page_hash:
                    is_duplicate = True
                
                # Create WebPage object
                page = WebPage(
                    url=url,
                    title=extracted['title'],
                    content=extracted['content'],
                    html_content=html_content,
                    meta_description=extracted['meta_description'],
                    meta_keywords=extracted['meta_keywords'],
                    links=extracted['links'],
                    images=extracted['images'],
                    status_code=status_code,
                    content_type=content_type,
                    content_length=content_length,
                    crawl_timestamp=datetime.now(),
                    depth=depth,
                    parent_url=parent_url,
                    page_hash=page_hash,
                    is_duplicate=is_duplicate
                )
                
                # Save to database
                self.db.save_web_page(page)
                
                # Add new URLs to crawl queue if within limits
                if depth < job.max_depth and not is_duplicate:
                    await self.add_new_urls_to_queue(page, job, depth + 1)
                
                return page
                
        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
            return None
    
    async def add_new_urls_to_queue(self, page: WebPage, job: CrawlJob, depth: int):
        """Add new URLs from page to crawl queue."""
        try:
            parsed_base_url = urlparse(page.url)
            base_domain = parsed_base_url.netloc
            
            for link in page.links:
                # Convert relative URLs to absolute
                absolute_url = urljoin(page.url, link)
                parsed_link = urlparse(absolute_url)
                
                # Skip if not following external links
                if not job.follow_external and parsed_link.netloc != base_domain:
                    continue
                
                # Skip if already in queue or crawled
                if self.db.get_web_page(absolute_url):
                    continue
                
                # Add to queue with lower priority for deeper pages
                priority = max(0, 10 - depth)
                self.db.add_to_crawl_queue(absolute_url, job.job_id, depth, page.url, priority)
                
        except Exception as e:
            logger.error(f"Error adding URLs to queue: {e}")
    
    async def run_crawl_job(self, job_id: str) -> bool:
        """Run a crawl job."""
        try:
            job = self.db.get_crawl_job(job_id)
            if not job:
                logger.error(f"Job not found: {job_id}")
                return False
            
            # Update job status
            job.status = "running"
            job.started_at = datetime.now()
            self.db.save_crawl_job(job)
            
            logger.info(f"Starting crawl job: {job.name}")
            
            while job.pages_crawled < job.max_pages:
                # Get next URL from queue
                next_url_data = self.db.get_next_crawl_url(job_id)
                if not next_url_data:
                    break  # No more URLs to crawl
                
                url, depth, parent_url = next_url_data
                
                # Crawl the page
                page = await self.crawl_page(url, job, depth, parent_url)
                
                if page:
                    job.pages_crawled += 1
                    if page.is_duplicate:
                        job.pages_crawled -= 1  # Don't count duplicates
                else:
                    job.pages_failed += 1
                
                # Mark URL as completed
                self.db.mark_url_completed(url, job_id)
                
                # Update job progress
                self.db.save_crawl_job(job)
                
                # Delay between requests
                if job.delay > 0:
                    await asyncio.sleep(job.delay)
            
            # Mark job as completed
            job.status = "completed"
            job.completed_at = datetime.now()
            self.db.save_crawl_job(job)
            
            logger.info(f"Completed crawl job: {job.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error running crawl job: {e}")
            job = self.db.get_crawl_job(job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now()
                self.db.save_crawl_job(job)
            return False
    
    def get_crawl_job(self, job_id: str) -> Optional[CrawlJob]:
        """Get crawl job by ID."""
        return self.db.get_crawl_job(job_id)
    
    def get_crawl_stats(self, job_id: str) -> CrawlStats:
        """Get crawl statistics."""
        return self.db.get_crawl_stats(job_id)
    
    def search_pages(self, query: str, job_id: str = None, limit: int = 20) -> List[WebPage]:
        """Search crawled pages."""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            if job_id:
                cursor.execute('''
                    SELECT * FROM web_pages 
                    WHERE url IN (SELECT url FROM crawl_queue WHERE job_id = ?)
                    AND (title LIKE ? OR content LIKE ? OR meta_description LIKE ?)
                    ORDER BY crawl_timestamp DESC
                    LIMIT ?
                ''', (job_id, f'%{query}%', f'%{query}%', f'%{query}%', limit))
            else:
                cursor.execute('''
                    SELECT * FROM web_pages 
                    WHERE title LIKE ? OR content LIKE ? OR meta_description LIKE ?
                    ORDER BY crawl_timestamp DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            pages = []
            for row in cursor.fetchall():
                page = WebPage(
                    url=row[0],
                    title=row[1] or "",
                    content=row[2] or "",
                    html_content=row[3] or "",
                    meta_description=row[4] or "",
                    meta_keywords=row[5] or "",
                    links=json.loads(row[6]) if row[6] else [],
                    images=json.loads(row[7]) if row[7] else [],
                    status_code=row[8] or 0,
                    content_type=row[9] or "",
                    content_length=row[10] or 0,
                    last_modified=datetime.fromisoformat(row[11]) if row[11] else None,
                    crawl_timestamp=datetime.fromisoformat(row[12]) if row[12] else datetime.now(),
                    depth=row[13] or 0,
                    parent_url=row[14],
                    page_hash=row[15] or "",
                    is_duplicate=bool(row[16])
                )
                pages.append(page)
            
            conn.close()
            return pages
        except Exception as e:
            logger.error(f"Error searching pages: {e}")
            return []

# Global service instance
web_crawler_service = WebCrawlerService()

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
        <title>Web Crawler Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .job { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .status.pending { background: #fff3cd; color: #856404; }
            .status.running { background: #d4edda; color: #155724; }
            .status.completed { background: #d1ecf1; color: #0c5460; }
            .status.failed { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Web Crawler Service</h1>
            
            <h2>Create New Crawl Job</h2>
            <form id="crawlForm">
                <div class="form-group">
                    <label for="name">Job Name:</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div class="form-group">
                    <label for="start_urls">Start URLs (one per line):</label>
                    <textarea id="start_urls" name="start_urls" rows="3" required></textarea>
                </div>
                <div class="form-group">
                    <label for="max_pages">Max Pages:</label>
                    <input type="number" id="max_pages" name="max_pages" value="1000" min="1" max="10000">
                </div>
                <div class="form-group">
                    <label for="max_depth">Max Depth:</label>
                    <input type="number" id="max_depth" name="max_depth" value="5" min="1" max="10">
                </div>
                <div class="form-group">
                    <label for="delay">Delay (seconds):</label>
                    <input type="number" id="delay" name="delay" value="1.0" min="0" max="10" step="0.1">
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="respect_robots" name="respect_robots" checked>
                        Respect robots.txt
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="follow_external" name="follow_external">
                        Follow external links
                    </label>
                </div>
                <button type="submit">Create Crawl Job</button>
            </form>
            
            <h2>Search Crawled Content</h2>
            <form id="searchForm">
                <div class="form-group">
                    <input type="text" id="search_query" name="query" placeholder="Search query..." required>
                </div>
                <button type="submit">Search</button>
            </form>
            
            <div id="results"></div>
        </div>
        
        <script>
            document.getElementById('crawlForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                data.start_urls = data.start_urls.split('\\n').filter(url => url.trim());
                data.respect_robots = document.getElementById('respect_robots').checked;
                data.follow_external = document.getElementById('follow_external').checked;
                
                try {
                    const response = await fetch('/api/crawl-jobs', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    alert(result.success ? 'Crawl job created successfully!' : 'Error: ' + result.error);
                    if (result.success) {
                        e.target.reset();
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            document.getElementById('searchForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const query = document.getElementById('search_query').value;
                
                try {
                    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const results = await response.json();
                    
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '<h3>Search Results</h3>';
                    
                    if (results.length === 0) {
                        resultsDiv.innerHTML += '<p>No results found.</p>';
                        return;
                    }
                    
                    results.forEach(page => {
                        resultsDiv.innerHTML += `
                            <div class="job">
                                <h4><a href="${page.url}" target="_blank">${page.title || page.url}</a></h4>
                                <p>${page.meta_description || page.content.substring(0, 200)}...</p>
                                <small>URL: ${page.url} | Crawled: ${new Date(page.crawl_timestamp).toLocaleString()}</small>
                            </div>
                        `;
                    });
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/api/crawl-jobs', methods=['POST'])
def create_crawl_job():
    """Create a new crawl job."""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('start_urls'):
        return jsonify({'success': False, 'error': 'Name and start URLs are required'})
    
    job = web_crawler_service.create_crawl_job(
        name=data['name'],
        start_urls=data['start_urls'],
        max_pages=int(data.get('max_pages', 1000)),
        max_depth=int(data.get('max_depth', 5)),
        delay=float(data.get('delay', 1.0)),
        respect_robots=data.get('respect_robots', True),
        follow_external=data.get('follow_external', False)
    )
    
    if job:
        return jsonify({'success': True, 'job_id': job.job_id})
    else:
        return jsonify({'success': False, 'error': 'Failed to create crawl job'})

@app.route('/api/crawl-jobs/<job_id>', methods=['GET'])
def get_crawl_job(job_id):
    """Get crawl job details."""
    job = web_crawler_service.get_crawl_job(job_id)
    if job:
        return jsonify({
            'success': True,
            'job': {
                'job_id': job.job_id,
                'name': job.name,
                'status': job.status,
                'pages_crawled': job.pages_crawled,
                'pages_failed': job.pages_failed,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Job not found'})

@app.route('/api/crawl-jobs/<job_id>/stats', methods=['GET'])
def get_crawl_stats(job_id):
    """Get crawl statistics."""
    stats = web_crawler_service.get_crawl_stats(job_id)
    return jsonify({
        'success': True,
        'stats': {
            'total_pages': stats.total_pages,
            'successful_pages': stats.successful_pages,
            'failed_pages': stats.failed_pages,
            'duplicate_pages': stats.duplicate_pages,
            'total_size': stats.total_size,
            'start_time': stats.start_time.isoformat() if stats.start_time else None,
            'end_time': stats.end_time.isoformat() if stats.end_time else None
        }
    })

@app.route('/api/search', methods=['GET'])
def search_pages():
    """Search crawled pages."""
    query = request.args.get('q', '')
    job_id = request.args.get('job_id')
    limit = int(request.args.get('limit', 20))
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter is required'})
    
    pages = web_crawler_service.search_pages(query, job_id, limit)
    
    results = []
    for page in pages:
        results.append({
            'url': page.url,
            'title': page.title,
            'content': page.content[:500] + '...' if len(page.content) > 500 else page.content,
            'meta_description': page.meta_description,
            'crawl_timestamp': page.crawl_timestamp.isoformat(),
            'status_code': page.status_code
        })
    
    return jsonify(results)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'web_crawler'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
