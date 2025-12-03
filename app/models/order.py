"""
EPS订单和预算分配数据模型
"""
from datetime import datetime
from decimal import Decimal

from app import db


class EPSOrder(db.Model):
    """EPS订单模型"""
    __tablename__ = 'eps_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=False, index=True)
    supplier = db.Column(db.String(100), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    items = db.relationship('EPSOrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    budget_allocations = db.relationship('BudgetAllocation', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EPSOrder {self.order_code}: {self.supplier}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_code': self.order_code,
            'requirement_id': self.requirement_id,
            'supplier': self.supplier,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class EPSOrderItem(db.Model):
    """EPS订单项模型"""
    __tablename__ = 'eps_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('eps_orders.id'), nullable=False, index=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('skus.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    
    def __repr__(self):
        return f'<EPSOrderItem Order:{self.order_id} SKU:{self.sku_id} x{self.quantity}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'sku_id': self.sku_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': float(self.subtotal)
        }


class BudgetAllocation(db.Model):
    """预算分配模型"""
    __tablename__ = 'budget_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('eps_orders.id'), nullable=False, index=True)
    budget_code = db.Column(db.String(50), nullable=False, index=True)
    allocation_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    def __repr__(self):
        return f'<BudgetAllocation Order:{self.order_id} {self.budget_code} {self.allocation_percentage}%>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'budget_code': self.budget_code,
            'allocation_percentage': float(self.allocation_percentage),
            'amount': float(self.amount)
        }
