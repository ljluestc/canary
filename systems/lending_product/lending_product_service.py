#!/usr/bin/env python3
"""
Lending Product Service

A comprehensive lending and financial services system for loan management,
credit scoring, payment processing, and risk assessment with support for
various loan types and automated decision making.
"""

import sqlite3
import hashlib
import time
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoanStatus(Enum):
    """Loan status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    PAID_OFF = "paid_off"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"

class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class LoanType(Enum):
    """Loan type enumeration."""
    PERSONAL = "personal"
    MORTGAGE = "mortgage"
    AUTO = "auto"
    BUSINESS = "business"
    STUDENT = "student"
    CREDIT_CARD = "credit_card"

class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class Customer:
    """Customer model."""
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    ssn: str
    date_of_birth: datetime
    address: str
    city: str
    state: str
    zip_code: str
    credit_score: int = 0
    annual_income: float = 0.0
    employment_status: str = "unemployed"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class LoanProduct:
    """Loan product model."""
    product_id: str
    name: str
    loan_type: LoanType
    min_amount: float
    max_amount: float
    min_term_months: int
    max_term_months: int
    interest_rate_min: float
    interest_rate_max: float
    min_credit_score: int
    max_ltv: float = 0.0  # Loan-to-value ratio for secured loans
    requires_collateral: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class LoanApplication:
    """Loan application model."""
    application_id: str
    customer_id: str
    product_id: str
    requested_amount: float
    requested_term_months: int
    purpose: str
    collateral_value: float = 0.0
    collateral_description: str = ""
    status: LoanStatus = LoanStatus.PENDING
    credit_score: int = 0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    interest_rate: float = 0.0
    monthly_payment: float = 0.0
    total_interest: float = 0.0
    total_amount: float = 0.0
    approval_reason: str = ""
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    funded_at: Optional[datetime] = None

@dataclass
class Loan:
    """Active loan model."""
    loan_id: str
    application_id: str
    customer_id: str
    product_id: str
    principal_amount: float
    interest_rate: float
    term_months: int
    monthly_payment: float
    remaining_balance: float
    next_payment_due: datetime
    status: LoanStatus = LoanStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Payment:
    """Payment model."""
    payment_id: str
    loan_id: str
    customer_id: str
    amount: float
    payment_date: datetime
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: str = "bank_transfer"
    reference_number: str = ""
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CreditReport:
    """Credit report model."""
    report_id: str
    customer_id: str
    credit_score: int
    credit_bureau: str
    report_date: datetime
    accounts: List[Dict[str, Any]] = field(default_factory=list)
    inquiries: List[Dict[str, Any]] = field(default_factory=list)
    public_records: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

class LendingProductDatabase:
    """Database operations for lending product service."""
    
    def __init__(self, db_path: str = "lending_product.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                ssn TEXT UNIQUE NOT NULL,
                date_of_birth TIMESTAMP NOT NULL,
                address TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                zip_code TEXT NOT NULL,
                credit_score INTEGER DEFAULT 0,
                annual_income REAL DEFAULT 0.0,
                employment_status TEXT DEFAULT 'unemployed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Loan products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loan_products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                loan_type TEXT NOT NULL,
                min_amount REAL NOT NULL,
                max_amount REAL NOT NULL,
                min_term_months INTEGER NOT NULL,
                max_term_months INTEGER NOT NULL,
                interest_rate_min REAL NOT NULL,
                interest_rate_max REAL NOT NULL,
                min_credit_score INTEGER NOT NULL,
                max_ltv REAL DEFAULT 0.0,
                requires_collateral BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Loan applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loan_applications (
                application_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                requested_amount REAL NOT NULL,
                requested_term_months INTEGER NOT NULL,
                purpose TEXT NOT NULL,
                collateral_value REAL DEFAULT 0.0,
                collateral_description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                credit_score INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'medium',
                interest_rate REAL DEFAULT 0.0,
                monthly_payment REAL DEFAULT 0.0,
                total_interest REAL DEFAULT 0.0,
                total_amount REAL DEFAULT 0.0,
                approval_reason TEXT DEFAULT '',
                rejection_reason TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                funded_at TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
                FOREIGN KEY (product_id) REFERENCES loan_products (product_id)
            )
        ''')
        
        # Loans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                loan_id TEXT PRIMARY KEY,
                application_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                principal_amount REAL NOT NULL,
                interest_rate REAL NOT NULL,
                term_months INTEGER NOT NULL,
                monthly_payment REAL NOT NULL,
                remaining_balance REAL NOT NULL,
                next_payment_due TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES loan_applications (application_id),
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
                FOREIGN KEY (product_id) REFERENCES loan_products (product_id)
            )
        ''')
        
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                loan_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_date TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_method TEXT DEFAULT 'bank_transfer',
                reference_number TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (loan_id) REFERENCES loans (loan_id),
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')
        
        # Credit reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_reports (
                report_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                credit_score INTEGER NOT NULL,
                credit_bureau TEXT NOT NULL,
                report_date TIMESTAMP NOT NULL,
                accounts TEXT DEFAULT '[]',
                inquiries TEXT DEFAULT '[]',
                public_records TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_customer(self, customer: Customer) -> bool:
        """Save customer to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO customers 
                (customer_id, first_name, last_name, email, phone, ssn, 
                 date_of_birth, address, city, state, zip_code, credit_score,
                 annual_income, employment_status, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer.customer_id, customer.first_name, customer.last_name,
                customer.email, customer.phone, customer.ssn, customer.date_of_birth,
                customer.address, customer.city, customer.state, customer.zip_code,
                customer.credit_score, customer.annual_income, customer.employment_status,
                customer.created_at, customer.updated_at, customer.is_active
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving customer: {e}")
            return False
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM customers WHERE customer_id = ?', (customer_id,))
            row = cursor.fetchone()
            
            if row:
                customer = Customer(
                    customer_id=row[0],
                    first_name=row[1],
                    last_name=row[2],
                    email=row[3],
                    phone=row[4],
                    ssn=row[5],
                    date_of_birth=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                    address=row[7],
                    city=row[8],
                    state=row[9],
                    zip_code=row[10],
                    credit_score=row[11] or 0,
                    annual_income=row[12] or 0.0,
                    employment_status=row[13] or "unemployed",
                    created_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[15]) if row[15] else datetime.now(),
                    is_active=bool(row[16])
                )
                conn.close()
                return customer
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting customer: {e}")
            return None
    
    def get_all_customers(self) -> List[Customer]:
        """Get all customers."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT customer_id, first_name, last_name, email, phone, ssn,
                       date_of_birth, address, city, state, zip_code, credit_score,
                       annual_income, employment_status, is_active,
                       created_at, updated_at
                FROM customers
                ORDER BY created_at DESC
            ''')
            
            customers = []
            for row in cursor.fetchall():
                customer = Customer(
                    customer_id=row[0],
                    first_name=row[1],
                    last_name=row[2],
                    email=row[3],
                    phone=row[4],
                    ssn=row[5],
                    date_of_birth=datetime.fromisoformat(row[6]) if row[6] else None,
                    address=row[7],
                    city=row[8],
                    state=row[9],
                    zip_code=row[10],
                    credit_score=row[11] or 0,
                    annual_income=row[12] or 0.0,
                    employment_status=row[13] or "unemployed",
                    is_active=bool(row[14])
                )
                customers.append(customer)
            
            conn.close()
            return customers
        except Exception as e:
            logger.error(f"Error getting all customers: {e}")
            return []
    
    def save_loan_product(self, product: LoanProduct) -> bool:
        """Save loan product to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO loan_products 
                (product_id, name, loan_type, min_amount, max_amount, min_term_months,
                 max_term_months, interest_rate_min, interest_rate_max, min_credit_score,
                 max_ltv, requires_collateral, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.product_id, product.name, product.loan_type.value,
                product.min_amount, product.max_amount, product.min_term_months,
                product.max_term_months, product.interest_rate_min, product.interest_rate_max,
                product.min_credit_score, product.max_ltv, product.requires_collateral,
                product.is_active, product.created_at, product.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving loan product: {e}")
            return False
    
    def get_loan_products(self, loan_type: LoanType = None) -> List[LoanProduct]:
        """Get loan products."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if loan_type:
                cursor.execute('''
                    SELECT * FROM loan_products 
                    WHERE loan_type = ? AND is_active = 1
                    ORDER BY created_at DESC
                ''', (loan_type.value,))
            else:
                cursor.execute('''
                    SELECT * FROM loan_products 
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                ''')
            
            products = []
            for row in cursor.fetchall():
                product = LoanProduct(
                    product_id=row[0],
                    name=row[1],
                    loan_type=LoanType(row[2]),
                    min_amount=row[3],
                    max_amount=row[4],
                    min_term_months=row[5],
                    max_term_months=row[6],
                    interest_rate_min=row[7],
                    interest_rate_max=row[8],
                    min_credit_score=row[9],
                    max_ltv=row[10] or 0.0,
                    requires_collateral=bool(row[11]),
                    is_active=bool(row[12]),
                    created_at=datetime.fromisoformat(row[13]) if row[13] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now()
                )
                products.append(product)
            
            conn.close()
            return products
        except Exception as e:
            logger.error(f"Error getting loan products: {e}")
            return []
    
    def save_loan_application(self, application: LoanApplication) -> bool:
        """Save loan application to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO loan_applications 
                (application_id, customer_id, product_id, requested_amount, requested_term_months,
                 purpose, collateral_value, collateral_description, status, credit_score, risk_level,
                 interest_rate, monthly_payment, total_interest, total_amount, approval_reason,
                 rejection_reason, created_at, updated_at, approved_at, funded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                application.application_id, application.customer_id, application.product_id,
                application.requested_amount, application.requested_term_months, application.purpose,
                application.collateral_value, application.collateral_description, application.status.value,
                application.credit_score, application.risk_level.value, application.interest_rate,
                application.monthly_payment, application.total_interest, application.total_amount,
                application.approval_reason, application.rejection_reason, application.created_at,
                application.updated_at, application.approved_at, application.funded_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving loan application: {e}")
            return False
    
    def get_loan_application(self, application_id: str) -> Optional[LoanApplication]:
        """Get loan application by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM loan_applications WHERE application_id = ?', (application_id,))
            row = cursor.fetchone()
            
            if row:
                application = LoanApplication(
                    application_id=row[0],
                    customer_id=row[1],
                    product_id=row[2],
                    requested_amount=row[3],
                    requested_term_months=row[4],
                    purpose=row[5],
                    collateral_value=row[6] or 0.0,
                    collateral_description=row[7] or "",
                    status=LoanStatus(row[8]),
                    credit_score=row[9] or 0,
                    risk_level=RiskLevel(row[10]),
                    interest_rate=row[11] or 0.0,
                    monthly_payment=row[12] or 0.0,
                    total_interest=row[13] or 0.0,
                    total_amount=row[14] or 0.0,
                    approval_reason=row[15] or "",
                    rejection_reason=row[16] or "",
                    created_at=datetime.fromisoformat(row[17]) if row[17] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[18]) if row[18] else datetime.now(),
                    approved_at=datetime.fromisoformat(row[19]) if row[19] else None,
                    funded_at=datetime.fromisoformat(row[20]) if row[20] else None
                )
                conn.close()
                return application
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting loan application: {e}")
            return None
    
    def save_loan(self, loan: Loan) -> bool:
        """Save loan to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO loans 
                (loan_id, application_id, customer_id, product_id, principal_amount,
                 interest_rate, term_months, monthly_payment, remaining_balance,
                 next_payment_due, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                loan.loan_id, loan.application_id, loan.customer_id, loan.product_id,
                loan.principal_amount, loan.interest_rate, loan.term_months,
                loan.monthly_payment, loan.remaining_balance, loan.next_payment_due,
                loan.status.value, loan.created_at, loan.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving loan: {e}")
            return False
    
    def get_loan(self, loan_id: str) -> Optional[Loan]:
        """Get loan by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM loans WHERE loan_id = ?', (loan_id,))
            row = cursor.fetchone()
            
            if row:
                loan = Loan(
                    loan_id=row[0],
                    application_id=row[1],
                    customer_id=row[2],
                    product_id=row[3],
                    principal_amount=row[4],
                    interest_rate=row[5],
                    term_months=row[6],
                    monthly_payment=row[7],
                    remaining_balance=row[8],
                    next_payment_due=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                    status=LoanStatus(row[10]),
                    created_at=datetime.fromisoformat(row[11]) if row[11] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[12]) if row[12] else datetime.now()
                )
                conn.close()
                return loan
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting loan: {e}")
            return None
    
    def save_payment(self, payment: Payment) -> bool:
        """Save payment to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payments 
                (payment_id, loan_id, customer_id, amount, payment_date, status,
                 payment_method, reference_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                payment.payment_id, payment.loan_id, payment.customer_id,
                payment.amount, payment.payment_date, payment.status.value,
                payment.payment_method, payment.reference_number, payment.created_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving payment: {e}")
            return False
    
    def get_loan_payments(self, loan_id: str) -> List[Payment]:
        """Get payments for a loan."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM payments 
                WHERE loan_id = ? 
                ORDER BY payment_date DESC
            ''', (loan_id,))
            
            payments = []
            for row in cursor.fetchall():
                payment = Payment(
                    payment_id=row[0],
                    loan_id=row[1],
                    customer_id=row[2],
                    amount=row[3],
                    payment_date=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                    status=PaymentStatus(row[5]),
                    payment_method=row[6] or "bank_transfer",
                    reference_number=row[7] or "",
                    created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now()
                )
                payments.append(payment)
            
            conn.close()
            return payments
        except Exception as e:
            logger.error(f"Error getting loan payments: {e}")
            return []

class LendingProductService:
    """Lending product service with credit scoring and risk assessment."""
    
    def __init__(self, db_path: str = "lending_product.db"):
        self.db = LendingProductDatabase(db_path)
        self.initialize_default_products()
    
    def initialize_default_products(self):
        """Initialize default loan products."""
        default_products = [
            LoanProduct(
                product_id="personal_001",
                name="Personal Loan",
                loan_type=LoanType.PERSONAL,
                min_amount=1000.0,
                max_amount=50000.0,
                min_term_months=12,
                max_term_months=60,
                interest_rate_min=5.99,
                interest_rate_max=29.99,
                min_credit_score=600
            ),
            LoanProduct(
                product_id="mortgage_001",
                name="Home Mortgage",
                loan_type=LoanType.MORTGAGE,
                min_amount=50000.0,
                max_amount=2000000.0,
                min_term_months=180,
                max_term_months=360,
                interest_rate_min=3.5,
                interest_rate_max=8.5,
                min_credit_score=620,
                max_ltv=0.95,
                requires_collateral=True
            ),
            LoanProduct(
                product_id="auto_001",
                name="Auto Loan",
                loan_type=LoanType.AUTO,
                min_amount=5000.0,
                max_amount=100000.0,
                min_term_months=24,
                max_term_months=84,
                interest_rate_min=2.99,
                interest_rate_max=15.99,
                min_credit_score=580,
                max_ltv=0.90,
                requires_collateral=True
            )
        ]
        
        for product in default_products:
            self.db.save_loan_product(product)
    
    def generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    def create_customer(self, first_name: str, last_name: str, email: str, phone: str,
                       ssn: str, date_of_birth: datetime, address: str, city: str,
                       state: str, zip_code: str, annual_income: float = 0.0,
                       employment_status: str = "unemployed") -> Optional[Customer]:
        """Create a new customer."""
        customer_id = self.generate_id("cust")
        
        customer = Customer(
            customer_id=customer_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            ssn=ssn,
            date_of_birth=date_of_birth,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            annual_income=annual_income,
            employment_status=employment_status
        )
        
        if self.db.save_customer(customer):
            return customer
        return None
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        return self.db.get_customer(customer_id)
    
    def calculate_credit_score(self, customer: Customer) -> int:
        """Calculate credit score based on customer data."""
        # Simplified credit scoring algorithm
        base_score = 300
        
        # Income factor
        if customer.annual_income > 100000:
            base_score += 100
        elif customer.annual_income > 50000:
            base_score += 75
        elif customer.annual_income > 25000:
            base_score += 50
        else:
            base_score += 25
        
        # Employment status factor
        if customer.employment_status == "employed":
            base_score += 50
        elif customer.employment_status == "self_employed":
            base_score += 30
        else:
            base_score += 10
        
        # Age factor (older customers get higher scores)
        age = (datetime.now() - customer.date_of_birth).days // 365
        if age > 50:
            base_score += 50
        elif age > 30:
            base_score += 30
        else:
            base_score += 10
        
        # Cap at 850 (max credit score)
        return min(base_score, 850)
    
    def assess_risk_level(self, credit_score: int, loan_amount: float, 
                         annual_income: float) -> RiskLevel:
        """Assess risk level for loan application."""
        # Debt-to-income ratio
        dti = (loan_amount / 12) / (annual_income / 12) if annual_income > 0 else 1.0
        
        if credit_score >= 750 and dti <= 0.3:
            return RiskLevel.LOW
        elif credit_score >= 650 and dti <= 0.4:
            return RiskLevel.MEDIUM
        elif credit_score >= 550 and dti <= 0.5:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def calculate_loan_terms(self, principal: float, annual_rate: float, 
                            term_months: int) -> Dict[str, float]:
        """Calculate loan payment terms."""
        monthly_rate = annual_rate / 100 / 12
        
        if monthly_rate == 0:
            monthly_payment = principal / term_months
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / \
                            ((1 + monthly_rate) ** term_months - 1)
        
        total_amount = monthly_payment * term_months
        total_interest = total_amount - principal
        
        return {
            'monthly_payment': round(monthly_payment, 2),
            'total_amount': round(total_amount, 2),
            'total_interest': round(total_interest, 2)
        }
    
    def submit_loan_application(self, customer_id: str, product_id: str,
                               requested_amount: float, requested_term_months: int,
                               purpose: str, collateral_value: float = 0.0,
                               collateral_description: str = "") -> Optional[LoanApplication]:
        """Submit a loan application."""
        # Get customer and product
        customer = self.db.get_customer(customer_id)
        products = self.db.get_loan_products()
        product = next((p for p in products if p.product_id == product_id), None)
        
        if not customer or not product:
            return None
        
        # Calculate credit score
        credit_score = self.calculate_credit_score(customer)
        
        # Assess risk level
        risk_level = self.assess_risk_level(credit_score, requested_amount, customer.annual_income)
        
        # Determine interest rate based on risk
        if risk_level == RiskLevel.LOW:
            interest_rate = product.interest_rate_min
        elif risk_level == RiskLevel.MEDIUM:
            interest_rate = (product.interest_rate_min + product.interest_rate_max) / 2
        elif risk_level == RiskLevel.HIGH:
            interest_rate = product.interest_rate_max * 0.8
        else:
            interest_rate = product.interest_rate_max
        
        # Calculate loan terms
        terms = self.calculate_loan_terms(requested_amount, interest_rate, requested_term_months)
        
        # Create application
        application_id = self.generate_id("app")
        application = LoanApplication(
            application_id=application_id,
            customer_id=customer_id,
            product_id=product_id,
            requested_amount=requested_amount,
            requested_term_months=requested_term_months,
            purpose=purpose,
            collateral_value=collateral_value,
            collateral_description=collateral_description,
            credit_score=credit_score,
            risk_level=risk_level,
            interest_rate=interest_rate,
            monthly_payment=terms['monthly_payment'],
            total_interest=terms['total_interest'],
            total_amount=terms['total_amount']
        )
        
        # Auto-approve or reject based on criteria
        if (credit_score >= product.min_credit_score and 
            product.min_amount <= requested_amount <= product.max_amount and
            product.min_term_months <= requested_term_months <= product.max_term_months and
            risk_level != RiskLevel.VERY_HIGH):
            application.status = LoanStatus.APPROVED
            application.approval_reason = f"Approved based on credit score {credit_score} and risk level {risk_level.value}"
            application.approved_at = datetime.now()
        else:
            application.status = LoanStatus.REJECTED
            application.rejection_reason = f"Rejected due to credit score {credit_score} or risk level {risk_level.value}"
        
        if self.db.save_loan_application(application):
            return application
        return None
    
    def fund_loan(self, application_id: str) -> Optional[Loan]:
        """Fund an approved loan application."""
        application = self.db.get_loan_application(application_id)
        
        if not application or application.status != LoanStatus.APPROVED:
            return None
        
        # Create loan
        loan_id = self.generate_id("loan")
        loan = Loan(
            loan_id=loan_id,
            application_id=application_id,
            customer_id=application.customer_id,
            product_id=application.product_id,
            principal_amount=application.requested_amount,
            interest_rate=application.interest_rate,
            term_months=application.requested_term_months,
            monthly_payment=application.monthly_payment,
            remaining_balance=application.requested_amount,
            next_payment_due=datetime.now() + timedelta(days=30)
        )
        
        if self.db.save_loan(loan):
            # Update application status
            application.status = LoanStatus.ACTIVE
            application.funded_at = datetime.now()
            application.updated_at = datetime.now()
            self.db.save_loan_application(application)
            
            return loan
        return None
    
    def process_payment(self, loan_id: str, amount: float, payment_method: str = "bank_transfer") -> Optional[Payment]:
        """Process a loan payment."""
        loan = self.db.get_loan(loan_id)
        
        if not loan or loan.status != LoanStatus.ACTIVE:
            return None
        
        # Create payment
        payment_id = self.generate_id("pay")
        payment = Payment(
            payment_id=payment_id,
            loan_id=loan_id,
            customer_id=loan.customer_id,
            amount=amount,
            payment_date=datetime.now(),
            payment_method=payment_method,
            reference_number=f"REF{payment_id[:8].upper()}"
        )
        
        # Process payment
        if amount >= loan.monthly_payment:
            payment.status = PaymentStatus.COMPLETED
            
            # Update loan balance
            loan.remaining_balance -= amount
            loan.updated_at = datetime.now()
            
            # Check if loan is paid off
            if loan.remaining_balance <= 0:
                loan.status = LoanStatus.PAID_OFF
                loan.remaining_balance = 0.0
            else:
                # Update next payment due date
                loan.next_payment_due = loan.next_payment_due + timedelta(days=30)
            
            self.db.save_loan(loan)
        else:
            payment.status = PaymentStatus.FAILED
        
        if self.db.save_payment(payment):
            return payment
        return None
    
    def get_loan_products(self, loan_type: LoanType = None) -> List[LoanProduct]:
        """Get available loan products."""
        return self.db.get_loan_products(loan_type)
    
    def get_customer_loans(self, customer_id: str) -> List[Loan]:
        """Get all loans for a customer."""
        # This would require a more complex query in a real implementation
        # For now, return empty list
        return []
    
    def get_loan_summary(self, loan_id: str) -> Dict[str, Any]:
        """Get loan summary with payment history."""
        loan = self.db.get_loan(loan_id)
        if not loan:
            return {}
        
        payments = self.db.get_loan_payments(loan_id)
        
        return {
            'loan_id': loan.loan_id,
            'principal_amount': loan.principal_amount,
            'interest_rate': loan.interest_rate,
            'monthly_payment': loan.monthly_payment,
            'remaining_balance': loan.remaining_balance,
            'next_payment_due': loan.next_payment_due.isoformat(),
            'status': loan.status.value,
            'total_payments': len(payments),
            'total_paid': sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED)
        }

# Global service instance
lending_product_service = LendingProductService()

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
        <title>Lending Product Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 1000px; margin: 0 auto; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .product { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .status.approved { background: #d4edda; color: #155724; }
            .status.rejected { background: #f8d7da; color: #721c24; }
            .status.pending { background: #fff3cd; color: #856404; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Lending Product Service</h1>
            
            <h2>Available Loan Products</h2>
            <div id="products"></div>
            
            <h2>Apply for Loan</h2>
            <form id="applicationForm">
                <div class="form-group">
                    <label for="customer_id">Customer ID:</label>
                    <input type="text" id="customer_id" name="customer_id" required>
                </div>
                <div class="form-group">
                    <label for="product_id">Loan Product:</label>
                    <select id="product_id" name="product_id" required>
                        <option value="">Select a product</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="requested_amount">Requested Amount:</label>
                    <input type="number" id="requested_amount" name="requested_amount" min="1000" required>
                </div>
                <div class="form-group">
                    <label for="requested_term_months">Term (months):</label>
                    <input type="number" id="requested_term_months" name="requested_term_months" min="12" max="360" required>
                </div>
                <div class="form-group">
                    <label for="purpose">Purpose:</label>
                    <input type="text" id="purpose" name="purpose" required>
                </div>
                <button type="submit">Submit Application</button>
            </form>
            
            <h2>Create Customer</h2>
            <form id="customerForm">
                <div class="form-group">
                    <label for="first_name">First Name:</label>
                    <input type="text" id="first_name" name="first_name" required>
                </div>
                <div class="form-group">
                    <label for="last_name">Last Name:</label>
                    <input type="text" id="last_name" name="last_name" required>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="phone">Phone:</label>
                    <input type="tel" id="phone" name="phone" required>
                </div>
                <div class="form-group">
                    <label for="ssn">SSN:</label>
                    <input type="text" id="ssn" name="ssn" required>
                </div>
                <div class="form-group">
                    <label for="date_of_birth">Date of Birth:</label>
                    <input type="date" id="date_of_birth" name="date_of_birth" required>
                </div>
                <div class="form-group">
                    <label for="address">Address:</label>
                    <input type="text" id="address" name="address" required>
                </div>
                <div class="form-group">
                    <label for="city">City:</label>
                    <input type="text" id="city" name="city" required>
                </div>
                <div class="form-group">
                    <label for="state">State:</label>
                    <input type="text" id="state" name="state" required>
                </div>
                <div class="form-group">
                    <label for="zip_code">ZIP Code:</label>
                    <input type="text" id="zip_code" name="zip_code" required>
                </div>
                <div class="form-group">
                    <label for="annual_income">Annual Income:</label>
                    <input type="number" id="annual_income" name="annual_income" min="0" step="0.01">
                </div>
                <div class="form-group">
                    <label for="employment_status">Employment Status:</label>
                    <select id="employment_status" name="employment_status">
                        <option value="employed">Employed</option>
                        <option value="self_employed">Self Employed</option>
                        <option value="unemployed">Unemployed</option>
                    </select>
                </div>
                <button type="submit">Create Customer</button>
            </form>
            
            <div id="results"></div>
        </div>
        
        <script>
            // Load products on page load
            loadProducts();
            
            async function loadProducts() {
                try {
                    const response = await fetch('/api/products');
                    const products = await response.json();
                    
                    const productsDiv = document.getElementById('products');
                    const productSelect = document.getElementById('product_id');
                    
                    productsDiv.innerHTML = '';
                    productSelect.innerHTML = '<option value="">Select a product</option>';
                    
                    products.forEach(product => {
                        productsDiv.innerHTML += `
                            <div class="product">
                                <h3>${product.name}</h3>
                                <p><strong>Type:</strong> ${product.loan_type}</p>
                                <p><strong>Amount:</strong> $${product.min_amount.toLocaleString()} - $${product.max_amount.toLocaleString()}</p>
                                <p><strong>Term:</strong> ${product.min_term_months} - ${product.max_term_months} months</p>
                                <p><strong>Interest Rate:</strong> ${product.interest_rate_min}% - ${product.interest_rate_max}%</p>
                                <p><strong>Min Credit Score:</strong> ${product.min_credit_score}</p>
                            </div>
                        `;
                        
                        productSelect.innerHTML += `<option value="${product.product_id}">${product.name}</option>`;
                    });
                } catch (error) {
                    console.error('Error loading products:', error);
                }
            }
            
            document.getElementById('customerForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                data.date_of_birth = new Date(data.date_of_birth).toISOString();
                data.annual_income = parseFloat(data.annual_income) || 0;
                
                try {
                    const response = await fetch('/api/customers', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    alert(result.success ? 'Customer created successfully! ID: ' + result.customer_id : 'Error: ' + result.error);
                    if (result.success) {
                        e.target.reset();
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            document.getElementById('applicationForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                data.requested_amount = parseFloat(data.requested_amount);
                data.requested_term_months = parseInt(data.requested_term_months);
                
                try {
                    const response = await fetch('/api/applications', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '<h3>Application Result</h3>';
                    
                    if (result.success) {
                        resultsDiv.innerHTML += `
                            <div class="product">
                                <h4>Application ${result.application_id}</h4>
                                <p><strong>Status:</strong> <span class="status ${result.status}">${result.status.toUpperCase()}</span></p>
                                <p><strong>Credit Score:</strong> ${result.credit_score}</p>
                                <p><strong>Risk Level:</strong> ${result.risk_level}</p>
                                <p><strong>Interest Rate:</strong> ${result.interest_rate}%</p>
                                <p><strong>Monthly Payment:</strong> $${result.monthly_payment}</p>
                                <p><strong>Total Amount:</strong> $${result.total_amount}</p>
                                ${result.approval_reason ? `<p><strong>Approval Reason:</strong> ${result.approval_reason}</p>` : ''}
                                ${result.rejection_reason ? `<p><strong>Rejection Reason:</strong> ${result.rejection_reason}</p>` : ''}
                            </div>
                        `;
                    } else {
                        resultsDiv.innerHTML += `<p>Error: ${result.error}</p>`;
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/api/customers', methods=['POST'])
def create_customer():
    """Create a new customer."""
    data = request.get_json()
    
    required_fields = ['first_name', 'last_name', 'email', 'phone', 'ssn', 
                      'date_of_birth', 'address', 'city', 'state', 'zip_code']
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        customer = lending_product_service.create_customer(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data['phone'],
            ssn=data['ssn'],
            date_of_birth=datetime.fromisoformat(data['date_of_birth']),
            address=data['address'],
            city=data['city'],
            state=data['state'],
            zip_code=data['zip_code'],
            annual_income=float(data.get('annual_income', 0)),
            employment_status=data.get('employment_status', 'unemployed')
        )
        
        if customer:
            return jsonify({'success': True, 'customer_id': customer.customer_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to create customer'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products')
def get_products():
    """Get available loan products."""
    products = lending_product_service.get_loan_products()
    
    results = []
    for product in products:
        results.append({
            'product_id': product.product_id,
            'name': product.name,
            'loan_type': product.loan_type.value,
            'min_amount': product.min_amount,
            'max_amount': product.max_amount,
            'min_term_months': product.min_term_months,
            'max_term_months': product.max_term_months,
            'interest_rate_min': product.interest_rate_min,
            'interest_rate_max': product.interest_rate_max,
            'min_credit_score': product.min_credit_score,
            'max_ltv': product.max_ltv,
            'requires_collateral': product.requires_collateral
        })
    
    return jsonify(results)

@app.route('/api/applications', methods=['POST'])
def submit_application():
    """Submit a loan application."""
    data = request.get_json()
    
    required_fields = ['customer_id', 'product_id', 'requested_amount', 
                      'requested_term_months', 'purpose']
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'})
    
    try:
        application = lending_product_service.submit_loan_application(
            customer_id=data['customer_id'],
            product_id=data['product_id'],
            requested_amount=float(data['requested_amount']),
            requested_term_months=int(data['requested_term_months']),
            purpose=data['purpose'],
            collateral_value=float(data.get('collateral_value', 0)),
            collateral_description=data.get('collateral_description', '')
        )
        
        if application:
            return jsonify({
                'success': True,
                'application_id': application.application_id,
                'status': application.status.value,
                'credit_score': application.credit_score,
                'risk_level': application.risk_level.value,
                'interest_rate': application.interest_rate,
                'monthly_payment': application.monthly_payment,
                'total_amount': application.total_amount,
                'approval_reason': application.approval_reason,
                'rejection_reason': application.rejection_reason
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to submit application'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/loans/<loan_id>')
def get_loan_summary(loan_id):
    """Get loan summary."""
    summary = lending_product_service.get_loan_summary(loan_id)
    return jsonify(summary)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'lending_product'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)