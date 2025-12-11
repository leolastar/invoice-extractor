import pytest
from datetime import date
from pydantic import ValidationError
from schemas import OrderCreate, OrderUpdate, LineItemCreate, LineItemUpdate


class TestOrderCreate:
    """Test OrderCreate schema"""
    
    def test_valid_order_create(self):
        """Test creating a valid order"""
        order_data = {
            'order_number': 'ORD-001',
            'invoice_number': 'INV-001',
            'invoice_date': date(2024, 1, 15),
            'customer_name': 'Test Customer',
            'customer_email': 'test@example.com',
            'subtotal': 1000.00,
            'total': 1100.00,
            'currency': 'USD',
            'line_items': []
        }
        
        order = OrderCreate(**order_data)
        assert order.order_number == 'ORD-001'
        assert order.customer_email == 'test@example.com'
    
    def test_order_create_defaults(self):
        """Test order create with defaults"""
        order_data = {
            'order_number': 'ORD-002'
        }
        
        order = OrderCreate(**order_data)
        assert order.currency == 'USD'
        assert order.status == 'pending'
        assert order.line_items == []
    
    def test_order_create_with_line_items(self):
        """Test order create with line items"""
        order_data = {
            'order_number': 'ORD-003',
            'line_items': [
                {
                    'line_number': 1,
                    'product_name': 'Product 1',
                    'quantity': 2,
                    'unit_price': 50.00,
                    'line_total': 100.00
                }
            ]
        }
        
        order = OrderCreate(**order_data)
        assert len(order.line_items) == 1
        assert order.line_items[0].product_name == 'Product 1'
    
    def test_order_create_invalid_email(self):
        """Test order create with invalid email"""
        order_data = {
            'order_number': 'ORD-004',
            'customer_email': 'invalid-email'
        }
        
        with pytest.raises(ValidationError):
            OrderCreate(**order_data)


class TestOrderUpdate:
    """Test OrderUpdate schema"""
    
    def test_valid_order_update(self):
        """Test valid order update"""
        update_data = {
            'customer_name': 'Updated Customer',
            'status': 'completed'
        }
        
        update = OrderUpdate(**update_data)
        assert update.customer_name == 'Updated Customer'
        assert update.status == 'completed'
    
    def test_order_update_partial(self):
        """Test partial order update"""
        update_data = {
            'customer_name': 'Partial Update'
        }
        
        update = OrderUpdate(**update_data)
        assert update.customer_name == 'Partial Update'
        assert update.status is None
    
    def test_order_update_with_dates(self):
        """Test order update with dates"""
        update_data = {
            'invoice_date': date(2024, 2, 1),
            'due_date': date(2024, 3, 1)
        }
        
        update = OrderUpdate(**update_data)
        assert update.invoice_date == date(2024, 2, 1)
        assert update.due_date == date(2024, 3, 1)
    
    def test_order_update_invalid_email(self):
        """Test order update with invalid email"""
        update_data = {
            'customer_email': 'not-an-email'
        }
        
        with pytest.raises(ValidationError):
            OrderUpdate(**update_data)


class TestLineItemCreate:
    """Test LineItemCreate schema"""
    
    def test_valid_line_item(self):
        """Test creating a valid line item"""
        item_data = {
            'line_number': 1,
            'product_code': 'PROD-001',
            'product_name': 'Test Product',
            'quantity': 5,
            'unit_price': 100.00,
            'line_total': 500.00
        }
        
        item = LineItemCreate(**item_data)
        assert item.line_number == 1
        assert item.quantity == 5.0
    
    def test_line_item_defaults(self):
        """Test line item defaults"""
        item_data = {
            'product_name': 'Product'
        }
        
        item = LineItemCreate(**item_data)
        assert item.discount == 0


class TestLineItemUpdate:
    """Test LineItemUpdate schema"""
    
    def test_valid_line_item_update(self):
        """Test valid line item update"""
        update_data = {
            'quantity': 10,
            'unit_price': 200.00
        }
        
        update = LineItemUpdate(**update_data)
        assert update.quantity == 10.0
        assert update.unit_price == 200.00
    
    def test_line_item_update_partial(self):
        """Test partial line item update"""
        update_data = {
            'quantity': 15
        }
        
        update = LineItemUpdate(**update_data)
        assert update.quantity == 15.0
        assert update.unit_price is None

