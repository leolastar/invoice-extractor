import pytest
import os
import tempfile
import sys
from flask import Flask

# Set test environment variables BEFORE importing app
# This prevents app from trying to connect to real database
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['TESTING'] = '1'
os.environ['FLASK_ENV'] = 'testing'
os.environ['CELERY_BROKER_URL'] = 'memory://'
os.environ['CELERY_RESULT_BACKEND'] = 'cache+memory://'
os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'

# Import app after setting environment variables
from app import app, db
from models import SalesOrderHeader, SalesOrderDetail


@pytest.fixture(scope='function', autouse=True)
def setup_test_db():
    """Setup test database for each test"""
    # Set TESTING flag first to prevent app from trying to connect to real DB
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    app.config['CELERY_BROKER_URL'] = 'memory://'
    app.config['CELERY_RESULT_BACKEND'] = 'cache+memory://'
    
    with app.app_context():
        # SQLite in-memory databases work per-connection, so we need to ensure
        # we're using the same connection. Flask-SQLAlchemy handles this.
        db.drop_all()
        db.create_all()
        yield
        db.session.rollback()
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client():
    """Create a test client"""
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        'order_number': 'ORD-20240101120000',
        'invoice_number': 'INV-001',
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '123-456-7890',
        'subtotal': 1000.00,
        'tax': 100.00,
        'total': 1100.00,
        'currency': 'USD',
        'status': 'pending'
    }


@pytest.fixture
def sample_order(client, sample_order_data):
    """Create a sample order in the database"""
    order = SalesOrderHeader(**sample_order_data)
    db.session.add(order)
    db.session.commit()
    return order


@pytest.fixture
def sample_order_with_items(client, sample_order_data):
    """Create a sample order with line items"""
    order = SalesOrderHeader(**sample_order_data)
    db.session.add(order)
    db.session.flush()
    
    line_items = [
        SalesOrderDetail(
            order_id=order.id,
            line_number=1,
            product_code='PROD-001',
            product_name='Test Product 1',
            description='Test Description 1',
            quantity=2,
            unit_price=500.00,
            discount=0,
            line_total=1000.00
        ),
        SalesOrderDetail(
            order_id=order.id,
            line_number=2,
            product_code='PROD-002',
            product_name='Test Product 2',
            description='Test Description 2',
            quantity=1,
            unit_price=100.00,
            discount=10,
            line_total=90.00
        )
    ]
    
    for item in line_items:
        db.session.add(item)
    
    db.session.commit()
    return order


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing"""
    import PyPDF2
    from io import BytesIO
    
    # Create a simple PDF in memory
    pdf_buffer = BytesIO()
    # For testing, we'll create a minimal PDF structure
    # In real tests, you'd use a proper PDF library or sample file
    return pdf_buffer

