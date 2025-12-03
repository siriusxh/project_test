"""
SKU管理集成测试
"""
import pytest
from decimal import Decimal

from app import create_app, db
from app.repositories import SKURepository


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_context(app):
    """提供应用上下文"""
    with app.app_context():
        yield


def test_sku_crud_operations(app_context):
    """测试SKU的CRUD操作"""
    # 创建SKU
    sku_data = {
        'sku_code': 'TEST001',
        'name': '测试服务器',
        'unit_price': Decimal('10000.00'),
        'supplier': 'Dell',
        'category': '服务器'
    }
    
    sku = SKURepository.create(sku_data)
    assert sku.id is not None
    assert sku.sku_code == 'TEST001'
    
    # 查询SKU
    found_sku = SKURepository.find_by_code('TEST001')
    assert found_sku is not None
    assert found_sku.name == '测试服务器'
    
    # 更新SKU价格
    update_data = {'unit_price': Decimal('12000.00')}
    updated_sku = SKURepository.update(sku.id, update_data, changed_by='admin')
    assert updated_sku.unit_price == Decimal('12000.00')
    
    # 验证价格历史
    price_history = SKURepository.get_price_history(sku.id)
    assert len(price_history) == 1
    assert price_history[0].old_price == Decimal('10000.00')
    assert price_history[0].new_price == Decimal('12000.00')
    
    # 搜索SKU
    search_results = SKURepository.search(keyword='测试')
    assert len(search_results) >= 1
    assert any(s.sku_code == 'TEST001' for s in search_results)
    
    # 删除SKU
    assert SKURepository.delete(sku.id) is True
    assert SKURepository.find_by_code('TEST001') is None


def test_sku_duplicate_code_rejection(app_context):
    """测试重复SKU编码被拒绝"""
    sku_data = {
        'sku_code': 'DUP001',
        'name': 'SKU1',
        'unit_price': Decimal('1000.00'),
        'supplier': 'Supplier1'
    }
    
    # 创建第一个SKU
    sku1 = SKURepository.create(sku_data)
    
    # 尝试创建重复编码的SKU
    with pytest.raises(ValueError, match="已存在"):
        SKURepository.create(sku_data)
    
    # 清理
    SKURepository.delete(sku1.id)


def test_sku_search_by_supplier(app_context):
    """测试按供应商搜索"""
    # 创建多个SKU
    sku1_data = {
        'sku_code': 'DELL001',
        'name': 'Dell服务器',
        'unit_price': Decimal('10000.00'),
        'supplier': 'Dell'
    }
    sku2_data = {
        'sku_code': 'HP001',
        'name': 'HP服务器',
        'unit_price': Decimal('9000.00'),
        'supplier': 'HP'
    }
    
    sku1 = SKURepository.create(sku1_data)
    sku2 = SKURepository.create(sku2_data)
    
    # 按供应商搜索
    dell_skus = SKURepository.search(supplier='Dell')
    assert len(dell_skus) >= 1
    assert all('Dell' in s.supplier for s in dell_skus)
    
    # 清理
    SKURepository.delete(sku1.id)
    SKURepository.delete(sku2.id)
