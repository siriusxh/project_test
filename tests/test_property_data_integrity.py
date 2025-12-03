"""
数据完整性相关属性测试
"""
import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models.sku import SKU
from app.models.requirement import Requirement, Configuration, ConfigurationItem
from app.models.order import EPSOrder, EPSOrderItem, BudgetAllocation
from app.services.data_integrity_service import DataIntegrityService
from app.exceptions import (
    ValidationError, 
    ReferentialIntegrityError, 
    ForeignKeyError,
    BusinessLogicError
)


# 自定义策略生成器
@st.composite
def requirement_data(draw):
    """生成需求数据"""
    return {
        'requirement_code': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'jira_case': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'description': draw(st.one_of(st.none(), st.text(max_size=500))),
        'status': draw(st.sampled_from(['draft', 'approved', 'completed']))
    }


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
def order_data(draw, requirement_id, supplier):
    """生成订单数据"""
    return {
        'order_code': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'requirement_id': requirement_id,
        'supplier': supplier,
        'total_amount': draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('999999.99'), places=2)),
        'status': draw(st.sampled_from(['pending', 'approved', 'completed']))
    }


@st.composite
def budget_code_generator(draw):
    """生成有效的预算Code"""
    # 以字母或数字开头
    first_char = draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'))
    # 后续字符可以包含字母、数字、连字符和下划线
    rest_length = draw(st.integers(min_value=2, max_value=49))
    rest_chars = draw(st.text(
        min_size=rest_length, 
        max_size=rest_length,
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    ))
    return first_char + rest_chars


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


# Feature: server-order-management, Property 21: 引用完整性约束
@given(
    req_data=requirement_data(),
    has_order=st.booleans()
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_referential_integrity_constraint(app_context, req_data, has_order):
    """
    对于任何有关联EPS订单的需求，删除操作应该被阻止，或者级联删除所有关联的订单及其子记录
    验证需求: 8.1
    """
    try:
        # 创建需求
        requirement = Requirement(**req_data)
        db.session.add(requirement)
        db.session.commit()
        
        if has_order:
            # 创建关联的订单
            order = EPSOrder(
                order_code=f"ORD_{requirement.id}",
                requirement_id=requirement.id,
                supplier="TestSupplier",
                total_amount=Decimal('1000.00'),
                status='pending'
            )
            db.session.add(order)
            db.session.commit()
            
            # 尝试检查依赖关系应该抛出异常
            with pytest.raises(ReferentialIntegrityError) as exc_info:
                DataIntegrityService.check_requirement_dependencies(requirement.id)
            
            # 验证异常信息
            assert exc_info.value.entity_type == 'requirement'
            assert exc_info.value.entity_id == requirement.id
            assert exc_info.value.dependent_count == 1
            
            # 测试级联删除
            stats = DataIntegrityService.cascade_delete_requirement(requirement.id)
            assert stats['orders'] == 1
            
            # 验证需求和订单都被删除
            assert Requirement.query.get(requirement.id) is None
            assert EPSOrder.query.get(order.id) is None
        else:
            # 没有关联订单，检查依赖关系应该不抛出异常
            try:
                DataIntegrityService.check_requirement_dependencies(requirement.id)
            except ReferentialIntegrityError:
                pytest.fail("没有关联订单时不应该抛出引用完整性错误")
            
            # 直接删除需求
            db.session.delete(requirement)
            db.session.commit()
            
            # 验证需求被删除
            assert Requirement.query.get(requirement.id) is None
        
    except Exception as e:
        db.session.rollback()
        # 如果是预期的异常，重新抛出
        if isinstance(e, (ReferentialIntegrityError, AssertionError)):
            raise
        # 其他异常也重新抛出以便调试
        raise


# Feature: server-order-management, Property 22: 外键存在性验证
@given(
    valid_requirement=st.booleans(),
    valid_sku=st.booleans()
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_foreign_key_existence_validation(app_context, valid_requirement, valid_sku):
    """
    对于任何创建包含外键的实体（如EPS订单引用需求ID），被引用的实体必须在数据库中存在，否则创建应该失败
    验证需求: 8.3
    """
    try:
        requirement_id = None
        sku_id = None
        
        # 如果需要有效的需求，创建一个
        if valid_requirement:
            requirement = Requirement(
                requirement_code="REQ001",
                jira_case="JIRA-001",
                description="Test requirement"
            )
            db.session.add(requirement)
            db.session.commit()
            requirement_id = requirement.id
        else:
            # 使用一个不存在的ID
            requirement_id = 99999
        
        # 如果需要有效的SKU，创建一个
        if valid_sku:
            sku = SKU(
                sku_code="SKU001",
                name="Test SKU",
                unit_price=Decimal('100.00'),
                supplier="TestSupplier"
            )
            db.session.add(sku)
            db.session.commit()
            sku_id = sku.id
        else:
            # 使用一个不存在的ID
            sku_id = 99999
        
        # 测试订单外键验证
        order_data = {
            'order_code': 'ORD001',
            'requirement_id': requirement_id,
            'supplier': 'TestSupplier',
            'total_amount': Decimal('1000.00')
        }
        
        if valid_requirement:
            # 有效的需求ID，验证应该通过
            assert DataIntegrityService.validate_foreign_keys('order', order_data) is True
        else:
            # 无效的需求ID，验证应该失败
            with pytest.raises(ForeignKeyError) as exc_info:
                DataIntegrityService.validate_foreign_keys('order', order_data)
            assert exc_info.value.foreign_key_field == 'requirement_id'
            assert exc_info.value.foreign_key_value == requirement_id
        
        # 测试配置项外键验证（需要配置ID和SKU ID）
        if valid_requirement and valid_sku:
            # 创建配置
            config = Configuration(
                requirement_id=requirement_id,
                config_name="Test Config",
                total_price=Decimal('1000.00')
            )
            db.session.add(config)
            db.session.commit()
            
            config_item_data = {
                'configuration_id': config.id,
                'sku_id': sku_id,
                'quantity': 1,
                'unit_price': Decimal('100.00'),
                'subtotal': Decimal('100.00')
            }
            
            # 验证应该通过
            assert DataIntegrityService.validate_foreign_keys('configuration_item', config_item_data) is True
            
            # 清理
            db.session.delete(config)
            db.session.commit()
        
        # 清理
        if valid_requirement:
            db.session.delete(requirement)
        if valid_sku:
            db.session.delete(sku)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        if isinstance(e, (ForeignKeyError, AssertionError)):
            raise
        raise


# Feature: server-order-management, Property 23: 关联数据查询一致性
@given(
    req_data=requirement_data(),
    num_configs=st.integers(min_value=0, max_value=3),
    num_orders=st.integers(min_value=0, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_association_query_consistency(app_context, req_data, num_configs, num_orders):
    """
    对于任何跨表关联查询，返回的所有关联记录都应该在数据库中存在且外键关系正确
    验证需求: 8.5
    """
    try:
        # 创建需求
        requirement = Requirement(**req_data)
        db.session.add(requirement)
        db.session.commit()
        
        # 创建SKU用于配置项
        sku = SKU(
            sku_code="SKU001",
            name="Test SKU",
            unit_price=Decimal('100.00'),
            supplier="TestSupplier"
        )
        db.session.add(sku)
        db.session.commit()
        
        # 创建配置
        configs = []
        for i in range(num_configs):
            config = Configuration(
                requirement_id=requirement.id,
                config_name=f"Config{i}",
                total_price=Decimal('100.00')
            )
            db.session.add(config)
            db.session.commit()
            
            # 为每个配置添加配置项
            config_item = ConfigurationItem(
                configuration_id=config.id,
                sku_id=sku.id,
                quantity=1,
                unit_price=Decimal('100.00'),
                subtotal=Decimal('100.00')
            )
            db.session.add(config_item)
            configs.append(config)
        
        # 创建订单
        orders = []
        for i in range(num_orders):
            order = EPSOrder(
                order_code=f"ORD{i}_{requirement.id}",
                requirement_id=requirement.id,
                supplier="TestSupplier",
                total_amount=Decimal('1000.00'),
                status='pending'
            )
            db.session.add(order)
            db.session.commit()
            
            # 为每个订单添加订单项
            order_item = EPSOrderItem(
                order_id=order.id,
                sku_id=sku.id,
                quantity=1,
                unit_price=Decimal('100.00'),
                subtotal=Decimal('100.00')
            )
            db.session.add(order_item)
            orders.append(order)
        
        db.session.commit()
        
        # 验证需求的关联数据一致性
        result = DataIntegrityService.verify_association_consistency('requirement', requirement.id)
        
        # 验证返回的数据
        assert result['requirement']['id'] == requirement.id
        assert len(result['configurations']) == num_configs
        assert len(result['orders']) == num_orders
        
        # 验证每个配置的外键
        for config_dict in result['configurations']:
            assert config_dict['requirement_id'] == requirement.id
        
        # 验证每个订单的外键
        for order_dict in result['orders']:
            assert order_dict['requirement_id'] == requirement.id
        
        # 如果有订单，验证订单的关联数据一致性
        if num_orders > 0:
            order = orders[0]
            order_result = DataIntegrityService.verify_association_consistency('order', order.id)
            
            assert order_result['order']['id'] == order.id
            assert order_result['requirement']['id'] == requirement.id
            assert len(order_result['order_items']) >= 1
        
        # 清理
        for order in orders:
            EPSOrderItem.query.filter_by(order_id=order.id).delete()
            db.session.delete(order)
        for config in configs:
            ConfigurationItem.query.filter_by(configuration_id=config.id).delete()
            db.session.delete(config)
        db.session.delete(sku)
        db.session.delete(requirement)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        if isinstance(e, (BusinessLogicError, ValidationError, AssertionError)):
            raise
        raise


# Feature: server-order-management, Property 19: 表单输入验证
@given(
    form_type=st.sampled_from(['sku', 'requirement', 'order', 'budget', 'configuration']),
    validation_scenario=st.sampled_from([
        'valid',
        'empty_required_field',
        'exceeds_max_length',
        'invalid_format',
        'out_of_range'
    ])
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_form_input_validation(app_context, form_type, validation_scenario):
    """
    对于任何无效的表单输入（空值、格式错误、超出范围），系统应该拒绝提交并返回明确的错误信息
    验证需求: 7.3, 8.4
    """
    try:
        if form_type == 'sku':
            if validation_scenario == 'valid':
                data = {
                    'sku_code': 'SKU001',
                    'name': 'Test SKU',
                    'unit_price': Decimal('100.00'),
                    'supplier': 'TestSupplier'
                }
                # 验证应该通过
                DataIntegrityService.validate_form_input('sku', data)
            
            elif validation_scenario == 'empty_required_field':
                # 测试空SKU编码
                data = {
                    'sku_code': '',
                    'name': 'Test SKU',
                    'unit_price': Decimal('100.00'),
                    'supplier': 'TestSupplier'
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('sku', data)
                assert 'SKU编码不能为空' in str(exc_info.value)
            
            elif validation_scenario == 'exceeds_max_length':
                # 测试超长SKU编码
                data = {
                    'sku_code': 'A' * 51,  # 超过50字符
                    'name': 'Test SKU',
                    'unit_price': Decimal('100.00'),
                    'supplier': 'TestSupplier'
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('sku', data)
                assert '长度' in str(exc_info.value) or '超过' in str(exc_info.value)
            
            elif validation_scenario == 'invalid_format':
                # 测试无效的单价格式
                data = {
                    'sku_code': 'SKU001',
                    'name': 'Test SKU',
                    'unit_price': 'invalid_price',
                    'supplier': 'TestSupplier'
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('sku', data)
                assert '格式' in str(exc_info.value) or '无效' in str(exc_info.value)
            
            elif validation_scenario == 'out_of_range':
                # 测试超出范围的单价
                data = {
                    'sku_code': 'SKU001',
                    'name': 'Test SKU',
                    'unit_price': Decimal('-10.00'),  # 负数
                    'supplier': 'TestSupplier'
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('sku', data)
                assert '大于' in str(exc_info.value) or '必须' in str(exc_info.value)
        
        elif form_type == 'requirement':
            if validation_scenario == 'valid':
                data = {
                    'requirement_code': 'REQ001',
                    'jira_case': 'JIRA-001'
                }
                DataIntegrityService.validate_form_input('requirement', data)
            
            elif validation_scenario == 'empty_required_field':
                # 测试空需求编码
                data = {
                    'requirement_code': '',
                    'jira_case': 'JIRA-001'
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('requirement', data)
                assert '需求编码不能为空' in str(exc_info.value)
            
            elif validation_scenario == 'exceeds_max_length':
                # 测试超长需求编码
                data = {
                    'requirement_code': 'R' * 51,
                    'jira_case': 'JIRA-001'
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('requirement', data)
                assert '长度' in str(exc_info.value)
            
            # 其他场景对requirement不适用，跳过
        
        elif form_type == 'order':
            if validation_scenario == 'valid':
                data = {
                    'order_code': 'ORD001',
                    'requirement_id': 1,
                    'supplier': 'TestSupplier'
                }
                DataIntegrityService.validate_form_input('order', data)
            
            elif validation_scenario == 'empty_required_field':
                # 测试空订单编码
                data = {
                    'order_code': '',
                    'requirement_id': 1,
                    'supplier': 'TestSupplier'
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('order', data)
                assert '订单编码不能为空' in str(exc_info.value)
            
            elif validation_scenario == 'exceeds_max_length':
                # 测试超长订单编码
                data = {
                    'order_code': 'O' * 51,
                    'requirement_id': 1,
                    'supplier': 'TestSupplier'
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('order', data)
                assert '长度' in str(exc_info.value)
        
        elif form_type == 'budget':
            if validation_scenario == 'valid':
                data = {
                    'budget_code': 'BUD001',
                    'allocation_percentage': Decimal('50.00')
                }
                DataIntegrityService.validate_form_input('budget', data)
            
            elif validation_scenario == 'empty_required_field':
                # 测试空预算Code
                data = {
                    'budget_code': '',
                    'allocation_percentage': Decimal('50.00')
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('budget', data)
                assert '预算Code不能为空' in str(exc_info.value)
            
            elif validation_scenario == 'invalid_format':
                # 测试无效的预算Code格式（以特殊字符开头）
                data = {
                    'budget_code': '-BUD001',
                    'allocation_percentage': Decimal('50.00')
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('budget', data)
                assert '格式' in str(exc_info.value) or '无效' in str(exc_info.value)
            
            elif validation_scenario == 'out_of_range':
                # 测试超出范围的分配比例
                data = {
                    'budget_code': 'BUD001',
                    'allocation_percentage': Decimal('150.00')  # 超过100
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('budget', data)
                assert '0-100' in str(exc_info.value) or '之间' in str(exc_info.value)
        
        elif form_type == 'configuration':
            if validation_scenario == 'valid':
                data = {
                    'config_name': 'Config1',
                    'requirement_id': 1
                }
                DataIntegrityService.validate_form_input('configuration', data)
            
            elif validation_scenario == 'empty_required_field':
                # 测试空配置名称
                data = {
                    'config_name': '',
                    'requirement_id': 1
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('configuration', data)
                assert '配置名称不能为空' in str(exc_info.value)
            
            elif validation_scenario == 'exceeds_max_length':
                # 测试超长配置名称
                data = {
                    'config_name': 'C' * 101,
                    'requirement_id': 1
                }
                with pytest.raises(ValidationError) as exc_info:
                    DataIntegrityService.validate_form_input('configuration', data)
                assert '长度' in str(exc_info.value)
        
    except Exception as e:
        db.session.rollback()
        if isinstance(e, (ValidationError, AssertionError)):
            raise
        raise
