"""
SKU相关属性测试
"""
import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models.sku import SKU, PriceHistory
from app.repositories import SKURepository


# 自定义策略生成器
@st.composite
def sku_data(draw):
    """生成SKU数据"""
    return {
        'sku_code': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'name': draw(st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        'unit_price': draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('999999.99'), places=2)),
        'supplier': draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        'category': draw(st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))))
    }


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


# Feature: server-order-management, Property 1: SKU编码唯一性
@given(data1=sku_data(), data2=sku_data())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_sku_code_uniqueness(app_context, data1, data2):
    """
    对于任何两个不同的SKU记录，它们的SKU编码必须不相同，尝试添加重复编码的SKU应该被系统拒绝
    验证需求: 1.2
    """
    try:
        # 创建第一个SKU
        sku1 = SKURepository.create(data1)
        
        # 如果两个SKU编码相同，尝试创建第二个应该失败
        if data2['sku_code'] == data1['sku_code']:
            with pytest.raises(ValueError, match="已存在"):
                SKURepository.create(data2)
        else:
            # 如果编码不同，应该能成功创建
            sku2 = SKURepository.create(data2)
            
            # 验证两个SKU的编码确实不同
            assert sku1.sku_code != sku2.sku_code
            
            # 清理第二个SKU
            db.session.delete(sku2)
            db.session.commit()
        
        # 清理第一个SKU
        db.session.delete(sku1)
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        raise


# Feature: server-order-management, Property 2: 价格变更历史完整性
@given(
    initial_data=sku_data(),
    new_price=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('999999.99'), places=2),
    changed_by=st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_price_change_history_completeness(app_context, initial_data, new_price, changed_by):
    """
    对于任何SKU的价格修改操作，价格历史表中应该存在一条记录，包含旧价格、新价格和变更时间
    验证需求: 1.3, 8.2
    """
    try:
        # 创建SKU
        sku = SKURepository.create(initial_data)
        old_price = sku.unit_price
        
        # 如果新价格与旧价格不同，更新价格
        if new_price != old_price:
            # 更新价格
            update_data = {'unit_price': new_price}
            SKURepository.update(sku.id, update_data, changed_by=changed_by)
            
            # 查询价格历史
            price_history = SKURepository.get_price_history(sku.id)
            
            # 验证价格历史存在
            assert len(price_history) > 0, "价格变更后应该有历史记录"
            
            # 验证最新的价格历史记录
            latest_history = price_history[0]
            assert latest_history.old_price == old_price, "历史记录应包含旧价格"
            assert latest_history.new_price == new_price, "历史记录应包含新价格"
            assert latest_history.changed_at is not None, "历史记录应包含变更时间"
            assert latest_history.changed_by == changed_by, "历史记录应包含修改人"
        
        # 清理
        db.session.delete(sku)
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        raise


# Feature: server-order-management, Property 3: SKU搜索结果匹配性
@given(
    skus_data=st.lists(sku_data(), min_size=1, max_size=10),
    search_keyword=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_sku_search_result_matching(app_context, skus_data, search_keyword):
    """
    对于任何搜索条件（编码、名称或供应商），返回的所有SKU记录都应该在相应字段中包含该搜索关键字
    验证需求: 1.4
    """
    try:
        # 创建多个SKU，确保编码唯一
        created_skus = []
        for i, data in enumerate(skus_data):
            # 确保每个SKU编码唯一
            data['sku_code'] = f"{data['sku_code']}_{i}"
            try:
                sku = SKURepository.create(data)
                created_skus.append(sku)
            except ValueError:
                # 如果仍然有重复，跳过
                continue
        
        # 如果没有成功创建任何SKU，跳过测试
        assume(len(created_skus) > 0)
        
        # 执行搜索
        search_results = SKURepository.search(keyword=search_keyword)
        
        # 验证所有搜索结果都包含关键字（在编码或名称中）
        for result in search_results:
            keyword_lower = search_keyword.lower()
            sku_code_lower = result.sku_code.lower()
            name_lower = result.name.lower()
            
            assert (keyword_lower in sku_code_lower or keyword_lower in name_lower), \
                f"搜索结果 {result.sku_code} 应该在编码或名称中包含关键字 {search_keyword}"
        
        # 清理
        for sku in created_skus:
            db.session.delete(sku)
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        raise
