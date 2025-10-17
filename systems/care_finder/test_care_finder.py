#!/usr/bin/env python3
"""
Comprehensive tests for the Care Finder system.
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

from care_finder_service import (
    CareFinderService, CareFinderDatabase, HealthcareProvider, Patient, Appointment, Review,
    Location, ProviderType, AppointmentStatus, InsuranceType, UrgencyLevel
)

class TestLocation(unittest.TestCase):
    """Test Location class."""
    
    def test_location_creation(self):
        """Test creating a Location."""
        location = Location(
            latitude=37.7749,
            longitude=-122.4194,
            address="123 Main St",
            city="San Francisco",
            state="CA",
            zip_code="94102"
        )
        
        self.assertEqual(location.latitude, 37.7749)
        self.assertEqual(location.longitude, -122.4194)
        self.assertEqual(location.address, "123 Main St")
        self.assertEqual(location.city, "San Francisco")
        self.assertEqual(location.state, "CA")
        self.assertEqual(location.zip_code, "94102")
        self.assertEqual(location.country, "USA")
    
    def test_location_distance_calculation(self):
        """Test distance calculation between locations."""
        sf = Location(37.7749, -122.4194, "San Francisco, CA", "San Francisco", "CA", "94102")
        ny = Location(40.7128, -74.0060, "New York, NY", "New York", "NY", "10001")
        
        distance = sf.distance_to(ny)
        
        # Distance should be approximately 4135 km
        self.assertAlmostEqual(distance, 4135, delta=100)
    
    def test_location_distance_same_location(self):
        """Test distance calculation for same location."""
        location = Location(37.7749, -122.4194, "San Francisco, CA", "San Francisco", "CA", "94102")
        distance = location.distance_to(location)
        
        self.assertEqual(distance, 0.0)

class TestHealthcareProvider(unittest.TestCase):
    """Test HealthcareProvider class."""
    
    def test_healthcare_provider_creation(self):
        """Test creating a HealthcareProvider."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = HealthcareProvider(
            provider_id="provider_1",
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com",
            rating=4.5,
            review_count=100,
            insurance_accepted=["Blue Cross", "Aetna"],
            languages=["English", "Spanish"],
            availability={"monday": "9:00-17:00", "tuesday": "9:00-17:00"},
            services=["Consultation", "Diagnosis"],
            qualifications=["MD", "Board Certified"]
        )
        
        self.assertEqual(provider.provider_id, "provider_1")
        self.assertEqual(provider.name, "Dr. John Smith")
        self.assertEqual(provider.provider_type, ProviderType.DOCTOR)
        self.assertEqual(provider.specialty, "Cardiology")
        self.assertEqual(provider.rating, 4.5)
        self.assertEqual(provider.review_count, 100)
        self.assertEqual(provider.insurance_accepted, ["Blue Cross", "Aetna"])
        self.assertEqual(provider.languages, ["English", "Spanish"])
        self.assertEqual(provider.availability, {"monday": "9:00-17:00", "tuesday": "9:00-17:00"})
        self.assertEqual(provider.services, ["Consultation", "Diagnosis"])
        self.assertEqual(provider.qualifications, ["MD", "Board Certified"])

class TestPatient(unittest.TestCase):
    """Test Patient class."""
    
    def test_patient_creation(self):
        """Test creating a Patient."""
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = Patient(
            patient_id="patient_1",
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address,
            emergency_contact={"name": "John Doe", "phone": "555-9999"},
            insurance_info={"provider": "Blue Cross", "policy_number": "123456"},
            medical_history=["Hypertension", "Diabetes"],
            allergies=["Penicillin"],
            medications=["Lisinopril", "Metformin"]
        )
        
        self.assertEqual(patient.patient_id, "patient_1")
        self.assertEqual(patient.first_name, "Jane")
        self.assertEqual(patient.last_name, "Doe")
        self.assertEqual(patient.gender, "Female")
        self.assertEqual(patient.phone, "555-5678")
        self.assertEqual(patient.email, "jane.doe@email.com")
        self.assertEqual(patient.emergency_contact, {"name": "John Doe", "phone": "555-9999"})
        self.assertEqual(patient.insurance_info, {"provider": "Blue Cross", "policy_number": "123456"})
        self.assertEqual(patient.medical_history, ["Hypertension", "Diabetes"])
        self.assertEqual(patient.allergies, ["Penicillin"])
        self.assertEqual(patient.medications, ["Lisinopril", "Metformin"])

class TestAppointment(unittest.TestCase):
    """Test Appointment class."""
    
    def test_appointment_creation(self):
        """Test creating an Appointment."""
        appointment = Appointment(
            appointment_id="appointment_1",
            patient_id="patient_1",
            provider_id="provider_1",
            appointment_date=datetime(2024, 1, 15, 10, 0),
            duration_minutes=30,
            status=AppointmentStatus.SCHEDULED,
            reason="Annual checkup",
            notes="Regular checkup",
            insurance_verified=True,
            cost=150.0
        )
        
        self.assertEqual(appointment.appointment_id, "appointment_1")
        self.assertEqual(appointment.patient_id, "patient_1")
        self.assertEqual(appointment.provider_id, "provider_1")
        self.assertEqual(appointment.status, AppointmentStatus.SCHEDULED)
        self.assertEqual(appointment.reason, "Annual checkup")
        self.assertEqual(appointment.insurance_verified, True)
        self.assertEqual(appointment.cost, 150.0)

class TestReview(unittest.TestCase):
    """Test Review class."""
    
    def test_review_creation(self):
        """Test creating a Review."""
        review = Review(
            review_id="review_1",
            provider_id="provider_1",
            patient_id="patient_1",
            rating=5,
            comment="Excellent care!",
            visit_date=datetime(2024, 1, 10)
        )
        
        self.assertEqual(review.review_id, "review_1")
        self.assertEqual(review.provider_id, "provider_1")
        self.assertEqual(review.patient_id, "patient_1")
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Excellent care!")

class TestCareFinderDatabase(unittest.TestCase):
    """Test CareFinderDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = CareFinderDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization."""
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_and_get_provider(self):
        """Test saving and retrieving healthcare providers."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = HealthcareProvider(
            provider_id="provider_1",
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com",
            rating=4.5,
            review_count=100,
            insurance_accepted=["Blue Cross", "Aetna"],
            languages=["English", "Spanish"],
            availability={"monday": "9:00-17:00", "tuesday": "9:00-17:00"},
            services=["Consultation", "Diagnosis"],
            qualifications=["MD", "Board Certified"]
        )
        
        # Save provider
        success = self.db.save_provider(provider)
        self.assertTrue(success)
        
        # Retrieve provider
        retrieved = self.db.get_provider("provider_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.provider_id, "provider_1")
        self.assertEqual(retrieved.name, "Dr. John Smith")
        self.assertEqual(retrieved.provider_type, ProviderType.DOCTOR)
        self.assertEqual(retrieved.specialty, "Cardiology")
    
    def test_search_providers(self):
        """Test searching providers."""
        # Add some test providers
        locations = [
            Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102"),
            Location(37.7849, -122.4094, "456 Oak St", "Oakland", "CA", "94601"),
            Location(37.7949, -122.3994, "789 Pine St", "Berkeley", "CA", "94701")
        ]
        
        for i, location in enumerate(locations):
            provider = HealthcareProvider(
                provider_id=f"provider_{i}",
                name=f"Dr. Smith {i}",
                provider_type=ProviderType.DOCTOR,
                specialty="Cardiology",
                location=location,
                phone=f"555-{1000+i}",
                email=f"doctor{i}@hospital.com",
                rating=4.0 + i * 0.1,
                review_count=50 + i * 10,
                insurance_accepted=["Blue Cross", "Aetna"],
                languages=["English", "Spanish"],
                availability={"monday": "9:00-17:00", "tuesday": "9:00-17:00"},
                services=["Consultation", "Diagnosis"],
                qualifications=["MD", "Board Certified"]
            )
            self.db.save_provider(provider)
        
        # Search for providers
        providers = self.db.search_providers("Smith", provider_type=ProviderType.DOCTOR)
        self.assertEqual(len(providers), 3)
        
        # Search with location and radius
        search_location = Location(37.7749, -122.4194, "", "", "", "")
        nearby_providers = self.db.search_providers("", location=search_location, radius=50.0)
        self.assertEqual(len(nearby_providers), 3)
    
    def test_save_and_get_patient(self):
        """Test saving and retrieving patients."""
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = Patient(
            patient_id="patient_1",
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address,
            emergency_contact={"name": "John Doe", "phone": "555-9999"},
            insurance_info={"provider": "Blue Cross", "policy_number": "123456"},
            medical_history=["Hypertension", "Diabetes"],
            allergies=["Penicillin"],
            medications=["Lisinopril", "Metformin"]
        )
        
        # Save patient
        success = self.db.save_patient(patient)
        self.assertTrue(success)
        
        # Retrieve patient
        retrieved = self.db.get_patient("patient_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.patient_id, "patient_1")
        self.assertEqual(retrieved.first_name, "Jane")
        self.assertEqual(retrieved.last_name, "Doe")
    
    def test_save_and_get_appointment(self):
        """Test saving and retrieving appointments."""
        appointment = Appointment(
            appointment_id="appointment_1",
            patient_id="patient_1",
            provider_id="provider_1",
            appointment_date=datetime(2024, 1, 15, 10, 0),
            duration_minutes=30,
            status=AppointmentStatus.SCHEDULED,
            reason="Annual checkup",
            notes="Regular checkup",
            insurance_verified=True,
            cost=150.0
        )
        
        # Save appointment
        success = self.db.save_appointment(appointment)
        self.assertTrue(success)
        
        # Retrieve appointments by patient
        patient_appointments = self.db.get_appointments_by_patient("patient_1")
        self.assertEqual(len(patient_appointments), 1)
        self.assertEqual(patient_appointments[0].appointment_id, "appointment_1")
        
        # Retrieve appointments by provider
        provider_appointments = self.db.get_appointments_by_provider("provider_1")
        self.assertEqual(len(provider_appointments), 1)
        self.assertEqual(provider_appointments[0].appointment_id, "appointment_1")
    
    def test_save_and_get_review(self):
        """Test saving and retrieving reviews."""
        review = Review(
            review_id="review_1",
            provider_id="provider_1",
            patient_id="patient_1",
            rating=5,
            comment="Excellent care!",
            visit_date=datetime(2024, 1, 10)
        )
        
        # Save review
        success = self.db.save_review(review)
        self.assertTrue(success)
        
        # Retrieve reviews by provider
        provider_reviews = self.db.get_reviews_by_provider("provider_1")
        self.assertEqual(len(provider_reviews), 1)
        self.assertEqual(provider_reviews[0].review_id, "review_1")
        self.assertEqual(provider_reviews[0].rating, 5)

class TestCareFinderService(unittest.TestCase):
    """Test CareFinderService class."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CareFinderService(self.temp_db.name)
    
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
    
    def test_register_provider(self):
        """Test registering a healthcare provider."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com"
        )
        
        self.assertIsNotNone(provider)
        self.assertEqual(provider.name, "Dr. John Smith")
        self.assertEqual(provider.provider_type, ProviderType.DOCTOR)
        self.assertEqual(provider.specialty, "Cardiology")
    
    def test_search_providers(self):
        """Test searching for providers."""
        # Add some test providers
        locations = [
            Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102"),
            Location(37.7849, -122.4094, "456 Oak St", "Oakland", "CA", "94601")
        ]
        
        for i, location in enumerate(locations):
            self.service.register_provider(
                name=f"Dr. Smith {i}",
                provider_type=ProviderType.DOCTOR,
                specialty="Cardiology",
                location=location,
                phone=f"555-{1000+i}",
                email=f"doctor{i}@hospital.com"
            )
        
        # Search for providers
        providers = self.service.search_providers("Smith", provider_type=ProviderType.DOCTOR)
        self.assertEqual(len(providers), 2)
    
    def test_get_provider_details(self):
        """Test getting provider details."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com"
        )
        
        retrieved = self.service.get_provider_details(provider.provider_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Dr. John Smith")
    
    def test_register_patient(self):
        """Test registering a patient."""
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        self.assertIsNotNone(patient)
        self.assertEqual(patient.first_name, "Jane")
        self.assertEqual(patient.last_name, "Doe")
    
    def test_get_patient_details(self):
        """Test getting patient details."""
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        retrieved = self.service.get_patient_details(patient.patient_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.first_name, "Jane")
    
    def test_schedule_appointment(self):
        """Test scheduling an appointment."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com"
        )
        
        # Schedule appointment
        appointment = self.service.schedule_appointment(
            patient_id=patient.patient_id,
            provider_id=provider.provider_id,
            appointment_date=datetime(2024, 1, 15, 10, 0),
            reason="Annual checkup"
        )
        
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.patient_id, patient.patient_id)
        self.assertEqual(appointment.provider_id, provider.provider_id)
        self.assertEqual(appointment.status, AppointmentStatus.SCHEDULED)
    
    def test_get_patient_appointments(self):
        """Test getting patient appointments."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com"
        )
        
        # Schedule appointment
        appointment = self.service.schedule_appointment(
            patient_id=patient.patient_id,
            provider_id=provider.provider_id,
            appointment_date=datetime(2024, 1, 15, 10, 0),
            reason="Annual checkup"
        )
        
        # Get patient appointments
        appointments = self.service.get_patient_appointments(patient.patient_id)
        self.assertEqual(len(appointments), 1)
        self.assertEqual(appointments[0].appointment_id, appointment.appointment_id)
    
    def test_add_review(self):
        """Test adding a review."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com"
        )
        
        # Add review
        review = self.service.add_review(
            provider_id=provider.provider_id,
            patient_id=patient.patient_id,
            rating=5,
            comment="Excellent care!",
            visit_date=datetime(2024, 1, 10)
        )
        
        self.assertIsNotNone(review)
        self.assertEqual(review.provider_id, provider.provider_id)
        self.assertEqual(review.patient_id, patient.patient_id)
        self.assertEqual(review.rating, 5)
    
    def test_get_provider_reviews(self):
        """Test getting provider reviews."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com"
        )
        
        # Add review
        review = self.service.add_review(
            provider_id=provider.provider_id,
            patient_id=patient.patient_id,
            rating=5,
            comment="Excellent care!",
            visit_date=datetime(2024, 1, 10)
        )
        
        # Get provider reviews
        reviews = self.service.get_provider_reviews(provider.provider_id)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].review_id, review.review_id)
    
    def test_find_emergency_care(self):
        """Test finding emergency care."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        
        # Add emergency provider
        emergency_provider = self.service.register_provider(
            name="Emergency Room",
            provider_type=ProviderType.EMERGENCY,
            specialty="Emergency Medicine",
            location=location,
            phone="555-911",
            email="emergency@hospital.com"
        )
        
        # Find emergency care
        emergency_providers = self.service.find_emergency_care(location, UrgencyLevel.EMERGENCY)
        self.assertEqual(len(emergency_providers), 1)
        self.assertEqual(emergency_providers[0].provider_type, ProviderType.EMERGENCY)
    
    def test_verify_insurance(self):
        """Test insurance verification."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address,
            insurance_info={"provider": "Blue Cross"}
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. John Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="john.smith@hospital.com",
            insurance_accepted=["Blue Cross", "Aetna"]
        )
        
        # Verify insurance
        verified = self.service.verify_insurance(patient.patient_id, provider.provider_id)
        self.assertTrue(verified)
    
    def test_get_nearby_providers(self):
        """Test getting nearby providers."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        
        # Add nearby provider
        nearby_provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        # Get nearby providers
        nearby_providers = self.service.get_nearby_providers(location)
        self.assertEqual(len(nearby_providers), 1)
        self.assertEqual(nearby_providers[0].provider_id, nearby_provider.provider_id)
    
    def test_search_by_specialty(self):
        """Test searching by specialty."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        
        # Add cardiology provider
        cardiology_provider = self.service.register_provider(
            name="Dr. Heart",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="heart@hospital.com"
        )
        
        # Search by specialty
        cardiology_providers = self.service.search_by_specialty("Cardiology", location)
        self.assertEqual(len(cardiology_providers), 1)
        self.assertEqual(cardiology_providers[0].specialty, "Cardiology")
    
    def test_get_provider_availability(self):
        """Test getting provider availability."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        # Get availability
        availability = self.service.get_provider_availability(provider.provider_id, datetime(2024, 1, 15))
        self.assertIsInstance(availability, list)
        self.assertGreater(len(availability), 0)

class TestFlaskApp(unittest.TestCase):
    """Test Flask API endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create service with temp database
        self.service = CareFinderService(self.temp_db.name)
        
        # Import and configure Flask app
        from care_finder_service import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Replace the global service instance used by Flask with our test service
        from care_finder_service import care_finder_service
        care_finder_service.db = self.service.db
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_health_check_api(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_search_providers_api(self):
        """Test search providers endpoint."""
        # Add some test providers
        locations = [
            Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102"),
            Location(37.7849, -122.4094, "456 Oak St", "Oakland", "CA", "94601")
        ]
        
        for i, location in enumerate(locations):
            self.service.register_provider(
                name=f"Dr. Smith {i}",
                provider_type=ProviderType.DOCTOR,
                specialty="Cardiology",
                location=location,
                phone=f"555-{1000+i}",
                email=f"doctor{i}@hospital.com"
            )
        
        response = self.client.get('/providers/search?query=Smith&provider_type=doctor')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['providers']), 2)
    
    def test_search_providers_with_location_api(self):
        """Test search providers endpoint with location."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        response = self.client.get('/providers/search?latitude=37.7749&longitude=-122.4194&radius=10.0')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['providers'][0]['name'], 'Dr. Smith')
    
    def test_get_provider_details_api(self):
        """Test get provider details endpoint."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        response = self.client.get(f'/providers/{provider.provider_id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['name'], 'Dr. Smith')
        self.assertEqual(data['specialty'], 'Cardiology')
    
    def test_get_provider_details_not_found_api(self):
        """Test get provider details endpoint for non-existent provider."""
        response = self.client.get('/providers/nonexistent_provider_id')
        self.assertEqual(response.status_code, 404)
        
        data = response.get_json()
        self.assertEqual(data['error'], 'Provider not found')
    
    def test_register_provider_api(self):
        """Test register provider endpoint."""
        data = {
            'name': 'Dr. Smith',
            'provider_type': 'doctor',
            'specialty': 'Cardiology',
            'location': {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'address': '123 Main St',
                'city': 'San Francisco',
                'state': 'CA',
                'zip_code': '94102'
            },
            'phone': '555-1234',
            'email': 'doctor@hospital.com'
        }
        
        response = self.client.post('/providers', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('provider_id', result)
    
    def test_register_provider_missing_data_api(self):
        """Test register provider endpoint with missing data."""
        data = {'name': 'Dr. Smith'}  # Missing required fields
        
        response = self.client.post('/providers', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing required fields')
    
    def test_register_patient_api(self):
        """Test register patient endpoint."""
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01T00:00:00',
            'gender': 'Female',
            'phone': '555-5678',
            'email': 'jane.doe@email.com',
            'address': {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'address': '456 Oak St',
                'city': 'San Francisco',
                'state': 'CA',
                'zip_code': '94103'
            }
        }
        
        response = self.client.post('/patients', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('patient_id', result)
    
    def test_register_patient_missing_data_api(self):
        """Test register patient endpoint with missing data."""
        data = {'first_name': 'Jane'}  # Missing required fields
        
        response = self.client.post('/patients', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing required fields')
    
    def test_schedule_appointment_api(self):
        """Test schedule appointment endpoint."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        data = {
            'patient_id': patient.patient_id,
            'provider_id': provider.provider_id,
            'appointment_date': '2024-01-15T10:00:00',
            'reason': 'Annual checkup'
        }
        
        response = self.client.post('/appointments', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('appointment_id', result)
    
    def test_schedule_appointment_missing_data_api(self):
        """Test schedule appointment endpoint with missing data."""
        data = {'patient_id': 'patient_1'}  # Missing required fields
        
        response = self.client.post('/appointments', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing required fields')
    
    def test_get_patient_appointments_api(self):
        """Test get patient appointments endpoint."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        # Schedule appointment
        appointment = self.service.schedule_appointment(
            patient_id=patient.patient_id,
            provider_id=provider.provider_id,
            appointment_date=datetime(2024, 1, 15, 10, 0),
            reason="Annual checkup"
        )
        
        response = self.client.get(f'/patients/{patient.patient_id}/appointments')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['appointments']), 1)
    
    def test_get_provider_reviews_api(self):
        """Test get provider reviews endpoint."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        # Add review
        review = self.service.add_review(
            provider_id=provider.provider_id,
            patient_id=patient.patient_id,
            rating=5,
            comment="Excellent care!",
            visit_date=datetime(2024, 1, 10)
        )
        
        response = self.client.get(f'/providers/{provider.provider_id}/reviews')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['reviews']), 1)
    
    def test_add_review_api(self):
        """Test add review endpoint."""
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        data = {
            'provider_id': provider.provider_id,
            'patient_id': patient.patient_id,
            'rating': 5,
            'comment': 'Excellent care!',
            'visit_date': '2024-01-10T00:00:00'
        }
        
        response = self.client.post('/reviews', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('review_id', result)
    
    def test_add_review_missing_data_api(self):
        """Test add review endpoint with missing data."""
        data = {'provider_id': 'provider_1'}  # Missing required fields
        
        response = self.client.post('/reviews', json=data)
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing required fields')
    
    def test_find_emergency_care_api(self):
        """Test find emergency care endpoint."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        
        # Add emergency provider
        self.service.register_provider(
            name="Emergency Room",
            provider_type=ProviderType.EMERGENCY,
            specialty="Emergency Medicine",
            location=location,
            phone="555-911",
            email="emergency@hospital.com"
        )
        
        response = self.client.get('/emergency?latitude=37.7749&longitude=-122.4194&urgency=emergency')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['providers'][0]['provider_type'], 'emergency')
    
    def test_find_emergency_care_missing_coordinates_api(self):
        """Test find emergency care endpoint with missing coordinates."""
        response = self.client.get('/emergency')
        self.assertEqual(response.status_code, 400)
        
        result = response.get_json()
        self.assertEqual(result['error'], 'Missing latitude or longitude')

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CareFinderService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_search_providers_empty_query(self):
        """Test searching providers with empty query."""
        providers = self.service.search_providers("")
        self.assertEqual(len(providers), 0)
    
    def test_search_providers_no_results(self):
        """Test searching providers with no results."""
        providers = self.service.search_providers("nonexistent_specialty_12345")
        self.assertEqual(len(providers), 0)
    
    def test_get_provider_details_nonexistent(self):
        """Test getting details for non-existent provider."""
        provider = self.service.get_provider_details("nonexistent_provider_id")
        self.assertIsNone(provider)
    
    def test_get_patient_details_nonexistent(self):
        """Test getting details for non-existent patient."""
        patient = self.service.get_patient_details("nonexistent_patient_id")
        self.assertIsNone(patient)
    
    def test_schedule_appointment_nonexistent_patient(self):
        """Test scheduling appointment with non-existent patient."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        appointment = self.service.schedule_appointment(
            patient_id="nonexistent_patient_id",
            provider_id=provider.provider_id,
            appointment_date=datetime(2024, 1, 15, 10, 0),
            reason="Annual checkup"
        )
        
        # Should still create appointment (validation would be in real system)
        self.assertIsNotNone(appointment)
    
    def test_verify_insurance_nonexistent_patient(self):
        """Test insurance verification with non-existent patient."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        verified = self.service.verify_insurance("nonexistent_patient_id", provider.provider_id)
        self.assertFalse(verified)
    
    def test_verify_insurance_nonexistent_provider(self):
        """Test insurance verification with non-existent provider."""
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        verified = self.service.verify_insurance(patient.patient_id, "nonexistent_provider_id")
        self.assertFalse(verified)
    
    def test_find_emergency_care_no_providers(self):
        """Test finding emergency care with no providers."""
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        emergency_providers = self.service.find_emergency_care(location)
        self.assertEqual(len(emergency_providers), 0)

class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CareFinderService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_bulk_provider_operations_performance(self):
        """Test performance of bulk provider operations."""
        import time
        
        # Test bulk provider registration
        start_time = time.time()
        
        for i in range(100):
            location = Location(37.7749 + i * 0.001, -122.4194 + i * 0.001, f"Address {i}", "San Francisco", "CA", "94102")
            self.service.register_provider(
                name=f"Dr. Smith {i}",
                provider_type=ProviderType.DOCTOR,
                specialty="Cardiology",
                location=location,
                phone=f"555-{1000+i}",
                email=f"doctor{i}@hospital.com"
            )
        
        registration_time = time.time() - start_time
        
        # Test bulk search
        start_time = time.time()
        
        providers = self.service.search_providers("Smith", limit=100)
        
        search_time = time.time() - start_time
        
        # Performance should be reasonable
        self.assertLess(registration_time, 5.0)  # Less than 5 seconds for 100 providers
        self.assertLess(search_time, 2.0)        # Less than 2 seconds for search
        self.assertEqual(len(providers), 100)
    
    def test_bulk_appointment_operations_performance(self):
        """Test performance of bulk appointment operations."""
        import time
        
        # Register a patient and provider first
        address = Location(37.7749, -122.4194, "456 Oak St", "San Francisco", "CA", "94103")
        patient = self.service.register_patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            gender="Female",
            phone="555-5678",
            email="jane.doe@email.com",
            address=address
        )
        
        location = Location(37.7749, -122.4194, "123 Main St", "San Francisco", "CA", "94102")
        provider = self.service.register_provider(
            name="Dr. Smith",
            provider_type=ProviderType.DOCTOR,
            specialty="Cardiology",
            location=location,
            phone="555-1234",
            email="doctor@hospital.com"
        )
        
        # Test bulk appointment scheduling
        start_time = time.time()
        
        for i in range(50):
            # Use modulo to keep dates within valid range
            day = 15 + (i % 15)  # Keep days between 15-29
            appointment_date = datetime(2024, 1, day, 10, 0)
            appointment = self.service.schedule_appointment(
                patient_id=patient.patient_id,
                provider_id=provider.provider_id,
                appointment_date=appointment_date,
                reason=f"Appointment {i}"
            )
            self.assertIsNotNone(appointment)
        
        scheduling_time = time.time() - start_time
        
        # Test bulk appointment retrieval
        start_time = time.time()
        
        appointments = self.service.get_patient_appointments(patient.patient_id)
        
        retrieval_time = time.time() - start_time
        
        # Performance should be reasonable
        self.assertLess(scheduling_time, 3.0)  # Less than 3 seconds for 50 appointments
        self.assertLess(retrieval_time, 1.0)   # Less than 1 second for retrieval
        self.assertEqual(len(appointments), 50)
    
    def test_memory_usage(self):
        """Test memory usage with large datasets."""
        # Add many providers
        for i in range(1000):
            location = Location(37.7749 + i * 0.001, -122.4194 + i * 0.001, f"Address {i}", "San Francisco", "CA", "94102")
            self.service.register_provider(
                name=f"Dr. Smith {i}",
                provider_type=ProviderType.DOCTOR,
                specialty="Cardiology",
                location=location,
                phone=f"555-{1000+i}",
                email=f"doctor{i}@hospital.com"
            )
        
        # Verify all providers can be retrieved
        providers = self.service.search_providers("Smith", limit=1000)
        self.assertEqual(len(providers), 1000)
        
        # Verify search performance
        start_time = time.time()
        nearby_providers = self.service.get_nearby_providers(Location(37.7749, -122.4194, "", "", "", ""))
        search_time = time.time() - start_time
        
        self.assertLess(search_time, 2.0)  # Less than 2 seconds for nearby search

if __name__ == '__main__':
    unittest.main()
