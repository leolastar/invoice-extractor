"""
Test utilities for creating sample invoice data
"""
import pytest
from faker import Faker
from datetime import date, timedelta
from app import app
from models import db, SalesOrderHeader, SalesOrderDetail

fake = Faker()


class TestSampleInvoiceGeneration:
    """Test sample invoice generation utilities"""
    
    def test_create_sample_invoice(self, client):
        """Test creating a sample invoice with fake data"""
        with app.app_context():
            order = SalesOrderHeader(
                order_number=fake.bothify('ORD-####-####'),
                invoice_number=fake.bothify('INV-####'),
                invoice_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                customer_name=fake.company(),
                customer_address=fake.address(),
                customer_email=fake.email(),
                customer_phone=fake.phone_number(),
                subtotal=1000.00,
                tax=100.00,
                total=1100.00,
                currency='USD',
                status='completed'
            )
            
            db.session.add(order)
            db.session.flush()
            
            # Add line items
            for i in range(3):
                line_item = SalesOrderDetail(
                    order_id=order.id,
                    line_number=i + 1,
                    product_code=fake.bothify('PROD-####'),
                    product_name=fake.catch_phrase(),
                    description=fake.text(max_nb_chars=100),
                    quantity=fake.random_int(min=1, max=10),
                    unit_price=fake.pyfloat(left_digits=3, right_digits=2, positive=True),
                    discount=round(fake.random.uniform(0, 20), 1),
                    line_total=fake.pyfloat(left_digits=3, right_digits=2, positive=True)
                )
                db.session.add(line_item)
            
            db.session.commit()
            
            assert order.id is not None
            assert len(order.line_items) == 3
    
    def test_create_multiple_sample_invoices(self, client):
        """Test creating multiple sample invoices"""
        with app.app_context():
            orders = []
            for _ in range(5):
                order = SalesOrderHeader(
                    order_number=fake.unique.bothify('ORD-####-####'),
                    customer_name=fake.company(),
                    total=fake.pyfloat(left_digits=4, right_digits=2, positive=True),
                    currency='USD',
                    status='completed'
                )
                db.session.add(order)
                orders.append(order)
            
            db.session.commit()
            
            assert len(orders) == 5
            assert all(order.id is not None for order in orders)

