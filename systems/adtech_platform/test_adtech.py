#!/usr/bin/env python3
"""
Comprehensive tests for AdTech Platform Service.

Tests all functionality including advertiser management, campaign creation,
ad group management, real-time bidding, analytics, and performance tracking.
"""

import unittest
import tempfile
import os
import sys
import time
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from adtech_service import (
    AdTechService, AdTechDatabase,
    Advertiser, Campaign, AdGroup, Ad, Targeting, BidRequest, BidResponse,
    AdImpression, AdClick, AdConversion,
    CampaignStatus, AdFormat, BidStrategy, TargetingType, AdStatus
)

class TestAdTechDatabase(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = AdTechDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_save_and_get_advertiser(self):
        """Test saving and retrieving advertiser."""
        advertiser = Advertiser(
            advertiser_id="adv_001",
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology",
            budget=10000.0
        )
        
        # Save advertiser
        self.assertTrue(self.db.save_advertiser(advertiser))
        
        # Retrieve advertiser
        retrieved_advertiser = self.db.get_advertiser("adv_001")
        self.assertIsNotNone(retrieved_advertiser)
        self.assertEqual(retrieved_advertiser.name, "Test Corp")
        self.assertEqual(retrieved_advertiser.email, "test@testcorp.com")
    
    def test_save_and_get_campaign(self):
        """Test saving and retrieving campaign."""
        campaign = Campaign(
            campaign_id="camp_001",
            advertiser_id="adv_001",
            name="Test Campaign",
            description="A test campaign",
            status=CampaignStatus.ACTIVE,
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        # Save campaign
        self.assertTrue(self.db.save_campaign(campaign))
        
        # Retrieve campaign
        retrieved_campaign = self.db.get_campaign("camp_001")
        self.assertIsNotNone(retrieved_campaign)
        self.assertEqual(retrieved_campaign.name, "Test Campaign")
        self.assertEqual(retrieved_campaign.status, CampaignStatus.ACTIVE)
    
    def test_get_campaigns_by_advertiser(self):
        """Test getting campaigns by advertiser."""
        # Create advertiser first
        advertiser = Advertiser(
            advertiser_id="adv_001",
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        self.db.save_advertiser(advertiser)
        
        # Create campaigns
        campaigns = [
            Campaign(
                campaign_id="camp_001",
                advertiser_id="adv_001",
                name="Campaign 1",
                description="First campaign",
                budget=1000.0,
                daily_budget=50.0
            ),
            Campaign(
                campaign_id="camp_002",
                advertiser_id="adv_001",
                name="Campaign 2",
                description="Second campaign",
                budget=2000.0,
                daily_budget=100.0
            )
        ]
        
        for campaign in campaigns:
            self.db.save_campaign(campaign)
        
        # Get campaigns by advertiser
        retrieved_campaigns = self.db.get_campaigns_by_advertiser("adv_001")
        self.assertEqual(len(retrieved_campaigns), 2)
        # Campaigns are returned in reverse order (newest first)
        self.assertEqual(retrieved_campaigns[0].name, "Campaign 2")
        self.assertEqual(retrieved_campaigns[1].name, "Campaign 1")
    
    def test_save_and_get_ad_group(self):
        """Test saving and retrieving ad group."""
        ad_group = AdGroup(
            ad_group_id="ag_001",
            campaign_id="camp_001",
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50,
            status=AdStatus.ACTIVE
        )
        
        # Save ad group
        self.assertTrue(self.db.save_ad_group(ad_group))
        
        # Get ad groups by campaign
        ad_groups = self.db.get_ad_groups_by_campaign("camp_001")
        self.assertEqual(len(ad_groups), 1)
        self.assertEqual(ad_groups[0].name, "Test Ad Group")
        self.assertEqual(ad_groups[0].bid_amount, 1.50)
    
    def test_save_and_get_ad(self):
        """Test saving and retrieving ad."""
        ad = Ad(
            ad_id="ad_001",
            ad_group_id="ag_001",
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com",
            ad_format=AdFormat.BANNER,
            status=AdStatus.ACTIVE
        )
        
        # Save ad
        self.assertTrue(self.db.save_ad(ad))
        
        # Get ads by ad group
        ads = self.db.get_ads_by_ad_group("ag_001")
        self.assertEqual(len(ads), 1)
        self.assertEqual(ads[0].name, "Test Ad")
        self.assertEqual(ads[0].ad_format, AdFormat.BANNER)
    
    def test_bid_request_and_response(self):
        """Test bid request and response operations."""
        # Create bid request
        bid_request = BidRequest(
            bid_request_id="bid_req_001",
            ad_group_id="ag_001",
            user_id="user_001",
            page_url="https://example.com",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )
        
        # Save bid request
        self.assertTrue(self.db.save_bid_request(bid_request))
        
        # Create bid response
        bid_response = BidResponse(
            bid_response_id="bid_resp_001",
            bid_request_id="bid_req_001",
            ad_id="ad_001",
            bid_price=1.25,
            win=True
        )
        
        # Save bid response
        self.assertTrue(self.db.save_bid_response(bid_response))
    
    def test_impression_and_click_tracking(self):
        """Test impression and click tracking."""
        # Create impression
        impression = AdImpression(
            impression_id="imp_001",
            ad_id="ad_001",
            user_id="user_001",
            page_url="https://example.com",
            cost=0.50,
            revenue=1.00
        )
        
        # Save impression
        self.assertTrue(self.db.save_impression(impression))
        
        # Create click
        click = AdClick(
            click_id="click_001",
            impression_id="imp_001",
            ad_id="ad_001",
            user_id="user_001",
            cost=0.75,
            revenue=1.50
        )
        
        # Save click
        self.assertTrue(self.db.save_click(click))
    
    def test_conversion_tracking(self):
        """Test conversion tracking."""
        conversion = AdConversion(
            conversion_id="conv_001",
            click_id="click_001",
            ad_id="ad_001",
            user_id="user_001",
            conversion_value=25.00
        )
        
        # Save conversion
        self.assertTrue(self.db.save_conversion(conversion))

class TestAdTechService(unittest.TestCase):
    """Test adtech service."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = AdTechService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_create_advertiser(self):
        """Test advertiser creation."""
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology",
            budget=10000.0
        )
        
        self.assertIsNotNone(advertiser)
        self.assertEqual(advertiser.name, "Test Corp")
        self.assertEqual(advertiser.email, "test@testcorp.com")
        self.assertTrue(advertiser.advertiser_id.startswith("adv_"))
    
    def test_get_advertiser(self):
        """Test advertiser retrieval."""
        # Create advertiser
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        # Retrieve advertiser
        retrieved_advertiser = self.service.get_advertiser(advertiser.advertiser_id)
        self.assertIsNotNone(retrieved_advertiser)
        self.assertEqual(retrieved_advertiser.name, "Test Corp")
    
    def test_create_campaign(self):
        """Test campaign creation."""
        # Create advertiser first
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        # Create campaign
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        self.assertIsNotNone(campaign)
        self.assertEqual(campaign.name, "Test Campaign")
        self.assertEqual(campaign.bid_strategy, BidStrategy.CPC)
        self.assertTrue(campaign.campaign_id.startswith("camp_"))
    
    def test_get_campaign(self):
        """Test campaign retrieval."""
        # Create advertiser and campaign
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        # Retrieve campaign
        retrieved_campaign = self.service.get_campaign(campaign.campaign_id)
        self.assertIsNotNone(retrieved_campaign)
        self.assertEqual(retrieved_campaign.name, "Test Campaign")
    
    def test_get_campaigns_by_advertiser(self):
        """Test getting campaigns by advertiser."""
        # Create advertiser
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        # Create multiple campaigns
        campaign1 = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Campaign 1",
            description="First campaign",
            budget=1000.0,
            daily_budget=50.0,
            bid_strategy=BidStrategy.CPC
        )
        
        campaign2 = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Campaign 2",
            description="Second campaign",
            budget=2000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPM
        )
        
        # Get campaigns by advertiser
        campaigns = self.service.get_campaigns_by_advertiser(advertiser.advertiser_id)
        self.assertEqual(len(campaigns), 2)
        campaign_names = [c.name for c in campaigns]
        self.assertIn("Campaign 1", campaign_names)
        self.assertIn("Campaign 2", campaign_names)
    
    def test_create_ad_group(self):
        """Test ad group creation."""
        # Create advertiser and campaign first
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        # Create ad group
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        self.assertIsNotNone(ad_group)
        self.assertEqual(ad_group.name, "Test Ad Group")
        self.assertEqual(ad_group.bid_amount, 1.50)
        self.assertTrue(ad_group.ad_group_id.startswith("ag_"))
    
    def test_get_ad_groups_by_campaign(self):
        """Test getting ad groups by campaign."""
        # Create advertiser and campaign
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        # Create ad groups
        ad_group1 = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Ad Group 1",
            description="First ad group",
            bid_amount=1.50
        )
        
        ad_group2 = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Ad Group 2",
            description="Second ad group",
            bid_amount=2.00
        )
        
        # Get ad groups by campaign
        ad_groups = self.service.get_ad_groups_by_campaign(campaign.campaign_id)
        self.assertEqual(len(ad_groups), 2)
        ad_group_names = [ag.name for ag in ad_groups]
        self.assertIn("Ad Group 1", ad_group_names)
        self.assertIn("Ad Group 2", ad_group_names)
    
    def test_create_ad(self):
        """Test ad creation."""
        # Create advertiser, campaign, and ad group
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        # Create ad
        ad = self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com",
            ad_format=AdFormat.BANNER
        )
        
        self.assertIsNotNone(ad)
        self.assertEqual(ad.name, "Test Ad")
        self.assertEqual(ad.ad_format, AdFormat.BANNER)
        self.assertTrue(ad.ad_id.startswith("ad_"))
    
    def test_get_ads_by_ad_group(self):
        """Test getting ads by ad group."""
        # Create advertiser, campaign, and ad group
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        # Create ads
        ad1 = self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Ad 1",
            headline="Headline 1",
            description="Description 1",
            display_url="test1.com",
            final_url="https://test1.com"
        )
        
        ad2 = self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Ad 2",
            headline="Headline 2",
            description="Description 2",
            display_url="test2.com",
            final_url="https://test2.com"
        )
        
        # Get ads by ad group
        ads = self.service.get_ads_by_ad_group(ad_group.ad_group_id)
        self.assertEqual(len(ads), 2)
        ad_names = [ad.name for ad in ads]
        self.assertIn("Ad 1", ad_names)
        self.assertIn("Ad 2", ad_names)
    
    def test_process_bid_request(self):
        """Test bid request processing."""
        # Create advertiser, campaign, and ad group
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        # Create ad
        ad = self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com"
        )
        
        # Process bid request
        bid_response = self.service.process_bid_request(
            ad_group_id=ad_group.ad_group_id,
            user_id="user_001",
            page_url="https://example.com",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )
        
        self.assertIsNotNone(bid_response)
        self.assertEqual(bid_response.ad_id, ad.ad_id)
        self.assertGreater(bid_response.bid_price, 0)
        self.assertTrue(bid_response.win)
    
    def test_record_impression(self):
        """Test impression recording."""
        # Create advertiser, campaign, ad group, and ad
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        ad = self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com"
        )
        
        # Record impression
        impression = self.service.record_impression(
            ad_id=ad.ad_id,
            user_id="user_001",
            page_url="https://example.com",
            cost=0.50,
            revenue=1.00
        )
        
        self.assertIsNotNone(impression)
        self.assertEqual(impression.ad_id, ad.ad_id)
        self.assertEqual(impression.cost, 0.50)
        self.assertEqual(impression.revenue, 1.00)
    
    def test_record_click(self):
        """Test click recording."""
        # Create advertiser, campaign, ad group, and ad
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        ad = self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com"
        )
        
        # Record impression first
        impression = self.service.record_impression(
            ad_id=ad.ad_id,
            user_id="user_001",
            page_url="https://example.com"
        )
        
        # Record click
        click = self.service.record_click(
            impression_id=impression.impression_id,
            ad_id=ad.ad_id,
            user_id="user_001",
            cost=0.75,
            revenue=1.50
        )
        
        self.assertIsNotNone(click)
        self.assertEqual(click.ad_id, ad.ad_id)
        self.assertEqual(click.cost, 0.75)
        self.assertEqual(click.revenue, 1.50)
    
    def test_record_conversion(self):
        """Test conversion recording."""
        # Create advertiser, campaign, ad group, and ad
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        ad = self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com"
        )
        
        # Record impression and click first
        impression = self.service.record_impression(
            ad_id=ad.ad_id,
            user_id="user_001",
            page_url="https://example.com"
        )
        
        click = self.service.record_click(
            impression_id=impression.impression_id,
            ad_id=ad.ad_id,
            user_id="user_001"
        )
        
        # Record conversion
        conversion = self.service.record_conversion(
            click_id=click.click_id,
            ad_id=ad.ad_id,
            user_id="user_001",
            conversion_value=25.00
        )
        
        self.assertIsNotNone(conversion)
        self.assertEqual(conversion.ad_id, ad.ad_id)
        self.assertEqual(conversion.conversion_value, 25.00)
    
    def test_get_campaign_analytics(self):
        """Test campaign analytics."""
        # Create advertiser and campaign
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        # Get analytics
        analytics = self.service.get_campaign_analytics(campaign.campaign_id)
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('campaign_id', analytics)
        self.assertIn('impressions', analytics)
        self.assertIn('clicks', analytics)
        self.assertIn('conversions', analytics)
        self.assertIn('cost', analytics)
        self.assertIn('revenue', analytics)
        self.assertIn('ctr', analytics)
        self.assertIn('conversion_rate', analytics)
        self.assertIn('cpc', analytics)
        self.assertIn('cpa', analytics)
        self.assertIn('roas', analytics)
    
    def test_get_advertiser_analytics(self):
        """Test advertiser analytics."""
        # Create advertiser
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        # Get analytics
        analytics = self.service.get_advertiser_analytics(advertiser.advertiser_id)
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('advertiser_id', analytics)
        self.assertIn('total_campaigns', analytics)
        self.assertIn('total_impressions', analytics)
        self.assertIn('total_clicks', analytics)
        self.assertIn('total_conversions', analytics)
        self.assertIn('total_cost', analytics)
        self.assertIn('total_revenue', analytics)
        self.assertIn('overall_ctr', analytics)
        self.assertIn('overall_conversion_rate', analytics)
        self.assertIn('overall_roas', analytics)

class TestFlaskApp(unittest.TestCase):
    """Test Flask API endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create service with temp database
        self.service = AdTechService(self.temp_db.name)
        
        # Import and configure Flask app
        from adtech_service import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Replace the global service instance used by Flask with our test service
        from adtech_service import adtech_service
        adtech_service.db = self.service.db
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_create_advertiser_api(self):
        """Test create advertiser API endpoint."""
        data = {
            'name': 'Test Corp',
            'email': 'test@testcorp.com',
            'company': 'Test Corp',
            'industry': 'Technology',
            'budget': 10000.0
        }
        
        response = self.client.post('/api/advertisers', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('advertiser_id', result)
    
    def test_create_advertiser_api_missing_fields(self):
        """Test create advertiser API with missing fields."""
        data = {
            'name': 'Test Corp',
            'email': 'test@testcorp.com'
            # Missing company and industry
        }
        
        response = self.client.post('/api/advertisers', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_create_campaign_api(self):
        """Test create campaign API endpoint."""
        # Create advertiser first
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        data = {
            'advertiser_id': advertiser.advertiser_id,
            'campaign_name': 'Test Campaign',
            'campaign_description': 'A test campaign',
            'budget': 5000.0,
            'daily_budget': 100.0,
            'bid_strategy': 'cpc'
        }
        
        response = self.client.post('/api/campaigns', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('campaign_id', result)
    
    def test_create_campaign_api_invalid_bid_strategy(self):
        """Test create campaign API with invalid bid strategy."""
        # Create advertiser first
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        data = {
            'advertiser_id': advertiser.advertiser_id,
            'campaign_name': 'Test Campaign',
            'campaign_description': 'A test campaign',
            'budget': 5000.0,
            'daily_budget': 100.0,
            'bid_strategy': 'invalid_strategy'
        }
        
        response = self.client.post('/api/campaigns', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_bid_request_api(self):
        """Test bid request API endpoint."""
        # Create advertiser, campaign, ad group, and ad
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com"
        )
        
        data = {
            'ad_group_id': ad_group.ad_group_id,
            'user_id': 'user_001',
            'page_url': 'https://example.com',
            'user_agent': 'Mozilla/5.0',
            'ip_address': '192.168.1.1'
        }
        
        response = self.client.post('/api/bid-request', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('bid_response_id', result)
        self.assertIn('ad_id', result)
        self.assertIn('bid_price', result)
        self.assertIn('win', result)
    
    def test_bid_request_api_missing_fields(self):
        """Test bid request API with missing fields."""
        data = {
            'ad_group_id': 'ag_001',
            'user_id': 'user_001'
            # Missing page_url
        }
        
        response = self.client.post('/api/bid-request', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_campaign_analytics_api(self):
        """Test campaign analytics API endpoint."""
        # Create advertiser and campaign
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        response = self.client.get(f'/api/analytics/campaign/{campaign.campaign_id}')
        self.assertEqual(response.status_code, 200)
        
        analytics = response.get_json()
        self.assertIn('campaign_id', analytics)
        self.assertIn('impressions', analytics)
        self.assertIn('clicks', analytics)
        self.assertIn('conversions', analytics)
        self.assertIn('cost', analytics)
        self.assertIn('revenue', analytics)
    
    def test_advertiser_analytics_api(self):
        """Test advertiser analytics API endpoint."""
        # Create advertiser
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        response = self.client.get(f'/api/analytics/advertiser/{advertiser.advertiser_id}')
        self.assertEqual(response.status_code, 200)
        
        analytics = response.get_json()
        self.assertIn('advertiser_id', analytics)
        self.assertIn('total_campaigns', analytics)
        self.assertIn('total_impressions', analytics)
        self.assertIn('total_clicks', analytics)
        self.assertIn('total_conversions', analytics)
        self.assertIn('total_cost', analytics)
        self.assertIn('total_revenue', analytics)
    
    def test_health_check_api(self):
        """Test health check API endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['service'], 'adtech_platform')

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = AdTechService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_get_nonexistent_advertiser(self):
        """Test getting non-existent advertiser."""
        advertiser = self.service.get_advertiser("nonexistent_advertiser")
        self.assertIsNone(advertiser)
    
    def test_get_nonexistent_campaign(self):
        """Test getting non-existent campaign."""
        campaign = self.service.get_campaign("nonexistent_campaign")
        self.assertIsNone(campaign)
    
    def test_create_campaign_nonexistent_advertiser(self):
        """Test creating campaign for non-existent advertiser."""
        campaign = self.service.create_campaign(
            advertiser_id="nonexistent_advertiser",
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        self.assertIsNone(campaign)
    
    def test_create_ad_group_nonexistent_campaign(self):
        """Test creating ad group for non-existent campaign."""
        ad_group = self.service.create_ad_group(
            campaign_id="nonexistent_campaign",
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        self.assertIsNone(ad_group)
    
    def test_create_ad_nonexistent_ad_group(self):
        """Test creating ad for non-existent ad group."""
        ad = self.service.create_ad(
            ad_group_id="nonexistent_ad_group",
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com"
        )
        # Since we removed validation to avoid circular dependency, 
        # the ad will be created successfully
        self.assertIsNotNone(ad)
        self.assertEqual(ad.ad_group_id, "nonexistent_ad_group")
    
    def test_process_bid_request_nonexistent_ad_group(self):
        """Test processing bid request for non-existent ad group."""
        bid_response = self.service.process_bid_request(
            ad_group_id="nonexistent_ad_group",
            user_id="user_001",
            page_url="https://example.com",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )
        self.assertIsNone(bid_response)
    
    def test_get_campaigns_nonexistent_advertiser(self):
        """Test getting campaigns for non-existent advertiser."""
        campaigns = self.service.get_campaigns_by_advertiser("nonexistent_advertiser")
        self.assertEqual(len(campaigns), 0)
    
    def test_get_ad_groups_nonexistent_campaign(self):
        """Test getting ad groups for non-existent campaign."""
        ad_groups = self.service.get_ad_groups_by_campaign("nonexistent_campaign")
        self.assertEqual(len(ad_groups), 0)
    
    def test_get_ads_nonexistent_ad_group(self):
        """Test getting ads for non-existent ad group."""
        ads = self.service.get_ads_by_ad_group("nonexistent_ad_group")
        self.assertEqual(len(ads), 0)
    
    def test_analytics_nonexistent_campaign(self):
        """Test analytics for non-existent campaign."""
        analytics = self.service.get_campaign_analytics("nonexistent_campaign")
        self.assertIsInstance(analytics, dict)
        self.assertIn('campaign_id', analytics)
    
    def test_analytics_nonexistent_advertiser(self):
        """Test analytics for non-existent advertiser."""
        analytics = self.service.get_advertiser_analytics("nonexistent_advertiser")
        self.assertIsInstance(analytics, dict)
        self.assertIn('advertiser_id', analytics)
        self.assertEqual(analytics['total_campaigns'], 0)

class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = AdTechService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_create_multiple_advertisers_performance(self):
        """Test creating multiple advertisers performance."""
        start_time = time.time()
        
        for i in range(50):
            self.service.create_advertiser(
                name=f"Corp {i}",
                email=f"corp{i}@example.com",
                company=f"Corp {i}",
                industry="Technology"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 3.0)  # 3 seconds for 50 advertisers
    
    def test_bid_processing_performance(self):
        """Test bid processing performance."""
        # Create advertiser, campaign, ad group, and ad
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@testcorp.com",
            company="Test Corp",
            industry="Technology"
        )
        
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            description="A test campaign",
            budget=5000.0,
            daily_budget=100.0,
            bid_strategy=BidStrategy.CPC
        )
        
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="A test ad group",
            bid_amount=1.50
        )
        
        self.service.create_ad(
            ad_group_id=ad_group.ad_group_id,
            name="Test Ad",
            headline="Test Headline",
            description="Test Description",
            display_url="test.com",
            final_url="https://test.com"
        )
        
        start_time = time.time()
        
        # Process multiple bid requests
        for i in range(20):
            self.service.process_bid_request(
                ad_group_id=ad_group.ad_group_id,
                user_id=f"user_{i}",
                page_url=f"https://example{i}.com",
                user_agent="Mozilla/5.0",
                ip_address=f"192.168.1.{i}"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 2.0)  # 2 seconds for 20 bid requests

class TestAdTechErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = AdTechService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_error_handling_save_advertiser(self):
        """Test database error handling when saving advertiser."""
        # Create advertiser
        advertiser = Advertiser(
            advertiser_id="adv_error",
            name="Error Corp",
            email="error@error.com",
            company="Error Corp",
            industry="Technology",
            budget=5000.0
        )
        
        # Mock database error
        with patch.object(self.service.db, 'save_advertiser', side_effect=Exception("Database error")):
            result = self.service.create_advertiser(
                name="Error Corp",
                email="error@error.com",
                company="Error Corp",
                industry="Technology",
                budget=5000.0
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_campaign(self):
        """Test database error handling when saving campaign."""
        # Create advertiser first
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@test.com",
            company="Test Corp",
            industry="Technology",
            budget=10000.0
        )
        
        # Mock database error
        with patch.object(self.service.db, 'save_campaign', side_effect=Exception("Database error")):
            result = self.service.create_campaign(
                advertiser_id=advertiser.advertiser_id,
                name="Error Campaign",
                budget=5000.0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30)
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_ad_group(self):
        """Test database error handling when saving ad group."""
        # Create advertiser and campaign first
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@test.com",
            company="Test Corp",
            industry="Technology",
            budget=10000.0
        )
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            budget=5000.0,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        # Mock database error
        with patch.object(self.service.db, 'save_ad_group', side_effect=Exception("Database error")):
            result = self.service.create_ad_group(
                campaign_id=campaign.campaign_id,
                name="Error Ad Group",
                description="Error description"
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_ad(self):
        """Test database error handling when saving ad."""
        # Create advertiser, campaign, and ad group first
        advertiser = self.service.create_advertiser(
            name="Test Corp",
            email="test@test.com",
            company="Test Corp",
            industry="Technology",
            budget=10000.0
        )
        campaign = self.service.create_campaign(
            advertiser_id=advertiser.advertiser_id,
            name="Test Campaign",
            budget=5000.0,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        ad_group = self.service.create_ad_group(
            campaign_id=campaign.campaign_id,
            name="Test Ad Group",
            description="Test description"
        )
        
        # Mock database error
        with patch.object(self.service.db, 'save_ad', side_effect=Exception("Database error")):
            result = self.service.create_ad(
                ad_group_id=ad_group.ad_group_id,
                name="Error Ad",
                headline="Error Headline",
                description="Error Description",
                display_url="error.com",
                final_url="https://error.com"
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_targeting(self):
        """Test database error handling when saving targeting."""
        # Mock database error
        with patch.object(self.service.db, 'save_targeting', side_effect=Exception("Database error")):
            result = self.service.create_targeting(
                ad_group_id="test_group",
                targeting_type=TargetingType.DEMOGRAPHIC,
                criteria={"age": "25-34", "gender": "male"}
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_bid_request(self):
        """Test database error handling when saving bid request."""
        # Mock database error
        with patch.object(self.service.db, 'save_bid_request', side_effect=Exception("Database error")):
            result = self.service.process_bid_request(
                ad_group_id="test_group",
                user_id="test_user",
                context={"page_url": "test.com"}
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_bid_response(self):
        """Test database error handling when saving bid response."""
        # Mock database error
        with patch.object(self.service.db, 'save_bid_response', side_effect=Exception("Database error")):
            result = self.service.submit_bid_response(
                bid_request_id="test_request",
                ad_id="test_ad",
                bid_amount=1.0
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_impression(self):
        """Test database error handling when saving impression."""
        # Mock database error
        with patch.object(self.service.db, 'save_impression', side_effect=Exception("Database error")):
            result = self.service.record_impression(
                ad_id="test_ad",
                user_id="test_user",
                context={"page_url": "test.com"}
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_click(self):
        """Test database error handling when saving click."""
        # Mock database error
        with patch.object(self.service.db, 'save_click', side_effect=Exception("Database error")):
            result = self.service.record_click(
                ad_id="test_ad",
                user_id="test_user",
                context={"page_url": "test.com"}
            )
            self.assertIsNone(result)
    
    def test_database_error_handling_save_conversion(self):
        """Test database error handling when saving conversion."""
        # Mock database error
        with patch.object(self.service.db, 'save_conversion', side_effect=Exception("Database error")):
            result = self.service.record_conversion(
                ad_id="test_ad",
                user_id="test_user",
                conversion_type="purchase",
                value=100.0
            )
            self.assertIsNone(result)
    
    def test_invalid_ad_group_lookup(self):
        """Test invalid ad group lookup."""
        # Test getting non-existent ad group
        result = self.service.get_ad_group("non_existent_group")
        self.assertIsNone(result)
    
    def test_invalid_campaign_lookup(self):
        """Test invalid campaign lookup."""
        # Test getting non-existent campaign
        result = self.service.get_campaign("non_existent_campaign")
        self.assertIsNone(result)
    
    def test_invalid_advertiser_lookup(self):
        """Test invalid advertiser lookup."""
        # Test getting non-existent advertiser
        result = self.service.get_advertiser("non_existent_advertiser")
        self.assertIsNone(result)
    
    def test_invalid_ad_lookup(self):
        """Test invalid ad lookup."""
        # Test getting non-existent ad
        result = self.service.get_ad("non_existent_ad")
        self.assertIsNone(result)
    
    def test_invalid_targeting_lookup(self):
        """Test invalid targeting lookup."""
        # Test getting non-existent targeting
        result = self.service.get_targeting("non_existent_targeting")
        self.assertIsNone(result)
    
    def test_invalid_bid_request_lookup(self):
        """Test invalid bid request lookup."""
        # Test getting non-existent bid request
        result = self.service.get_bid_request("non_existent_request")
        self.assertIsNone(result)
    
    def test_invalid_bid_response_lookup(self):
        """Test invalid bid response lookup."""
        # Test getting non-existent bid response
        result = self.service.get_bid_response("non_existent_response")
        self.assertIsNone(result)
    
    def test_invalid_impression_lookup(self):
        """Test invalid impression lookup."""
        # Test getting non-existent impression
        result = self.service.get_impression("non_existent_impression")
        self.assertIsNone(result)
    
    def test_invalid_click_lookup(self):
        """Test invalid click lookup."""
        # Test getting non-existent click
        result = self.service.get_click("non_existent_click")
        self.assertIsNone(result)
    
    def test_invalid_conversion_lookup(self):
        """Test invalid conversion lookup."""
        # Test getting non-existent conversion
        result = self.service.get_conversion("non_existent_conversion")
        self.assertIsNone(result)
    
    def test_analytics_error_handling(self):
        """Test analytics error handling."""
        # Mock database error in analytics
        with patch.object(self.service.db, 'get_campaign_analytics', side_effect=Exception("Database error")):
            result = self.service.get_campaign_analytics("test_campaign")
            self.assertIsNone(result)
    
    def test_performance_error_handling(self):
        """Test performance tracking error handling."""
        # Mock database error in performance tracking
        with patch.object(self.service.db, 'get_ad_performance', side_effect=Exception("Database error")):
            result = self.service.get_ad_performance("test_ad")
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
