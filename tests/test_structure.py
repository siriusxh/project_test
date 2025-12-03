"""
项目结构测试
"""
from pathlib import Path


def test_project_structure():
    """测试项目目录结构是否完整"""
    base_dir = Path(__file__).parent.parent
    
    # 检查主要目录
    assert (base_dir / 'app').is_dir(), "app目录不存在"
    assert (base_dir / 'app' / 'models').is_dir(), "models目录不存在"
    assert (base_dir / 'app' / 'services').is_dir(), "services目录不存在"
    assert (base_dir / 'app' / 'repositories').is_dir(), "repositories目录不存在"
    assert (base_dir / 'app' / 'templates').is_dir(), "templates目录不存在"
    assert (base_dir / 'app' / 'static').is_dir(), "static目录不存在"
    assert (base_dir / 'tests').is_dir(), "tests目录不存在"
    
    # 检查主要文件
    assert (base_dir / 'config.py').is_file(), "config.py不存在"
    assert (base_dir / 'run.py').is_file(), "run.py不存在"
    assert (base_dir / 'requirements.txt').is_file(), "requirements.txt不存在"
    assert (base_dir / 'README.md').is_file(), "README.md不存在"
    assert (base_dir / '.gitignore').is_file(), ".gitignore不存在"
    
    # 检查__init__.py文件
    assert (base_dir / 'app' / '__init__.py').is_file(), "app/__init__.py不存在"
    assert (base_dir / 'app' / 'models' / '__init__.py').is_file(), "models/__init__.py不存在"
    assert (base_dir / 'app' / 'services' / '__init__.py').is_file(), "services/__init__.py不存在"
    assert (base_dir / 'app' / 'repositories' / '__init__.py').is_file(), "repositories/__init__.py不存在"
    
    print("✓ 所有目录和文件结构完整")


def test_config_file_content():
    """测试配置文件内容"""
    base_dir = Path(__file__).parent.parent
    config_file = base_dir / 'config.py'
    
    content = config_file.read_text(encoding='utf-8')
    
    assert 'class Config' in content, "Config类不存在"
    assert 'class DevelopmentConfig' in content, "DevelopmentConfig类不存在"
    assert 'class ProductionConfig' in content, "ProductionConfig类不存在"
    assert 'class TestConfig' in content, "TestConfig类不存在"
    assert 'SQLALCHEMY_DATABASE_URI' in content, "数据库URI配置不存在"
    assert 'LOG_DIR' in content, "日志目录配置不存在"
    
    print("✓ 配置文件内容完整")


def test_app_init_content():
    """测试应用初始化文件内容"""
    base_dir = Path(__file__).parent.parent
    init_file = base_dir / 'app' / '__init__.py'
    
    content = init_file.read_text(encoding='utf-8')
    
    assert 'def create_app' in content, "create_app函数不存在"
    assert 'SQLAlchemy' in content, "SQLAlchemy未导入"
    assert '_setup_logging' in content, "日志配置函数不存在"
    assert '_register_error_handlers' in content, "错误处理器注册函数不存在"
    assert 'db.create_all()' in content, "数据库初始化代码不存在"
    
    print("✓ 应用初始化文件内容完整")


def test_requirements_file():
    """测试依赖文件"""
    base_dir = Path(__file__).parent.parent
    req_file = base_dir / 'requirements.txt'
    
    content = req_file.read_text(encoding='utf-8')
    
    assert 'Flask' in content, "Flask依赖不存在"
    assert 'SQLAlchemy' in content, "SQLAlchemy依赖不存在"
    assert 'pytest' in content, "pytest依赖不存在"
    assert 'hypothesis' in content, "hypothesis依赖不存在"
    assert 'WTForms' in content, "WTForms依赖不存在"
    assert 'openpyxl' in content, "openpyxl依赖不存在"
    assert 'waitress' in content, "waitress依赖不存在"
    
    print("✓ 依赖文件完整")


if __name__ == '__main__':
    test_project_structure()
    test_config_file_content()
    test_app_init_content()
    test_requirements_file()
    print("\n所有结构测试通过！项目设置完成。")
