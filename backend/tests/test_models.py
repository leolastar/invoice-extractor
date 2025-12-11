import pytest
from datetime import datetime, date
from app import app
from models import db, SalesOrderHeader, SalesOrderDetail


class TestSalesOrderHeader:
    """Test SalesOrderHeader model"""
    
    def test_create_order_header(self, client, sample_order_data):
        """Test creating an order header"""
        with app.app_context():
            order = SalesOrderHeader(**sample_order_data)
            db.session.add(order)
            db.session.commit()
            
            assert order.id is not None
            assert order.order_number == sample_order_data['order_number']
            assert order.customer_name == sample_order_data['customer_name']
            assert order.status == 'pending'
            assert order.processing_status == 'pending'
    
    def test_order_to_dict(self, sample_order):
        """Test order serialization to dict"""
        with app.app_context():
            order_dict = sample_order.to_dict()
            
            assert 'id' in order_dict
            assert 'order_number' in order_dict
            assert 'customer_name' in order_dict
            assert 'line_items' in order_dict
            assert isinstance(order_dict['line_items'], list)
    
    def test_order_with_dates(self, client):
        """Test order with date fields"""
        with app.app_context():
            order = SalesOrderHeader(
                order_number='ORD-DATE-TEST',
                invoice_date=date(2024, 1, 15),
                due_date=date(2024, 2, 15)
            )
            db.session.add(order)
            db.session.commit()
            
            assert order.invoice_date == date(2024, 1, 15)
            assert order.due_date == date(2024, 2, 15)
            
            order_dict = order.to_dict()
            assert order_dict['invoice_date'] == '2024-01-15'
            assert order_dict['due_date'] == '2024-02-15'
    
    def test_order_defaults(self, client):
        """Test order default values"""
        with app.app_context():
            order = SalesOrderHeader(order_number='ORD-DEFAULTS')
            db.session.add(order)
            db.session.commit()
            
            assert order.currency == 'USD'
            assert order.status == 'pending'
            assert order.processing_status == 'pending'
            assert order.created_at is not None
            assert order.updated_at is not None
    
    def test_order_unique_constraint(self, client, sample_order):
        """Test order number uniqueness"""
        with app.app_context():
            duplicate_order = SalesOrderHeader(
                order_number=sample_order.order_number
            )
            db.session.add(duplicate_order)
            
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()


class TestSalesOrderDetail:
    """Test SalesOrderDetail model"""
    
    def test_create_line_item(self, client, sample_order):
        """Test creating a line item"""
        with app.app_context():
            line_item = SalesOrderDetail(
                order_id=sample_order.id,
                line_number=1,
                product_code='PROD-001',
                product_name='Test Product',
                quantity=5,
                unit_price=100.00,
                line_total=500.00
            )
            db.session.add(line_item)
            db.session.commit()
            
            assert line_item.id is not None
            assert line_item.order_id == sample_order.id
            assert line_item.product_name == 'Test Product'
            assert line_item.discount == 0  # Default value
    
    def test_line_item_to_dict(self, client, sample_order):
        """Test line item serialization"""
        with app.app_context():
            line_item = SalesOrderDetail(
                order_id=sample_order.id,
                line_number=1,
                product_code='PROD-001',
                quantity=2,
                unit_price=50.00,
                line_total=100.00
            )
            db.session.add(line_item)
            db.session.commit()
            
            item_dict = line_item.to_dict()
            assert 'id' in item_dict
            assert 'order_id' in item_dict
            assert item_dict['quantity'] == 2.0
            assert item_dict['unit_price'] == 50.0
    
    def test_line_item_relationship(self, sample_order_with_items):
        """Test relationship between order and line items"""
        with app.app_context():
            assert len(sample_order_with_items.line_items) == 2
            assert sample_order_with_items.line_items[0].product_code == 'PROD-001'
            assert sample_order_with_items.line_items[1].product_code == 'PROD-002'
    
    def test_cascade_delete(self, client, sample_order_with_items):
        """Test that deleting order deletes line items"""
        with app.app_context():
            order_id = sample_order_with_items.id
            assert SalesOrderDetail.query.filter_by(order_id=order_id).count() == 2
            
            # Get fresh instance from database to ensure it's in the session
            order = SalesOrderHeader.query.get(order_id)
            db.session.delete(order)
            db.session.commit()
            
            assert SalesOrderDetail.query.filter_by(order_id=order_id).count() == 0
    
    def test_line_item_discount(self, client, sample_order):
        """Test line item with discount"""
        with app.app_context():
            line_item = SalesOrderDetail(
                order_id=sample_order.id,
                quantity=10,
                unit_price=100.00,
                discount=15.5,
                line_total=845.00
            )
            db.session.add(line_item)
            db.session.commit()
            
            assert line_item.discount == 15.5
            item_dict = line_item.to_dict()
            assert item_dict['discount'] == 15.5

