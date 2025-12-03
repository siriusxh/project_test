"""
属性测试: 数据持久化往返一致性
Feature: server-order-management, Property 4: 数据持久化往返一致性
验证需求: 1.5, 2.5, 3.5, 6.3
"""
import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime

from app import create_app, db
from app.models import (
    SKU, PriceHistory,
    Requirement, Configuration, ConfigurationItem,
    EPSOrder, EPSOrderItem, BudgetAllocation
)


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


@st.composite
def requirement_data(draw):
    """生成需求数据"""
    return {
        'requirement_code': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'jira_case': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd')))),
        'description': draw(st.one_of(st.none(), st.text(max_size=500))),
        'status': draw(st.sampled_from(['draft', 'pending', 'approved', 'completed']))
    }


@st.composite
def configuration_data(draw, requirement_id):
    """生成配置数据"""
    return {
        'requirement_id': requirement_id,
        'config_name': draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        'total_price': draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('9999999.99'), places=2))
    }


@st.composite
def eps_order_data(draw, requirement_id):
    """生成EPS订单数据"""
    return {
        'order_code': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'requirement_id': requirement_id,
        'supplier': draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        'total_amount': draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('9999999.99'), places=2)),
        'status': draw(st.sampled_from(['pending', 'approved', 'completed', 'cancelled']))
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


# Feature: server-order-management, Property 4: 数据持久化往返一致性
@given(data=sku_data())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_sku_persistence_round_trip(app_context, data):
    """
    对于任何SKU实体，保存到数据库后重新查询应该返回等价的数据对象
    验证需求: 1.5
    """
    # 创建SKU
    sku = SKU(
        sku_code=data['sku_code'],
        name=data['name'],
        unit_price=data['unit_price'],
        supplier=data['supplier'],
        category=data['category']
    )
    
    db.session.add(sku)
    db.session.commit()
    sku_id = sku.id
    
    # 清除会话以确保从数据库重新加载
    db.session.expunge_all()
    
    # 重新查询
    retrieved_sku = db.session.get(SKU, sku_id)
    
    # 验证数据一致性
    assert retrieved_sku is not None
    assert retrieved_sku.sku_code == data['sku_code']
    assert retrieved_sku.name == data['name']
    assert retrieved_sku.unit_price == data['unit_price']
    assert retrieved_sku.supplier == data['supplier']
    assert retrieved_sku.category == data['category']
    
    # 清理
    db.session.delete(retrieved_sku)
    db.session.commit()


# Feature: server-order-management, Property 4: 数据持久化往返一致性
@given(data=requirement_data())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_requirement_persistence_round_trip(app_context, data):
    """
    对于任何需求实体，保存到数据库后重新查询应该返回等价的数据对象
    验证需求: 2.5
    """
    # 创建需求
    requirement = Requirement(
        requirement_code=data['requirement_code'],
        jira_case=data['jira_case'],
        description=data['description'],
        status=data['status']
    )
    
    db.session.add(requirement)
    db.session.commit()
    requirement_id = requirement.id
    
    # 清除会话
    db.session.expunge_all()
    
    # 重新查询
    retrieved_req = db.session.get(Requirement, requirement_id)
    
    # 验证数据一致性
    assert retrieved_req is not None
    assert retrieved_req.requirement_code == data['requirement_code']
    assert retrieved_req.jira_case == data['jira_case']
    assert retrieved_req.description == data['description']
    assert retrieved_req.status == data['status']
    
    # 清理
    db.session.delete(retrieved_req)
    db.session.commit()


# Feature: server-order-management, Property 4: 数据持久化往返一致性
@given(
    req_data=requirement_data(),
    config_name=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    total_price=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('9999999.99'), places=2)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_configuration_persistence_round_trip(app_context, req_data, config_name, total_price):
    """
    对于任何配置实体，保存到数据库后重新查询应该返回等价的数据对象
    验证需求: 2.5
    """
    try:
        # 先创建需求
        requirement = Requirement(
            requirement_code=req_data['requirement_code'],
            jira_case=req_data['jira_case'],
            description=req_data['description'],
            status=req_data['status']
        )
        db.session.add(requirement)
        db.session.commit()
        requirement_id = requirement.id
        
        # 创建配置
        configuration = Configuration(
            requirement_id=requirement_id,
            config_name=config_name,
            total_price=total_price
        )
        
        db.session.add(configuration)
        db.session.commit()
        config_id = configuration.id
        
        # 清除会话
        db.session.expunge_all()
        
        # 重新查询
        retrieved_config = db.session.get(Configuration, config_id)
        
        # 验证数据一致性
        assert retrieved_config is not None
        assert retrieved_config.requirement_id == requirement_id
        assert retrieved_config.config_name == config_name
        assert retrieved_config.total_price == total_price
        
        # 清理
        db.session.delete(retrieved_config)
        retrieved_req = db.session.get(Requirement, requirement_id)
        db.session.delete(retrieved_req)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


# Feature: server-order-management, Property 4: 数据持久化往返一致性
@given(
    req_data=requirement_data(),
    order_code=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    supplier=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    total_amount=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('9999999.99'), places=2),
    status=st.sampled_from(['pending', 'approved', 'completed', 'cancelled'])
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_eps_order_persistence_round_trip(app_context, req_data, order_code, supplier, total_amount, status):
    """
    对于任何EPS订单实体，保存到数据库后重新查询应该返回等价的数据对象
    验证需求: 3.5, 6.3
    """
    try:
        # 先创建需求
        requirement = Requirement(
            requirement_code=req_data['requirement_code'],
            jira_case=req_data['jira_case'],
            description=req_data['description'],
            status=req_data['status']
        )
        db.session.add(requirement)
        db.session.commit()
        requirement_id = requirement.id
        
        # 创建EPS订单
        order = EPSOrder(
            order_code=order_code,
            requirement_id=requirement_id,
            supplier=supplier,
            total_amount=total_amount,
            status=status
        )
        
        db.session.add(order)
        db.session.commit()
        order_id = order.id
        
        # 清除会话
        db.session.expunge_all()
        
        # 重新查询
        retrieved_order = db.session.get(EPSOrder, order_id)
        
        # 验证数据一致性
        assert retrieved_order is not None
        assert retrieved_order.order_code == order_code
        assert retrieved_order.requirement_id == requirement_id
        assert retrieved_order.supplier == supplier
        assert retrieved_order.total_amount == total_amount
        assert retrieved_order.status == status
        
        # 清理
        db.session.delete(retrieved_order)
        retrieved_req = db.session.get(Requirement, requirement_id)
        db.session.delete(retrieved_req)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
