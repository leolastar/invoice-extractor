import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from app import app
from models import db, SalesOrderHeader, SalesOrderDetail
from tasks import extract_text_from_pdf, extract_invoice_data_with_llm, _process_invoice_task_impl

# Set test environment variables
os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'


class TestExtractTextFromPDF:
    """Test PDF text extraction"""
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'%PDF-1.4 fake pdf')
    @patch('tasks.PyPDF2.PdfReader')
    def test_extract_text_success(self, mock_pdf_reader, mock_file):
        """Test successful PDF text extraction"""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Invoice text content"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        text = extract_text_from_pdf('/fake/path.pdf')
        assert text == "Invoice text content\n"
    
    @patch('builtins.open', side_effect=IOError("File not found"))
    def test_extract_text_file_error(self, mock_file):
        """Test PDF extraction with file error"""
        text = extract_text_from_pdf('/nonexistent/path.pdf')
        assert text == ""


class TestExtractInvoiceDataWithLLM:
    """Test LLM invoice extraction"""
    
    @patch('tasks.load_dotenv')
    @patch('tasks.OpenAI')
    @patch('tasks.os.getenv')
    @patch('tasks.os.environ.get')
    def test_extract_data_success(self, mock_environ_get, mock_getenv, mock_openai_class, mock_load_dotenv):
        """Test successful LLM extraction"""
        import tasks
        
        # Mock environment variables
        mock_getenv.return_value = 'test-key'
        mock_environ_get.return_value = 'test-key'
        
        # Create mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"order_number": "ORD-001", "customer_name": "Test", "total": 1000, "line_items": []}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Set the global openai_client before calling the function
        original_client = tasks.openai_client
        tasks.openai_client = mock_client
        
        try:
            result = extract_invoice_data_with_llm("Invoice text")
            assert result['order_number'] == 'ORD-001'
            assert result['customer_name'] == 'Test'
        finally:
            tasks.openai_client = original_client
    
    @patch('tasks.load_dotenv')
    @patch('tasks.OpenAI')
    @patch('tasks.os.getenv')
    @patch('tasks.os.environ.get')
    def test_extract_data_with_markdown(self, mock_environ_get, mock_getenv, mock_openai_class, mock_load_dotenv):
        """Test LLM extraction with markdown code blocks"""
        import tasks
        
        # Mock environment variables
        mock_getenv.return_value = 'test-key'
        mock_environ_get.return_value = 'test-key'
        
        # Create mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '```json\n{"order_number": "ORD-001"}\n```'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Set the global openai_client
        original_client = tasks.openai_client
        tasks.openai_client = mock_client
        
        try:
            result = extract_invoice_data_with_llm("Invoice text")
            assert result['order_number'] == 'ORD-001'
        finally:
            tasks.openai_client = original_client
    
    @patch('tasks.load_dotenv')
    @patch('tasks.os.getenv')
    @patch('tasks.os.environ.get')
    def test_extract_data_no_api_key(self, mock_environ_get, mock_getenv, mock_load_dotenv):
        """Test extraction without API key"""
        import tasks
        
        # Mock no API key available
        mock_getenv.return_value = ''
        mock_environ_get.return_value = ''
        
        original_client = tasks.openai_client
        tasks.openai_client = None
        
        try:
            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                extract_invoice_data_with_llm("Invoice text")
        finally:
            tasks.openai_client = original_client
    
    @patch('tasks.load_dotenv')
    @patch('tasks.OpenAI')
    @patch('tasks.os.getenv')
    @patch('tasks.os.environ.get')
    def test_extract_data_invalid_json(self, mock_environ_get, mock_getenv, mock_openai_class, mock_load_dotenv):
        """Test extraction with invalid JSON response"""
        import tasks
        
        # Mock environment variables
        mock_getenv.return_value = 'test-key'
        mock_environ_get.return_value = 'test-key'
        
        # Create mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = 'Invalid JSON'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Set the global openai_client
        original_client = tasks.openai_client
        tasks.openai_client = mock_client
        
        try:
            with pytest.raises(Exception):  # Should raise JSON decode error
                extract_invoice_data_with_llm("Invoice text")
        finally:
            tasks.openai_client = original_client


class TestProcessInvoiceTask:
    """Test Celery task for processing invoices"""
    
    @patch('tasks.extract_text_from_pdf')
    @patch('tasks.extract_invoice_data_with_llm')
    @patch('tasks.openai_client')
    def test_process_invoice_success(self, mock_openai, mock_llm, mock_pdf, client):
        """Test successful invoice processing"""
        with app.app_context():
            # Create order
            order = SalesOrderHeader(
                order_number='ORD-TEST',
                processing_status='pending',
                file_path='/fake/path.pdf'
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id
            
            # Mock functions
            mock_pdf.return_value = "Invoice text content"
            mock_llm.return_value = {
                'order_number': 'ORD-TEST',
                'invoice_number': 'INV-001',
                'customer_name': 'Test Customer',
                'subtotal': 1000.00,
                'tax': 100.00,
                'total': 1100.00,
                'line_items': [
                    {
                        'line_number': 1,
                        'product_name': 'Product 1',
                        'quantity': 2,
                        'unit_price': 500.00,
                        'line_total': 1000.00
                    }
                ]
            }
            
            # Set openai_client for the function
            import tasks
            tasks.openai_client = mock_openai
            
            # Execute task implementation directly (bypassing Celery decorator)
            mock_self = MagicMock()
            result = _process_invoice_task_impl(mock_self, order_id, '/fake/path.pdf')
            
            # Verify result
            assert result['status'] == 'success'
            assert result['order_id'] == order_id
            
            # Refresh session to get updated data
            db.session.expire_all()
            updated_order = SalesOrderHeader.query.get(order_id)
            assert updated_order.processing_status == 'completed'
            assert updated_order.customer_name == 'Test Customer'
            assert len(updated_order.line_items) == 1
    
    @patch('tasks.extract_text_from_pdf')
    @patch('tasks.openai_client')
    def test_process_invoice_extraction_error(self, mock_openai, mock_pdf, client):
        """Test invoice processing with extraction error"""
        with app.app_context():
            order = SalesOrderHeader(
                order_number='ORD-ERROR',
                processing_status='pending',
                file_path='/fake/path.pdf'
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id
            
            mock_pdf.return_value = ""  # Empty text
            
            # Set openai_client
            import tasks
            tasks.openai_client = mock_openai
            
            mock_self = MagicMock()
            with pytest.raises(ValueError):
                _process_invoice_task_impl(mock_self, order_id, '/fake/path.pdf')
            
            # Refresh session to get updated data
            db.session.expire_all()
            updated_order = SalesOrderHeader.query.get(order_id)
            assert updated_order.processing_status == 'failed'
            assert updated_order.error_message is not None
    
    @patch('tasks.extract_text_from_pdf')
    @patch('tasks.extract_invoice_data_with_llm')
    @patch('tasks.openai_client')
    def test_process_invoice_llm_error(self, mock_openai, mock_llm, mock_pdf, client):
        """Test invoice processing with LLM error"""
        with app.app_context():
            order = SalesOrderHeader(
                order_number='ORD-LLM-ERROR',
                processing_status='pending',
                file_path='/fake/path.pdf'
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id
            
            mock_pdf.return_value = "Invoice text"
            mock_llm.side_effect = Exception("LLM API error")
            
            # Set openai_client
            import tasks
            tasks.openai_client = mock_openai
            
            mock_self = MagicMock()
            with pytest.raises(Exception):
                _process_invoice_task_impl(mock_self, order_id, '/fake/path.pdf')
            
            # Refresh session to get updated data
            db.session.expire_all()
            updated_order = SalesOrderHeader.query.get(order_id)
            assert updated_order.processing_status == 'failed'
    
    @patch('tasks.openai_client')
    def test_process_invoice_order_not_found(self, mock_openai, client):
        """Test processing with non-existent order"""
        with app.app_context():
            # Set openai_client
            import tasks
            tasks.openai_client = mock_openai
            
            mock_self = MagicMock()
            with pytest.raises(ValueError, match="Order.*not found"):
                _process_invoice_task_impl(mock_self, 99999, '/fake/path.pdf')

