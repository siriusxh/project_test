"""
路由蓝图包
"""
from .main_routes import main_bp
from .sku_routes import sku_bp
from .requirement_routes import requirement_bp
from .order_routes import order_bp

__all__ = ['main_bp', 'sku_bp', 'requirement_bp', 'order_bp']
