"""
数据库同步服务
处理数据库文件外部修改检测和刷新机制
"""
import os
import sqlite3
from pathlib import Path
from flask import current_app
from app import db


class DatabaseSyncService:
    """数据库同步服务类"""
    
    @staticmethod
    def get_database_path():
        """获取数据库文件路径"""
        database_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if database_uri.startswith('sqlite:///'):
            # 移除 'sqlite:///' 前缀
            db_path = database_uri.replace('sqlite:///', '')
            return Path(db_path)
        return None
    
    @staticmethod
    def get_database_modification_time():
        """
        获取数据库文件的最后修改时间
        
        Returns:
            float: 文件修改时间戳，如果文件不存在返回None
        """
        db_path = DatabaseSyncService.get_database_path()
        if db_path and db_path.exists():
            return os.path.getmtime(db_path)
        return None
    
    @staticmethod
    def check_database_integrity():
        """
        检查数据库文件完整性
        
        Returns:
            tuple: (is_valid, error_message)
        """
        db_path = DatabaseSyncService.get_database_path()
        
        if not db_path:
            return False, "无法确定数据库文件路径"
        
        if not db_path.exists():
            return False, "数据库文件不存在"
        
        try:
           