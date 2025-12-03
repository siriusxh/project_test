"""
项目设置验证脚本
验证任务1的所有要求是否完成
"""
from pathlib import Path
import sys


def verify_directory_structure():
    """验证目录结构"""
    print("=" * 60)
    print("验证目录结构")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    required_dirs = [
        'app',
        'app/models',
        'app/services',
        'app/repositories',
        'app/templates',
        'app/static',
        'tests'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        exists = full_path.is_dir()
        status = "✓" if exists else "✗"
        print(f"{status} {dir_path}/")
        if not exists:
            all_exist = False
    
    return all_exist


def verify_config_files():
    """验证配置文件"""
    print("\n" + "=" * 60)
    print("验证配置文件")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    required_files = [
        'config.py',
        'run.py',
        'requirements.txt',
        'README.md',
        '.gitignore'
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_dir / file_path
        exists = full_path.is_file()
        status = "✓" if exists else "✗"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def verify_config_content():
    """验证配置内容"""
    print("\n" + "=" * 60)
    print("验证配置内容")
    print("=" * 60)
    
    try:
        from config import Config, DevelopmentConfig, ProductionConfig, TestConfig, config
        
        checks = [
            ("Config基类", Config is not None),
            ("DevelopmentConfig", DevelopmentConfig is not None),
            ("ProductionConfig", ProductionConfig is not None),
            ("TestConfig", TestConfig is not None),
            ("配置字典", config is not None),
            ("SQLAlchemy配置", hasattr(Config, 'SQLALCHEMY_DATABASE_URI')),
            ("日志配置", hasattr(Config, 'LOG_DIR')),
            ("数据库路径配置", hasattr(Config, 'DATABASE_FILE')),
        ]
        
        all_pass = True
        for name, result in checks:
            status = "✓" if result else "✗"
            print(f"{status} {name}")
            if not result:
                all_pass = False
        
        return all_pass
    except Exception as e:
        print(f"✗ 配置导入失败: {e}")
        return False


def verify_app_factory():
    """验证Flask应用工厂函数"""
    print("\n" + "=" * 60)
    print("验证Flask应用工厂函数")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    init_file = base_dir / 'app' / '__init__.py'
    
    if not init_file.is_file():
        print("✗ app/__init__.py不存在")
        return False
    
    content = init_file.read_text(encoding='utf-8')
    
    checks = [
        ("create_app函数", "def create_app" in content),
        ("SQLAlchemy初始化", "SQLAlchemy" in content and "db = SQLAlchemy()" in content),
        ("日志配置函数", "_setup_logging" in content),
        ("错误处理器", "_register_error_handlers" in content),
        ("数据库初始化", "db.create_all()" in content),
        ("目录创建", "_ensure_directories" in content),
    ]
    
    all_pass = True
    for name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
        if not result:
            all_pass = False
    
    return all_pass


def verify_logging_setup():
    """验证日志系统配置"""
    print("\n" + "=" * 60)
    print("验证日志系统配置")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    init_file = base_dir / 'app' / '__init__.py'
    content = init_file.read_text(encoding='utf-8')
    
    checks = [
        ("RotatingFileHandler", "RotatingFileHandler" in content),
        ("日志格式化", "setFormatter" in content),
        ("应用日志", "LOG_FILE" in content),
        ("错误日志", "ERROR_LOG_FILE" in content),
        ("日志级别设置", "setLevel" in content),
    ]
    
    all_pass = True
    for name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
        if not result:
            all_pass = False
    
    return all_pass


def verify_requirements():
    """验证依赖文件"""
    print("\n" + "=" * 60)
    print("验证依赖文件")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    req_file = base_dir / 'requirements.txt'
    content = req_file.read_text(encoding='utf-8')
    
    required_packages = [
        'Flask',
        'Flask-SQLAlchemy',
        'SQLAlchemy',
        'WTForms',
        'openpyxl',
        'waitress',
        'pytest',
        'pytest-flask',
        'pytest-cov',
        'hypothesis'
    ]
    
    all_present = True
    for package in required_packages:
        present = package in content
        status = "✓" if present else "✗"
        print(f"{status} {package}")
        if not present:
            all_present = False
    
    return all_present


def main():
    """主验证函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "任务1: 设置项目结构和核心配置" + " " * 16 + "║")
    print("║" + " " * 20 + "验证报告" + " " * 26 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    results.append(("目录结构", verify_directory_structure()))
    results.append(("配置文件", verify_config_files()))
    results.append(("配置内容", verify_config_content()))
    results.append(("应用工厂函数", verify_app_factory()))
    results.append(("日志系统", verify_logging_setup()))
    results.append(("依赖文件", verify_requirements()))
    
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有验证通过！任务1完成。")
        print("\n任务1完成内容:")
        print("  • 创建了Flask应用目录结构")
        print("  • 配置了开发/生产/测试环境")
        print("  • 配置了SQLAlchemy和SQLite数据库")
        print("  • 设置了日志系统（文件轮转）")
        print("  • 创建了Flask应用工厂函数")
        print("  • 添加了全局错误处理器")
        print("\n下一步: 安装依赖并实现数据模型")
        print("  pip install -r requirements.txt")
        return 0
    else:
        print("✗ 部分验证失败，请检查上述错误。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
