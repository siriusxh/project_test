"""
SKU和价格历史数据模型
"""
from datetime import datetime
from decimal import Decimal

from app import db


class SKU(db.Model):
    """SKU模型 - 库存单位"""
    __tablename__ = 'skus'
    
    id = db.Column(db.Integer, primary_key=True)
    sku_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    supplier = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    price_history = db.relationship('PriceHistory', backref='sku', lazy='dynamic', cascade='all, delete-orphan')
    configuration_items = db.relationship('ConfigurationItem', backref='sku', lazy='dynamic')
    order_items = db.relationship('EPSOrderItem', backref='sku', lazy='dynamic')
    
    def __repr__(self):
        return f'<SKU {self.sku_code}: {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'sku_code': self.sku_code,
            'name': self.name,
            'unit_price': float(self.unit_price),
            'supplier': self.supplier,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PriceHistory(db.Model):
    """价格历史模型"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('skus.id'), nullable=False, index=True)
    old_price = db.Column(db.Numeric(10, 2), nullable=False)
    new_price = db.Column(db.Numeric(10, 2), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<PriceHistory SKU:{self.sku_id} {self.old_price}->{self.new_price}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'sku_id': self.sku_id,
            'old_price': float(self.old_price),
            'new_price': float(self.new_price),
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'changed_by': self.changed_by
        }
