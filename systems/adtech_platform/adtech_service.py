#!/usr/bin/env python3
"""
AdTech Platform Service

A comprehensive advertising technology platform for managing
ad campaigns, targeting, bidding, analytics, and revenue optimization
with support for various ad formats and real-time bidding.
"""

import sqlite3
import hashlib
import time
import json
import logging
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignStatus(Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AdFormat(Enum):
    """Ad format enumeration."""
    BANNER = "banner"
    VIDEO = "video"
    NATIVE = "native"
    DISPLAY = "display"
    MOBILE = "mobile"
    RICH_MEDIA = "rich_media"

class BidStrategy(Enum):
    """Bid strategy enumeration."""
    CPC = "cpc"  # Cost Per Click
    CPM = "cpm"  # Cost Per Mille
    CPA = "cpa"  # Cost Per Acquisition
    CPV = "cpv"  # Cost Per View
    TARGET_CPA = "target_cpa"
    TARGET_ROAS = "target_roas"

class TargetingType(Enum):
    """Targeting type enumeration."""
    DEMOGRAPHIC = "demographic"
    GEOGRAPHIC = "geographic"
    BEHAVIORAL = "behavioral"
    CONTEXTUAL = "contextual"
    LOOKALIKE = "lookalike"
    CUSTOM_AUDIENCE = "custom_audience"

class AdStatus(Enum):
    """Ad status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    DISAPPROVED = "disapproved"

@dataclass
class Advertiser:
    """Advertiser model."""
    advertiser_id: str
    name: str
    email: str
    company: str
    industry: str
    budget: float = 0.0
    currency: str = "USD"
    billing_address: str = ""
    phone: str = ""
    website: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class Campaign:
    """Campaign model."""
    campaign_id: str
    advertiser_id: str
    name: str
    description: str
    status: CampaignStatus = CampaignStatus.DRAFT
    budget: float = 0.0
    daily_budget: float = 0.0
    bid_strategy: BidStrategy = BidStrategy.CPC
    target_cpa: float = 0.0
    target_roas: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class AdGroup:
    """Ad group model."""
    ad_group_id: str
    campaign_id: str
    name: str
    description: str
    bid_amount: float = 0.0
    status: AdStatus = AdStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Ad:
    """Ad model."""
    ad_id: str
    ad_group_id: str
    name: str
    headline: str
    description: str
    display_url: str
    final_url: str
    ad_format: AdFormat = AdFormat.BANNER
    status: AdStatus = AdStatus.ACTIVE
    image_url: str = ""
    video_url: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Targeting:
    """Targeting model."""
    targeting_id: str
    ad_group_id: str
    targeting_type: TargetingType
    value: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class BidRequest:
    """Bid request model."""
    bid_request_id: str
    ad_group_id: str
    user_id: str
    page_url: str
    user_agent: str
    ip_address: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class BidResponse:
    """Bid response model."""
    bid_response_id: str
    bid_request_id: str
    ad_id: str
    bid_price: float
    currency: str = "USD"
    win: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AdImpression:
    """Ad impression model."""
    impression_id: str
    ad_id: str
    user_id: str
    page_url: str
    timestamp: datetime = field(default_factory=datetime.now)
    cost: float = 0.0
    revenue: float = 0.0

@dataclass
class AdClick:
    """Ad click model."""
    click_id: str
    impression_id: str
    ad_id: str
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    cost: float = 0.0
    revenue: float = 0.0

@dataclass
class AdConversion:
    """Ad conversion model."""
    conversion_id: str
    click_id: str
    ad_id: str
    user_id: str
    conversion_value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class AdTechDatabase:
    """Database operations for adtech platform."""
    
    def __init__(self, db_path: str = "adtech.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Advertisers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS advertisers (
                advertiser_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                company TEXT NOT NULL,
                industry TEXT NOT NULL,
                budget REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'USD',
                billing_address TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                website TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                campaign_id TEXT PRIMARY KEY,
                advertiser_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                budget REAL DEFAULT 0.0,
                daily_budget REAL DEFAULT 0.0,
                bid_strategy TEXT DEFAULT 'cpc',
                target_cpa REAL DEFAULT 0.0,
                target_roas REAL DEFAULT 0.0,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (advertiser_id) REFERENCES advertisers (advertiser_id)
            )
        ''')
        
        # Ad groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ad_groups (
                ad_group_id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                bid_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id)
            )
        ''')
        
        # Ads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                ad_id TEXT PRIMARY KEY,
                ad_group_id TEXT NOT NULL,
                name TEXT NOT NULL,
                headline TEXT NOT NULL,
                description TEXT NOT NULL,
                display_url TEXT NOT NULL,
                final_url TEXT NOT NULL,
                ad_format TEXT DEFAULT 'banner',
                status TEXT DEFAULT 'active',
                image_url TEXT DEFAULT '',
                video_url TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ad_group_id) REFERENCES ad_groups (ad_group_id)
            )
        ''')
        
        # Targeting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS targeting (
                targeting_id TEXT PRIMARY KEY,
                ad_group_id TEXT NOT NULL,
                targeting_type TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ad_group_id) REFERENCES ad_groups (ad_group_id)
            )
        ''')
        
        # Bid requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_requests (
                bid_request_id TEXT PRIMARY KEY,
                ad_group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                page_url TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ad_group_id) REFERENCES ad_groups (ad_group_id)
            )
        ''')
        
        # Bid responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_responses (
                bid_response_id TEXT PRIMARY KEY,
                bid_request_id TEXT NOT NULL,
                ad_id TEXT NOT NULL,
                bid_price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                win BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bid_request_id) REFERENCES bid_requests (bid_request_id),
                FOREIGN KEY (ad_id) REFERENCES ads (ad_id)
            )
        ''')
        
        # Ad impressions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ad_impressions (
                impression_id TEXT PRIMARY KEY,
                ad_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                page_url TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cost REAL DEFAULT 0.0,
                revenue REAL DEFAULT 0.0,
                FOREIGN KEY (ad_id) REFERENCES ads (ad_id)
            )
        ''')
        
        # Ad clicks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ad_clicks (
                click_id TEXT PRIMARY KEY,
                impression_id TEXT NOT NULL,
                ad_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cost REAL DEFAULT 0.0,
                revenue REAL DEFAULT 0.0,
                FOREIGN KEY (impression_id) REFERENCES ad_impressions (impression_id),
                FOREIGN KEY (ad_id) REFERENCES ads (ad_id)
            )
        ''')
        
        # Ad conversions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ad_conversions (
                conversion_id TEXT PRIMARY KEY,
                click_id TEXT NOT NULL,
                ad_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                conversion_value REAL DEFAULT 0.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (click_id) REFERENCES ad_clicks (click_id),
                FOREIGN KEY (ad_id) REFERENCES ads (ad_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_advertiser(self, advertiser: Advertiser) -> bool:
        """Save advertiser to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO advertisers 
                (advertiser_id, name, email, company, industry, budget, currency,
                 billing_address, phone, website, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                advertiser.advertiser_id, advertiser.name, advertiser.email,
                advertiser.company, advertiser.industry, advertiser.budget,
                advertiser.currency, advertiser.billing_address, advertiser.phone,
                advertiser.website, advertiser.created_at, advertiser.updated_at,
                advertiser.is_active
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving advertiser: {e}")
            return False
    
    def get_advertiser(self, advertiser_id: str) -> Optional[Advertiser]:
        """Get advertiser by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM advertisers WHERE advertiser_id = ?', (advertiser_id,))
            row = cursor.fetchone()
            
            if row:
                advertiser = Advertiser(
                    advertiser_id=row[0],
                    name=row[1],
                    email=row[2],
                    company=row[3],
                    industry=row[4],
                    budget=row[5] or 0.0,
                    currency=row[6] or "USD",
                    billing_address=row[7] or "",
                    phone=row[8] or "",
                    website=row[9] or "",
                    created_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[11]) if row[11] else datetime.now(),
                    is_active=bool(row[12])
                )
                conn.close()
                return advertiser
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting advertiser: {e}")
            return None
    
    def save_campaign(self, campaign: Campaign) -> bool:
        """Save campaign to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO campaigns 
                (campaign_id, advertiser_id, name, description, status, budget,
                 daily_budget, bid_strategy, target_cpa, target_roas, start_date,
                 end_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                campaign.campaign_id, campaign.advertiser_id, campaign.name,
                campaign.description, campaign.status.value, campaign.budget,
                campaign.daily_budget, campaign.bid_strategy.value,
                campaign.target_cpa, campaign.target_roas, campaign.start_date,
                campaign.end_date, campaign.created_at, campaign.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving campaign: {e}")
            return False
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM campaigns WHERE campaign_id = ?', (campaign_id,))
            row = cursor.fetchone()
            
            if row:
                campaign = Campaign(
                    campaign_id=row[0],
                    advertiser_id=row[1],
                    name=row[2],
                    description=row[3],
                    status=CampaignStatus(row[4]),
                    budget=row[5] or 0.0,
                    daily_budget=row[6] or 0.0,
                    bid_strategy=BidStrategy(row[7]),
                    target_cpa=row[8] or 0.0,
                    target_roas=row[9] or 0.0,
                    start_date=datetime.fromisoformat(row[10]) if row[10] else None,
                    end_date=datetime.fromisoformat(row[11]) if row[11] else None,
                    created_at=datetime.fromisoformat(row[12]) if row[12] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[13]) if row[13] else datetime.now()
                )
                conn.close()
                return campaign
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting campaign: {e}")
            return None
    
    def get_campaigns_by_advertiser(self, advertiser_id: str) -> List[Campaign]:
        """Get campaigns by advertiser."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM campaigns 
                WHERE advertiser_id = ?
                ORDER BY created_at DESC
            ''', (advertiser_id,))
            
            campaigns = []
            for row in cursor.fetchall():
                campaign = Campaign(
                    campaign_id=row[0],
                    advertiser_id=row[1],
                    name=row[2],
                    description=row[3],
                    status=CampaignStatus(row[4]),
                    budget=row[5] or 0.0,
                    daily_budget=row[6] or 0.0,
                    bid_strategy=BidStrategy(row[7]),
                    target_cpa=row[8] or 0.0,
                    target_roas=row[9] or 0.0,
                    start_date=datetime.fromisoformat(row[10]) if row[10] else None,
                    end_date=datetime.fromisoformat(row[11]) if row[11] else None,
                    created_at=datetime.fromisoformat(row[12]) if row[12] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[13]) if row[13] else datetime.now()
                )
                campaigns.append(campaign)
            
            conn.close()
            return campaigns
        except Exception as e:
            logger.error(f"Error getting campaigns by advertiser: {e}")
            return []
    
    def save_ad_group(self, ad_group: AdGroup) -> bool:
        """Save ad group to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ad_groups 
                (ad_group_id, campaign_id, name, description, bid_amount, status,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ad_group.ad_group_id, ad_group.campaign_id, ad_group.name,
                ad_group.description, ad_group.bid_amount, ad_group.status.value,
                ad_group.created_at, ad_group.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving ad group: {e}")
            return False
    
    def get_ad_groups_by_campaign(self, campaign_id: str) -> List[AdGroup]:
        """Get ad groups by campaign."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM ad_groups 
                WHERE campaign_id = ?
                ORDER BY created_at DESC
            ''', (campaign_id,))
            
            ad_groups = []
            for row in cursor.fetchall():
                ad_group = AdGroup(
                    ad_group_id=row[0],
                    campaign_id=row[1],
                    name=row[2],
                    description=row[3],
                    bid_amount=row[4] or 0.0,
                    status=AdStatus(row[5]),
                    created_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now()
                )
                ad_groups.append(ad_group)
            
            conn.close()
            return ad_groups
        except Exception as e:
            logger.error(f"Error getting ad groups by campaign: {e}")
            return []
    
    def save_ad(self, ad: Ad) -> bool:
        """Save ad to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ads 
                (ad_id, ad_group_id, name, headline, description, display_url,
                 final_url, ad_format, status, image_url, video_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ad.ad_id, ad.ad_group_id, ad.name, ad.headline, ad.description,
                ad.display_url, ad.final_url, ad.ad_format.value, ad.status.value,
                ad.image_url, ad.video_url, ad.created_at, ad.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving ad: {e}")
            return False
    
    def get_ads_by_ad_group(self, ad_group_id: str) -> List[Ad]:
        """Get ads by ad group."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM ads 
                WHERE ad_group_id = ?
                ORDER BY created_at DESC
            ''', (ad_group_id,))
            
            ads = []
            for row in cursor.fetchall():
                ad = Ad(
                    ad_id=row[0],
                    ad_group_id=row[1],
                    name=row[2],
                    headline=row[3],
                    description=row[4],
                    display_url=row[5],
                    final_url=row[6],
                    ad_format=AdFormat(row[7]),
                    status=AdStatus(row[8]),
                    image_url=row[9] or "",
                    video_url=row[10] or "",
                    created_at=datetime.fromisoformat(row[11]) if row[11] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[12]) if row[12] else datetime.now()
                )
                ads.append(ad)
            
            conn.close()
            return ads
        except Exception as e:
            logger.error(f"Error getting ads by ad group: {e}")
            return []
    
    def save_bid_request(self, bid_request: BidRequest) -> bool:
        """Save bid request to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO bid_requests 
                (bid_request_id, ad_group_id, user_id, page_url, user_agent,
                 ip_address, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                bid_request.bid_request_id, bid_request.ad_group_id, bid_request.user_id,
                bid_request.page_url, bid_request.user_agent, bid_request.ip_address,
                bid_request.timestamp
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving bid request: {e}")
            return False
    
    def save_bid_response(self, bid_response: BidResponse) -> bool:
        """Save bid response to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO bid_responses 
                (bid_response_id, bid_request_id, ad_id, bid_price, currency, win, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                bid_response.bid_response_id, bid_response.bid_request_id,
                bid_response.ad_id, bid_response.bid_price, bid_response.currency,
                bid_response.win, bid_response.timestamp
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving bid response: {e}")
            return False
    
    def save_impression(self, impression: AdImpression) -> bool:
        """Save ad impression to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ad_impressions 
                (impression_id, ad_id, user_id, page_url, timestamp, cost, revenue)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                impression.impression_id, impression.ad_id, impression.user_id,
                impression.page_url, impression.timestamp, impression.cost,
                impression.revenue
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving impression: {e}")
            return False
    
    def save_click(self, click: AdClick) -> bool:
        """Save ad click to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ad_clicks 
                (click_id, impression_id, ad_id, user_id, timestamp, cost, revenue)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                click.click_id, click.impression_id, click.ad_id, click.user_id,
                click.timestamp, click.cost, click.revenue
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving click: {e}")
            return False
    
    def save_conversion(self, conversion: AdConversion) -> bool:
        """Save ad conversion to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ad_conversions 
                (conversion_id, click_id, ad_id, user_id, conversion_value, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                conversion.conversion_id, conversion.ad_id, conversion.click_id,
                conversion.user_id, conversion.conversion_value, conversion.timestamp
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving conversion: {e}")
            return False

class AdTechService:
    """AdTech platform service with campaign management and real-time bidding."""
    
    def __init__(self, db_path: str = "adtech.db"):
        self.db = AdTechDatabase(db_path)
        self.initialize_default_data()
    
    def initialize_default_data(self):
        """Initialize default advertisers and campaigns."""
        # Create default advertiser
        advertiser = Advertiser(
            advertiser_id="adv_001",
            name="TechCorp Inc",
            email="ads@techcorp.com",
            company="TechCorp Inc",
            industry="Technology",
            budget=10000.0,
            currency="USD"
        )
        self.db.save_advertiser(advertiser)
        
        # Create default campaign
        campaign = Campaign(
            campaign_id="camp_001",
            advertiser_id="adv_001",
            name="TechCorp Brand Campaign",
            description="Brand awareness campaign for TechCorp",
            status=CampaignStatus.ACTIVE,
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        self.db.save_campaign(campaign)
        
        # Create default ad group
        ad_group = AdGroup(
            ad_group_id="ag_001",
            campaign_id="camp_001",
            name="TechCorp Display Ads",
            description="Display advertising for TechCorp",
            bid_amount=1.50,
            status=AdStatus.ACTIVE
        )
        self.db.save_ad_group(ad_group)
        
        # Create default ad
        ad = Ad(
            ad_id="ad_001",
            ad_group_id="ag_001",
            name="TechCorp Banner Ad",
            headline="Revolutionary Technology Solutions",
            description="Discover our cutting-edge technology solutions for your business needs.",
            display_url="techcorp.com",
            final_url="https://techcorp.com/solutions",
            ad_format=AdFormat.BANNER,
            status=AdStatus.ACTIVE,
            image_url="https://techcorp.com/images/banner.jpg"
        )
        self.db.save_ad(ad)
    
    def generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def create_advertiser(self, name: str, email: str, company: str, industry: str,
                         budget: float = 0.0, currency: str = "USD") -> Optional[Advertiser]:
        """Create a new advertiser."""
        advertiser_id = self.generate_id("adv")
        
        advertiser = Advertiser(
            advertiser_id=advertiser_id,
            name=name,
            email=email,
            company=company,
            industry=industry,
            budget=budget,
            currency=currency
        )
        
        try:
            if self.db.save_advertiser(advertiser):
                return advertiser
            return None
        except Exception as e:
            logger.error(f"Error creating advertiser: {e}")
            return None
    
    def get_advertiser(self, advertiser_id: str) -> Optional[Advertiser]:
        """Get advertiser by ID."""
        return self.db.get_advertiser(advertiser_id)
    
    def create_campaign(self, advertiser_id: str, name: str, description: str,
                       budget: float, daily_budget: float, bid_strategy: BidStrategy,
                       target_cpa: float = 0.0, target_roas: float = 0.0) -> Optional[Campaign]:
        """Create a new campaign."""
        # Check if advertiser exists
        advertiser = self.db.get_advertiser(advertiser_id)
        if not advertiser:
            return None
        
        campaign_id = self.generate_id("camp")
        
        campaign = Campaign(
            campaign_id=campaign_id,
            advertiser_id=advertiser_id,
            name=name,
            description=description,
            budget=budget,
            daily_budget=daily_budget,
            bid_strategy=bid_strategy,
            target_cpa=target_cpa,
            target_roas=target_roas,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        try:
            if self.db.save_campaign(campaign):
                return campaign
            return None
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return None
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        return self.db.get_campaign(campaign_id)
    
    def get_campaigns_by_advertiser(self, advertiser_id: str) -> List[Campaign]:
        """Get campaigns by advertiser."""
        return self.db.get_campaigns_by_advertiser(advertiser_id)
    
    def create_ad_group(self, campaign_id: str, name: str, description: str,
                       bid_amount: float) -> Optional[AdGroup]:
        """Create a new ad group."""
        # Check if campaign exists
        campaign = self.db.get_campaign(campaign_id)
        if not campaign:
            return None
        
        ad_group_id = self.generate_id("ag")
        
        ad_group = AdGroup(
            ad_group_id=ad_group_id,
            campaign_id=campaign_id,
            name=name,
            description=description,
            bid_amount=bid_amount
        )
        
        try:
            if self.db.save_ad_group(ad_group):
                return ad_group
            return None
        except Exception as e:
            logger.error(f"Error creating ad group: {e}")
            return None
    
    def get_ad_groups_by_campaign(self, campaign_id: str) -> List[AdGroup]:
        """Get ad groups by campaign."""
        return self.db.get_ad_groups_by_campaign(campaign_id)
    
    def get_ad_group(self, ad_group_id: str) -> Optional[AdGroup]:
        """Get ad group by ID."""
        # This is a simplified implementation - in real implementation would have proper ad group lookup
        # For now, we'll check if any ads exist for this ad group
        ads = self.db.get_ads_by_ad_group(ad_group_id)
        if ads:
            # If ads exist, we can assume the ad group exists
            # In a real implementation, we'd have a proper ad group table lookup
            return AdGroup(
                ad_group_id=ad_group_id,
                campaign_id="unknown",  # We don't have this info in this simplified version
                name="Unknown",
                description="Unknown"
            )
        return None
    
    def create_ad(self, ad_group_id: str, name: str, headline: str, description: str,
                 display_url: str, final_url: str, ad_format: AdFormat = AdFormat.BANNER,
                 image_url: str = "", video_url: str = "") -> Optional[Ad]:
        """Create a new ad."""
        # For now, we'll skip validation to avoid circular dependency
        # In a real implementation, we'd have proper foreign key constraints
        ad_id = self.generate_id("ad")
        
        ad = Ad(
            ad_id=ad_id,
            ad_group_id=ad_group_id,
            name=name,
            headline=headline,
            description=description,
            display_url=display_url,
            final_url=final_url,
            ad_format=ad_format,
            image_url=image_url,
            video_url=video_url
        )
        
        try:
            if self.db.save_ad(ad):
                return ad
            return None
        except Exception as e:
            logger.error(f"Error creating ad: {e}")
            return None
    
    def get_ads_by_ad_group(self, ad_group_id: str) -> List[Ad]:
        """Get ads by ad group."""
        return self.db.get_ads_by_ad_group(ad_group_id)
    
    def process_bid_request(self, ad_group_id: str, user_id: str, page_url: str,
                           user_agent: str, ip_address: str) -> Optional[BidResponse]:
        """Process a bid request and return bid response."""
        try:
            bid_request_id = self.generate_id("bid_req")

            bid_request = BidRequest(
                bid_request_id=bid_request_id,
                ad_group_id=ad_group_id,
                user_id=user_id,
                page_url=page_url,
                user_agent=user_agent,
                ip_address=ip_address
            )

            if not self.db.save_bid_request(bid_request):
                return None

            # Get ads for the ad group
            ads = self.get_ads_by_ad_group(ad_group_id)
            if not ads:
                return None

            # Select best ad (simple logic - in real implementation would be more complex)
            selected_ad = ads[0]  # For simplicity, select first ad

            # Calculate bid price (simple logic)
            bid_price = random.uniform(0.50, 2.00)  # Random bid between $0.50 and $2.00

            bid_response_id = self.generate_id("bid_resp")
            bid_response = BidResponse(
                bid_response_id=bid_response_id,
                bid_request_id=bid_request_id,
                ad_id=selected_ad.ad_id,
                bid_price=bid_price,
                win=True  # For simplicity, always win
            )

            if self.db.save_bid_response(bid_response):
                return bid_response
            return None
        except Exception as e:
            logger.error(f"Error processing bid request: {e}")
            return None
    
    def record_impression(self, ad_id: str, user_id: str, page_url: str,
                         cost: float = 0.0, revenue: float = 0.0) -> Optional[AdImpression]:
        """Record an ad impression."""
        try:
            impression_id = self.generate_id("imp")

            impression = AdImpression(
                impression_id=impression_id,
                ad_id=ad_id,
                user_id=user_id,
                page_url=page_url,
                cost=cost,
                revenue=revenue
            )

            if self.db.save_impression(impression):
                return impression
            return None
        except Exception as e:
            logger.error(f"Error recording impression: {e}")
            return None
    
    def record_click(self, impression_id: str, ad_id: str, user_id: str,
                    cost: float = 0.0, revenue: float = 0.0) -> Optional[AdClick]:
        """Record an ad click."""
        try:
            click_id = self.generate_id("click")

            click = AdClick(
                click_id=click_id,
                impression_id=impression_id,
                ad_id=ad_id,
                user_id=user_id,
                cost=cost,
                revenue=revenue
            )

            if self.db.save_click(click):
                return click
            return None
        except Exception as e:
            logger.error(f"Error recording click: {e}")
            return None
    
    def record_conversion(self, click_id: str, ad_id: str, user_id: str,
                         conversion_value: float = 0.0) -> Optional[AdConversion]:
        """Record an ad conversion."""
        try:
            conversion_id = self.generate_id("conv")

            conversion = AdConversion(
                conversion_id=conversion_id,
                click_id=click_id,
                ad_id=ad_id,
                user_id=user_id,
                conversion_value=conversion_value
            )

            if self.db.save_conversion(conversion):
                return conversion
            return None
        except Exception as e:
            logger.error(f"Error recording conversion: {e}")
            return None
    
    def get_campaign_analytics(self, campaign_id: str, start_date: datetime = None,
                              end_date: datetime = None) -> Dict[str, Any]:
        """Get campaign analytics."""
        # This would require complex queries in a real implementation
        # For now, return mock data
        return {
            'campaign_id': campaign_id,
            'impressions': random.randint(1000, 10000),
            'clicks': random.randint(50, 500),
            'conversions': random.randint(5, 50),
            'cost': random.uniform(100.0, 1000.0),
            'revenue': random.uniform(200.0, 2000.0),
            'ctr': random.uniform(0.01, 0.05),  # Click-through rate
            'conversion_rate': random.uniform(0.01, 0.10),  # Conversion rate
            'cpc': random.uniform(0.50, 2.00),  # Cost per click
            'cpa': random.uniform(10.0, 50.0),  # Cost per acquisition
            'roas': random.uniform(1.5, 4.0)  # Return on ad spend
        }
    
    def get_advertiser_analytics(self, advertiser_id: str, start_date: datetime = None,
                                end_date: datetime = None) -> Dict[str, Any]:
        """Get advertiser analytics."""
        campaigns = self.get_campaigns_by_advertiser(advertiser_id)
        
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        total_cost = 0.0
        total_revenue = 0.0
        
        for campaign in campaigns:
            analytics = self.get_campaign_analytics(campaign.campaign_id, start_date, end_date)
            total_impressions += analytics['impressions']
            total_clicks += analytics['clicks']
            total_conversions += analytics['conversions']
            total_cost += analytics['cost']
            total_revenue += analytics['revenue']
        
        return {
            'advertiser_id': advertiser_id,
            'total_campaigns': len(campaigns),
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'total_conversions': total_conversions,
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'overall_ctr': total_clicks / total_impressions if total_impressions > 0 else 0,
            'overall_conversion_rate': total_conversions / total_clicks if total_clicks > 0 else 0,
            'overall_roas': total_revenue / total_cost if total_cost > 0 else 0
        }

# Global service instance
adtech_service = AdTechService()

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
        <title>AdTech Platform</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .campaign { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .campaign h3 { margin-top: 0; }
            .campaign-meta { color: #666; font-size: 14px; }
            .tabs { border-bottom: 1px solid #ddd; margin-bottom: 20px; }
            .tab { display: inline-block; padding: 10px 20px; cursor: pointer; border-bottom: 2px solid transparent; }
            .tab.active { border-bottom-color: #007cba; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .analytics { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 10px 0; }
            .metric { display: inline-block; margin-right: 20px; }
            .metric-value { font-size: 24px; font-weight: bold; color: #007cba; }
            .metric-label { font-size: 12px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AdTech Platform</h1>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('advertisers')">Advertisers</div>
                <div class="tab" onclick="showTab('campaigns')">Campaigns</div>
                <div class="tab" onclick="showTab('analytics')">Analytics</div>
                <div class="tab" onclick="showTab('bidding')">Real-time Bidding</div>
            </div>
            
            <div id="advertisers" class="tab-content active">
                <h2>Advertiser Management</h2>
                <form id="advertiserForm">
                    <div class="form-group">
                        <label for="name">Company Name:</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="company">Company:</label>
                        <input type="text" id="company" name="company" required>
                    </div>
                    <div class="form-group">
                        <label for="industry">Industry:</label>
                        <select id="industry" name="industry" required>
                            <option value="Technology">Technology</option>
                            <option value="Healthcare">Healthcare</option>
                            <option value="Finance">Finance</option>
                            <option value="Retail">Retail</option>
                            <option value="Education">Education</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="budget">Budget:</label>
                        <input type="number" id="budget" name="budget" step="0.01" min="0">
                    </div>
                    <button type="submit">Create Advertiser</button>
                </form>
            </div>
            
            <div id="campaigns" class="tab-content">
                <h2>Campaign Management</h2>
                <form id="campaignForm">
                    <div class="form-group">
                        <label for="advertiser_id">Advertiser ID:</label>
                        <input type="text" id="advertiser_id" name="advertiser_id" required>
                    </div>
                    <div class="form-group">
                        <label for="campaign_name">Campaign Name:</label>
                        <input type="text" id="campaign_name" name="campaign_name" required>
                    </div>
                    <div class="form-group">
                        <label for="campaign_description">Description:</label>
                        <textarea id="campaign_description" name="campaign_description" rows="3"></textarea>
                    </div>
                    <div class="form-group">
                        <label for="budget">Budget:</label>
                        <input type="number" id="budget" name="budget" step="0.01" min="0" required>
                    </div>
                    <div class="form-group">
                        <label for="daily_budget">Daily Budget:</label>
                        <input type="number" id="daily_budget" name="daily_budget" step="0.01" min="0" required>
                    </div>
                    <div class="form-group">
                        <label for="bid_strategy">Bid Strategy:</label>
                        <select id="bid_strategy" name="bid_strategy" required>
                            <option value="cpc">Cost Per Click (CPC)</option>
                            <option value="cpm">Cost Per Mille (CPM)</option>
                            <option value="cpa">Cost Per Acquisition (CPA)</option>
                            <option value="cpv">Cost Per View (CPV)</option>
                        </select>
                    </div>
                    <button type="submit">Create Campaign</button>
                </form>
            </div>
            
            <div id="analytics" class="tab-content">
                <h2>Analytics Dashboard</h2>
                <div class="form-group">
                    <label for="analytics_campaign_id">Campaign ID:</label>
                    <input type="text" id="analytics_campaign_id" name="analytics_campaign_id">
                    <button onclick="loadAnalytics()">Load Analytics</button>
                </div>
                <div id="analyticsResults"></div>
            </div>
            
            <div id="bidding" class="tab-content">
                <h2>Real-time Bidding</h2>
                <form id="biddingForm">
                    <div class="form-group">
                        <label for="ad_group_id">Ad Group ID:</label>
                        <input type="text" id="ad_group_id" name="ad_group_id" required>
                    </div>
                    <div class="form-group">
                        <label for="user_id">User ID:</label>
                        <input type="text" id="user_id" name="user_id" required>
                    </div>
                    <div class="form-group">
                        <label for="page_url">Page URL:</label>
                        <input type="url" id="page_url" name="page_url" required>
                    </div>
                    <button type="submit">Submit Bid Request</button>
                </form>
                <div id="biddingResults"></div>
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
            
            document.getElementById('advertiserForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/api/advertisers', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    alert(result.success ? 'Advertiser created successfully! ID: ' + result.advertiser_id : 'Error: ' + result.error);
                    if (result.success) {
                        e.target.reset();
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            document.getElementById('campaignForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/api/campaigns', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    alert(result.success ? 'Campaign created successfully! ID: ' + result.campaign_id : 'Error: ' + result.error);
                    if (result.success) {
                        e.target.reset();
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            document.getElementById('biddingForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/api/bid-request', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    
                    const resultsDiv = document.getElementById('biddingResults');
                    if (result.success) {
                        resultsDiv.innerHTML = `
                            <div class="analytics">
                                <h3>Bid Response</h3>
                                <p><strong>Bid Price:</strong> $${result.bid_price.toFixed(2)}</p>
                                <p><strong>Ad ID:</strong> ${result.ad_id}</p>
                                <p><strong>Win:</strong> ${result.win ? 'Yes' : 'No'}</p>
                            </div>
                        `;
                    } else {
                        resultsDiv.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            async function loadAnalytics() {
                const campaignId = document.getElementById('analytics_campaign_id').value;
                if (!campaignId) {
                    alert('Please enter a Campaign ID');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/analytics/campaign/${campaignId}`);
                    const analytics = await response.json();
                    
                    const resultsDiv = document.getElementById('analyticsResults');
                    resultsDiv.innerHTML = `
                        <div class="analytics">
                            <h3>Campaign Analytics</h3>
                            <div class="metric">
                                <div class="metric-value">${analytics.impressions.toLocaleString()}</div>
                                <div class="metric-label">Impressions</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${analytics.clicks.toLocaleString()}</div>
                                <div class="metric-label">Clicks</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${analytics.conversions.toLocaleString()}</div>
                                <div class="metric-label">Conversions</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">$${analytics.cost.toFixed(2)}</div>
                                <div class="metric-label">Cost</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">$${analytics.revenue.toFixed(2)}</div>
                                <div class="metric-label">Revenue</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${(analytics.ctr * 100).toFixed(2)}%</div>
                                <div class="metric-label">CTR</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${(analytics.conversion_rate * 100).toFixed(2)}%</div>
                                <div class="metric-label">Conv. Rate</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${analytics.roas.toFixed(2)}x</div>
                                <div class="metric-label">ROAS</div>
                            </div>
                        </div>
                    `;
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/api/advertisers', methods=['POST'])
def create_advertiser():
    """Create a new advertiser."""
    data = request.get_json()
    
    required_fields = ['name', 'email', 'company', 'industry']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        advertiser = adtech_service.create_advertiser(
            name=data['name'],
            email=data['email'],
            company=data['company'],
            industry=data['industry'],
            budget=float(data.get('budget', 0)),
            currency=data.get('currency', 'USD')
        )
        
        if advertiser:
            return jsonify({'success': True, 'advertiser_id': advertiser.advertiser_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to create advertiser'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/campaigns', methods=['POST'])
def create_campaign():
    """Create a new campaign."""
    data = request.get_json()
    
    required_fields = ['advertiser_id', 'campaign_name', 'budget', 'daily_budget', 'bid_strategy']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        from adtech_service import BidStrategy
        bid_strategy = BidStrategy(data['bid_strategy'])
        
        campaign = adtech_service.create_campaign(
            advertiser_id=data['advertiser_id'],
            name=data['campaign_name'],
            description=data.get('campaign_description', ''),
            budget=float(data['budget']),
            daily_budget=float(data['daily_budget']),
            bid_strategy=bid_strategy,
            target_cpa=float(data.get('target_cpa', 0)),
            target_roas=float(data.get('target_roas', 0))
        )
        
        if campaign:
            return jsonify({'success': True, 'campaign_id': campaign.campaign_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to create campaign'})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid bid strategy'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bid-request', methods=['POST'])
def process_bid_request():
    """Process a bid request."""
    data = request.get_json()
    
    required_fields = ['ad_group_id', 'user_id', 'page_url']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        bid_response = adtech_service.process_bid_request(
            ad_group_id=data['ad_group_id'],
            user_id=data['user_id'],
            page_url=data['page_url'],
            user_agent=data.get('user_agent', ''),
            ip_address=data.get('ip_address', '127.0.0.1')
        )
        
        if bid_response:
            return jsonify({
                'success': True,
                'bid_response_id': bid_response.bid_response_id,
                'ad_id': bid_response.ad_id,
                'bid_price': bid_response.bid_price,
                'win': bid_response.win
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to process bid request'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics/campaign/<campaign_id>')
def get_campaign_analytics(campaign_id):
    """Get campaign analytics."""
    try:
        analytics = adtech_service.get_campaign_analytics(campaign_id)
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/analytics/advertiser/<advertiser_id>')
def get_advertiser_analytics(advertiser_id):
    """Get advertiser analytics."""
    try:
        analytics = adtech_service.get_advertiser_analytics(advertiser_id)
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'adtech_platform'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
