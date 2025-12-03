"""
需求和配置数据模型
"""
from datetime import datetime
from decimal import Decimal

from app import db


class Requirement(db.Model):
    """需求模型"""
    __tablename__ = 'requirements'
    
    id = db.Column(db.Integer, primary_key=True)
    requirement_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    jira_case = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    configurations = db.relationship('Configuration', backref='requirement', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('EPSOrder', backref='requirement', lazy='dynamic')
    
    def __repr__(self):
        return f'<Requirement {self.requirement_code}: {self.jira_case}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'requirement_code': self.requirement_code,
            'jira_case': self.jira_case,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Configuration(db.Model):
    """配置方案模型"""
    __tablename__ = 'configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=False, index=True)
    config_name = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    items = db.relationship('ConfigurationItem', backref='configuration', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Configuration {self.config_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'config_name': self.config_name,
            'total_price': float(self.total_price),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ConfigurationItem(db.Model):
    """配置项模型"""
    __tablename__ = 'configuration_items'
    
    id = db.Column(db.Integer, primary_key=True)
    configuration_id = db.Column(db.Integer, db.ForeignKey('configurations.id'), nullable=False, index=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('skus.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)  # 快照价格
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    
    def __repr__(self):
        return f'<ConfigurationItem SKU:{self.sku_id} x{self.quantity}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'configuration_id': self.configuration_id,
            'sku_id': self.sku_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': float(self.subtotal)
        }
