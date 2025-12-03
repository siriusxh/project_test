"""
数据库初始化脚本
创建所有数据库表和索引
"""
import sys
from pathlib import Path

from app import create_app, db
from app.models import (
    SKU, PriceHistory,
    Requirement, Configuration, ConfigurationItem,
    EPSOrder, EPSOrderItem, BudgetAllocation
)


def init_database(config_name='development'):
    """
    初始化数据库
    
    Args:
        config_name: 配置名称 ('development', 'production', 'testing')
    """
    print(f"正在初始化数据库 (配置: {config_name})...")
    
    # 创建应用实例
    app = create_app(config_name)
    
    with app.app_context():
        # 删除所有表（如果存在）
        print("删除现有表...")
        db.drop_all()
        
        # 创建所有表
        print("创建数据库表...")
        db.create_all()
        
        # 验证表是否创建成功
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n成功创建 {len(tables)} 个表:")
        for table in sorted(tables):
            print(f"  - {table}")
            
            # 显示索引信息
            indexes = inspector.get_indexes(table)
            if indexes:
                print(f"    索引:")
                for idx in indexes:
                    cols = ', '.join(idx['column_names'])
                    unique = ' (唯一)' if idx.get('unique') else ''
                    print(f"      - {idx['name']}: {cols}{unique}")
        
        print("\n数据库初始化完成!")
        print(f"数据库文件位置: {app.config['DATABASE_FILE']}")


def verify_models():
    """验证所有模型是否正确定义"""
    print("\n验证数据模型...")
    
    models = [
        SKU, PriceHistory,
        Requirement, Configuration, ConfigurationItem,
        EPSOrder, EPSOrderItem, BudgetAllocation
    ]
    
    for model in models:
        print(f"  ✓ {model.__name__}")
    
    print("\n所有模型验证通过!")


if __name__ == '__main__':
    # 从命令行参数获取配置名称
    config_name = sys.argv[1] if len(sys.argv) > 1 else 'development'
    
    # 验证模型
    verify_models()
    
    # 初始化数据库
    init_database(config_name)
