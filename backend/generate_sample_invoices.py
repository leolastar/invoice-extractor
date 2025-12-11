"""
Script to generate sample invoice PDFs for testing
This creates simple text-based PDFs that can be used for testing
"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()


def create_sample_invoice(filename, invoice_data=None):
    """Create a sample invoice PDF"""
    if invoice_data is None:
        invoice_data = {
            'invoice_number': fake.bothify('INV-####'),
            'order_number': fake.bothify('ORD-####'),
            'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            'due_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'customer_name': fake.company(),
            'customer_address': fake.address().replace('\n', ', '),
            'customer_email': fake.email(),
            'customer_phone': fake.phone_number(),
            'line_items': [
                {
                    'product_code': 'PROD-001',
                    'product_name': fake.catch_phrase(),
                    'description': fake.text(max_nb_chars=50),
                    'quantity': 2,
                    'unit_price': 500.00,
                    'line_total': 1000.00
                },
                {
                    'product_code': 'PROD-002',
                    'product_name': fake.catch_phrase(),
                    'description': fake.text(max_nb_chars=50),
                    'quantity': 1,
                    'unit_price': 200.00,
                    'line_total': 200.00
                }
            ],
            'subtotal': 1200.00,
            'tax': 120.00,
            'total': 1320.00
        }
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1 * inch, height - 1 * inch, "INVOICE")
    
    # Invoice details
    c.setFont("Helvetica", 12)
    y = height - 1.5 * inch
    c.drawString(1 * inch, y, f"Invoice Number: {invoice_data['invoice_number']}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Order Number: {invoice_data['order_number']}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Date: {invoice_data['invoice_date']}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Due Date: {invoice_data['due_date']}")
    
    # Customer information
    y -= 0.5 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Bill To:")
    y -= 0.25 * inch
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, y, invoice_data['customer_name'])
    y -= 0.25 * inch
    c.drawString(1 * inch, y, invoice_data['customer_address'])
    y -= 0.25 * inch
    c.drawString(1 * inch, y, invoice_data['customer_email'])
    y -= 0.25 * inch
    c.drawString(1 * inch, y, invoice_data['customer_phone'])
    
    # Line items table
    y -= 0.5 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, y, "Items:")
    y -= 0.3 * inch
    
    # Table header
    c.drawString(1 * inch, y, "Code")
    c.drawString(2 * inch, y, "Product")
    c.drawString(4 * inch, y, "Qty")
    c.drawString(4.5 * inch, y, "Price")
    c.drawString(5.5 * inch, y, "Total")
    y -= 0.25 * inch
    c.line(1 * inch, y, 6.5 * inch, y)
    y -= 0.2 * inch
    
    # Table rows
    c.setFont("Helvetica", 10)
    for item in invoice_data['line_items']:
        c.drawString(1 * inch, y, item['product_code'])
        c.drawString(2 * inch, y, item['product_name'][:30])
        c.drawString(4 * inch, y, str(item['quantity']))
        c.drawString(4.5 * inch, y, f"${item['unit_price']:.2f}")
        c.drawString(5.5 * inch, y, f"${item['line_total']:.2f}")
        y -= 0.3 * inch
    
    # Totals
    y -= 0.3 * inch
    c.line(1 * inch, y, 6.5 * inch, y)
    y -= 0.3 * inch
    c.setFont("Helvetica", 12)
    c.drawString(4.5 * inch, y, "Subtotal:")
    c.drawString(5.5 * inch, y, f"${invoice_data['subtotal']:.2f}")
    y -= 0.25 * inch
    c.drawString(4.5 * inch, y, "Tax:")
    c.drawString(5.5 * inch, y, f"${invoice_data['tax']:.2f}")
    y -= 0.25 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(4.5 * inch, y, "Total:")
    c.drawString(5.5 * inch, y, f"${invoice_data['total']:.2f}")
    
    c.save()
    print(f"Created sample invoice: {filename}")


if __name__ == '__main__':
    # Create sample-invoices directory in project root if it doesn't exist
    sample_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sample-invoices')
    os.makedirs(sample_dir, exist_ok=True)
    
    # Generate different types of sample invoices
    print("Generating sample invoices...")
    
    # Standard invoice
    create_sample_invoice(os.path.join(sample_dir, 'invoice_standard.pdf'))
    
    # Invoice with different format
    invoice_data_2 = {
        'invoice_number': 'INV-2024-001',
        'order_number': 'ORD-2024-001',
        'invoice_date': '2024-01-15',
        'due_date': '2024-02-15',
        'customer_name': 'Acme Corporation',
        'customer_address': '123 Business St, City, State 12345',
        'customer_email': 'billing@acme.com',
        'customer_phone': '555-0123',
        'line_items': [
            {
                'product_code': 'SRV-001',
                'product_name': 'Consulting Services',
                'description': 'Monthly consulting retainer',
                'quantity': 1,
                'unit_price': 5000.00,
                'line_total': 5000.00
            },
            {
                'product_code': 'SRV-002',
                'product_name': 'Support Services',
                'description': 'Technical support hours',
                'quantity': 10,
                'unit_price': 150.00,
                'line_total': 1500.00
            }
        ],
        'subtotal': 6500.00,
        'tax': 650.00,
        'total': 7150.00
    }
    create_sample_invoice(os.path.join(sample_dir, 'invoice_services.pdf'), invoice_data_2)
    
    # Invoice with multiple line items
    invoice_data_3 = {
        'invoice_number': 'INV-2024-002',
        'order_number': 'ORD-2024-002',
        'invoice_date': '2024-01-20',
        'due_date': '2024-02-20',
        'customer_name': 'Tech Solutions Inc.',
        'customer_address': '456 Innovation Ave, Tech City, TC 67890',
        'customer_email': 'accounts@techsolutions.com',
        'customer_phone': '555-0456',
        'line_items': [
            {
                'product_code': 'HW-001',
                'product_name': 'Server Hardware',
                'description': 'Dell PowerEdge Server',
                'quantity': 2,
                'unit_price': 2500.00,
                'line_total': 5000.00
            },
            {
                'product_code': 'SW-001',
                'product_name': 'Software License',
                'description': 'Annual software license',
                'quantity': 5,
                'unit_price': 500.00,
                'line_total': 2500.00
            },
            {
                'product_code': 'INST-001',
                'product_name': 'Installation',
                'description': 'On-site installation service',
                'quantity': 1,
                'unit_price': 1000.00,
                'line_total': 1000.00
            }
        ],
        'subtotal': 8500.00,
        'tax': 850.00,
        'total': 9350.00
    }
    create_sample_invoice(os.path.join(sample_dir, 'invoice_multiple_items.pdf'), invoice_data_3)
    
    # Invoice with different currency and format
    invoice_data_4 = {
        'invoice_number': 'INV-2024-003',
        'order_number': 'ORD-2024-003',
        'invoice_date': '2024-02-01',
        'due_date': '2024-03-01',
        'customer_name': 'Global Trading Co.',
        'customer_address': '789 International Blvd, Suite 100, New York, NY 10001',
        'customer_email': 'finance@globaltrading.com',
        'customer_phone': '212-555-7890',
        'line_items': [
            {
                'product_code': 'ITEM-A100',
                'product_name': 'Premium Widget Package',
                'description': 'Package of 50 premium widgets',
                'quantity': 3,
                'unit_price': 1250.00,
                'line_total': 3750.00
            },
            {
                'product_code': 'ITEM-B200',
                'product_name': 'Standard Widget Package',
                'description': 'Package of 100 standard widgets',
                'quantity': 5,
                'unit_price': 800.00,
                'line_total': 4000.00
            }
        ],
        'subtotal': 7750.00,
        'tax': 775.00,
        'total': 8525.00
    }
    create_sample_invoice(os.path.join(sample_dir, 'invoice_trading.pdf'), invoice_data_4)
    
    # Simple single-item invoice
    invoice_data_5 = {
        'invoice_number': 'INV-2024-004',
        'order_number': 'ORD-2024-004',
        'invoice_date': '2024-02-10',
        'due_date': '2024-03-10',
        'customer_name': 'Small Business LLC',
        'customer_address': '321 Main Street, Anytown, ST 12345',
        'customer_email': 'info@smallbiz.com',
        'customer_phone': '555-1234',
        'line_items': [
            {
                'product_code': 'SVC-001',
                'product_name': 'Website Development',
                'description': 'Complete website development and deployment',
                'quantity': 1,
                'unit_price': 3500.00,
                'line_total': 3500.00
            }
        ],
        'subtotal': 3500.00,
        'tax': 350.00,
        'total': 3850.00
    }
    create_sample_invoice(os.path.join(sample_dir, 'invoice_simple.pdf'), invoice_data_5)
    
    print("Sample invoices generated successfully!")
    print(f"Generated 5 sample invoices in {sample_dir}/ directory")

