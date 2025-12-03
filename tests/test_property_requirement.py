"""
需求管理属性测试
Feature: server-order-management
"""
import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from app import create_app, db
from app.models.requirement import Requirement, Configuration, ConfigurationItem
from app.models.sku import SKU
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.configuration_repository import ConfigurationRepository
from app.services.price_calculation_service import PriceCalculationService


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


# Feature: server-order-management, Property 5: 需求ID唯一性
@given(
    requirement_code1=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
    requirement_code2=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
    jira_case=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_requirement_code_uniqueness(app_context, requirement_code1, requirement_code2, jira_case):
    """
    对于任何两个不同的需求记录，它们的需求编码必须不相同
    验证需求: 2.1
    """
    try:
        # 清理数据库
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 创建第一个需求
        requirement_data1 = {
            'requirement_code': requirement_code1,
            'jira_case': jira_case,
            'description': 'Test requirement 1'
        }
        
        requirement1 = RequirementRepository.create(requirement_data1)
        assert requirement1 is not None
        assert requirement1.requirement_code == requirement_code1
        
        # 尝试创建第二个需求
        requirement_data2 = {
            'requirement_code': requirement_code2,
            'jira_case': jira_case,
            'description': 'Test requirement 2'
        }
        
        if requirement_code1 == requirement_code2:
            # 如果编码相同，应该抛出异常
            with pytest.raises(ValueError, match="已存在"):
                RequirementRepository.create(requirement_data2)
        else:
            # 如果编码不同，应该成功创建
            requirement2 = RequirementRepository.create(requirement_data2)
            assert requirement2 is not None
            assert requirement2.requirement_code == requirement_code2
            assert requirement1.id != requirement2.id
            
            # 清理第二个需求
            db.session.delete(requirement2)
            db.session.commit()
        
        # 清理第一个需求
        db.session.delete(requirement1)
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        raise


# Feature: server-order-management, Property 6: 配置项小计计算正确性
@given(
    unit_price=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('999999.99'), places=2),
    quantity=st.integers(min_value=1, max_value=10000)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_configuration_item_subtotal_calculation(app, unit_price, quantity):
    """
    对于任何配置项，其小计金额应该等于SKU单价乘以数量
    验证需求: 2.3
    """
    with app.app_context():
        # 清理数据库
        db.session.query(ConfigurationItem).delete()
        db.session.query(Configuration).delete()
        db.session.query(Requirement).delete()
        db.session.query(SKU).delete()
        db.session.commit()
        
        # 创建测试SKU
        sku = SKU(
            sku_code=f'TEST-SKU-{quantity}',
            name='Test SKU',
            unit_price=unit_price,
            supplier='Test Supplier'
        )
        db.session.add(sku)
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code=f'TEST-REQ-{quantity}',
            jira_case='TEST-JIRA',
            description='Test requirement'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建测试配置
        configuration = Configuration(
            requirement_id=requirement.id,
            config_name='Test Config',
            total_price=Decimal('0')
        )
        db.session.add(configuration)
        db.session.commit()
        
        # 创建配置项
        item = ConfigurationItem(
            configuration_id=configuration.id,
            sku_id=sku.id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=unit_price * quantity
        )
        db.session.add(item)
        db.session.commit()
        
        # 验证小计计算
        expected_subtotal = unit_price * quantity
        assert item.subtotal == expected_subtotal
        
        # 使用服务计算小计
        calculated_subtotal = PriceCalculationService.calculate_item_subtotal(unit_price, quantity)
        assert calculated_subtotal == expected_subtotal


# Feature: server-order-management, Property 7: 配置总价计算正确性
@given(
    items=st.lists(
        st.tuples(
            st.decimals(min_value=Decimal('0.01'), max_value=Decimal('9999.99'), places=2),  # unit_price
            st.integers(min_value=1, max_value=100)  # quantity
        ),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_configuration_total_price_calculation(app, items):
    """
    对于任何配置方案，其总价应该等于所有配置项小计金额之和
    验证需求: 2.4
    """
    with app.app_context():
        # 清理数据库
        db.session.query(ConfigurationItem).delete()
        db.session.query(Configuration).delete()
        db.session.query(Requirement).delete()
        db.session.query(SKU).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='TEST-REQ-TOTAL',
            jira_case='TEST-JIRA',
            description='Test requirement'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建测试SKU和配置项数据
        items_data = []
        expected_total = Decimal('0')
        
        for idx, (unit_price, quantity) in enumerate(items):
            # 创建SKU
            sku = SKU(
                sku_code=f'TEST-SKU-{idx}',
                name=f'Test SKU {idx}',
                unit_price=unit_price,
                supplier='Test Supplier'
            )
            db.session.add(sku)
            db.session.flush()
            
            subtotal = unit_price * quantity
            expected_total += subtotal
            
            items_data.append({
                'sku_id': sku.id,
                'quantity': quantity,
                'unit_price': unit_price
            })
        
        db.session.commit()
        
        # 使用ConfigurationRepository创建配置及配置项
        configuration_data = {
            'requirement_id': requirement.id,
            'config_name': 'Test Configuration'
        }
        
        configuration = ConfigurationRepository.create_with_items(configuration_data, items_data)
        
        # 验证配置总价
        assert configuration.total_price == expected_total
        
        # 验证每个配置项的小计
        for item in configuration.items:
            expected_item_subtotal = item.unit_price * item.quantity
            assert item.subtotal == expected_item_subtotal
        
        # 使用服务重新计算总价
        recalculated_total = PriceCalculationService.recalculate_configuration_total(configuration)
        assert recalculated_total == expected_total
