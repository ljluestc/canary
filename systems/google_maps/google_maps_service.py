#!/usr/bin/env python3
"""
Google Maps-like Mapping Service

A comprehensive mapping and geolocation service with features like:
- Geocoding and reverse geocoding
- Route planning and navigation
- Place search and discovery
- Real-time traffic information
- Street view imagery
- Location-based services
"""

import json
import sqlite3
import math
import time
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TravelMode(Enum):
    """Travel modes for routing."""
    DRIVING = "driving"
    WALKING = "walking"
    BICYCLING = "bicycling"
    TRANSIT = "transit"

class PlaceType(Enum):
    """Types of places."""
    RESTAURANT = "restaurant"
    GAS_STATION = "gas_station"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    BANK = "bank"
    PHARMACY = "pharmacy"
    SHOPPING_MALL = "shopping_mall"
    PARK = "park"
    MUSEUM = "museum"
    HOTEL = "hotel"

@dataclass
class Location:
    """Represents a geographical location."""
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

@dataclass
class Place:
    """Represents a place of interest."""
    place_id: str
    name: str
    location: Location
    place_type: PlaceType
    rating: float
    price_level: int
    phone_number: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[Dict[str, str]] = None
    photos: List[str] = None
    reviews: List[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.photos is None:
            self.photos = []
        if self.reviews is None:
            self.reviews = []
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Route:
    """Represents a route between two locations."""
    route_id: str
    start_location: Location
    end_location: Location
    travel_mode: TravelMode
    distance: float
    duration: int  # in minutes
    steps: List[Dict[str, Any]]
    traffic_info: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TrafficInfo:
    """Real-time traffic information."""
    location: Location
    congestion_level: str
    speed: float  # km/h
    delay_minutes: int
    timestamp: datetime

class GoogleMapsDatabase:
    """Database layer for the Google Maps service."""
    
    def __init__(self, db_path: str = "google_maps.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Places table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS places (
                    place_id TEXT PRIMARY KEY,
                    name TEXT,
                    latitude REAL,
                    longitude REAL,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    country TEXT,
                    postal_code TEXT,
                    place_type TEXT,
                    rating REAL,
                    price_level INTEGER,
                    phone_number TEXT,
                    website TEXT,
                    opening_hours TEXT,
                    photos TEXT,
                    reviews TEXT,
                    created_at TEXT
                )
            ''')
            
            # Routes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS routes (
                    route_id TEXT PRIMARY KEY,
                    start_latitude REAL,
                    start_longitude REAL,
                    end_latitude REAL,
                    end_longitude REAL,
                    travel_mode TEXT,
                    distance REAL,
                    duration INTEGER,
                    steps TEXT,
                    traffic_info TEXT,
                    created_at TEXT
                )
            ''')
            
            # Traffic info table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL,
                    longitude REAL,
                    congestion_level TEXT,
                    speed REAL,
                    delay_minutes INTEGER,
                    timestamp TEXT
                )
            ''')
            
            # Search history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    location_latitude REAL,
                    location_longitude REAL,
                    results_count INTEGER,
                    timestamp TEXT
                )
            ''')
            
            conn.commit()
    
    def save_place(self, place: Place) -> bool:
        """Save a place."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO places
                    (place_id, name, latitude, longitude, address, city, state, country, postal_code,
                     place_type, rating, price_level, phone_number, website, opening_hours, photos, reviews, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    place.place_id,
                    place.name,
                    place.location.latitude,
                    place.location.longitude,
                    place.location.address,
                    place.location.city,
                    place.location.state,
                    place.location.country,
                    place.location.postal_code,
                    place.place_type.value,
                    place.rating,
                    place.price_level,
                    place.phone_number,
                    place.website,
                    json.dumps(place.opening_hours) if place.opening_hours else None,
                    json.dumps(place.photos),
                    json.dumps(place.reviews),
                    place.created_at.isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving place: {e}")
            return False
    
    def get_place(self, place_id: str) -> Optional[Place]:
        """Get a place by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT place_id, name, latitude, longitude, address, city, state, country, postal_code,
                           place_type, rating, price_level, phone_number, website, opening_hours, photos, reviews, created_at
                    FROM places WHERE place_id = ?
                ''', (place_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                location = Location(
                    latitude=row[2],
                    longitude=row[3],
                    address=row[4],
                    city=row[5],
                    state=row[6],
                    country=row[7],
                    postal_code=row[8]
                )
                
                return Place(
                    place_id=row[0],
                    name=row[1],
                    location=location,
                    place_type=PlaceType(row[9]),
                    rating=row[10],
                    price_level=row[11],
                    phone_number=row[12],
                    website=row[13],
                    opening_hours=json.loads(row[14]) if row[14] else None,
                    photos=json.loads(row[15]) if row[15] else [],
                    reviews=json.loads(row[16]) if row[16] else [],
                    created_at=datetime.fromisoformat(row[17])
                )
        except Exception as e:
            logger.error(f"Error getting place: {e}")
            return None
    
    def search_places(self, query: str, location: Location = None, radius: float = 10.0, 
                     place_type: PlaceType = None, limit: int = 20) -> List[Place]:
        """Search for places."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build search query
                where_conditions = []
                params = []
                
                if query:
                    where_conditions.append("name LIKE ?")
                    params.append(f"%{query}%")
                
                if place_type:
                    where_conditions.append("place_type = ?")
                    params.append(place_type.value)
                
                if location:
                    # Add distance calculation (simplified)
                    where_conditions.append("""
                        (6371 * acos(cos(radians(?)) * cos(radians(latitude)) * 
                         cos(radians(longitude) - radians(?)) + sin(radians(?)) * 
                         sin(radians(latitude)))) <= ?
                    """)
                    params.extend([location.latitude, location.longitude, location.latitude, radius])
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                cursor.execute(f'''
                    SELECT place_id, name, latitude, longitude, address, city, state, country, postal_code,
                           place_type, rating, price_level, phone_number, website, opening_hours, photos, reviews, created_at
                    FROM places WHERE {where_clause}
                    ORDER BY rating DESC
                    LIMIT ?
                ''', params + [limit])
                
                places = []
                for row in cursor.fetchall():
                    location = Location(
                        latitude=row[2],
                        longitude=row[3],
                        address=row[4],
                        city=row[5],
                        state=row[6],
                        country=row[7],
                        postal_code=row[8]
                    )
                    
                    places.append(Place(
                        place_id=row[0],
                        name=row[1],
                        location=location,
                        place_type=PlaceType(row[9]),
                        rating=row[10],
                        price_level=row[11],
                        phone_number=row[12],
                        website=row[13],
                        opening_hours=json.loads(row[14]) if row[14] else None,
                        photos=json.loads(row[15]) if row[15] else [],
                        reviews=json.loads(row[16]) if row[16] else [],
                        created_at=datetime.fromisoformat(row[17])
                    ))
                
                return places
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            return []
    
    def save_route(self, route: Route) -> bool:
        """Save a route."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO routes
                    (route_id, start_latitude, start_longitude, end_latitude, end_longitude,
                     travel_mode, distance, duration, steps, traffic_info, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    route.route_id,
                    route.start_location.latitude,
                    route.start_location.longitude,
                    route.end_location.latitude,
                    route.end_location.longitude,
                    route.travel_mode.value,
                    route.distance,
                    route.duration,
                    json.dumps(route.steps),
                    json.dumps(route.traffic_info) if route.traffic_info else None,
                    route.created_at.isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving route: {e}")
            return False
    
    def get_route(self, route_id: str) -> Optional[Route]:
        """Get a route by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT route_id, start_latitude, start_longitude, end_latitude, end_longitude,
                           travel_mode, distance, duration, steps, traffic_info, created_at
                    FROM routes WHERE route_id = ?
                ''', (route_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                start_location = Location(latitude=row[1], longitude=row[2])
                end_location = Location(latitude=row[3], longitude=row[4])
                
                return Route(
                    route_id=row[0],
                    start_location=start_location,
                    end_location=end_location,
                    travel_mode=TravelMode(row[5]),
                    distance=row[6],
                    duration=row[7],
                    steps=json.loads(row[8]) if row[8] else [],
                    traffic_info=json.loads(row[9]) if row[9] else None,
                    created_at=datetime.fromisoformat(row[10])
                )
        except Exception as e:
            logger.error(f"Error getting route: {e}")
            return None
    
    def save_traffic_info(self, traffic_info: TrafficInfo) -> bool:
        """Save traffic information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO traffic_info
                    (latitude, longitude, congestion_level, speed, delay_minutes, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    traffic_info.location.latitude,
                    traffic_info.location.longitude,
                    traffic_info.congestion_level,
                    traffic_info.speed,
                    traffic_info.delay_minutes,
                    traffic_info.timestamp.isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving traffic info: {e}")
            return False
    
    def get_traffic_info(self, location: Location, radius: float = 1.0) -> List[TrafficInfo]:
        """Get traffic information for a location."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT latitude, longitude, congestion_level, speed, delay_minutes, timestamp
                    FROM traffic_info
                    WHERE (6371 * acos(cos(radians(?)) * cos(radians(latitude)) * 
                           cos(radians(longitude) - radians(?)) + sin(radians(?)) * 
                           sin(radians(latitude)))) <= ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (location.latitude, location.longitude, location.latitude, radius))
                
                traffic_info_list = []
                for row in cursor.fetchall():
                    traffic_info_list.append(TrafficInfo(
                        location=Location(latitude=row[0], longitude=row[1]),
                        congestion_level=row[2],
                        speed=row[3],
                        delay_minutes=row[4],
                        timestamp=datetime.fromisoformat(row[5])
                    ))
                
                return traffic_info_list
        except Exception as e:
            logger.error(f"Error getting traffic info: {e}")
            return []
    
    def save_search_history(self, query: str, location: Location = None, results_count: int = 0) -> bool:
        """Save search history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO search_history
                    (query, location_latitude, location_longitude, results_count, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    query,
                    location.latitude if location else None,
                    location.longitude if location else None,
                    results_count,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving search history: {e}")
            return False

class GoogleMapsService:
    """Main Google Maps service."""
    
    def __init__(self, db_path: str = "google_maps.db"):
        self.db = GoogleMapsDatabase(db_path)
        self.geocoding_cache = {}
        self.route_cache = {}
    
    def generate_id(self, prefix: str = "") -> str:
        """Generate a unique ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def geocode(self, address: str) -> Optional[Location]:
        """Convert address to coordinates (simplified geocoding)."""
        # Check cache first
        if address in self.geocoding_cache:
            return self.geocoding_cache[address]
        
        # Simplified geocoding - in a real implementation, this would call a geocoding API
        # For now, we'll use some mock coordinates based on common addresses
        mock_coordinates = {
            "1600 Amphitheatre Parkway, Mountain View, CA": Location(37.4220, -122.0841, address),
            "Times Square, New York, NY": Location(40.7580, -73.9855, address),
            "Golden Gate Bridge, San Francisco, CA": Location(37.8199, -122.4783, address),
            "Eiffel Tower, Paris, France": Location(48.8584, 2.2945, address),
            "Big Ben, London, UK": Location(51.4994, -0.1245, address),
        }
        
        if address in mock_coordinates:
            location = mock_coordinates[address]
            self.geocoding_cache[address] = location
            return location
        
        # Default fallback
        location = Location(37.7749, -122.4194, address)  # San Francisco
        self.geocoding_cache[address] = location
        return location
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Location]:
        """Convert coordinates to address (simplified reverse geocoding)."""
        # Simplified reverse geocoding
        address = f"{latitude:.4f}, {longitude:.4f}"
        return Location(latitude, longitude, address)
    
    def search_places(self, query: str, location: Location = None, radius: float = 10.0,
                     place_type: PlaceType = None, limit: int = 20) -> List[Place]:
        """Search for places."""
        places = self.db.search_places(query, location, radius, place_type, limit)
        
        # Save search history
        self.db.save_search_history(query, location, len(places))
        
        return places
    
    def get_place_details(self, place_id: str) -> Optional[Place]:
        """Get detailed information about a place."""
        return self.db.get_place(place_id)
    
    def add_place(self, name: str, location: Location, place_type: PlaceType,
                  rating: float = 0.0, price_level: int = 0, phone_number: str = None,
                  website: str = None, opening_hours: Dict[str, str] = None) -> Optional[Place]:
        """Add a new place."""
        place_id = self.generate_id("place")
        
        place = Place(
            place_id=place_id,
            name=name,
            location=location,
            place_type=place_type,
            rating=rating,
            price_level=price_level,
            phone_number=phone_number,
            website=website,
            opening_hours=opening_hours
        )
        
        if self.db.save_place(place):
            return place
        return None
    
    def calculate_route(self, start: Location, end: Location, 
                       travel_mode: TravelMode = TravelMode.DRIVING) -> Optional[Route]:
        """Calculate route between two locations."""
        # Check cache first
        cache_key = f"{start.latitude},{start.longitude}-{end.latitude},{end.longitude}-{travel_mode.value}"
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]
        
        # Calculate distance
        distance = start.distance_to(end)
        
        # Calculate duration based on travel mode (simplified)
        base_speed = {
            TravelMode.DRIVING: 50,  # km/h
            TravelMode.WALKING: 5,
            TravelMode.BICYCLING: 15,
            TravelMode.TRANSIT: 25
        }
        
        duration = int((distance / base_speed[travel_mode]) * 60)  # minutes
        
        # Generate route steps (simplified)
        steps = [
            {
                "instruction": f"Start at {start.address or 'your location'}",
                "distance": 0,
                "duration": 0
            },
            {
                "instruction": f"Head towards {end.address or 'destination'}",
                "distance": distance,
                "duration": duration
            },
            {
                "instruction": f"Arrive at {end.address or 'destination'}",
                "distance": 0,
                "duration": 0
            }
        ]
        
        route = Route(
            route_id=self.generate_id("route"),
            start_location=start,
            end_location=end,
            travel_mode=travel_mode,
            distance=distance,
            duration=duration,
            steps=steps
        )
        
        # Save route
        if self.db.save_route(route):
            self.route_cache[cache_key] = route
            return route
        
        return None
    
    def get_traffic_info(self, location: Location, radius: float = 1.0) -> List[TrafficInfo]:
        """Get traffic information for a location."""
        return self.db.get_traffic_info(location, radius)
    
    def update_traffic_info(self, location: Location, congestion_level: str, 
                           speed: float, delay_minutes: int = 0) -> bool:
        """Update traffic information for a location."""
        traffic_info = TrafficInfo(
            location=location,
            congestion_level=congestion_level,
            speed=speed,
            delay_minutes=delay_minutes,
            timestamp=datetime.now()
        )
        
        return self.db.save_traffic_info(traffic_info)
    
    def get_nearby_places(self, location: Location, radius: float = 5.0,
                          place_type: PlaceType = None) -> List[Place]:
        """Get nearby places."""
        return self.search_places("", location, radius, place_type)
    
    def get_route_alternatives(self, start: Location, end: Location) -> List[Route]:
        """Get alternative routes between two locations."""
        routes = []
        
        # Generate routes with different travel modes
        for travel_mode in TravelMode:
            route = self.calculate_route(start, end, travel_mode)
            if route:
                routes.append(route)
        
        return routes
    
    def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on query."""
        # This would typically query a search suggestions API
        # For now, return some mock suggestions
        suggestions = [
            "restaurants near me",
            "gas stations",
            "hospitals",
            "shopping malls",
            "parks",
            "hotels",
            "banks",
            "pharmacies"
        ]
        
        return [s for s in suggestions if query.lower() in s.lower()][:limit]

# Flask API
from flask import Flask, request, jsonify

app = Flask(__name__)
google_maps_service = GoogleMapsService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/geocode', methods=['POST'])
def geocode_address():
    """Geocode an address."""
    data = request.get_json()
    
    if not data or 'address' not in data:
        return jsonify({"error": "Missing address"}), 400
    
    location = google_maps_service.geocode(data['address'])
    
    if location:
        return jsonify({
            "latitude": location.latitude,
            "longitude": location.longitude,
            "address": location.address
        })
    else:
        return jsonify({"error": "Address not found"}), 404

@app.route('/reverse_geocode', methods=['POST'])
def reverse_geocode_coordinates():
    """Reverse geocode coordinates."""
    data = request.get_json()
    
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"error": "Missing latitude or longitude"}), 400
    
    location = google_maps_service.reverse_geocode(data['latitude'], data['longitude'])
    
    if location:
        return jsonify({
            "latitude": location.latitude,
            "longitude": location.longitude,
            "address": location.address
        })
    else:
        return jsonify({"error": "Location not found"}), 404

@app.route('/search', methods=['GET'])
def search_places():
    """Search for places."""
    query = request.args.get('query', '')
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    radius = request.args.get('radius', 10.0, type=float)
    place_type = request.args.get('place_type')
    limit = request.args.get('limit', 20, type=int)
    
    location = None
    if latitude is not None and longitude is not None:
        location = Location(latitude, longitude)
    
    place_type_enum = None
    if place_type:
        try:
            place_type_enum = PlaceType(place_type)
        except ValueError:
            return jsonify({"error": "Invalid place type"}), 400
    
    places = google_maps_service.search_places(query, location, radius, place_type_enum, limit)
    
    return jsonify({
        "places": [
            {
                "place_id": place.place_id,
                "name": place.name,
                "location": {
                    "latitude": place.location.latitude,
                    "longitude": place.location.longitude,
                    "address": place.location.address
                },
                "place_type": place.place_type.value,
                "rating": place.rating,
                "price_level": place.price_level
            }
            for place in places
        ],
        "count": len(places)
    })

@app.route('/places/<place_id>', methods=['GET'])
def get_place_details(place_id):
    """Get place details."""
    place = google_maps_service.get_place_details(place_id)
    
    if place:
        return jsonify({
            "place_id": place.place_id,
            "name": place.name,
            "location": {
                "latitude": place.location.latitude,
                "longitude": place.location.longitude,
                "address": place.location.address,
                "city": place.location.city,
                "state": place.location.state,
                "country": place.location.country,
                "postal_code": place.location.postal_code
            },
            "place_type": place.place_type.value,
            "rating": place.rating,
            "price_level": place.price_level,
            "phone_number": place.phone_number,
            "website": place.website,
            "opening_hours": place.opening_hours,
            "photos": place.photos,
            "reviews": place.reviews
        })
    else:
        return jsonify({"error": "Place not found"}), 404

@app.route('/routes', methods=['POST'])
def calculate_route():
    """Calculate route between two locations."""
    data = request.get_json()
    
    if not data or 'start' not in data or 'end' not in data:
        return jsonify({"error": "Missing start or end location"}), 400
    
    start_data = data['start']
    end_data = data['end']
    travel_mode = data.get('travel_mode', 'driving')
    
    try:
        travel_mode_enum = TravelMode(travel_mode)
    except ValueError:
        return jsonify({"error": "Invalid travel mode"}), 400
    
    start_location = Location(
        latitude=start_data['latitude'],
        longitude=start_data['longitude'],
        address=start_data.get('address')
    )
    
    end_location = Location(
        latitude=end_data['latitude'],
        longitude=end_data['longitude'],
        address=end_data.get('address')
    )
    
    route = google_maps_service.calculate_route(start_location, end_location, travel_mode_enum)
    
    if route:
        return jsonify({
            "route_id": route.route_id,
            "start_location": {
                "latitude": route.start_location.latitude,
                "longitude": route.start_location.longitude,
                "address": route.start_location.address
            },
            "end_location": {
                "latitude": route.end_location.latitude,
                "longitude": route.end_location.longitude,
                "address": route.end_location.address
            },
            "travel_mode": route.travel_mode.value,
            "distance": route.distance,
            "duration": route.duration,
            "steps": route.steps
        })
    else:
        return jsonify({"error": "Route not found"}), 404

@app.route('/traffic', methods=['GET'])
def get_traffic_info():
    """Get traffic information."""
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    radius = request.args.get('radius', 1.0, type=float)
    
    if latitude is None or longitude is None:
        return jsonify({"error": "Missing latitude or longitude"}), 400
    
    location = Location(latitude, longitude)
    traffic_info = google_maps_service.get_traffic_info(location, radius)
    
    return jsonify({
        "traffic_info": [
            {
                "location": {
                    "latitude": info.location.latitude,
                    "longitude": info.location.longitude
                },
                "congestion_level": info.congestion_level,
                "speed": info.speed,
                "delay_minutes": info.delay_minutes,
                "timestamp": info.timestamp.isoformat()
            }
            for info in traffic_info
        ]
    })

@app.route('/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get search suggestions."""
    query = request.args.get('query', '')
    limit = request.args.get('limit', 5, type=int)
    
    suggestions = google_maps_service.get_search_suggestions(query, limit)
    
    return jsonify({"suggestions": suggestions})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
