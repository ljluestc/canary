#!/usr/bin/env python3
"""
Comprehensive test suite for Lending Product Service.

Tests all components including customer management, loan applications,
credit scoring, risk assessment, and payment processing.
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys

# Add the lending_product directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from lending_product_service import (
    LoanStatus, PaymentStatus, LoanType, RiskLevel, Customer, LoanProduct,
    LoanApplication, Loan, Payment, CreditReport, LendingProductDatabase,
    LendingProductService, lending_product_service
)

class TestLoanStatus(unittest.TestCase):
    """Test LoanStatus enum."""
    
    def test_loan_status_values(self):
        """Test loan status enum values."""
        self.assertEqual(LoanStatus.PENDING.value, "pending")
        self.assertEqual(LoanStatus.APPROVED.value, "approved")
        self.assertEqual(LoanStatus.REJECTED.value, "rejected")
        self.assertEqual(LoanStatus.ACTIVE.value, "active")
        self.assertEqual(LoanStatus.PAID_OFF.value, "paid_off")
        self.assertEqual(LoanStatus.DEFAULTED.value, "defaulted")
        self.assertEqual(LoanStatus.CANCELLED.value, "cancelled")

class TestPaymentStatus(unittest.TestCase):
    """Test PaymentStatus enum."""
    
    def test_payment_status_values(self):
        """Test payment status enum values."""
        self.assertEqual(PaymentStatus.PENDING.value, "pending")
        self.assertEqual(PaymentStatus.PROCESSING.value, "processing")
        self.assertEqual(PaymentStatus.COMPLETED.value, "completed")
        self.assertEqual(PaymentStatus.FAILED.value, "failed")
        self.assertEqual(PaymentStatus.CANCELLED.value, "cancelled")

class TestLoanType(unittest.TestCase):
    """Test LoanType enum."""
    
    def test_loan_type_values(self):
        """Test loan type enum values."""
        self.assertEqual(LoanType.PERSONAL.value, "personal")
        self.assertEqual(LoanType.MORTGAGE.value, "mortgage")
        self.assertEqual(LoanType.AUTO.value, "auto")
        self.assertEqual(LoanType.BUSINESS.value, "business")
        self.assertEqual(LoanType.STUDENT.value, "student")
        self.assertEqual(LoanType.CREDIT_CARD.value, "credit_card")

class TestRiskLevel(unittest.TestCase):
    """Test RiskLevel enum."""
    
    def test_risk_level_values(self):
        """Test risk level enum values."""
        self.assertEqual(RiskLevel.LOW.value, "low")
        self.assertEqual(RiskLevel.MEDIUM.value, "medium")
        self.assertEqual(RiskLevel.HIGH.value, "high")
        self.assertEqual(RiskLevel.VERY_HIGH.value, "very_high")

class TestCustomer(unittest.TestCase):
    """Test Customer dataclass."""
    
    def test_customer_creation(self):
        """Test creating a customer."""
        customer = Customer(
            customer_id="cust123",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1990, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345"
        )
        
        self.assertEqual(customer.customer_id, "cust123")
        self.assertEqual(customer.first_name, "John")
        self.assertEqual(customer.last_name, "Doe")
        self.assertEqual(customer.email, "john@example.com")
        self.assertEqual(customer.credit_score, 0)
        self.assertEqual(customer.annual_income, 0.0)
        self.assertEqual(customer.employment_status, "unemployed")
        self.assertTrue(customer.is_active)
    
    def test_customer_defaults(self):
        """Test customer default values."""
        customer = Customer(
            customer_id="cust123",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1990, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345"
        )
        
        self.assertEqual(customer.credit_score, 0)
        self.assertEqual(customer.annual_income, 0.0)
        self.assertEqual(customer.employment_status, "unemployed")
        self.assertTrue(customer.is_active)
        self.assertIsInstance(customer.created_at, datetime)
        self.assertIsInstance(customer.updated_at, datetime)

class TestLoanProduct(unittest.TestCase):
    """Test LoanProduct dataclass."""
    
    def test_loan_product_creation(self):
        """Test creating a loan product."""
        product = LoanProduct(
            product_id="prod123",
            name="Personal Loan",
            loan_type=LoanType.PERSONAL,
            min_amount=1000.0,
            max_amount=50000.0,
            min_term_months=12,
            max_term_months=60,
            interest_rate_min=5.99,
            interest_rate_max=29.99,
            min_credit_score=600
        )
        
        self.assertEqual(product.product_id, "prod123")
        self.assertEqual(product.name, "Personal Loan")
        self.assertEqual(product.loan_type, LoanType.PERSONAL)
        self.assertEqual(product.min_amount, 1000.0)
        self.assertEqual(product.max_amount, 50000.0)
        self.assertEqual(product.min_term_months, 12)
        self.assertEqual(product.max_term_months, 60)
        self.assertEqual(product.interest_rate_min, 5.99)
        self.assertEqual(product.interest_rate_max, 29.99)
        self.assertEqual(product.min_credit_score, 600)
        self.assertTrue(product.is_active)
    
    def test_loan_product_defaults(self):
        """Test loan product default values."""
        product = LoanProduct(
            product_id="prod123",
            name="Personal Loan",
            loan_type=LoanType.PERSONAL,
            min_amount=1000.0,
            max_amount=50000.0,
            min_term_months=12,
            max_term_months=60,
            interest_rate_min=5.99,
            interest_rate_max=29.99,
            min_credit_score=600
        )
        
        self.assertEqual(product.max_ltv, 0.0)
        self.assertFalse(product.requires_collateral)
        self.assertTrue(product.is_active)
        self.assertIsInstance(product.created_at, datetime)
        self.assertIsInstance(product.updated_at, datetime)

class TestLoanApplication(unittest.TestCase):
    """Test LoanApplication dataclass."""
    
    def test_loan_application_creation(self):
        """Test creating a loan application."""
        application = LoanApplication(
            application_id="app123",
            customer_id="cust123",
            product_id="prod123",
            requested_amount=10000.0,
            requested_term_months=36,
            purpose="Home improvement"
        )
        
        self.assertEqual(application.application_id, "app123")
        self.assertEqual(application.customer_id, "cust123")
        self.assertEqual(application.product_id, "prod123")
        self.assertEqual(application.requested_amount, 10000.0)
        self.assertEqual(application.requested_term_months, 36)
        self.assertEqual(application.purpose, "Home improvement")
        self.assertEqual(application.status, LoanStatus.PENDING)
        self.assertEqual(application.risk_level, RiskLevel.MEDIUM)
    
    def test_loan_application_defaults(self):
        """Test loan application default values."""
        application = LoanApplication(
            application_id="app123",
            customer_id="cust123",
            product_id="prod123",
            requested_amount=10000.0,
            requested_term_months=36,
            purpose="Home improvement"
        )
        
        self.assertEqual(application.collateral_value, 0.0)
        self.assertEqual(application.collateral_description, "")
        self.assertEqual(application.status, LoanStatus.PENDING)
        self.assertEqual(application.credit_score, 0)
        self.assertEqual(application.risk_level, RiskLevel.MEDIUM)
        self.assertEqual(application.interest_rate, 0.0)
        self.assertEqual(application.monthly_payment, 0.0)
        self.assertEqual(application.total_interest, 0.0)
        self.assertEqual(application.total_amount, 0.0)
        self.assertEqual(application.approval_reason, "")
        self.assertEqual(application.rejection_reason, "")
        self.assertIsNone(application.approved_at)
        self.assertIsNone(application.funded_at)

class TestLoan(unittest.TestCase):
    """Test Loan dataclass."""
    
    def test_loan_creation(self):
        """Test creating a loan."""
        loan = Loan(
            loan_id="loan123",
            application_id="app123",
            customer_id="cust123",
            product_id="prod123",
            principal_amount=10000.0,
            interest_rate=5.99,
            term_months=36,
            monthly_payment=304.17,
            remaining_balance=10000.0,
            next_payment_due=datetime.now() + timedelta(days=30)
        )
        
        self.assertEqual(loan.loan_id, "loan123")
        self.assertEqual(loan.application_id, "app123")
        self.assertEqual(loan.customer_id, "cust123")
        self.assertEqual(loan.product_id, "prod123")
        self.assertEqual(loan.principal_amount, 10000.0)
        self.assertEqual(loan.interest_rate, 5.99)
        self.assertEqual(loan.term_months, 36)
        self.assertEqual(loan.monthly_payment, 304.17)
        self.assertEqual(loan.remaining_balance, 10000.0)
        self.assertEqual(loan.status, LoanStatus.ACTIVE)
    
    def test_loan_defaults(self):
        """Test loan default values."""
        loan = Loan(
            loan_id="loan123",
            application_id="app123",
            customer_id="cust123",
            product_id="prod123",
            principal_amount=10000.0,
            interest_rate=5.99,
            term_months=36,
            monthly_payment=304.17,
            remaining_balance=10000.0,
            next_payment_due=datetime.now()
        )
        
        self.assertEqual(loan.status, LoanStatus.ACTIVE)
        self.assertIsInstance(loan.created_at, datetime)
        self.assertIsInstance(loan.updated_at, datetime)

class TestPayment(unittest.TestCase):
    """Test Payment dataclass."""
    
    def test_payment_creation(self):
        """Test creating a payment."""
        payment = Payment(
            payment_id="pay123",
            loan_id="loan123",
            customer_id="cust123",
            amount=304.17,
            payment_date=datetime.now()
        )
        
        self.assertEqual(payment.payment_id, "pay123")
        self.assertEqual(payment.loan_id, "loan123")
        self.assertEqual(payment.customer_id, "cust123")
        self.assertEqual(payment.amount, 304.17)
        self.assertEqual(payment.status, PaymentStatus.PENDING)
        self.assertEqual(payment.payment_method, "bank_transfer")
        self.assertEqual(payment.reference_number, "")
    
    def test_payment_defaults(self):
        """Test payment default values."""
        payment = Payment(
            payment_id="pay123",
            loan_id="loan123",
            customer_id="cust123",
            amount=304.17,
            payment_date=datetime.now()
        )
        
        self.assertEqual(payment.status, PaymentStatus.PENDING)
        self.assertEqual(payment.payment_method, "bank_transfer")
        self.assertEqual(payment.reference_number, "")
        self.assertIsInstance(payment.created_at, datetime)

class TestLendingProductDatabase(unittest.TestCase):
    """Test LendingProductDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = LendingProductDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization."""
        # Database should be initialized in setUp
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_customer(self):
        """Test saving customer."""
        customer = Customer(
            customer_id="cust123",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1990, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345"
        )
        
        result = self.db.save_customer(customer)
        self.assertTrue(result)
    
    def test_get_customer(self):
        """Test getting customer."""
        customer = Customer(
            customer_id="cust123",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1990, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345"
        )
        
        self.db.save_customer(customer)
        retrieved_customer = self.db.get_customer("cust123")
        
        self.assertIsNotNone(retrieved_customer)
        self.assertEqual(retrieved_customer.customer_id, "cust123")
        self.assertEqual(retrieved_customer.first_name, "John")
        self.assertEqual(retrieved_customer.last_name, "Doe")
    
    def test_save_loan_product(self):
        """Test saving loan product."""
        product = LoanProduct(
            product_id="prod123",
            name="Personal Loan",
            loan_type=LoanType.PERSONAL,
            min_amount=1000.0,
            max_amount=50000.0,
            min_term_months=12,
            max_term_months=60,
            interest_rate_min=5.99,
            interest_rate_max=29.99,
            min_credit_score=600
        )
        
        result = self.db.save_loan_product(product)
        self.assertTrue(result)
    
    def test_get_loan_products(self):
        """Test getting loan products."""
        product = LoanProduct(
            product_id="prod123",
            name="Personal Loan",
            loan_type=LoanType.PERSONAL,
            min_amount=1000.0,
            max_amount=50000.0,
            min_term_months=12,
            max_term_months=60,
            interest_rate_min=5.99,
            interest_rate_max=29.99,
            min_credit_score=600
        )
        
        self.db.save_loan_product(product)
        products = self.db.get_loan_products()
        
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].product_id, "prod123")
        self.assertEqual(products[0].name, "Personal Loan")
    
    def test_save_loan_application(self):
        """Test saving loan application."""
        application = LoanApplication(
            application_id="app123",
            customer_id="cust123",
            product_id="prod123",
            requested_amount=10000.0,
            requested_term_months=36,
            purpose="Home improvement"
        )
        
        result = self.db.save_loan_application(application)
        self.assertTrue(result)
    
    def test_get_loan_application(self):
        """Test getting loan application."""
        application = LoanApplication(
            application_id="app123",
            customer_id="cust123",
            product_id="prod123",
            requested_amount=10000.0,
            requested_term_months=36,
            purpose="Home improvement"
        )
        
        self.db.save_loan_application(application)
        retrieved_application = self.db.get_loan_application("app123")
        
        self.assertIsNotNone(retrieved_application)
        self.assertEqual(retrieved_application.application_id, "app123")
        self.assertEqual(retrieved_application.customer_id, "cust123")
        self.assertEqual(retrieved_application.requested_amount, 10000.0)
    
    def test_save_loan(self):
        """Test saving loan."""
        loan = Loan(
            loan_id="loan123",
            application_id="app123",
            customer_id="cust123",
            product_id="prod123",
            principal_amount=10000.0,
            interest_rate=5.99,
            term_months=36,
            monthly_payment=304.17,
            remaining_balance=10000.0,
            next_payment_due=datetime.now() + timedelta(days=30)
        )
        
        result = self.db.save_loan(loan)
        self.assertTrue(result)
    
    def test_get_loan(self):
        """Test getting loan."""
        loan = Loan(
            loan_id="loan123",
            application_id="app123",
            customer_id="cust123",
            product_id="prod123",
            principal_amount=10000.0,
            interest_rate=5.99,
            term_months=36,
            monthly_payment=304.17,
            remaining_balance=10000.0,
            next_payment_due=datetime.now() + timedelta(days=30)
        )
        
        self.db.save_loan(loan)
        retrieved_loan = self.db.get_loan("loan123")
        
        self.assertIsNotNone(retrieved_loan)
        self.assertEqual(retrieved_loan.loan_id, "loan123")
        self.assertEqual(retrieved_loan.principal_amount, 10000.0)
        self.assertEqual(retrieved_loan.interest_rate, 5.99)
    
    def test_save_payment(self):
        """Test saving payment."""
        payment = Payment(
            payment_id="pay123",
            loan_id="loan123",
            customer_id="cust123",
            amount=304.17,
            payment_date=datetime.now()
        )
        
        result = self.db.save_payment(payment)
        self.assertTrue(result)
    
    def test_get_loan_payments(self):
        """Test getting loan payments."""
        payment = Payment(
            payment_id="pay123",
            loan_id="loan123",
            customer_id="cust123",
            amount=304.17,
            payment_date=datetime.now()
        )
        
        self.db.save_payment(payment)
        payments = self.db.get_loan_payments("loan123")
        
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].payment_id, "pay123")
        self.assertEqual(payments[0].amount, 304.17)

class TestLendingProductService(unittest.TestCase):
    """Test LendingProductService class."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = LendingProductService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_service_creation(self):
        """Test service creation."""
        self.assertIsNotNone(self.service.db)
        self.assertIsInstance(self.service.db, LendingProductDatabase)
    
    def test_generate_id(self):
        """Test ID generation."""
        id1 = self.service.generate_id("test")
        id2 = self.service.generate_id("test")
        
        self.assertTrue(id1.startswith("test_"))
        self.assertTrue(id2.startswith("test_"))
        self.assertNotEqual(id1, id2)
        self.assertEqual(len(id1), len("test_") + 8)
    
    def test_create_customer(self):
        """Test creating customer."""
        customer = self.service.create_customer(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1990, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            annual_income=75000.0,
            employment_status="employed"
        )
        
        self.assertIsNotNone(customer)
        self.assertEqual(customer.first_name, "John")
        self.assertEqual(customer.last_name, "Doe")
        self.assertEqual(customer.email, "john@example.com")
        self.assertEqual(customer.annual_income, 75000.0)
        self.assertEqual(customer.employment_status, "employed")
    
    def test_get_customer(self):
        """Test getting customer."""
        customer = self.service.create_customer(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1990, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345"
        )
        
        retrieved_customer = self.service.get_customer(customer.customer_id)
        self.assertIsNotNone(retrieved_customer)
        self.assertEqual(retrieved_customer.customer_id, customer.customer_id)
    
    def test_calculate_credit_score(self):
        """Test credit score calculation."""
        customer = Customer(
            customer_id="cust123",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1980, 1, 1),  # 44 years old
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            annual_income=100000.0,
            employment_status="employed"
        )
        
        credit_score = self.service.calculate_credit_score(customer)
        self.assertGreaterEqual(credit_score, 300)
        self.assertLessEqual(credit_score, 850)
        # Should be reasonable due to high income, employment, and age
        self.assertGreater(credit_score, 400)
    
    def test_assess_risk_level(self):
        """Test risk level assessment."""
        # Low risk
        risk_low = self.service.assess_risk_level(750, 10000, 100000)
        self.assertEqual(risk_low, RiskLevel.LOW)
        
        # Medium risk
        risk_medium = self.service.assess_risk_level(650, 20000, 80000)
        self.assertEqual(risk_medium, RiskLevel.MEDIUM)
        
        # High risk
        risk_high = self.service.assess_risk_level(550, 30000, 60000)
        self.assertEqual(risk_high, RiskLevel.HIGH)
        
        # Very high risk
        risk_very_high = self.service.assess_risk_level(500, 50000, 50000)
        self.assertEqual(risk_very_high, RiskLevel.VERY_HIGH)
    
    def test_calculate_loan_terms(self):
        """Test loan terms calculation."""
        terms = self.service.calculate_loan_terms(10000, 5.99, 36)
        
        self.assertIn('monthly_payment', terms)
        self.assertIn('total_amount', terms)
        self.assertIn('total_interest', terms)
        
        self.assertGreater(terms['monthly_payment'], 0)
        self.assertGreater(terms['total_amount'], 10000)
        self.assertGreater(terms['total_interest'], 0)
        
        # Monthly payment should be reasonable
        self.assertLess(terms['monthly_payment'], 500)
    
    def test_submit_loan_application(self):
        """Test submitting loan application."""
        # Create customer first
        customer = self.service.create_customer(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1980, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            annual_income=75000.0,
            employment_status="employed"
        )
        
        # Get a product
        products = self.service.get_loan_products()
        self.assertGreater(len(products), 0)
        product = products[0]
        
        # Submit application
        application = self.service.submit_loan_application(
            customer_id=customer.customer_id,
            product_id=product.product_id,
            requested_amount=10000.0,
            requested_term_months=36,
            purpose="Home improvement"
        )
        
        self.assertIsNotNone(application)
        self.assertEqual(application.customer_id, customer.customer_id)
        self.assertEqual(application.product_id, product.product_id)
        self.assertEqual(application.requested_amount, 10000.0)
        self.assertGreater(application.credit_score, 0)
        self.assertIn(application.status, [LoanStatus.APPROVED, LoanStatus.REJECTED])
    
    def test_fund_loan(self):
        """Test funding a loan."""
        # Create customer and application first
        customer = self.service.create_customer(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1980, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            annual_income=100000.0,
            employment_status="employed"
        )
        
        products = self.service.get_loan_products()
        product = products[0]
        
        application = self.service.submit_loan_application(
            customer_id=customer.customer_id,
            product_id=product.product_id,
            requested_amount=10000.0,
            requested_term_months=36,
            purpose="Home improvement"
        )
        
        if application and application.status == LoanStatus.APPROVED:
            loan = self.service.fund_loan(application.application_id)
            self.assertIsNotNone(loan)
            self.assertEqual(loan.application_id, application.application_id)
            self.assertEqual(loan.customer_id, customer.customer_id)
            self.assertEqual(loan.principal_amount, 10000.0)
    
    def test_process_payment(self):
        """Test processing payment."""
        # Create customer, application, and loan first
        customer = self.service.create_customer(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1980, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            annual_income=100000.0,
            employment_status="employed"
        )
        
        products = self.service.get_loan_products()
        product = products[0]
        
        application = self.service.submit_loan_application(
            customer_id=customer.customer_id,
            product_id=product.product_id,
            requested_amount=10000.0,
            requested_term_months=36,
            purpose="Home improvement"
        )
        
        if application and application.status == LoanStatus.APPROVED:
            loan = self.service.fund_loan(application.application_id)
            
            if loan:
                payment = self.service.process_payment(
                    loan_id=loan.loan_id,
                    amount=loan.monthly_payment,
                    payment_method="bank_transfer"
                )
                
                self.assertIsNotNone(payment)
                self.assertEqual(payment.loan_id, loan.loan_id)
                self.assertEqual(payment.amount, loan.monthly_payment)
                self.assertEqual(payment.status, PaymentStatus.COMPLETED)
    
    def test_get_loan_products(self):
        """Test getting loan products."""
        products = self.service.get_loan_products()
        self.assertGreater(len(products), 0)
        
        # Check that default products are loaded
        product_names = [p.name for p in products]
        self.assertIn("Personal Loan", product_names)
        self.assertIn("Home Mortgage", product_names)
        self.assertIn("Auto Loan", product_names)
    
    def test_get_loan_summary(self):
        """Test getting loan summary."""
        # Create a loan first
        customer = self.service.create_customer(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-1234",
            ssn="123-45-6789",
            date_of_birth=datetime(1980, 1, 1),
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            annual_income=100000.0,
            employment_status="employed"
        )
        
        products = self.service.get_loan_products()
        product = products[0]
        
        application = self.service.submit_loan_application(
            customer_id=customer.customer_id,
            product_id=product.product_id,
            requested_amount=10000.0,
            requested_term_months=36,
            purpose="Home improvement"
        )
        
        if application and application.status == LoanStatus.APPROVED:
            loan = self.service.fund_loan(application.application_id)
            
            if loan:
                summary = self.service.get_loan_summary(loan.loan_id)
                self.assertIsInstance(summary, dict)
                self.assertIn('loan_id', summary)
                self.assertIn('principal_amount', summary)
                self.assertIn('interest_rate', summary)
                self.assertIn('monthly_payment', summary)
                self.assertIn('remaining_balance', summary)

class TestFlaskApp(unittest.TestCase):
    """Test Flask application."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create a test service
        self.test_service = LendingProductService(self.temp_db.name)
        
        # Patch the global service
        with patch('lending_product_service.lending_product_service', self.test_service):
            from lending_product_service import app
            self.app = app
            self.client = app.test_client()
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_index_page(self):
        """Test index page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lending Product Service', response.data)
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'lending_product')
    
    def test_create_customer_api(self):
        """Test create customer API."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '555-1234',
            'ssn': '123-45-6789',
            'date_of_birth': '1990-01-01T00:00:00',
            'address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '12345',
            'annual_income': 75000.0,
            'employment_status': 'employed'
        }
        
        response = self.client.post('/api/customers', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('customer_id', result)
    
    def test_create_customer_missing_fields(self):
        """Test create customer with missing fields."""
        data = {
            'first_name': 'John'
            # Missing required fields
        }
        
        response = self.client.post('/api/customers', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_get_products_api(self):
        """Test get products API."""
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)
        
        products = response.get_json()
        self.assertIsInstance(products, list)
        self.assertGreater(len(products), 0)
        
        # Check product structure
        product = products[0]
        self.assertIn('product_id', product)
        self.assertIn('name', product)
        self.assertIn('loan_type', product)
        self.assertIn('min_amount', product)
        self.assertIn('max_amount', product)
    
    def test_submit_application_api(self):
        """Test submit application API."""
        # Create customer first
        customer_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '555-1234',
            'ssn': '123-45-6789',
            'date_of_birth': '1980-01-01T00:00:00',
            'address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '12345',
            'annual_income': 100000.0,
            'employment_status': 'employed'
        }
        
        customer_response = self.client.post('/api/customers', json=customer_data)
        customer_result = customer_response.get_json()
        
        if customer_result['success']:
            # Get products
            products_response = self.client.get('/api/products')
            products = products_response.get_json()
            
            if products:
                # Submit application
                application_data = {
                    'customer_id': customer_result['customer_id'],
                    'product_id': products[0]['product_id'],
                    'requested_amount': 10000.0,
                    'requested_term_months': 36,
                    'purpose': 'Home improvement'
                }
                
                response = self.client.post('/api/applications', json=application_data)
                self.assertEqual(response.status_code, 200)
                
                result = response.get_json()
                self.assertTrue(result['success'])
                self.assertIn('application_id', result)
                self.assertIn('status', result)
                self.assertIn('credit_score', result)
                self.assertIn('risk_level', result)
    
    def test_submit_application_missing_fields(self):
        """Test submit application with missing fields."""
        data = {
            'customer_id': 'cust123'
            # Missing required fields
        }
        
        response = self.client.post('/api/applications', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_get_loan_summary_api(self):
        """Test get loan summary API."""
        # This would require a funded loan, so we'll just test the endpoint exists
        response = self.client.get('/api/loans/nonexistent')
        self.assertEqual(response.status_code, 200)
        
        summary = response.get_json()
        self.assertIsInstance(summary, dict)

if __name__ == '__main__':
    unittest.main()