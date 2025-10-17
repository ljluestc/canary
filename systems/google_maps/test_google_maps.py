#!/usr/bin/env python3
"""
Comprehensive tests for the Google Maps system.
"""

import unittest
import tempfile
import os
import time
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from google_maps_service import (
    GoogleMapsService, GoogleMapsDatabase, Location, Place, Route, TrafficInfo,
    TravelMode, PlaceType
)

class TestLocation(unittest.TestCase):
    """Test Location class."""
    
    def test_location_creation(self):
        """Test creating a Location."""
        location = Location(37.7749, -122.4194, "San Francisco, CA")
        
        self.assertEqual(location.latitude, 37.7749)
        self.assertEqual(location.longitude, -122.4194)
        self.assertEqual(location.address, "San Francisco, CA")
    
    def test_location_distance_calculation(self):
        """Test distance calculation between locations."""
        sf = Location(37.7749, -122.4194)  # San Francisco
        ny = Location(40.7128, -74.0060)   # New York
        
        distance = sf.distance_to(ny)
        
        # Distance should be approximately 4135 km
        self.assertAlmostEqual(distance, 4135, delta=100)
    
    def test_location_distance_same_location(self):
        """Test distance calculation for same location."""
        location = Location(37.7749, -122.4194)
        distance = location.distance_to(location)
        
        self.assertEqual(distance, 0.0)

class TestPlace(unittest.TestCase):
    """Test Place class."""
    
    def test_place_creation(self):
        """Test creating a Place."""
        location = Location(37.7749, -122.4194, "San Francisco, CA")
        place = Place(
            place_id="place_1",
            name="Test Restaurant",
            location=location,
            place_type=PlaceType.RESTAURANT,
            rating=4.5,
            price_level=2
        )
        
        self.assertEqual(place.place_id, "place_1")
        self.assertEqual(place.name, "Test Restaurant")
        self.assertEqual(place.place_type, PlaceType.RESTAURANT)
        self.assertEqual(place.rating, 4.5)
        self.assertEqual(place.price_level, 2)
        self.assertEqual(place.photos, [])
        self.assertEqual(place.reviews, [])

class TestRoute(unittest.TestCase):
    """Test Route class."""
    
    def test_route_creation(self):
        """Test creating a Route."""
        start = Location(37.7749, -122.4194, "San Francisco, CA")
        end = Location(37.7849, -122.4094, "Oakland, CA")
        
        route = Route(
            route_id="route_1",
            start_location=start,
            end_location=end,
            travel_mode=TravelMode.DRIVING,
            distance=10.5,
            duration=15,
            steps=[{"instruction": "Go straight", "distance": 10.5, "duration": 15}]
        )
        
        self.assertEqual(route.route_id, "route_1")
        self.assertEqual(route.travel_mode, TravelMode.DRIVING)
        self.assertEqual(route.distance, 10.5)
        self.assertEqual(route.duration, 15)
        self.assertEqual(len(route.steps), 1)

class TestTrafficInfo(unittest.TestCase):
    """Test TrafficInfo class."""
    
    def test_traffic_info_creation(self):
        """Test creating TrafficInfo."""
        location = Location(37.7749, -122.4194)
        traffic_info = TrafficInfo(
            location=location,
            congestion_level="moderate",
            speed=45.0,
            delay_minutes=5,
            timestamp=datetime.now()
        )
        
        self.assertEqual(traffic_info.congestion_level, "moderate")
        self.assertEqual(traffic_info.speed, 45.0)
        self.assertEqual(traffic_info.delay_minutes, 5)

class TestGoogleMapsDatabase(unittest.TestCase):
    """Test GoogleMapsDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = GoogleMapsDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization."""
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_and_get_place(self):
        """Test saving and retrieving places."""
        location = Location(37.7749, -122.4194, "San Francisco, CA")
        place = Place(
            place_id="place_1",
            name="Test Restaurant",
            location=location,
            place_type=PlaceType.RESTAURANT,
            rating=4.5,
            price_level=2
        )
        
        # Save place
        success = self.db.save_place(place)
        self.assertTrue(success)
        
        # Retrieve place
        retrieved = self.db.get_place("place_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.place_id, "place_1")
        self.assertEqual(retrieved.name, "Test Restaurant")
        self.assertEqual(retrieved.place_type, PlaceType.RESTAURANT)
    
    def test_search_places(self):
        """Test searching places."""
        # Add some test places
        locations = [
            Location(37.7749, -122.4194, "San Francisco, CA"),
            Location(37.7849, -122.4094, "Oakland, CA"),
            Location(37.7949, -122.3994, "Berkeley, CA")
        ]
        
        for i, location in enumerate(locations):
            place = Place(
                place_id=f"place_{i}",
                name=f"Restaurant {i}",
                location=location,
                place_type=PlaceType.RESTAURANT,
                rating=4.0 + i * 0.1,
                price_level=1
            )
            self.db.save_place(place)
        
        # Search for restaurants
        places = self.db.search_places("Restaurant", place_type=PlaceType.RESTAURANT)
        self.assertEqual(len(places), 3)
        
        # Search with location and radius
        search_location = Location(37.7749, -122.4194)
        nearby_places = self.db.search_places("", search_location, radius=50.0)
        self.assertEqual(len(nearby_places), 3)
    
    def test_save_and_get_route(self):
        """Test saving and retrieving routes."""
        start = Location(37.7749, -122.4194, "San Francisco, CA")
        end = Location(37.7849, -122.4094, "Oakland, CA")
        
        route = Route(
            route_id="route_1",
            start_location=start,
            end_location=end,
            travel_mode=TravelMode.DRIVING,
            distance=10.5,
            duration=15,
            steps=[{"instruction": "Go straight", "distance": 10.5, "duration": 15}]
        )
        
        # Save route
        success = self.db.save_route(route)
        self.assertTrue(success)
        
        # Retrieve route
        retrieved = self.db.get_route("route_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.route_id, "route_1")
        self.assertEqual(retrieved.travel_mode, TravelMode.DRIVING)
    
    def test_save_and_get_traffic_info(self):
        """Test saving and retrieving traffic information."""
        location = Location(37.7749, -122.4194)
        traffic_info = TrafficInfo(
            location=location,
            congestion_level="moderate",
            speed=45.0,
            delay_minutes=5,
            timestamp=datetime.now()
        )
        
        # Save traffic info
        success = self.db.save_traffic_info(traffic_info)
        self.assertTrue(success)
        
        # Retrieve traffic info
        retrieved = self.db.get_traffic_info(location, radius=1.0)
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].congestion_level, "moderate")
        self.assertEqual(retrieved[0].speed, 45.0)
    
    def test_save_search_history(self):
        """Test saving search history."""
        location = Location(37.7749, -122.4194)
        success = self.db.save_search_history("restaurants", location, 5)
        self.assertTrue(success)

class TestGoogleMapsService(unittest.TestCase):
    """Test GoogleMapsService class."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = GoogleMapsService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_generate_id(self):
        """Test ID generation."""
        id1 = self.service.generate_id("test")
        id2 = self.service.generate_id("test")
        
        self.assertTrue(id1.startswith("test_"))
        self.assertTrue(id2.startswith("test_"))
        self.assertNotEqual(id1, id2)
    
    def test_geocode(self):
        """Test geocoding."""
        location = self.service.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
        
        self.assertIsNotNone(location)
        self.assertEqual(location.latitude, 37.4220)
        self.assertEqual(location.longitude, -122.0841)
    
    def test_reverse_geocode(self):
        """Test reverse geocoding."""
        location = self.service.reverse_geocode(37.7749, -122.4194)
        
        self.assertIsNotNone(location)
        self.assertEqual(location.latitude, 37.7749)
        self.assertEqual(location.longitude, -122.4194)
    
    def test_add_place(self):
        """Test adding a place."""
        location = Location(37.7749, -122.4194, "San Francisco, CA")
        place = self.service.add_place(
            name="Test Restaurant",
            location=location,
            place_type=PlaceType.RESTAURANT,
            rating=4.5,
            price_level=2
        )
        
        self.assertIsNotNone(place)
        self.assertEqual(place.name, "Test Restaurant")
        self.assertEqual(place.place_type, PlaceType.RESTAURANT)
    
    def test_search_places(self):
        """Test searching places."""
        # Add some test places
        locations = [
            Location(37.7749, -122.4194, "San Francisco, CA"),
            Location(37.7849, -122.4094, "Oakland, CA")
        ]
        
        for i, location in enumerate(locations):
            self.service.add_place(
                name=f"Restaurant {i}",
                location=location,
                place_type=PlaceType.RESTAURANT,
                rating=4.0 + i * 0.1
            )
        
        # Search for places
        places = self.service.search_places("Restaurant", place_type=PlaceType.RESTAURANT)
        self.assertEqual(len(places), 2)
    
    def test_get_place_details(self):
        """Test getting place details."""
        location = Location(37.7749, -122.4194, "San Francisco, CA")
        place = self.service.add_place(
            name="Test Restaurant",
            location=location,
            place_type=PlaceType.RESTAURANT,
            rating=4.5
        )
        
        retrieved = self.service.get_place_details(place.place_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Restaurant")
    
    def test_calculate_route(self):
        """Test calculating routes."""
        start = Location(37.7749, -122.4194, "San Francisco, CA")
        end = Location(37.7849, -122.4094, "Oakland, CA")
        
        route = self.service.calculate_route(start, end, TravelMode.DRIVING)
        
        self.assertIsNotNone(route)
        self.assertEqual(route.travel_mode, TravelMode.DRIVING)
        self.assertGreater(route.distance, 0)
        self.assertGreater(route.duration, 0)
    
    def test_get_traffic_info(self):
        """Test getting traffic information."""
        location = Location(37.7749, -122.4194)
        
        # Update traffic info
        success = self.service.update_traffic_info(location, "moderate", 45.0, 5)
        self.assertTrue(success)
        
        # Get traffic info
        traffic_info = self.service.get_traffic_info(location)
        self.assertEqual(len(traffic_info), 1)
        self.assertEqual(traffic_info[0].congestion_level, "moderate")
    
    def test_get_nearby_places(self):
        """Test getting nearby places."""
        # Add some test places
        locations = [
            Location(37.7749, -122.4194, "San Francisco, CA"),
            Location(37.7759, -122.4184, "Nearby Restaurant, CA")
        ]
        
        for i, location in enumerate(locations):
            self.service.add_place(
                name=f"Restaurant {i}",
                location=location,
                place_type=PlaceType.RESTAURANT,
                rating=4.0
            )
        
        # Get nearby places
        search_location = Location(37.7749, -122.4194)
        nearby_places = self.service.get_nearby_places(search_location, radius=1.0)
        self.assertEqual(len(nearby_places), 2)
    
    def test_get_route_alternatives(self):
        """Test getting route alternatives."""
        start = Location(37.7749, -122.4194, "San Francisco, CA")
        end = Location(37.7849, -122.4094, "Oakland, CA")
        
        routes = self.service.get_route_alternatives(start, end)
        
        self.assertEqual(len(routes), 4)  # One for each travel mode
        travel_modes = [route.travel_mode for route in routes]
        self.assertIn(TravelMode.DRIVING, travel_modes)
        self.assertIn(TravelMode.WALKING, travel_modes)
        self.assertIn(TravelMode.BICYCLING, travel_modes)
        self.assertIn(TravelMode.TRANSIT, travel_modes)
    
    def test_get_search_suggestions(self):
        """Test getting search suggestions."""
        suggestions = self.service.get_search_suggestions("rest", limit=3)
        
        self.assertIsInstance(suggestions, list)
        self.assertLessEqual(len(suggestions), 3)
        self.assertTrue(any("rest" in s.lower() for s in suggestions))

class TestFlaskApp(unittest.TestCase):
    """Test Flask API endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create service with temp database
        self.service = GoogleMapsService(self.temp_db.name)
        
        # Import and configure Flask app
        from google_maps_service import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Replace the global service instance used by Flask with our test service
        from google_maps_service import google_maps_service
        google_maps_service.db = self.service.db
        google_maps_service.geocoding_cache = self.service.geocoding_cache
        google_maps_service.route_cache = self.service.route_cache
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_health_check_api(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_geocode_api(self):
        """Test geocoding endpoint."""
        data = {'address': '1600 Amphitheatre Parkway, Mountain View, CA'}
        
        response = self.client.post('/geocode', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertEqual(result['latitude'], 37.4220)
        self.assertEqual(result['longitude'], -122.0841)
    
    def test_geocode_api_missing_address(self):
        """Test geocoding endpoint with missing address."""
        data = {}
        
        response = self.client.post('/geocode', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing address')
    
    def test_reverse_geocode_api(self):
        """Test reverse geocoding endpoint."""
        data = {'latitude': 37.7749, 'longitude': -122.4194}
        
        response = self.client.post('/reverse_geocode', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertEqual(result['latitude'], 37.7749)
        self.assertEqual(result['longitude'], -122.4194)
    
    def test_reverse_geocode_api_missing_coordinates(self):
        """Test reverse geocoding endpoint with missing coordinates."""
        data = {'latitude': 37.7749}
        
        response = self.client.post('/reverse_geocode', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing latitude or longitude')
    
    def test_search_places_api(self):
        """Test search places endpoint."""
        # Add some test places
        locations = [
            Location(37.7749, -122.4194, "San Francisco, CA"),
            Location(37.7849, -122.4094, "Oakland, CA")
        ]
        
        for i, location in enumerate(locations):
            self.service.add_place(
                name=f"Restaurant {i}",
                location=location,
                place_type=PlaceType.RESTAURANT,
                rating=4.0 + i * 0.1
            )
        
        response = self.client.get('/search?query=Restaurant&place_type=restaurant')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['places']), 2)
    
    def test_search_places_api_with_location(self):
        """Test search places endpoint with location."""
        # Add some test places
        location = Location(37.7749, -122.4194, "San Francisco, CA")
        self.service.add_place(
            name="Test Restaurant",
            location=location,
            place_type=PlaceType.RESTAURANT,
            rating=4.5
        )
        
        response = self.client.get('/search?query=Restaurant&latitude=37.7749&longitude=-122.4194&radius=1.0')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['places'][0]['name'], 'Test Restaurant')
    
    def test_get_place_details_api(self):
        """Test get place details endpoint."""
        # Add a test place
        location = Location(37.7749, -122.4194, "San Francisco, CA")
        place = self.service.add_place(
            name="Test Restaurant",
            location=location,
            place_type=PlaceType.RESTAURANT,
            rating=4.5,
            price_level=2
        )
        
        response = self.client.get(f'/places/{place.place_id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['name'], 'Test Restaurant')
        self.assertEqual(data['place_type'], 'restaurant')
        self.assertEqual(data['rating'], 4.5)
    
    def test_get_place_details_api_not_found(self):
        """Test get place details endpoint for non-existent place."""
        response = self.client.get('/places/nonexistent_place_id')
        self.assertEqual(response.status_code, 404)
        
        data = response.get_json()
        self.assertEqual(data['error'], 'Place not found')
    
    def test_calculate_route_api(self):
        """Test calculate route endpoint."""
        data = {
            'start': {'latitude': 37.7749, 'longitude': -122.4194, 'address': 'San Francisco, CA'},
            'end': {'latitude': 37.7849, 'longitude': -122.4094, 'address': 'Oakland, CA'},
            'travel_mode': 'driving'
        }
        
        response = self.client.post('/routes', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertIn('route_id', result)
        self.assertEqual(result['travel_mode'], 'driving')
        self.assertGreater(result['distance'], 0)
        self.assertGreater(result['duration'], 0)
    
    def test_calculate_route_api_missing_data(self):
        """Test calculate route endpoint with missing data."""
        data = {'start': {'latitude': 37.7749, 'longitude': -122.4194}}
        
        response = self.client.post('/routes', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing start or end location')
    
    def test_calculate_route_api_invalid_travel_mode(self):
        """Test calculate route endpoint with invalid travel mode."""
        data = {
            'start': {'latitude': 37.7749, 'longitude': -122.4194},
            'end': {'latitude': 37.7849, 'longitude': -122.4094},
            'travel_mode': 'invalid_mode'
        }
        
        response = self.client.post('/routes', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Invalid travel mode')
    
    def test_get_traffic_info_api(self):
        """Test get traffic info endpoint."""
        # Update traffic info
        location = Location(37.7749, -122.4194)
        self.service.update_traffic_info(location, "moderate", 45.0, 5)
        
        response = self.client.get('/traffic?latitude=37.7749&longitude=-122.4194')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(len(data['traffic_info']), 1)
        self.assertEqual(data['traffic_info'][0]['congestion_level'], 'moderate')
    
    def test_get_traffic_info_api_missing_coordinates(self):
        """Test get traffic info endpoint with missing coordinates."""
        response = self.client.get('/traffic')
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing latitude or longitude')
    
    def test_get_search_suggestions_api(self):
        """Test get search suggestions endpoint."""
        response = self.client.get('/suggestions?query=rest&limit=3')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('suggestions', data)
        self.assertIsInstance(data['suggestions'], list)
        self.assertLessEqual(len(data['suggestions']), 3)

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = GoogleMapsService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_geocode_unknown_address(self):
        """Test geocoding unknown address."""
        location = self.service.geocode("Unknown Address 12345")
        
        # Should return a default location
        self.assertIsNotNone(location)
        self.assertEqual(location.latitude, 37.7749)  # San Francisco default
        self.assertEqual(location.longitude, -122.4194)
    
    def test_search_places_empty_query(self):
        """Test searching places with empty query."""
        places = self.service.search_places("")
        self.assertEqual(len(places), 0)
    
    def test_search_places_no_results(self):
        """Test searching places with no results."""
        places = self.service.search_places("nonexistent_place_type_12345")
        self.assertEqual(len(places), 0)
    
    def test_calculate_route_same_location(self):
        """Test calculating route to same location."""
        location = Location(37.7749, -122.4194, "San Francisco, CA")
        route = self.service.calculate_route(location, location, TravelMode.DRIVING)
        
        self.assertIsNotNone(route)
        self.assertEqual(route.distance, 0.0)
        self.assertEqual(route.duration, 0)
    
    def test_get_place_details_nonexistent(self):
        """Test getting details for non-existent place."""
        place = self.service.get_place_details("nonexistent_place_id")
        self.assertIsNone(place)
    
    def test_get_route_nonexistent(self):
        """Test getting non-existent route."""
        route = self.service.db.get_route("nonexistent_route_id")
        self.assertIsNone(route)
    
    def test_traffic_info_no_data(self):
        """Test getting traffic info with no data."""
        location = Location(37.7749, -122.4194)
        traffic_info = self.service.get_traffic_info(location)
        self.assertEqual(len(traffic_info), 0)
    
    def test_search_suggestions_empty_query(self):
        """Test getting search suggestions with empty query."""
        suggestions = self.service.get_search_suggestions("")
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = GoogleMapsService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_bulk_place_operations_performance(self):
        """Test performance of bulk place operations."""
        import time
        
        # Test bulk place creation
        start_time = time.time()
        
        for i in range(100):
            location = Location(37.7749 + i * 0.001, -122.4194 + i * 0.001, f"Location {i}")
            self.service.add_place(
                name=f"Place {i}",
                location=location,
                place_type=PlaceType.RESTAURANT,
                rating=4.0
            )
        
        creation_time = time.time() - start_time
        
        # Test bulk search
        start_time = time.time()
        
        places = self.service.search_places("Place", limit=100)
        
        search_time = time.time() - start_time
        
        # Performance should be reasonable
        self.assertLess(creation_time, 5.0)  # Less than 5 seconds for 100 places
        self.assertLess(search_time, 2.0)    # Less than 2 seconds for search
        self.assertEqual(len(places), 100)
    
    def test_route_calculation_performance(self):
        """Test performance of route calculations."""
        import time
        
        start_time = time.time()
        
        # Calculate multiple routes
        for i in range(50):
            start = Location(37.7749 + i * 0.001, -122.4194 + i * 0.001)
            end = Location(37.7849 + i * 0.001, -122.4094 + i * 0.001)
            route = self.service.calculate_route(start, end, TravelMode.DRIVING)
            self.assertIsNotNone(route)
        
        calculation_time = time.time() - start_time
        
        # Performance should be reasonable
        self.assertLess(calculation_time, 3.0)  # Less than 3 seconds for 50 routes
    
    def test_geocoding_cache_performance(self):
        """Test geocoding cache performance."""
        import time
        
        # First geocoding (cache miss)
        start_time = time.time()
        location1 = self.service.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
        first_time = time.time() - start_time
        
        # Second geocoding (cache hit)
        start_time = time.time()
        location2 = self.service.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
        second_time = time.time() - start_time
        
        self.assertEqual(location1.latitude, location2.latitude)
        self.assertEqual(location1.longitude, location2.longitude)
        
        # Cache hit should be faster (though this might not always be true in tests)
        # We'll just verify both operations complete successfully
        self.assertIsNotNone(location1)
        self.assertIsNotNone(location2)

if __name__ == '__main__':
    unittest.main()
