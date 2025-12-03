"""
Flask应用工厂函数
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 初始化扩展
db = SQLAlchemy()


def create_app(config_name='default'):
    """
    Flask应用工厂函数
    
    Args:
        config_name: 配置名称 ('development', 'production', 'testing')
    
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    from config import config
    app.config.from_object(config[config_name])
    
    # 确保必要的目录存在
    _ensure_directories(app)
    
    # 初始化扩展
    db.init_app(app)
    
    # 配置日志
    _setup_logging(app)
    
    # 注册蓝图（路由）
    from app.routes import main_bp, sku_bp, requirement_bp, order_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(sku_bp)
    app.register_blueprint(requirement_bp)
    app.register_blueprint(order_bp)
    
    # 注册错误处理器
    _register_error_handlers(app)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    app.logger.info('Flask应用启动成功')
    
    return app


def _ensure_directories(app):
    """确保必要的目录存在"""
    # 创建日志目录
    log_dir = Path(app.config['LOG_DIR'])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建数据目录
    data_dir = Path(app.config['DATA_DIR'])
    data_dir.mkdir(parents=True, exist_ok=True)


def _setup_logging(app):
    """配置日志系统"""
    if not app.debug and not app.testing:
        # 配置应用日志
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s] - %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # 配置错误日志
        error_handler = RotatingFileHandler(
            app.config['ERROR_LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        error_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s] - %(message)s\n'
            'Exception: %(exc_info)s'
        ))
        error_handler.setLevel(logging.ERROR)
        app.logger.addHandler(error_handler)
        
        app.logger.setLevel(logging.INFO)
    else:
        # 开发环境使用控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] - %(message)s'
        ))
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)


def _register_error_handlers(app):
    """注册全局错误处理器"""
    from app.exceptions import (
        ValidationError, 
        BusinessLogicError, 
        DatabaseError,
        ReferentialIntegrityError,
        ForeignKeyError
    )
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError as SQLIntegrityError
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """处理验证错误"""
        app.logger.warning(f'Validation error: {error.message}')
        return {'error': error.message, 'field': error.field}, 400
    
    @app.errorhandler(ForeignKeyError)
    def handle_foreign_key_error(error):
        """处理外键错误"""
        app.logger.warning(f'Foreign key error: {error.message}')
        return {
            'error': error.message, 
            'field': error.foreign_key_field,
            'value': error.foreign_key_value
        }, 400
    
    @app.errorhandler(ReferentialIntegrityError)
    def handle_referential_integrity_error(error):
        """处理引用完整性错误"""
        app.logger.warning(f'Referential integrity error: {error.message}')
        return {
            'error': error.message,
            'entity_type': error.entity_type,
            'entity_id': error.entity_id,
            'dependent_count': error.dependent_count
        }, 409
    
    @app.errorhandler(BusinessLogicError)
    def handle_business_logic_error(error):
        """处理业务逻辑错误"""
        app.logger.warning(f'Business logic error: {error.message}')
        return {'error': error.message}, 409
    
    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        """处理数据库错误"""
        app.logger.error(f'Database error: {error.message}', exc_info=error.original_error)
        db.session.rollback()
        return {'error': '数据库操作失败'}, 500
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """处理SQLAlchemy错误"""
        app.logger.error(f'SQLAlchemy error: {error}', exc_info=True)
        db.session.rollback()
        return {'error': '数据库操作失败'}, 500
    
    @app.errorhandler(SQLIntegrityError)
    def handle_sql_integrity_error(error):
        """处理SQL完整性错误"""
        app.logger.error(f'SQL integrity error: {error}', exc_info=True)
        db.session.rollback()
        return {'error': '数据完整性约束违反'}, 409
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f'Bad request: {error}')
        return {'error': '请求参数错误'}, 400
    
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f'Not found: {error}')
        return {'error': '资源不存在'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal error: {error}', exc_info=True)
        db.session.rollback()
        return {'error': '系统错误，请联系管理员'}, 500
