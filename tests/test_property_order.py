"""
订单管理属性测试
Feature: server-order-management
"""
import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from app import create_app, db
from app.models.order import EPSOrder, EPSOrderItem, BudgetAllocation
from app.models.requirement import Requirement, Configuration, ConfigurationItem
from app.models.sku import SKU
from app.repositories.order_repository import OrderRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.configuration_repository import ConfigurationRepository
from app.services.order_service import OrderService


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


# Feature: server-order-management, Property 8: 订单拆分完整性
@given(
    num_suppliers=st.integers(min_value=1, max_value=5),
    items_per_supplier=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_order_split_completeness(app, num_suppliers, items_per_supplier):
    """
    对于任何需求和供应商选择，拆分生成的所有EPS订单应该包含该需求的所有配置项，
    且每个配置项只出现在一个订单中
    验证需求: 3.1
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(ConfigurationItem).delete()
        db.session.query(Configuration).delete()
        db.session.query(Requirement).delete()
        db.session.query(SKU).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code=f'TEST-REQ-SPLIT',
            jira_case='TEST-JIRA',
            description='Test requirement for order splitting'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建多个供应商的SKU
        suppliers = [f'Supplier-{i}' for i in range(num_suppliers)]
        all_skus = []
        
        for supplier_idx, supplier in enumerate(suppliers):
            for item_idx in range(items_per_supplier):
                sku = SKU(
                    sku_code=f'SKU-{supplier_idx}-{item_idx}',
                    name=f'Test SKU {supplier_idx}-{item_idx}',
                    unit_price=Decimal('100.00'),
                    supplier=supplier
                )
                db.session.add(sku)
                all_skus.append(sku)
        
        db.session.commit()
        
        # 创建配置和配置项
        configuration = Configuration(
            requirement_id=requirement.id,
            config_name='Test Configuration',
            total_price=Decimal('0')
        )
        db.session.add(configuration)
        db.session.commit()
        
        all_config_items = []
        total_price = Decimal('0')
        
        for sku in all_skus:
            quantity = 2
            unit_price = sku.unit_price
            subtotal = unit_price * quantity
            
            item = ConfigurationItem(
                configuration_id=configuration.id,
                sku_id=sku.id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal
            )
            db.session.add(item)
            all_config_items.append(item)
            total_price += subtotal
        
        configuration.total_price = total_price
        db.session.commit()
        
        # 拆分订单
        orders = OrderService.split_requirement_to_orders(requirement.id)
        
        # 验证：订单数量应该等于供应商数量
        assert len(orders) == num_suppliers, f"Expected {num_suppliers} orders, got {len(orders)}"
        
        # 收集所有订单项
        all_order_items = []
        for order in orders:
            items = OrderRepository.get_items(order.id)
            all_order_items.extend(items)
        
        # 验证：订单项总数应该等于配置项总数
        assert len(all_order_items) == len(all_config_items), \
            f"Expected {len(all_config_items)} order items, got {len(all_order_items)}"
        
        # 验证：每个配置项都应该出现在某个订单中
        config_item_skus = {item.sku_id for item in all_config_items}
        order_item_skus = {item.sku_id for item in all_order_items}
        assert config_item_skus == order_item_skus, "Not all configuration items are in orders"
        
        # 验证：每个SKU只出现在一个订单中（按供应商分组）
        sku_to_order = {}
        for order in orders:
            items = OrderRepository.get_items(order.id)
            for item in items:
                assert item.sku_id not in sku_to_order, f"SKU {item.sku_id} appears in multiple orders"
                sku_to_order[item.sku_id] = order.id
        
        # 验证：每个订单的供应商应该与其订单项的SKU供应商一致
        for order in orders:
            items = OrderRepository.get_items(order.id)
            for item in items:
                assert item.sku.supplier == order.supplier, \
                    f"Order supplier {order.supplier} doesn't match SKU supplier {item.sku.supplier}"


# Feature: server-order-management, Property 9: EPS订单编号唯一性
@given(
    order_code1=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
    order_code2=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_order_code_uniqueness(app, order_code1, order_code2):
    """
    对于任何两个不同的EPS订单，它们的订单编号必须不相同
    验证需求: 3.2
    """
    with app.app_context():
        try:
            # 清理数据库
            db.session.query(BudgetAllocation).delete()
            db.session.query(EPSOrderItem).delete()
            db.session.query(EPSOrder).delete()
            db.session.query(ConfigurationItem).delete()
            db.session.query(Configuration).delete()
            db.session.query(Requirement).delete()
            db.session.commit()
            
            # 创建测试需求
            requirement = Requirement(
                requirement_code='TEST-REQ-UNIQUE',
                jira_case='TEST-JIRA',
                description='Test requirement'
            )
            db.session.add(requirement)
            db.session.commit()
            
            requirement_id = requirement.id
            
            # 创建第一个订单
            order_data1 = {
                'order_code': order_code1,
                'requirement_id': requirement_id,
                'supplier': 'Test Supplier',
                'total_amount': Decimal('1000.00')
            }
            
            order1 = OrderRepository.create(order_data1)
            assert order1 is not None
            assert order1.order_code == order_code1
            
            # 尝试创建第二个订单
            order_data2 = {
                'order_code': order_code2,
                'requirement_id': requirement_id,
                'supplier': 'Test Supplier',
                'total_amount': Decimal('2000.00')
            }
            
            if order_code1 == order_code2:
                # 如果订单编号相同，应该抛出异常
                with pytest.raises(ValueError, match="已存在"):
                    OrderRepository.create(order_data2)
            else:
                # 如果订单编号不同，应该成功创建
                order2 = OrderRepository.create(order_data2)
                assert order2 is not None
                assert order2.order_code == order_code2
                assert order1.id != order2.id
                
                # 清理第二个订单
                db.session.delete(order2)
                db.session.commit()
            
            # 清理第一个订单
            db.session.delete(order1)
            db.session.commit()
            
        except Exception:
            db.session.rollback()
            raise


# Feature: server-order-management, Property 10: 预算分配比例总和验证
@given(
    allocations=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),  # budget_code
            st.decimals(min_value=Decimal('0.01'), max_value=Decimal('100'), places=2)  # percentage
        ),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_budget_allocation_percentage_sum(app, allocations):
    """
    对于任何EPS订单的预算分配，所有预算Code的分配比例之和必须等于100%，
    否则系统应该拒绝保存
    验证需求: 3.4
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(ConfigurationItem).delete()
        db.session.query(Configuration).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='TEST-REQ-BUDGET',
            jira_case='TEST-JIRA',
            description='Test requirement'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建测试订单
        order = EPSOrder(
            order_code='TEST-ORDER-BUDGET',
            requirement_id=requirement.id,
            supplier='Test Supplier',
            total_amount=Decimal('10000.00')
        )
        db.session.add(order)
        db.session.commit()
        
        # 准备预算分配数据
        allocations_data = []
        total_percentage = Decimal('0')
        
        for budget_code, percentage in allocations:
            allocations_data.append({
                'budget_code': budget_code,
                'allocation_percentage': percentage
            })
            total_percentage += percentage
        
        # 验证预算分配
        if abs(total_percentage - Decimal('100')) > Decimal('0.01'):
            # 如果总和不等于100%，应该抛出异常
            with pytest.raises(ValueError, match="100%"):
                OrderService.allocate_budget(order.id, allocations_data)
        else:
            # 如果总和等于100%，应该成功分配
            budget_allocations = OrderService.allocate_budget(order.id, allocations_data)
            assert len(budget_allocations) == len(allocations_data)
            
            # 验证分配比例总和
            saved_total = sum(alloc.allocation_percentage for alloc in budget_allocations)
            assert abs(saved_total - Decimal('100')) <= Decimal('0.01')
            
            # 验证分配金额总和等于订单总额
            saved_amount_total = sum(alloc.amount for alloc in budget_allocations)
            assert abs(saved_amount_total - order.total_amount) <= Decimal('0.01')



# Feature: server-order-management, Property 11: 需求ID筛选完整性
@given(
    num_requirements=st.integers(min_value=2, max_value=5),
    target_req_index=st.integers(min_value=0, max_value=4)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_requirement_id_filter_completeness(app, num_requirements, target_req_index):
    """
    对于任何需求ID筛选操作，返回的所有EPS订单的需求ID字段都应该等于筛选条件中的需求ID
    验证需求: 4.2
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(ConfigurationItem).delete()
        db.session.query(Configuration).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 确保target_req_index在有效范围内
        target_req_index = target_req_index % num_requirements
        
        # 创建多个需求和订单
        requirements = []
        for i in range(num_requirements):
            requirement = Requirement(
                requirement_code=f'REQ-FILTER-{i}',
                jira_case=f'JIRA-{i}',
                description=f'Test requirement {i}'
            )
            db.session.add(requirement)
            requirements.append(requirement)
        
        db.session.commit()
        
        # 为每个需求创建1-3个订单
        for req_idx, requirement in enumerate(requirements):
            num_orders = (req_idx % 3) + 1
            for order_idx in range(num_orders):
                order = EPSOrder(
                    order_code=f'ORDER-{req_idx}-{order_idx}',
                    requirement_id=requirement.id,
                    supplier=f'Supplier-{req_idx}',
                    total_amount=Decimal('1000.00')
                )
                db.session.add(order)
        
        db.session.commit()
        
        # 选择目标需求进行筛选
        target_requirement = requirements[target_req_index]
        
        # 使用需求ID筛选订单
        filtered_orders = OrderRepository.find_by_requirement(target_requirement.id)
        
        # 验证：所有返回的订单都应该属于目标需求
        assert len(filtered_orders) > 0, "Should return at least one order"
        
        for order in filtered_orders:
            assert order.requirement_id == target_requirement.id, \
                f"Order {order.order_code} has requirement_id {order.requirement_id}, expected {target_requirement.id}"


# Feature: server-order-management, Property 12: Jira Case筛选完整性
@given(
    num_jira_cases=st.integers(min_value=2, max_value=5),
    target_jira_index=st.integers(min_value=0, max_value=4)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_jira_case_filter_completeness(app, num_jira_cases, target_jira_index):
    """
    对于任何Jira Case筛选操作，返回的所有需求的Jira Case字段都应该等于筛选条件
    验证需求: 4.3
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(ConfigurationItem).delete()
        db.session.query(Configuration).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 确保target_jira_index在有效范围内
        target_jira_index = target_jira_index % num_jira_cases
        
        # 创建多个Jira Case和需求
        jira_cases = [f'JIRA-CASE-{i}' for i in range(num_jira_cases)]
        
        for jira_case in jira_cases:
            # 为每个Jira Case创建1-2个需求
            num_reqs = (jira_cases.index(jira_case) % 2) + 1
            for req_idx in range(num_reqs):
                requirement = Requirement(
                    requirement_code=f'REQ-{jira_case}-{req_idx}',
                    jira_case=jira_case,
                    description=f'Test requirement for {jira_case}'
                )
                db.session.add(requirement)
        
        db.session.commit()
        
        # 选择目标Jira Case进行筛选
        target_jira_case = jira_cases[target_jira_index]
        
        # 使用Jira Case筛选需求
        filtered_requirements = RequirementRepository.find_by_jira_case(target_jira_case)
        
        # 验证：所有返回的需求都应该属于目标Jira Case
        assert len(filtered_requirements) > 0, "Should return at least one requirement"
        
        for requirement in filtered_requirements:
            assert requirement.jira_case == target_jira_case, \
                f"Requirement {requirement.requirement_code} has jira_case {requirement.jira_case}, expected {target_jira_case}"


# Feature: server-order-management, Property 13: 订单详情查询完整性
@given(
    num_items=st.integers(min_value=1, max_value=5),
    num_budget_allocations=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_order_details_query_completeness(app, num_items, num_budget_allocations):
    """
    对于任何EPS订单，查询其详情应该返回所有关联的订单项和预算分配记录
    验证需求: 4.4
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(ConfigurationItem).delete()
        db.session.query(Configuration).delete()
        db.session.query(Requirement).delete()
        db.session.query(SKU).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='REQ-DETAILS',
            jira_case='JIRA-DETAILS',
            description='Test requirement for order details'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建SKU
        skus = []
        for i in range(num_items):
            sku = SKU(
                sku_code=f'SKU-DETAILS-{i}',
                name=f'Test SKU {i}',
                unit_price=Decimal('100.00'),
                supplier='Test Supplier'
            )
            db.session.add(sku)
            skus.append(sku)
        
        db.session.commit()
        
        # 创建订单
        order = EPSOrder(
            order_code='ORDER-DETAILS',
            requirement_id=requirement.id,
            supplier='Test Supplier',
            total_amount=Decimal('10000.00')
        )
        db.session.add(order)
        db.session.commit()
        
        # 创建订单项
        for i, sku in enumerate(skus):
            item = EPSOrderItem(
                order_id=order.id,
                sku_id=sku.id,
                quantity=i + 1,
                unit_price=sku.unit_price,
                subtotal=sku.unit_price * (i + 1)
            )
            db.session.add(item)
        
        db.session.commit()
        
        # 创建预算分配
        percentage_per_allocation = Decimal('100') / num_budget_allocations
        for i in range(num_budget_allocations):
            # 对于最后一个分配，使用剩余比例以确保总和为100%
            if i == num_budget_allocations - 1:
                percentage = Decimal('100') - (percentage_per_allocation * (num_budget_allocations - 1))
            else:
                percentage = percentage_per_allocation
            
            amount = order.total_amount * percentage / Decimal('100')
            
            allocation = BudgetAllocation(
                order_id=order.id,
                budget_code=f'BUDGET-{i}',
                allocation_percentage=percentage,
                amount=amount
            )
            db.session.add(allocation)
        
        db.session.commit()
        
        # 查询订单详情
        order_details = OrderService.get_order_details(order.id)
        
        # 验证：返回的订单应该是正确的订单
        assert order_details['order'].id == order.id
        assert order_details['order'].order_code == 'ORDER-DETAILS'
        
        # 验证：返回的订单项数量应该等于创建的订单项数量
        assert len(order_details['items']) == num_items, \
            f"Expected {num_items} items, got {len(order_details['items'])}"
        
        # 验证：所有订单项都应该属于该订单
        for item in order_details['items']:
            assert item.order_id == order.id, \
                f"Item {item.id} belongs to order {item.order_id}, expected {order.id}"
        
        # 验证：返回的预算分配数量应该等于创建的预算分配数量
        assert len(order_details['budget_allocations']) == num_budget_allocations, \
            f"Expected {num_budget_allocations} budget allocations, got {len(order_details['budget_allocations'])}"
        
        # 验证：所有预算分配都应该属于该订单
        for allocation in order_details['budget_allocations']:
            assert allocation.order_id == order.id, \
                f"Allocation {allocation.id} belongs to order {allocation.order_id}, expected {order.id}"
        
        # 验证：返回的需求应该是正确的需求
        assert order_details['requirement'].id == requirement.id


# Feature: server-order-management, Property 14: 预算Code筛选和金额汇总正确性
@given(
    num_orders=st.integers(min_value=2, max_value=5),
    target_budget_code=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_budget_code_filter_and_sum_correctness(app, num_orders, target_budget_code):
    """
    对于任何预算Code筛选操作，返回的订单总支出应该等于所有使用该预算Code的订单中
    分配给该Code的金额之和
    验证需求: 4.5
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(ConfigurationItem).delete()
        db.session.query(Configuration).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='REQ-BUDGET-FILTER',
            jira_case='JIRA-BUDGET',
            description='Test requirement for budget filtering'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建多个订单，部分使用目标预算Code
        expected_total = Decimal('0')
        
        for i in range(num_orders):
            order = EPSOrder(
                order_code=f'ORDER-BUDGET-{i}',
                requirement_id=requirement.id,
                supplier=f'Supplier-{i}',
                total_amount=Decimal(str((i + 1) * 1000))
            )
            db.session.add(order)
            db.session.flush()
            
            # 为每个订单创建预算分配
            # 部分订单使用目标预算Code
            if i % 2 == 0:
                # 使用目标预算Code（100%分配）
                allocation = BudgetAllocation(
                    order_id=order.id,
                    budget_code=target_budget_code,
                    allocation_percentage=Decimal('100'),
                    amount=order.total_amount
                )
                db.session.add(allocation)
                expected_total += order.total_amount
            else:
                # 使用其他预算Code（50%目标，50%其他）
                allocation1 = BudgetAllocation(
                    order_id=order.id,
                    budget_code=target_budget_code,
                    allocation_percentage=Decimal('50'),
                    amount=order.total_amount * Decimal('0.5')
                )
                db.session.add(allocation1)
                expected_total += order.total_amount * Decimal('0.5')
                
                allocation2 = BudgetAllocation(
                    order_id=order.id,
                    budget_code=f'OTHER-BUDGET-{i}',
                    allocation_percentage=Decimal('50'),
                    amount=order.total_amount * Decimal('0.5')
                )
                db.session.add(allocation2)
        
        db.session.commit()
        
        # 使用预算Code筛选订单
        filtered_orders = OrderRepository.find_by_budget_code(target_budget_code)
        
        # 验证：应该返回使用该预算Code的所有订单
        assert len(filtered_orders) == num_orders, \
            f"Expected {num_orders} orders, got {len(filtered_orders)}"
        
        # 计算实际总支出
        actual_total = OrderService.calculate_budget_total(target_budget_code)
        
        # 验证：实际总支出应该等于预期总支出
        assert abs(actual_total - expected_total) <= Decimal('0.01'), \
            f"Expected total {expected_total}, got {actual_total}"
