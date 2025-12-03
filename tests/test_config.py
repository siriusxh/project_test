"""
配置测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_config_classes_exist():
    """测试配置类是否存在"""
    from config import Config, DevelopmentConfig, ProductionConfig, TestConfig, config
    
    assert Config is not None
    assert DevelopmentConfig is not None
    assert ProductionConfig is not None
    assert TestConfig is not None
    assert config is not None


def test_development_config():
    """测试开发环境配置"""
    from config import DevelopmentConfig
    
    assert DevelopmentConfig.DEBUG is True
    assert DevelopmentConfig.SQLALCHEMY_ECHO is True


def test_production_config():
    """测试生产环境配置"""
    from config import ProductionConfig
    
    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.SQLALCHEMY_ECHO is False


def test_test_config():
    """测试测试环境配置"""
    from config import TestConfig
    
    assert TestConfig.TESTING is True
    assert 'memory' in TestConfig.SQLALCHEMY_DATABASE_URI


def test_config_dict():
    """测试配置字典"""
    from config import config
    
    assert 'development' in config
    assert 'production' in config
    assert 'testing' in config
    assert 'default' in config


def test_database_paths():
    """测试数据库路径配置"""
    from config import Config
    
    assert Config.DATA_DIR is not None
    assert Config.DATABASE_FILE is not None
    assert str(Config.DATABASE_FILE).endswith('server_orders.db')


def test_log_paths():
    """测试日志路径配置"""
    from config import Config
    
    assert Config.LOG_DIR is not None
    assert Config.LOG_FILE is not None
    assert Config.ERROR_LOG_FILE is not None
    assert str(Config.LOG_FILE).endswith('app.log')
    assert str(Config.ERROR_LOG_FILE).endswith('error.log')


if __name__ == '__main__':
    # 运行基本验证
    test_config_classes_exist()
    test_development_config()
    test_production_config()
    test_test_config()
    test_config_dict()
    test_database_paths()
    test_log_paths()
    print("所有配置测试通过！")
