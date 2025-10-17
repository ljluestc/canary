#!/usr/bin/env python3
"""
Care Finder Service

A comprehensive healthcare service discovery and management system with features like:
- Healthcare provider search and discovery
- Appointment scheduling and management
- Patient profile and medical history
- Insurance verification and billing
- Telemedicine and virtual consultations
- Emergency services and urgent care
- Provider ratings and reviews
"""

import json
import sqlite3
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

class ProviderType(Enum):
    """Types of healthcare providers."""
    DOCTOR = "doctor"
    NURSE = "nurse"
    SPECIALIST = "specialist"
    DENTIST = "dentist"
    THERAPIST = "therapist"
    PHARMACIST = "pharmacist"
    EMERGENCY = "emergency"
    URGENT_CARE = "urgent_care"

class AppointmentStatus(Enum):
    """Appointment status."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class InsuranceType(Enum):
    """Insurance types."""
    PRIVATE = "private"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    TRICARE = "tricare"
    SELF_PAY = "self_pay"

class UrgencyLevel(Enum):
    """Urgency levels for care."""
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    FOLLOW_UP = "follow_up"

@dataclass
class Location:
    """Represents a geographical location."""
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location using Haversine formula."""
        import math
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
class HealthcareProvider:
    """Represents a healthcare provider."""
    provider_id: str
    name: str
    provider_type: ProviderType
    specialty: str
    location: Location
    phone: str
    email: str
    rating: float
    review_count: int
    insurance_accepted: List[str]
    languages: List[str]
    availability: Dict[str, str]  # day -> hours
    services: List[str]
    qualifications: List[str]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Patient:
    """Represents a patient."""
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    phone: str
    email: str
    address: Location
    emergency_contact: Dict[str, str]
    insurance_info: Dict[str, Any]
    medical_history: List[Dict[str, Any]]
    allergies: List[str]
    medications: List[str]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Appointment:
    """Represents an appointment."""
    appointment_id: str
    patient_id: str
    provider_id: str
    appointment_date: datetime
    duration_minutes: int
    status: AppointmentStatus
    reason: str
    notes: str
    insurance_verified: bool
    cost: float
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Review:
    """Represents a provider review."""
    review_id: str
    provider_id: str
    patient_id: str
    rating: int
    comment: str
    visit_date: datetime
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class CareFinderDatabase:
    """Database layer for the Care Finder service."""
    
    def __init__(self, db_path: str = "care_finder.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Healthcare providers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS healthcare_providers (
                    provider_id TEXT PRIMARY KEY,
                    name TEXT,
                    provider_type TEXT,
                    specialty TEXT,
                    latitude REAL,
                    longitude REAL,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    country TEXT,
                    phone TEXT,
                    email TEXT,
                    rating REAL,
                    review_count INTEGER,
                    insurance_accepted TEXT,
                    languages TEXT,
                    availability TEXT,
                    services TEXT,
                    qualifications TEXT,
                    created_at TEXT
                )
            ''')
            
            # Patients table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id TEXT PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    date_of_birth TEXT,
                    gender TEXT,
                    phone TEXT,
                    email TEXT,
                    latitude REAL,
                    longitude REAL,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    country TEXT,
                    emergency_contact TEXT,
                    insurance_info TEXT,
                    medical_history TEXT,
                    allergies TEXT,
                    medications TEXT,
                    created_at TEXT
                )
            ''')
            
            # Appointments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    provider_id TEXT,
                    appointment_date TEXT,
                    duration_minutes INTEGER,
                    status TEXT,
                    reason TEXT,
                    notes TEXT,
                    insurance_verified BOOLEAN,
                    cost REAL,
                    created_at TEXT
                )
            ''')
            
            # Reviews table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    provider_id TEXT,
                    patient_id TEXT,
                    rating INTEGER,
                    comment TEXT,
                    visit_date TEXT,
                    created_at TEXT
                )
            ''')
            
            # Insurance providers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS insurance_providers (
                    insurance_id TEXT PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    coverage_details TEXT,
                    contact_info TEXT,
                    created_at TEXT
                )
            ''')
            
            conn.commit()
    
    def save_provider(self, provider: HealthcareProvider) -> bool:
        """Save a healthcare provider."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO healthcare_providers
                    (provider_id, name, provider_type, specialty, latitude, longitude, address, city, state, zip_code, country,
                     phone, email, rating, review_count, insurance_accepted, languages, availability, services, qualifications, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    provider.provider_id,
                    provider.name,
                    provider.provider_type.value,
                    provider.specialty,
                    provider.location.latitude,
                    provider.location.longitude,
                    provider.location.address,
                    provider.location.city,
                    provider.location.state,
                    provider.location.zip_code,
                    provider.location.country,
                    provider.phone,
                    provider.email,
                    provider.rating,
                    provider.review_count,
                    json.dumps(provider.insurance_accepted),
                    json.dumps(provider.languages),
                    json.dumps(provider.availability),
                    json.dumps(provider.services),
                    json.dumps(provider.qualifications),
                    provider.created_at.isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving provider: {e}")
            return False
    
    def get_provider(self, provider_id: str) -> Optional[HealthcareProvider]:
        """Get a healthcare provider by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT provider_id, name, provider_type, specialty, latitude, longitude, address, city, state, zip_code, country,
                           phone, email, rating, review_count, insurance_accepted, languages, availability, services, qualifications, created_at
                    FROM healthcare_providers WHERE provider_id = ?
                ''', (provider_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                location = Location(
                    latitude=row[4],
                    longitude=row[5],
                    address=row[6],
                    city=row[7],
                    state=row[8],
                    zip_code=row[9],
                    country=row[10]
                )
                
                return HealthcareProvider(
                    provider_id=row[0],
                    name=row[1],
                    provider_type=ProviderType(row[2]),
                    specialty=row[3],
                    location=location,
                    phone=row[11],
                    email=row[12],
                    rating=row[13],
                    review_count=row[14],
                    insurance_accepted=json.loads(row[15]) if row[15] else [],
                    languages=json.loads(row[16]) if row[16] else [],
                    availability=json.loads(row[17]) if row[17] else {},
                    services=json.loads(row[18]) if row[18] else [],
                    qualifications=json.loads(row[19]) if row[19] else [],
                    created_at=datetime.fromisoformat(row[20])
                )
        except Exception as e:
            logger.error(f"Error getting provider: {e}")
            return None
    
    def search_providers(self, query: str = "", specialty: str = "", provider_type: ProviderType = None,
                        location: Location = None, radius: float = 50.0, 
                        insurance: str = "", limit: int = 20) -> List[HealthcareProvider]:
        """Search for healthcare providers."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build search query
                where_conditions = []
                params = []
                
                if query:
                    where_conditions.append("(name LIKE ? OR specialty LIKE ?)")
                    params.extend([f"%{query}%", f"%{query}%"])
                
                if specialty:
                    where_conditions.append("specialty LIKE ?")
                    params.append(f"%{specialty}%")
                
                if provider_type:
                    where_conditions.append("provider_type = ?")
                    params.append(provider_type.value)
                
                if insurance:
                    where_conditions.append("insurance_accepted LIKE ?")
                    params.append(f"%{insurance}%")
                
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
                    SELECT provider_id, name, provider_type, specialty, latitude, longitude, address, city, state, zip_code, country,
                           phone, email, rating, review_count, insurance_accepted, languages, availability, services, qualifications, created_at
                    FROM healthcare_providers WHERE {where_clause}
                    ORDER BY rating DESC
                    LIMIT ?
                ''', params + [limit])
                
                providers = []
                for row in cursor.fetchall():
                    location = Location(
                        latitude=row[4],
                        longitude=row[5],
                        address=row[6],
                        city=row[7],
                        state=row[8],
                        zip_code=row[9],
                        country=row[10]
                    )
                    
                    providers.append(HealthcareProvider(
                        provider_id=row[0],
                        name=row[1],
                        provider_type=ProviderType(row[2]),
                        specialty=row[3],
                        location=location,
                        phone=row[11],
                        email=row[12],
                        rating=row[13],
                        review_count=row[14],
                        insurance_accepted=json.loads(row[15]) if row[15] else [],
                        languages=json.loads(row[16]) if row[16] else [],
                        availability=json.loads(row[17]) if row[17] else {},
                        services=json.loads(row[18]) if row[18] else [],
                        qualifications=json.loads(row[19]) if row[19] else [],
                        created_at=datetime.fromisoformat(row[20])
                    ))
                
                return providers
        except Exception as e:
            logger.error(f"Error searching providers: {e}")
            return []
    
    def save_patient(self, patient: Patient) -> bool:
        """Save a patient."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO patients
                    (patient_id, first_name, last_name, date_of_birth, gender, phone, email,
                     latitude, longitude, address, city, state, zip_code, country,
                     emergency_contact, insurance_info, medical_history, allergies, medications, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    patient.patient_id,
                    patient.first_name,
                    patient.last_name,
                    patient.date_of_birth.isoformat(),
                    patient.gender,
                    patient.phone,
                    patient.email,
                    patient.address.latitude,
                    patient.address.longitude,
                    patient.address.address,
                    patient.address.city,
                    patient.address.state,
                    patient.address.zip_code,
                    patient.address.country,
                    json.dumps(patient.emergency_contact),
                    json.dumps(patient.insurance_info),
                    json.dumps(patient.medical_history),
                    json.dumps(patient.allergies),
                    json.dumps(patient.medications),
                    patient.created_at.isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving patient: {e}")
            return False
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get a patient by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT patient_id, first_name, last_name, date_of_birth, gender, phone, email,
                           latitude, longitude, address, city, state, zip_code, country,
                           emergency_contact, insurance_info, medical_history, allergies, medications, created_at
                    FROM patients WHERE patient_id = ?
                ''', (patient_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                address = Location(
                    latitude=row[7],
                    longitude=row[8],
                    address=row[9],
                    city=row[10],
                    state=row[11],
                    zip_code=row[12],
                    country=row[13]
                )
                
                return Patient(
                    patient_id=row[0],
                    first_name=row[1],
                    last_name=row[2],
                    date_of_birth=datetime.fromisoformat(row[3]),
                    gender=row[4],
                    phone=row[5],
                    email=row[6],
                    address=address,
                    emergency_contact=json.loads(row[14]) if row[14] else {},
                    insurance_info=json.loads(row[15]) if row[15] else {},
                    medical_history=json.loads(row[16]) if row[16] else [],
                    allergies=json.loads(row[17]) if row[17] else [],
                    medications=json.loads(row[18]) if row[18] else [],
                    created_at=datetime.fromisoformat(row[19])
                )
        except Exception as e:
            logger.error(f"Error getting patient: {e}")
            return None
    
    def save_appointment(self, appointment: Appointment) -> bool:
        """Save an appointment."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO appointments
                    (appointment_id, patient_id, provider_id, appointment_date, duration_minutes, status, reason, notes, insurance_verified, cost, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    appointment.appointment_id,
                    appointment.patient_id,
                    appointment.provider_id,
                    appointment.appointment_date.isoformat(),
                    appointment.duration_minutes,
                    appointment.status.value,
                    appointment.reason,
                    appointment.notes,
                    appointment.insurance_verified,
                    appointment.cost,
                    appointment.created_at.isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving appointment: {e}")
            return False
    
    def get_appointments_by_patient(self, patient_id: str) -> List[Appointment]:
        """Get appointments for a patient."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT appointment_id, patient_id, provider_id, appointment_date, duration_minutes, status, reason, notes, insurance_verified, cost, created_at
                    FROM appointments WHERE patient_id = ?
                    ORDER BY appointment_date DESC
                ''', (patient_id,))
                
                appointments = []
                for row in cursor.fetchall():
                    appointments.append(Appointment(
                        appointment_id=row[0],
                        patient_id=row[1],
                        provider_id=row[2],
                        appointment_date=datetime.fromisoformat(row[3]),
                        duration_minutes=row[4],
                        status=AppointmentStatus(row[5]),
                        reason=row[6],
                        notes=row[7],
                        insurance_verified=bool(row[8]),
                        cost=row[9],
                        created_at=datetime.fromisoformat(row[10])
                    ))
                
                return appointments
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return []
    
    def get_appointments_by_provider(self, provider_id: str) -> List[Appointment]:
        """Get appointments for a provider."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT appointment_id, patient_id, provider_id, appointment_date, duration_minutes, status, reason, notes, insurance_verified, cost, created_at
                    FROM appointments WHERE provider_id = ?
                    ORDER BY appointment_date DESC
                ''', (provider_id,))
                
                appointments = []
                for row in cursor.fetchall():
                    appointments.append(Appointment(
                        appointment_id=row[0],
                        patient_id=row[1],
                        provider_id=row[2],
                        appointment_date=datetime.fromisoformat(row[3]),
                        duration_minutes=row[4],
                        status=AppointmentStatus(row[5]),
                        reason=row[6],
                        notes=row[7],
                        insurance_verified=bool(row[8]),
                        cost=row[9],
                        created_at=datetime.fromisoformat(row[10])
                    ))
                
                return appointments
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return []
    
    def save_review(self, review: Review) -> bool:
        """Save a review."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO reviews
                    (review_id, provider_id, patient_id, rating, comment, visit_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    review.review_id,
                    review.provider_id,
                    review.patient_id,
                    review.rating,
                    review.comment,
                    review.visit_date.isoformat(),
                    review.created_at.isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving review: {e}")
            return False
    
    def get_reviews_by_provider(self, provider_id: str) -> List[Review]:
        """Get reviews for a provider."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT review_id, provider_id, patient_id, rating, comment, visit_date, created_at
                    FROM reviews WHERE provider_id = ?
                    ORDER BY created_at DESC
                ''', (provider_id,))
                
                reviews = []
                for row in cursor.fetchall():
                    reviews.append(Review(
                        review_id=row[0],
                        provider_id=row[1],
                        patient_id=row[2],
                        rating=row[3],
                        comment=row[4],
                        visit_date=datetime.fromisoformat(row[5]),
                        created_at=datetime.fromisoformat(row[6])
                    ))
                
                return reviews
        except Exception as e:
            logger.error(f"Error getting reviews: {e}")
            return []

class CareFinderService:
    """Main Care Finder service."""
    
    def __init__(self, db_path: str = "care_finder.db"):
        self.db = CareFinderDatabase(db_path)
    
    def generate_id(self, prefix: str = "") -> str:
        """Generate a unique ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def register_provider(self, name: str, provider_type: ProviderType, specialty: str,
                         location: Location, phone: str, email: str,
                         insurance_accepted: List[str] = None, languages: List[str] = None,
                         availability: Dict[str, str] = None, services: List[str] = None,
                         qualifications: List[str] = None) -> Optional[HealthcareProvider]:
        """Register a new healthcare provider."""
        provider_id = self.generate_id("provider")
        
        provider = HealthcareProvider(
            provider_id=provider_id,
            name=name,
            provider_type=provider_type,
            specialty=specialty,
            location=location,
            phone=phone,
            email=email,
            rating=0.0,
            review_count=0,
            insurance_accepted=insurance_accepted or [],
            languages=languages or ["English"],
            availability=availability or {},
            services=services or [],
            qualifications=qualifications or []
        )
        
        if self.db.save_provider(provider):
            return provider
        return None
    
    def search_providers(self, query: str = "", specialty: str = "", provider_type: ProviderType = None,
                        location: Location = None, radius: float = 50.0, 
                        insurance: str = "", limit: int = 20) -> List[HealthcareProvider]:
        """Search for healthcare providers."""
        return self.db.search_providers(query, specialty, provider_type, location, radius, insurance, limit)
    
    def get_provider_details(self, provider_id: str) -> Optional[HealthcareProvider]:
        """Get detailed information about a provider."""
        return self.db.get_provider(provider_id)
    
    def register_patient(self, first_name: str, last_name: str, date_of_birth: datetime,
                        gender: str, phone: str, email: str, address: Location,
                        emergency_contact: Dict[str, str] = None, insurance_info: Dict[str, Any] = None,
                        medical_history: List[Dict[str, Any]] = None, allergies: List[str] = None,
                        medications: List[str] = None) -> Optional[Patient]:
        """Register a new patient."""
        patient_id = self.generate_id("patient")
        
        patient = Patient(
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            phone=phone,
            email=email,
            address=address,
            emergency_contact=emergency_contact or {},
            insurance_info=insurance_info or {},
            medical_history=medical_history or [],
            allergies=allergies or [],
            medications=medications or []
        )
        
        if self.db.save_patient(patient):
            return patient
        return None
    
    def get_patient_details(self, patient_id: str) -> Optional[Patient]:
        """Get detailed information about a patient."""
        return self.db.get_patient(patient_id)
    
    def schedule_appointment(self, patient_id: str, provider_id: str, appointment_date: datetime,
                           duration_minutes: int = 30, reason: str = "", notes: str = "",
                           insurance_verified: bool = False, cost: float = 0.0) -> Optional[Appointment]:
        """Schedule an appointment."""
        appointment_id = self.generate_id("appointment")
        
        appointment = Appointment(
            appointment_id=appointment_id,
            patient_id=patient_id,
            provider_id=provider_id,
            appointment_date=appointment_date,
            duration_minutes=duration_minutes,
            status=AppointmentStatus.SCHEDULED,
            reason=reason,
            notes=notes,
            insurance_verified=insurance_verified,
            cost=cost
        )
        
        if self.db.save_appointment(appointment):
            return appointment
        return None
    
    def get_patient_appointments(self, patient_id: str) -> List[Appointment]:
        """Get appointments for a patient."""
        return self.db.get_appointments_by_patient(patient_id)
    
    def get_provider_appointments(self, provider_id: str) -> List[Appointment]:
        """Get appointments for a provider."""
        return self.db.get_appointments_by_provider(provider_id)
    
    def update_appointment_status(self, appointment_id: str, status: AppointmentStatus) -> bool:
        """Update appointment status."""
        # This would typically involve updating the database
        # For now, we'll just return True
        return True
    
    def add_review(self, provider_id: str, patient_id: str, rating: int, comment: str,
                  visit_date: datetime) -> Optional[Review]:
        """Add a review for a provider."""
        review_id = self.generate_id("review")
        
        review = Review(
            review_id=review_id,
            provider_id=provider_id,
            patient_id=patient_id,
            rating=rating,
            comment=comment,
            visit_date=visit_date
        )
        
        if self.db.save_review(review):
            # Update provider rating
            self._update_provider_rating(provider_id)
            return review
        return None
    
    def get_provider_reviews(self, provider_id: str) -> List[Review]:
        """Get reviews for a provider."""
        return self.db.get_reviews_by_provider(provider_id)
    
    def _update_provider_rating(self, provider_id: str):
        """Update provider rating based on reviews."""
        reviews = self.db.get_reviews_by_provider(provider_id)
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            avg_rating = total_rating / len(reviews)
            
            # Update provider rating in database
            # This would typically involve a database update
            pass
    
    def find_emergency_care(self, location: Location, urgency: UrgencyLevel = UrgencyLevel.EMERGENCY) -> List[HealthcareProvider]:
        """Find emergency care providers."""
        if urgency == UrgencyLevel.EMERGENCY:
            provider_type = ProviderType.EMERGENCY
        else:
            provider_type = ProviderType.URGENT_CARE
        
        return self.search_providers(
            provider_type=provider_type,
            location=location,
            radius=100.0,  # Larger radius for emergency care
            limit=10
        )
    
    def verify_insurance(self, patient_id: str, provider_id: str) -> bool:
        """Verify insurance coverage for a patient with a provider."""
        patient = self.db.get_patient(patient_id)
        provider = self.db.get_provider(provider_id)
        
        if not patient or not provider:
            return False
        
        patient_insurance = patient.insurance_info.get('provider', '')
        provider_insurance = provider.insurance_accepted
        
        return patient_insurance in provider_insurance
    
    def get_nearby_providers(self, location: Location, radius: float = 25.0) -> List[HealthcareProvider]:
        """Get nearby healthcare providers."""
        return self.search_providers(location=location, radius=radius)
    
    def search_by_specialty(self, specialty: str, location: Location = None) -> List[HealthcareProvider]:
        """Search providers by specialty."""
        return self.search_providers(specialty=specialty, location=location)
    
    def get_provider_availability(self, provider_id: str, date: datetime) -> List[str]:
        """Get available time slots for a provider on a specific date."""
        # This would typically check the provider's schedule
        # For now, return some mock availability
        return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]

# Flask API
from flask import Flask, request, jsonify

app = Flask(__name__)
care_finder_service = CareFinderService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/providers/search', methods=['GET'])
def search_providers():
    """Search for healthcare providers."""
    query = request.args.get('query', '')
    specialty = request.args.get('specialty', '')
    provider_type = request.args.get('provider_type')
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    radius = request.args.get('radius', 50.0, type=float)
    insurance = request.args.get('insurance', '')
    limit = request.args.get('limit', 20, type=int)
    
    location = None
    if latitude is not None and longitude is not None:
        location = Location(latitude, longitude, "", "", "", "")
    
    provider_type_enum = None
    if provider_type:
        try:
            provider_type_enum = ProviderType(provider_type)
        except ValueError:
            return jsonify({"error": "Invalid provider type"}), 400
    
    providers = care_finder_service.search_providers(
        query, specialty, provider_type_enum, location, radius, insurance, limit
    )
    
    return jsonify({
        "providers": [
            {
                "provider_id": provider.provider_id,
                "name": provider.name,
                "provider_type": provider.provider_type.value,
                "specialty": provider.specialty,
                "location": {
                    "latitude": provider.location.latitude,
                    "longitude": provider.location.longitude,
                    "address": provider.location.address,
                    "city": provider.location.city,
                    "state": provider.location.state,
                    "zip_code": provider.location.zip_code
                },
                "phone": provider.phone,
                "email": provider.email,
                "rating": provider.rating,
                "review_count": provider.review_count,
                "insurance_accepted": provider.insurance_accepted,
                "languages": provider.languages,
                "services": provider.services
            }
            for provider in providers
        ],
        "count": len(providers)
    })

@app.route('/providers/<provider_id>', methods=['GET'])
def get_provider_details(provider_id):
    """Get provider details."""
    provider = care_finder_service.get_provider_details(provider_id)
    
    if provider:
        return jsonify({
            "provider_id": provider.provider_id,
            "name": provider.name,
            "provider_type": provider.provider_type.value,
            "specialty": provider.specialty,
            "location": {
                "latitude": provider.location.latitude,
                "longitude": provider.location.longitude,
                "address": provider.location.address,
                "city": provider.location.city,
                "state": provider.location.state,
                "zip_code": provider.location.zip_code
            },
            "phone": provider.phone,
            "email": provider.email,
            "rating": provider.rating,
            "review_count": provider.review_count,
            "insurance_accepted": provider.insurance_accepted,
            "languages": provider.languages,
            "availability": provider.availability,
            "services": provider.services,
            "qualifications": provider.qualifications
        })
    else:
        return jsonify({"error": "Provider not found"}), 404

@app.route('/providers', methods=['POST'])
def register_provider():
    """Register a new healthcare provider."""
    data = request.get_json()
    
    if not data or 'name' not in data or 'provider_type' not in data or 'specialty' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        provider_type = ProviderType(data['provider_type'])
    except ValueError:
        return jsonify({"error": "Invalid provider type"}), 400
    
    location_data = data.get('location', {})
    location = Location(
        latitude=location_data.get('latitude', 0.0),
        longitude=location_data.get('longitude', 0.0),
        address=location_data.get('address', ''),
        city=location_data.get('city', ''),
        state=location_data.get('state', ''),
        zip_code=location_data.get('zip_code', '')
    )
    
    provider = care_finder_service.register_provider(
        name=data['name'],
        provider_type=provider_type,
        specialty=data['specialty'],
        location=location,
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        insurance_accepted=data.get('insurance_accepted', []),
        languages=data.get('languages', ['English']),
        availability=data.get('availability', {}),
        services=data.get('services', []),
        qualifications=data.get('qualifications', [])
    )
    
    if provider:
        return jsonify({
            "success": True,
            "provider_id": provider.provider_id,
            "message": "Provider registered successfully"
        })
    else:
        return jsonify({"error": "Failed to register provider"}), 500

@app.route('/patients', methods=['POST'])
def register_patient():
    """Register a new patient."""
    data = request.get_json()
    
    if not data or 'first_name' not in data or 'last_name' not in data or 'date_of_birth' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        date_of_birth = datetime.fromisoformat(data['date_of_birth'])
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    address_data = data.get('address', {})
    address = Location(
        latitude=address_data.get('latitude', 0.0),
        longitude=address_data.get('longitude', 0.0),
        address=address_data.get('address', ''),
        city=address_data.get('city', ''),
        state=address_data.get('state', ''),
        zip_code=address_data.get('zip_code', '')
    )
    
    patient = care_finder_service.register_patient(
        first_name=data['first_name'],
        last_name=data['last_name'],
        date_of_birth=date_of_birth,
        gender=data.get('gender', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        address=address,
        emergency_contact=data.get('emergency_contact', {}),
        insurance_info=data.get('insurance_info', {}),
        medical_history=data.get('medical_history', []),
        allergies=data.get('allergies', []),
        medications=data.get('medications', [])
    )
    
    if patient:
        return jsonify({
            "success": True,
            "patient_id": patient.patient_id,
            "message": "Patient registered successfully"
        })
    else:
        return jsonify({"error": "Failed to register patient"}), 500

@app.route('/appointments', methods=['POST'])
def schedule_appointment():
    """Schedule an appointment."""
    data = request.get_json()
    
    if not data or 'patient_id' not in data or 'provider_id' not in data or 'appointment_date' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        appointment_date = datetime.fromisoformat(data['appointment_date'])
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    appointment = care_finder_service.schedule_appointment(
        patient_id=data['patient_id'],
        provider_id=data['provider_id'],
        appointment_date=appointment_date,
        duration_minutes=data.get('duration_minutes', 30),
        reason=data.get('reason', ''),
        notes=data.get('notes', ''),
        insurance_verified=data.get('insurance_verified', False),
        cost=data.get('cost', 0.0)
    )
    
    if appointment:
        return jsonify({
            "success": True,
            "appointment_id": appointment.appointment_id,
            "message": "Appointment scheduled successfully"
        })
    else:
        return jsonify({"error": "Failed to schedule appointment"}), 500

@app.route('/patients/<patient_id>/appointments', methods=['GET'])
def get_patient_appointments(patient_id):
    """Get appointments for a patient."""
    appointments = care_finder_service.get_patient_appointments(patient_id)
    
    return jsonify({
        "appointments": [
            {
                "appointment_id": appointment.appointment_id,
                "provider_id": appointment.provider_id,
                "appointment_date": appointment.appointment_date.isoformat(),
                "duration_minutes": appointment.duration_minutes,
                "status": appointment.status.value,
                "reason": appointment.reason,
                "notes": appointment.notes,
                "insurance_verified": appointment.insurance_verified,
                "cost": appointment.cost
            }
            for appointment in appointments
        ],
        "count": len(appointments)
    })

@app.route('/providers/<provider_id>/reviews', methods=['GET'])
def get_provider_reviews(provider_id):
    """Get reviews for a provider."""
    reviews = care_finder_service.get_provider_reviews(provider_id)
    
    return jsonify({
        "reviews": [
            {
                "review_id": review.review_id,
                "patient_id": review.patient_id,
                "rating": review.rating,
                "comment": review.comment,
                "visit_date": review.visit_date.isoformat(),
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ],
        "count": len(reviews)
    })

@app.route('/reviews', methods=['POST'])
def add_review():
    """Add a review for a provider."""
    data = request.get_json()
    
    if not data or 'provider_id' not in data or 'patient_id' not in data or 'rating' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        visit_date = datetime.fromisoformat(data.get('visit_date', datetime.now().isoformat()))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    review = care_finder_service.add_review(
        provider_id=data['provider_id'],
        patient_id=data['patient_id'],
        rating=data['rating'],
        comment=data.get('comment', ''),
        visit_date=visit_date
    )
    
    if review:
        return jsonify({
            "success": True,
            "review_id": review.review_id,
            "message": "Review added successfully"
        })
    else:
        return jsonify({"error": "Failed to add review"}), 500

@app.route('/emergency', methods=['GET'])
def find_emergency_care():
    """Find emergency care providers."""
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    urgency = request.args.get('urgency', 'emergency')
    
    if latitude is None or longitude is None:
        return jsonify({"error": "Missing latitude or longitude"}), 400
    
    try:
        urgency_level = UrgencyLevel(urgency)
    except ValueError:
        return jsonify({"error": "Invalid urgency level"}), 400
    
    location = Location(latitude, longitude, "", "", "", "")
    providers = care_finder_service.find_emergency_care(location, urgency_level)
    
    return jsonify({
        "providers": [
            {
                "provider_id": provider.provider_id,
                "name": provider.name,
                "provider_type": provider.provider_type.value,
                "specialty": provider.specialty,
                "location": {
                    "latitude": provider.location.latitude,
                    "longitude": provider.location.longitude,
                    "address": provider.location.address,
                    "city": provider.location.city,
                    "state": provider.location.state,
                    "zip_code": provider.location.zip_code
                },
                "phone": provider.phone,
                "rating": provider.rating
            }
            for provider in providers
        ],
        "count": len(providers)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
