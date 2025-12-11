import pytest
import json
import os
from io import BytesIO
from unittest.mock import patch, MagicMock
from app import app, db
from models import SalesOrderHeader, SalesOrderDetail


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns healthy status"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestUpload:
    """Test upload endpoint"""
    
    @patch('app.process_invoice_task')
    def test_upload_pdf_success(self, mock_task, client):
        """Test successful PDF upload"""
        mock_task_instance = MagicMock()
        mock_task_instance.id = 'task-123'
        mock_task.delay.return_value = mock_task_instance
        
        # Create a mock PDF file
        data = {
            'file': (BytesIO(b'%PDF-1.4 fake pdf content'), 'test.pdf')
        }
        
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 202
        
        response_data = json.loads(response.data)
        assert 'order_id' in response_data
        assert 'task_id' in response_data
        assert response_data['processing_status'] == 'pending'
    
    def test_upload_no_file(self, client):
        """Test upload without file"""
        response = client.post('/api/upload')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_upload_unsupported_type(self, client):
        """Test upload with unsupported file type"""
        data = {
            'file': (BytesIO(b'content'), 'test.txt')
        }
        
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Unsupported file type' in data['error']


class TestGetOrders:
    """Test get orders endpoint"""
    
    def test_get_orders_empty(self, client):
        """Test getting orders when none exist"""
        response = client.get('/api/orders')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert data['orders'] == []
    
    def test_get_orders_with_data(self, client, sample_order):
        """Test getting orders with data"""
        response = client.get('/api/orders')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert len(data['orders']) == 1
        assert data['orders'][0]['order_number'] == sample_order.order_number
    
    def test_get_orders_with_items(self, client, sample_order_with_items):
        """Test getting orders with line items"""
        response = client.get('/api/orders')
        assert response.status_code == 200
        data = json.loads(response.data)
        order = data['orders'][0]
        assert len(order['line_items']) == 2


class TestGetOrder:
    """Test get single order endpoint"""
    
    def test_get_order_success(self, client, sample_order):
        """Test getting a specific order"""
        response = client.get(f'/api/orders/{sample_order.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_order.id
        assert data['order_number'] == sample_order.order_number
    
    def test_get_order_not_found(self, client):
        """Test getting non-existent order"""
        response = client.get('/api/orders/99999')
        assert response.status_code == 404


class TestUpdateOrder:
    """Test update order endpoint"""
    
    def test_update_order_success(self, client, sample_order):
        """Test successful order update"""
        update_data = {
            'customer_name': 'Updated Customer',
            'status': 'completed'
        }
        
        response = client.put(
            f'/api/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['order']['customer_name'] == 'Updated Customer'
        assert data['order']['status'] == 'completed'
    
    def test_update_order_invalid_data(self, client, sample_order):
        """Test update with invalid data"""
        update_data = {
            'customer_email': 'invalid-email'
        }
        
        response = client.put(
            f'/api/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_order_with_line_items(self, client, sample_order):
        """Test updating order with line items"""
        update_data = {
            'customer_name': 'Updated',
            'line_items': [
                {
                    'line_number': 1,
                    'product_name': 'New Product',
                    'quantity': 3,
                    'unit_price': 50.00,
                    'line_total': 150.00
                }
            ]
        }
        
        response = client.put(
            f'/api/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['order']['line_items']) == 1
        assert data['order']['line_items'][0]['product_name'] == 'New Product'
    
    def test_update_order_not_found(self, client):
        """Test updating non-existent order"""
        update_data = {'customer_name': 'Test'}
        response = client.put(
            '/api/orders/99999',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 404


class TestDeleteOrder:
    """Test delete order endpoint"""
    
    def test_delete_order_success(self, client, sample_order):
        """Test successful order deletion"""
        order_id = sample_order.id
        response = client.delete(f'/api/orders/{order_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        
        # Verify order is deleted
        get_response = client.get(f'/api/orders/{order_id}')
        assert get_response.status_code == 404
    
    def test_delete_order_with_items(self, client, sample_order_with_items):
        """Test deleting order with line items"""
        order_id = sample_order_with_items.id
        response = client.delete(f'/api/orders/{order_id}')
        
        assert response.status_code == 200
        
        # Verify order and items are deleted
        with client.application.app_context():
            assert SalesOrderHeader.query.get(order_id) is None
            assert SalesOrderDetail.query.filter_by(order_id=order_id).count() == 0
    
    def test_delete_order_not_found(self, client):
        """Test deleting non-existent order"""
        response = client.delete('/api/orders/99999')
        assert response.status_code == 404


class TestStats:
    """Test stats endpoint"""
    
    def test_stats_empty(self, client):
        """Test stats with no orders"""
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_orders'] == 0
        assert data['total_value'] == 0.0
        assert data['average_order_value'] == 0.0
    
    def test_stats_with_orders(self, client, sample_order):
        """Test stats with orders"""
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_orders'] == 1
        assert data['total_value'] == 1100.0
        assert data['average_order_value'] == 1100.0
    
    def test_stats_multiple_orders(self, client):
        """Test stats with multiple orders"""
        with app.app_context():
            order1 = SalesOrderHeader(
                order_number='ORD-001',
                total=1000.00
            )
            order2 = SalesOrderHeader(
                order_number='ORD-002',
                total=2000.00
            )
            db.session.add(order1)
            db.session.add(order2)
            db.session.commit()
        
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_orders'] == 2
        assert data['total_value'] == 3000.0
        assert data['average_order_value'] == 1500.0


class TestTaskStatus:
    """Test task status endpoint"""
    
    @patch('app.process_invoice_task')
    def test_get_task_status_pending(self, mock_task_class, client):
        """Test getting pending task status"""
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_task.info = None
        mock_task_class.AsyncResult.return_value = mock_task
        
        response = client.get('/api/tasks/task-123')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['state'] == 'PENDING'
    
    @patch('app.process_invoice_task')
    def test_get_task_status_success(self, mock_task_class, client):
        """Test getting successful task status"""
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.result = {'status': 'success', 'order_id': 1}
        mock_task.info = None
        mock_task_class.AsyncResult.return_value = mock_task
        
        response = client.get('/api/tasks/task-123')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['state'] == 'SUCCESS'
        assert 'result' in data

