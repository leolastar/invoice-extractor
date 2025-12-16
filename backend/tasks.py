from celery import Celery
from models import db, SalesOrderHeader, SalesOrderDetail
from datetime import datetime
import os
import sys
import json
import traceback
import PyPDF2
from openai import OpenAI
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
# Try multiple paths to find .env file (for both local and Docker environments)
env_paths = [
    os.path.join(os.path.dirname(__file__), '.env'),  # Same directory as tasks.py
    os.path.join(os.path.dirname(__file__), '..', '.env'),  # Parent directory
    '.env',  # Current working directory
    '/app/.env',  # Docker container path
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
        break
else:
    # If no .env file found, try default load_dotenv() which searches current directory
    load_dotenv()
    print("Using default load_dotenv() - checking current directory and parent directories")

# Initialize Celery with connection retry settings
# Use lazy connection to avoid connecting during import
celery = Celery(
    'invoice_extractor',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

# Configure Celery with optimized settings following best practices
# Connection and retry settings
celery.conf.broker_connection_retry_on_startup = True
celery.conf.broker_connection_retry = True
celery.conf.broker_connection_max_retries = 30
celery.conf.broker_connection_retry_delay = 1.0
celery.conf.broker_connection_timeout = 30
celery.conf.result_backend_always_retry = True

# Serialization - use JSON for better performance and security
celery.conf.task_serializer = 'json'
celery.conf.result_serializer = 'json'
celery.conf.accept_content = ['json']
celery.conf.result_accept_content = ['json']

# Task execution settings
celery.conf.task_acks_late = True  # Acknowledge tasks after completion
celery.conf.task_reject_on_worker_lost = True  # Reject tasks if worker dies
celery.conf.worker_prefetch_multiplier = 1  # Process one task at a time per worker
celery.conf.task_time_limit = 300  # Hard time limit (5 minutes)
celery.conf.task_soft_time_limit = 240  # Soft time limit (4 minutes) - raises SoftTimeLimitExceeded

# Result backend settings
celery.conf.result_expires = 3600  # Results expire after 1 hour
celery.conf.result_backend_transport_options = {
    'retry_policy': {
        'timeout': 10.0
    },
    'visibility_timeout': 3600
}

# Broker transport options
celery.conf.broker_transport_options = {
    'retry_policy': {
        'timeout': 10.0
    },
    'visibility_timeout': 3600,
    'fanout_prefix': True,
    'fanout_patterns': True
}

# Worker settings
celery.conf.worker_max_tasks_per_child = 1000  # Restart worker after N tasks to prevent memory leaks
celery.conf.worker_disable_rate_limits = False  # Enable rate limiting
celery.conf.worker_send_task_events = True  # Send task events for monitoring

# Initialize OpenAI client (will be re-initialized when Flask app is available)
def get_openai_client():
    """Get OpenAI client, re-reading API key from environment"""
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        # Provide helpful error message
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        error_msg = (
            "OpenAI API key not configured.\n"
            f"Please set OPENAI_API_KEY environment variable or add it to {env_file}\n"
            "In Docker, ensure the environment variable is set in docker-compose.yml"
        )
        raise ValueError(error_msg)
    return OpenAI(api_key=api_key)

# Module-level client (will be updated when app initializes)
openai_client = None

def _init_openai_client():
    """Initialize OpenAI client from environment"""
    global openai_client
    try:
        # Try all possible .env file locations
        env_paths = [
            os.path.join(os.path.dirname(__file__), '.env'),  # Same directory as tasks.py
            '/app/.env',  # Docker container path
            '.env',  # Current working directory
        ]
        loaded = False
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path, override=True)
                print(f"Loaded .env from: {env_path}")
                loaded = True
                break
        
        if not loaded:
            # Fallback to default load_dotenv
            load_dotenv(override=True)
            print("Using default load_dotenv()")
        
        # Check environment variable
        api_key = os.getenv('OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
        if api_key:
            openai_client = OpenAI(api_key=api_key)
            print(f"OpenAI client initialized successfully (key length: {len(api_key)} chars)")
        else:
            raise ValueError("OPENAI_API_KEY not found in environment or .env file")
    except ValueError as e:
        openai_client = None
        print(f"Warning: OpenAI API key not found: {e}")
        print("LLM extraction will not work. Set OPENAI_API_KEY environment variable.")
    except Exception as e:
        openai_client = None
        print(f"Warning: Failed to initialize OpenAI client: {e}")

# Try to initialize on module load
_init_openai_client()

# Auto-initialize Flask app when running as Celery worker
# This ensures the app context is available for tasks
if os.getenv('CELERY_WORKER', '').lower() in ('1', 'true', 'yes') or \
   any('celery' in arg and 'worker' in arg for arg in sys.argv if isinstance(arg, str)):
    try:
        from app import app as _worker_flask_app
        _flask_app = _worker_flask_app
        # make_celery should have been called in app.py, but ensure it
        if not hasattr(celery, 'flask_app'):
            make_celery(_worker_flask_app)
    except ImportError:
        # Will be initialized in _ensure_flask_app if needed
        pass


# Global variable to store Flask app for tasks
_flask_app = None

def make_celery(app):
    """Initialize Celery with Flask app context"""
    global _flask_app
    _flask_app = app
    
    # Update Celery config from Flask config, but filter out old CELERY_* keys
    # and convert them to new format
    celery_config = {}
    for key, value in app.config.items():
        if key == 'CELERY_BROKER_URL':
            celery_config['broker_url'] = value
        elif key == 'CELERY_RESULT_BACKEND':
            celery_config['result_backend'] = value
        elif not key.startswith('CELERY_'):
            # Only include non-CELERY_ prefixed keys to avoid conflicts
            celery_config[key] = value
    
    celery.conf.update(celery_config)
    
    # Store the Flask app in the celery instance so ContextTask can access it
    celery.flask_app = app
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            # Use the Flask app from global or celery instance
            flask_app = _flask_app or getattr(celery, 'flask_app', None)
            if not flask_app:
                raise RuntimeError("Flask app not available. Make sure make_celery(app) was called.")
            with flask_app.app_context():
                return self.run(*args, **kwargs)
        
        def on_failure(self, exc, task_id, args, kwargs, einfo):
            """Handle task failures with app context."""
            # Use the Flask app from global or celery instance
            flask_app = _flask_app or getattr(celery, 'flask_app', None)
            if not flask_app:
                print("Warning: Flask app not available in on_failure handler")
                return
            with flask_app.app_context():
                # Try to update order status if possible
                try:
                    if args and len(args) >= 1:
                        order_id = args[0]
                        order = SalesOrderHeader.query.get(order_id)
                        if order:
                            order.processing_status = 'failed'
                            order.error_message = str(exc)
                            db.session.commit()
                except Exception as e:
                    print(f"Error updating order status on failure: {e}")
    
    celery.Task = ContextTask
    return celery


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""


def extract_invoice_data_with_llm(text_content):
    """Use OpenAI to extract structured invoice data"""
    
    # Re-initialize client if needed (in case env var was set after module load)
    global openai_client
    
    # Always try to reload environment variables and re-initialize client
    # This ensures we have the latest API key even if it was set after module load
    try:
        # Try all possible .env file locations
        env_paths = [
            os.path.join(os.path.dirname(__file__), '.env'),  # Same directory as tasks.py
            '/app/.env',  # Docker container path
            '.env',  # Current working directory
        ]
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path, override=True)
                print(f"Reloaded .env from: {env_path}")
                break
        else:
            # Fallback to default load_dotenv
            load_dotenv(override=True)
        
        # Check if API key is available
        api_key = os.getenv('OPENAI_API_KEY', '')
        if not api_key:
            # Try to get from environment (might be set by docker-compose)
            api_key = os.environ.get('OPENAI_API_KEY', '')
        
        if not api_key:
            raise ValueError(
                "OpenAI API key not found in environment.\n"
                f"Checked paths: {env_paths}\n"
                "Please ensure OPENAI_API_KEY is set in:\n"
                "1. backend/.env file, or\n"
                "2. docker-compose.yml environment section, or\n"
                "3. Host environment variable"
            )
        
        # Re-initialize client with the API key only if not already set
        if not openai_client:
            openai_client = OpenAI(api_key=api_key)
            print(f"OpenAI client initialized (key length: {len(api_key)} chars)")
        
    except ValueError as e:
        raise ValueError(f"OpenAI API key not configured: {e}") from e
    except Exception as e:
        raise ValueError(f"Failed to initialize OpenAI client: {e}") from e
    
    if not openai_client:
        raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
    
    prompt = f"""Extract invoice information from the following document text and return it as a JSON object with this exact structure:

{{
  "order_number": "string or null",
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "customer_name": "string or null",
  "customer_address": "string or null",
  "customer_email": "string or null",
  "customer_phone": "string or null",
  "subtotal": number or null,
  "tax": number or null,
  "total": number or null,
  "currency": "string (default: USD)",
  "line_items": [
    {{
      "line_number": number,
      "product_code": "string or null",
      "product_name": "string or null",
      "description": "string or null",
      "quantity": number,
      "unit_price": number,
      "discount": number (default: 0),
      "line_total": number
    }}
  ]
}}

Document text:
{text_content[:4000]}

Return ONLY valid JSON, no additional text or explanation."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from invoices. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {e}"
        print(f"Error with LLM extraction: {error_msg}")
        print(f"Response content: {content[:500] if 'content' in locals() else 'N/A'}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Error with LLM extraction: {e}"
        print(error_msg)
        raise ValueError(error_msg)


def _process_invoice_task_impl(self, order_id, file_path):
    """Internal implementation of invoice processing task"""
    try:
        # Update status to processing
        order = SalesOrderHeader.query.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.processing_status = 'processing'
        db.session.commit()
        
        # Extract text from file
        file_ext = file_path.lower().split('.')[-1]
        if file_ext == 'pdf':
            text_content = extract_text_from_pdf(file_path)
        else:
            # For images, we'd use OCR here
            text_content = "Image file detected. OCR processing would happen here."
        
        if not text_content or len(text_content.strip()) < 10:
            raise ValueError("Could not extract text from document")
        
        # Extract structured data using LLM
        extracted_data = extract_invoice_data_with_llm(text_content)
        
        # Generate order number if not present
        if not extracted_data.get('order_number'):
            extracted_data['order_number'] = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Parse dates
        invoice_date = None
        due_date = None
        if extracted_data.get('invoice_date'):
            try:
                invoice_date = datetime.strptime(extracted_data['invoice_date'], '%Y-%m-%d').date()
            except:
                pass
        if extracted_data.get('due_date'):
            try:
                due_date = datetime.strptime(extracted_data['due_date'], '%Y-%m-%d').date()
            except:
                pass
        
        # Update order header
        order.invoice_number = extracted_data.get('invoice_number') or order.invoice_number
        order.invoice_date = invoice_date or order.invoice_date
        order.due_date = due_date or order.due_date
        order.customer_name = extracted_data.get('customer_name') or order.customer_name
        order.customer_address = extracted_data.get('customer_address') or order.customer_address
        order.customer_email = extracted_data.get('customer_email') or order.customer_email
        order.customer_phone = extracted_data.get('customer_phone') or order.customer_phone
        order.subtotal = extracted_data.get('subtotal') or order.subtotal
        order.tax = extracted_data.get('tax') or order.tax
        order.total = extracted_data.get('total') or order.total
        order.currency = extracted_data.get('currency', 'USD')
        order.processing_status = 'completed'
        order.status = 'completed'
        order.error_message = None
        
        # Delete existing line items
        SalesOrderDetail.query.filter_by(order_id=order_id).delete()
        
        # Create line items
        for item_data in extracted_data.get('line_items', []):
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
        
        return {
            'status': 'success',
            'order_id': order_id,
            'message': 'Invoice processed successfully'
        }
        
    except Exception as e:
        # Update order with error
        error_msg = str(e)
        print(f"Error processing invoice for order {order_id}: {error_msg}")
        print(traceback.format_exc())
        
        order = SalesOrderHeader.query.get(order_id)
        if order:
            order.processing_status = 'failed'
            order.error_message = error_msg
            db.session.commit()
        
        # Re-raise to let Celery know the task failed
        raise


# Initialize Flask app for worker process if not already initialized
def _ensure_flask_app():
    """Ensure Flask app is initialized for worker process"""
    global _flask_app, openai_client
    if _flask_app is None:
        try:
            # Try to import app from app.py (this will call make_celery)
            from app import app as flask_app
            _flask_app = flask_app
            # make_celery should have been called in app.py, but ensure it
            if not hasattr(celery, 'flask_app'):
                make_celery(flask_app)
            # Re-initialize OpenAI client now that we have the app context
            _init_openai_client()
        except ImportError as e:
            # If app.py can't be imported, create a minimal app
            print(f"Warning: Could not import app from app.py: {e}")
            print("Creating minimal Flask app for worker...")
            flask_app = Flask(__name__)
            # Use individual environment variables or fall back to DATABASE_URL or defaults
            POSTGRES_USER = os.getenv('POSTGRES_USER', 'invoice_user')
            POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'invoice_pass')
            POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')
            POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
            POSTGRES_DB = os.getenv('POSTGRES_DB', 'invoice_db')
            
            # Construct DATABASE_URL from individual variables if DATABASE_URL is not set
            if os.getenv('DATABASE_URL'):
                database_url = os.getenv('DATABASE_URL')
            else:
                database_url = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
            
            flask_app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            db.init_app(flask_app)
            _flask_app = flask_app
            make_celery(flask_app)
            # Re-initialize OpenAI client
            _init_openai_client()

@celery.task(
    bind=True,
    name='process_invoice',
    max_retries=3,
    default_retry_delay=60,  # Wait 60 seconds before retry
    soft_time_limit=240,  # 4 minutes soft limit
    time_limit=300,  # 5 minutes hard limit
    retry_backoff=True,  # Exponential backoff for retries
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True  # Add randomness to retry delays to prevent thundering herd
)
def process_invoice_task(self, order_id, file_path):
    """Celery task to process invoice document with retry logic"""
    # Ensure Flask app is initialized (for worker process)
    _ensure_flask_app()
    
    # Ensure we have Flask app context
    # ContextTask.__call__ should provide this, but add explicit check
    from flask import has_app_context
    if not has_app_context():
        # If somehow we don't have context, try to get it from global
        flask_app = _flask_app or getattr(celery, 'flask_app', None)
        if flask_app:
            with flask_app.app_context():
                return _process_invoice_task_impl(self, order_id, file_path)
        else:
            raise RuntimeError("No Flask application context available and no Flask app found")
    
    try:
        return _process_invoice_task_impl(self, order_id, file_path)
    except (ValueError, RuntimeError) as exc:
        # Don't retry on these errors - they're likely permanent failures
        raise
    except Exception as exc:
        # Log the error and retry for transient failures
        print(f"Task {self.request.id} failed with transient error: {exc}")
        # Retry with exponential backoff (handled by retry_backoff=True)
        raise self.retry(exc=exc)

