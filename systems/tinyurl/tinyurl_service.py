#!/usr/bin/env python3
"""
TinyURL System - URL Shortening Service

This system provides:
- URL shortening with custom and auto-generated short codes
- URL redirection with analytics tracking
- Rate limiting and abuse prevention
- Admin dashboard for URL management
- API for programmatic access
"""

import hashlib
import random
import string
import time
import json
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, render_template_string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import logging


@dataclass
class URLRecord:
    """Represents a URL record in the system."""
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    click_count: int = 0
    last_clicked: Optional[datetime] = None
    user_id: Optional[str] = None
    is_active: bool = True
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'short_code': self.short_code,
            'original_url': self.original_url,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'click_count': self.click_count,
            'last_clicked': self.last_clicked.isoformat() if self.last_clicked else None,
            'user_id': self.user_id,
            'is_active': self.is_active,
            'metadata': self.metadata
        }


class TinyURLDatabase:
    """Database operations for TinyURL system."""

    def __init__(self, db_path: str = "tinyurl.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # URLs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    short_code TEXT PRIMARY KEY,
                    original_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    click_count INTEGER DEFAULT 0,
                    last_clicked TIMESTAMP,
                    user_id TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT
                )
            ''')
            
            # Analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_code TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    referer TEXT,
                    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    country TEXT,
                    city TEXT,
                    FOREIGN KEY (short_code) REFERENCES urls (short_code)
                )
            ''')
            
            # Users table (for future user management)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            conn.commit()

    def create_url(self, url_record: URLRecord) -> bool:
        """
        Create a new URL record.

        Args:
            url_record: URL record to create

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO urls (short_code, original_url, created_at, expires_at, 
                                    click_count, last_clicked, user_id, is_active, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url_record.short_code,
                    url_record.original_url,
                    url_record.created_at.isoformat(),
                    url_record.expires_at.isoformat() if url_record.expires_at else None,
                    url_record.click_count,
                    url_record.last_clicked.isoformat() if url_record.last_clicked else None,
                    url_record.user_id,
                    url_record.is_active,
                    json.dumps(url_record.metadata)
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            logging.error(f"Error creating URL: {e}")
            return False

    def get_url(self, short_code: str) -> Optional[URLRecord]:
        """
        Get URL record by short code.

        Args:
            short_code: Short code to lookup

        Returns:
            URLRecord if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT short_code, original_url, created_at, expires_at,
                           click_count, last_clicked, user_id, is_active, metadata
                    FROM urls WHERE short_code = ? AND is_active = 1
                ''', (short_code,))
                
                row = cursor.fetchone()
                if row:
                    return URLRecord(
                        short_code=row[0],
                        original_url=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        expires_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        click_count=row[4],
                        last_clicked=datetime.fromisoformat(row[5]) if row[5] else None,
                        user_id=row[6],
                        is_active=bool(row[7]),
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                return None
        except Exception as e:
            logging.error(f"Error getting URL: {e}")
            return None

    def increment_click_count(self, short_code: str) -> bool:
        """
        Increment click count for a URL.

        Args:
            short_code: Short code to update

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE urls 
                    SET click_count = click_count + 1, last_clicked = CURRENT_TIMESTAMP
                    WHERE short_code = ?
                ''', (short_code,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error incrementing click count: {e}")
            return False

    def add_analytics(self, short_code: str, ip_address: str, user_agent: str, 
                     referer: str = None, country: str = None, city: str = None) -> bool:
        """
        Add analytics record for a click.

        Args:
            short_code: Short code that was clicked
            ip_address: IP address of the clicker
            user_agent: User agent string
            referer: Referer header
            country: Country of the clicker
            city: City of the clicker

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO analytics (short_code, ip_address, user_agent, 
                                         referer, country, city)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (short_code, ip_address, user_agent, referer, country, city))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding analytics: {e}")
            return False

    def get_analytics(self, short_code: str, limit: int = 100) -> List[Dict]:
        """
        Get analytics for a short code.

        Args:
            short_code: Short code to get analytics for
            limit: Maximum number of records to return

        Returns:
            List of analytics records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT ip_address, user_agent, referer, clicked_at, country, city
                    FROM analytics 
                    WHERE short_code = ?
                    ORDER BY clicked_at DESC
                    LIMIT ?
                ''', (short_code, limit))
                
                rows = cursor.fetchall()
                return [
                    {
                        'ip_address': row[0],
                        'user_agent': row[1],
                        'referer': row[2],
                        'clicked_at': row[3],
                        'country': row[4],
                        'city': row[5]
                    }
                    for row in rows
                ]
        except Exception as e:
            logging.error(f"Error getting analytics: {e}")
            return []

    def get_user_urls(self, user_id: str) -> List[URLRecord]:
        """
        Get all URLs for a user.

        Args:
            user_id: User ID

        Returns:
            List of URL records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT short_code, original_url, created_at, expires_at,
                           click_count, last_clicked, user_id, is_active, metadata
                    FROM urls WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                rows = cursor.fetchall()
                return [
                    URLRecord(
                        short_code=row[0],
                        original_url=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        expires_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        click_count=row[4],
                        last_clicked=datetime.fromisoformat(row[5]) if row[5] else None,
                        user_id=row[6],
                        is_active=bool(row[7]),
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                    for row in rows
                ]
        except Exception as e:
            logging.error(f"Error getting user URLs: {e}")
            return []

    def delete_url(self, short_code: str, user_id: str = None) -> bool:
        """
        Delete a URL (soft delete by setting is_active=False).

        Args:
            short_code: Short code to delete
            user_id: User ID (for authorization)

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute('''
                        UPDATE urls SET is_active = 0 
                        WHERE short_code = ? AND user_id = ?
                    ''', (short_code, user_id))
                else:
                    cursor.execute('''
                        UPDATE urls SET is_active = 0 
                        WHERE short_code = ?
                    ''', (short_code,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting URL: {e}")
            return False


class TinyURLGenerator:
    """Generates short codes for URLs."""

    def __init__(self, length: int = 6):
        """
        Initialize generator.

        Args:
            length: Length of generated short codes
        """
        self.length = length
        self.chars = string.ascii_letters + string.digits

    def generate_short_code(self) -> str:
        """
        Generate a random short code.

        Returns:
            Random short code
        """
        return ''.join(random.choice(self.chars) for _ in range(self.length))

    def generate_custom_code(self, custom_code: str) -> str:
        """
        Generate a custom short code (with validation).

        Args:
            custom_code: Custom code to use

        Returns:
            Validated custom code
        """
        # Remove invalid characters and convert to lowercase
        cleaned = ''.join(c for c in custom_code.lower() if c in self.chars)
        return cleaned[:self.length].ljust(self.length, random.choice(self.chars))

    def generate_from_url(self, url: str) -> str:
        """
        Generate a deterministic short code from URL hash.

        Args:
            url: Original URL

        Returns:
            Deterministic short code
        """
        hash_obj = hashlib.md5(url.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hex to our character set
        result = []
        for i in range(0, len(hash_hex), 2):
            hex_pair = hash_hex[i:i+2]
            index = int(hex_pair, 16) % len(self.chars)
            result.append(self.chars[index])
        
        return ''.join(result[:self.length])


class TinyURLService:
    """Main TinyURL service."""

    def __init__(self, db_path: str = "tinyurl.db", redis_url: str = None):
        """
        Initialize TinyURL service.

        Args:
            db_path: Path to SQLite database
            redis_url: Redis URL for caching
        """
        self.db = TinyURLDatabase(db_path)
        self.generator = TinyURLGenerator()
        self.redis_client = None
        
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logging.warning(f"Failed to connect to Redis: {e}")

    def shorten_url(self, original_url: str, custom_code: str = None, 
                   expires_in_days: int = None, user_id: str = None) -> Dict:
        """
        Shorten a URL.

        Args:
            original_url: Original URL to shorten
            custom_code: Optional custom short code
            expires_in_days: Optional expiration in days
            user_id: Optional user ID

        Returns:
            Dictionary with result
        """
        # Validate URL
        if not self._is_valid_url(original_url):
            return {'success': False, 'error': 'Invalid URL'}

        # Generate short code
        if custom_code:
            short_code = self.generator.generate_custom_code(custom_code)
        else:
            short_code = self.generator.generate_short_code()

        # Check if short code already exists
        existing = self.db.get_url(short_code)
        if existing:
            if custom_code:
                return {'success': False, 'error': 'Custom code already exists'}
            else:
                # Generate a new random code
                attempts = 0
                while existing and attempts < 10:
                    short_code = self.generator.generate_short_code()
                    existing = self.db.get_url(short_code)
                    attempts += 1
                
                if existing:
                    return {'success': False, 'error': 'Unable to generate unique code'}

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        # Create URL record
        url_record = URLRecord(
            short_code=short_code,
            original_url=original_url,
            created_at=datetime.now(),
            expires_at=expires_at,
            user_id=user_id
        )

        # Save to database
        if self.db.create_url(url_record):
            # Cache in Redis if available
            if self.redis_client:
                try:
                    self.redis_client.setex(
                        f"url:{short_code}",
                        3600,  # 1 hour cache
                        json.dumps(url_record.to_dict())
                    )
                except Exception as e:
                    logging.warning(f"Failed to cache URL: {e}")

            return {
                'success': True,
                'short_code': short_code,
                'short_url': f"http://localhost:5000/{short_code}",
                'original_url': original_url,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
        else:
            return {'success': False, 'error': 'Failed to create URL'}

    def expand_url(self, short_code: str) -> Optional[str]:
        """
        Expand a short code to original URL.

        Args:
            short_code: Short code to expand

        Returns:
            Original URL if found, None otherwise
        """
        # Check cache first
        if self.redis_client:
            try:
                cached = self.redis_client.get(f"url:{short_code}")
                if cached:
                    url_data = json.loads(cached)
                    return url_data['original_url']
            except Exception as e:
                logging.warning(f"Failed to get from cache: {e}")

        # Get from database
        url_record = self.db.get_url(short_code)
        if url_record:
            # Check expiration
            if url_record.expires_at and url_record.expires_at < datetime.now():
                return None
            
            # Update click count
            self.db.increment_click_count(short_code)
            
            # Add analytics
            self.db.add_analytics(
                short_code=short_code,
                ip_address=request.remote_addr if request else 'unknown',
                user_agent=request.headers.get('User-Agent', 'unknown') if request else 'unknown',
                referer=request.headers.get('Referer') if request else None
            )
            
            return url_record.original_url
        
        return None

    def get_url_info(self, short_code: str) -> Optional[Dict]:
        """
        Get information about a short URL.

        Args:
            short_code: Short code to get info for

        Returns:
            URL information dictionary
        """
        url_record = self.db.get_url(short_code)
        if url_record:
            analytics = self.db.get_analytics(short_code, limit=10)
            return {
                **url_record.to_dict(),
                'recent_clicks': analytics
            }
        return None

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return pattern.match(url) is not None


# Flask application
app = Flask(__name__)
# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Initialize service
tinyurl_service = TinyURLService()


@app.route('/')
def index():
    """Home page with URL shortening form."""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>TinyURL Service</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 4px; }
            .error { background: #f8d7da; color: #721c24; }
            .success { background: #d4edda; color: #155724; }
        </style>
    </head>
    <body>
        <h1>TinyURL Service</h1>
        <form method="POST" action="/shorten">
            <div class="form-group">
                <label for="url">Enter URL to shorten:</label>
                <input type="text" id="url" name="url" placeholder="https://example.com" required>
            </div>
            <div class="form-group">
                <label for="custom_code">Custom short code (optional):</label>
                <input type="text" id="custom_code" name="custom_code" placeholder="mycode">
            </div>
            <button type="submit">Shorten URL</button>
        </form>
        
        <div id="result"></div>
        
        <script>
            document.querySelector('form').addEventListener('submit', async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const response = await fetch('/shorten', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                const resultDiv = document.getElementById('result');
                if (result.success) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <h3>Success!</h3>
                            <p><strong>Short URL:</strong> <a href="${result.short_url}" target="_blank">${result.short_url}</a></p>
                            <p><strong>Original URL:</strong> ${result.original_url}</p>
                            <p><strong>Short Code:</strong> ${result.short_code}</p>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <h3>Error</h3>
                            <p>${result.error}</p>
                        </div>
                    `;
                }
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)


@app.route('/shorten', methods=['POST'])
@limiter.limit("10 per minute")
def shorten_url():
    """API endpoint to shorten URLs."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    original_url = data.get('url')
    custom_code = data.get('custom_code')
    expires_in_days = data.get('expires_in_days')
    user_id = data.get('user_id')

    if not original_url:
        return jsonify({'success': False, 'error': 'URL is required'})

    result = tinyurl_service.shorten_url(
        original_url=original_url,
        custom_code=custom_code,
        expires_in_days=int(expires_in_days) if expires_in_days else None,
        user_id=user_id
    )

    return jsonify(result)


@app.route('/<short_code>')
def redirect_url(short_code):
    """Redirect short code to original URL."""
    original_url = tinyurl_service.expand_url(short_code)
    
    if original_url:
        return redirect(original_url)
    else:
        return jsonify({'error': 'Short URL not found or expired'}), 404


@app.route('/api/info/<short_code>')
def get_url_info(short_code):
    """Get information about a short URL."""
    info = tinyurl_service.get_url_info(short_code)
    
    if info:
        return jsonify({'success': True, 'data': info})
    else:
        return jsonify({'success': False, 'error': 'Short URL not found'}), 404


@app.route('/api/analytics/<short_code>')
@limiter.limit("100 per hour")
def get_analytics(short_code):
    """Get analytics for a short URL."""
    analytics = tinyurl_service.db.get_analytics(short_code, limit=100)
    return jsonify({'success': True, 'data': analytics})


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=5000)
