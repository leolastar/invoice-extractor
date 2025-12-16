from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from dotenv import load_dotenv
from pydantic import ValidationError

from models import db, SalesOrderHeader, SalesOrderDetail
from schemas import OrderUpdate
from tasks import make_celery, process_invoice_task

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
# Use individual environment variables or fall back to DATABASE_URL or defaults
POSTGRES_USER = os.getenv('POSTGRES_USER', 'invoice_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'invoice_pass')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'invoice_db')

# Construct DATABASE_URL from individual variables if DATABASE_URL is not set
if os.getenv('DATABASE_URL'):
    DATABASE_URL = os.getenv('DATABASE_URL')
else:
    DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# Validate and fix connection string if needed (skip in testing mode)
if not app.config.get('TESTING') and DATABASE_URL:
    # Ensure database name is present (not using username as database)
    if DATABASE_URL.endswith(f'@{POSTGRES_HOST}:{POSTGRES_PORT}') or DATABASE_URL.endswith(f'@{POSTGRES_HOST}'):
        DATABASE_URL = DATABASE_URL + f'/{POSTGRES_DB}'
    # Fix common mistake: using username as database name
    if f'/{POSTGRES_USER}' in DATABASE_URL and not DATABASE_URL.endswith(f'/{POSTGRES_DB}'):
        DATABASE_URL = DATABASE_URL.replace(f'/{POSTGRES_USER}', f'/{POSTGRES_DB}')

# Set database URI - use test database if TESTING is set
if os.getenv('TESTING') == '1' or app.config.get('TESTING'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print(f"Database URL configured: {POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")  # Log without password

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# Store Celery config in Flask config for make_celery to use (using new format)
app.config['broker_url'] = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
app.config['result_backend'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# Initialize database
db.init_app(app)

# Initialize Celery
celery = make_celery(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'invoice-extractor-api'})


@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload document and queue processing task"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    file_ext = file.filename.lower().split('.')[-1]
    if file_ext not in ['pdf', 'jpg', 'jpeg', 'png', 'gif']:
        return jsonify({'error': 'Unsupported file type. Supported: PDF, JPG, PNG, GIF'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create order record with pending status
        order_header = SalesOrderHeader(
            order_number=order_number,
            processing_status='pending',
            status='pending',
            file_path=file_path
        )
        
        db.session.add(order_header)
        db.session.commit()
        
        # Queue processing task
        task = process_invoice_task.delay(order_header.id, file_path)
        
        return jsonify({
            'message': 'Invoice uploaded and queued for processing',
            'order_id': order_header.id,
            'order_number': order_number,
            'task_id': task.id,
            'processing_status': 'pending',
            'order': order_header.to_dict()
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    orders = SalesOrderHeader.query.order_by(SalesOrderHeader.created_at.desc()).all()
    return jsonify({
        'orders': [order.to_dict() for order in orders],
        'count': len(orders)
    })


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a specific order"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    return jsonify(order.to_dict())


@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """Update an order with Pydantic validation"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    
    try:
        # Validate input with Pydantic
        update_data = OrderUpdate(**request.json)
        
        # Update header fields
        update_dict = update_data.dict(exclude_unset=True)
        
        if 'invoice_number' in update_dict:
            order.invoice_number = update_dict['invoice_number']
        if 'invoice_date' in update_dict and update_dict['invoice_date']:
            order.invoice_date = update_dict['invoice_date']
        if 'due_date' in update_dict and update_dict['due_date']:
            order.due_date = update_dict['due_date']
        if 'customer_name' in update_dict:
            order.customer_name = update_dict['customer_name']
        if 'customer_address' in update_dict:
            order.customer_address = update_dict['customer_address']
        if 'customer_email' in update_dict:
            order.customer_email = update_dict['customer_email']
        if 'customer_phone' in update_dict:
            order.customer_phone = update_dict['customer_phone']
        if 'subtotal' in update_dict:
            order.subtotal = update_dict['subtotal']
        if 'tax' in update_dict:
            order.tax = update_dict['tax']
        if 'total' in update_dict:
            order.total = update_dict['total']
        if 'currency' in update_dict:
            order.currency = update_dict['currency']
        if 'status' in update_dict:
            order.status = update_dict['status']
        
        order.updated_at = datetime.utcnow()
        
        # Update line items if provided
        if 'line_items' in update_dict and update_dict['line_items']:
            # Delete existing line items
            SalesOrderDetail.query.filter_by(order_id=order_id).delete()
            
            # Add new line items
            for item_data in update_dict['line_items']:
                line_item = SalesOrderDetail(
                    order_id=order.id,
                    line_number=item_data.get('line_number'),
                    product_code=item_data.get('product_code'),
                    product_name=item_data.get('product_name'),
                    description=item_data.get('description'),
                    quantity=item_data.get('quantity'),
                    unit_price=item_data.get('unit_price'),
                    discount=item_data.get('discount', 0),
                    line_total=item_data.get('line_total')
                )
                db.session.add(line_item)
        
        db.session.commit()
        return jsonify({
            'message': 'Order updated successfully',
            'order': order.to_dict()
        })
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Update failed: {str(e)}'}), 500


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Delete an order"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    
    # Delete associated file if exists
    if order.file_path and os.path.exists(order.file_path):
        try:
            os.remove(order.file_path)
        except:
            pass
    
    db.session.delete(order)
    db.session.commit()
    
    return jsonify({'message': 'Order deleted successfully'})


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get Celery task status"""
    task = process_invoice_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to be processed'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'status': task.info.get('status', 'Processing...')
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'status': 'Task completed successfully',
            'result': task.result
        }
    else:  # FAILURE
        response = {
            'state': task.state,
            'status': 'Task failed',
            'error': str(task.info)
        }
    
    return jsonify(response)


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about orders"""
    total_orders = SalesOrderHeader.query.count()
    total_value = db.session.query(db.func.sum(SalesOrderHeader.total)).scalar() or 0
    
    return jsonify({
        'total_orders': total_orders,
        'total_value': float(total_value),
        'average_order_value': float(total_value / total_orders) if total_orders > 0 else 0
    })


# Initialize database tables (only when not in testing mode)
if not app.config.get('TESTING'):
    import time
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            with app.app_context():
                db.create_all()
                print("Database tables created successfully")
                break
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"Database connection failed, retrying ({retry_count}/{max_retries}): {e}")
                time.sleep(2)
            else:
                print(f"Warning: Could not create database tables after {max_retries} attempts: {e}")


if __name__ == '__main__':
    # For development
    app.run(host='0.0.0.0', port=5000, debug=True)
