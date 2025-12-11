from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class SalesOrderHeader(db.Model):
    __tablename__ = 'sales_order_header'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(100), unique=True, nullable=False)
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    customer_name = db.Column(db.String(200))
    customer_address = db.Column(db.Text)
    customer_email = db.Column(db.String(200))
    customer_phone = db.Column(db.String(50))
    subtotal = db.Column(db.Numeric(10, 2))
    tax = db.Column(db.Numeric(10, 2))
    total = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.String(50), default='pending')
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    file_path = db.Column(db.String(500))
    error_message = db.Column(db.Text)
    
    # Relationship
    line_items = db.relationship('SalesOrderDetail', backref='order', cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'customer_name': self.customer_name,
            'customer_address': self.customer_address,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'subtotal': float(self.subtotal) if self.subtotal else None,
            'tax': float(self.tax) if self.tax else None,
            'total': float(self.total) if self.total else None,
            'currency': self.currency,
            'status': self.status,
            'processing_status': self.processing_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'file_path': self.file_path,
            'error_message': self.error_message,
            'line_items': [item.to_dict() for item in self.line_items]
        }


class SalesOrderDetail(db.Model):
    __tablename__ = 'sales_order_detail'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('sales_order_header.id'), nullable=False)
    line_number = db.Column(db.Integer)
    product_code = db.Column(db.String(100))
    product_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    quantity = db.Column(db.Numeric(10, 2))
    unit_price = db.Column(db.Numeric(10, 2))
    discount = db.Column(db.Numeric(10, 2), default=0)
    line_total = db.Column(db.Numeric(10, 2))
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'line_number': self.line_number,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'description': self.description,
            'quantity': float(self.quantity) if self.quantity else None,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'discount': float(self.discount) if self.discount else None,
            'line_total': float(self.line_total) if self.line_total else None
        }

