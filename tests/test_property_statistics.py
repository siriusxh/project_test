"""
统计功能属性测试
Feature: server-order-management
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck

from app import create_app, db
from app.models.order import EPSOrder, EPSOrderItem, BudgetAllocation
from app.models.requirement import Requirement
from app.models.sku import SKU
from app.services.statistics_service import StatisticsService


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


# Feature: server-order-management, Property 15: 统计聚合计算正确性
@given(
    num_suppliers=st.integers(min_value=1, max_value=5),
    orders_per_supplier=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_supplier_statistics_aggregation_correctness(app, num_suppliers, orders_per_supplier):
    """
    对于任何聚合维度（供应商），统计的总金额应该等于该维度下所有订单的金额之和
    验证需求: 5.1
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='REQ-STATS-SUPPLIER',
            jira_case='JIRA-STATS',
            description='Test requirement for supplier statistics'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建多个供应商的订单
        expected_totals = {}  # {supplier: total_amount}
        expected_counts = {}  # {supplier: order_count}
        
        for supplier_idx in range(num_suppliers):
            supplier = f'Supplier-{supplier_idx}'
            expected_totals[supplier] = Decimal('0')
            expected_counts[supplier] = 0
            
            for order_idx in range(orders_per_supplier):
                amount = Decimal(str((supplier_idx + 1) * (order_idx + 1) * 1000))
                
                order = EPSOrder(
                    order_code=f'ORDER-STATS-{supplier_idx}-{order_idx}',
                    requirement_id=requirement.id,
                    supplier=supplier,
                    total_amount=amount
                )
                db.session.add(order)
                
                expected_totals[supplier] += amount
                expected_counts[supplier] += 1
        
        db.session.commit()
        
        # 获取供应商统计
        statistics = StatisticsService.get_supplier_statistics()
        
        # 验证：统计结果数量应该等于供应商数量
        assert len(statistics) == num_suppliers, \
            f"Expected {num_suppliers} suppliers, got {len(statistics)}"
        
        # 验证：每个供应商的统计金额和订单数量应该正确
        for stat in statistics:
            supplier = stat['supplier']
            assert supplier in expected_totals, f"Unexpected supplier {supplier}"
            
            # 验证总金额
            assert abs(stat['total_amount'] - expected_totals[supplier]) <= Decimal('0.01'), \
                f"Supplier {supplier}: expected {expected_totals[supplier]}, got {stat['total_amount']}"
            
            # 验证订单数量
            assert stat['order_count'] == expected_counts[supplier], \
                f"Supplier {supplier}: expected {expected_counts[supplier]} orders, got {stat['order_count']}"


# Feature: server-order-management, Property 15: 统计聚合计算正确性（预算Code维度）
@given(
    num_budget_codes=st.integers(min_value=1, max_value=5),
    orders_per_budget=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_budget_statistics_aggregation_correctness(app, num_budget_codes, orders_per_budget):
    """
    对于任何聚合维度（预算Code），统计的总金额应该等于该维度下所有订单的金额之和
    验证需求: 5.3
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='REQ-STATS-BUDGET',
            jira_case='JIRA-STATS',
            description='Test requirement for budget statistics'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建多个预算Code的订单
        expected_totals = {}  # {budget_code: total_amount}
        expected_counts = {}  # {budget_code: order_count}
        
        for budget_idx in range(num_budget_codes):
            budget_code = f'BUDGET-{budget_idx}'
            expected_totals[budget_code] = Decimal('0')
            expected_counts[budget_code] = 0
            
            for order_idx in range(orders_per_budget):
                amount = Decimal(str((budget_idx + 1) * (order_idx + 1) * 1000))
                
                order = EPSOrder(
                    order_code=f'ORDER-BUDGET-{budget_idx}-{order_idx}',
                    requirement_id=requirement.id,
                    supplier=f'Supplier-{budget_idx}',
                    total_amount=amount
                )
                db.session.add(order)
                db.session.flush()
                
                # 为订单分配100%到该预算Code
                allocation = BudgetAllocation(
                    order_id=order.id,
                    budget_code=budget_code,
                    allocation_percentage=Decimal('100'),
                    amount=amount
                )
                db.session.add(allocation)
                
                expected_totals[budget_code] += amount
                expected_counts[budget_code] += 1
        
        db.session.commit()
        
        # 获取预算统计
        statistics = StatisticsService.get_budget_statistics()
        
        # 验证：统计结果数量应该等于预算Code数量
        assert len(statistics) == num_budget_codes, \
            f"Expected {num_budget_codes} budget codes, got {len(statistics)}"
        
        # 验证：每个预算Code的统计金额和订单数量应该正确
        for stat in statistics:
            budget_code = stat['budget_code']
            assert budget_code in expected_totals, f"Unexpected budget code {budget_code}"
            
            # 验证总金额
            assert abs(stat['total_amount'] - expected_totals[budget_code]) <= Decimal('0.01'), \
                f"Budget {budget_code}: expected {expected_totals[budget_code]}, got {stat['total_amount']}"
            
            # 验证订单数量
            assert stat['order_count'] == expected_counts[budget_code], \
                f"Budget {budget_code}: expected {expected_counts[budget_code]} orders, got {stat['order_count']}"


# Feature: server-order-management, Property 15: 统计聚合计算正确性（SKU维度）
@given(
    num_skus=st.integers(min_value=1, max_value=5),
    orders_per_sku=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_sku_statistics_aggregation_correctness(app, num_skus, orders_per_sku):
    """
    对于任何聚合维度（SKU），统计的总金额应该等于该维度下所有订单项的金额之和
    验证需求: 5.4
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(Requirement).delete()
        db.session.query(SKU).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='REQ-STATS-SKU',
            jira_case='JIRA-STATS',
            description='Test requirement for SKU statistics'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建SKU
        skus = []
        for sku_idx in range(num_skus):
            sku = SKU(
                sku_code=f'SKU-STATS-{sku_idx}',
                name=f'Test SKU {sku_idx}',
                unit_price=Decimal('100.00'),
                supplier=f'Supplier-{sku_idx}'
            )
            db.session.add(sku)
            skus.append(sku)
        
        db.session.commit()
        
        # 创建订单和订单项
        expected_quantities = {sku.id: 0 for sku in skus}  # {sku_id: total_quantity}
        expected_amounts = {sku.id: Decimal('0') for sku in skus}  # {sku_id: total_amount}
        
        for order_idx in range(orders_per_sku):
            order = EPSOrder(
                order_code=f'ORDER-SKU-{order_idx}',
                requirement_id=requirement.id,
                supplier='Test Supplier',
                total_amount=Decimal('10000.00')
            )
            db.session.add(order)
            db.session.flush()
            
            # 为每个SKU创建订单项
            for sku in skus:
                quantity = order_idx + 1
                unit_price = sku.unit_price
                subtotal = unit_price * quantity
                
                item = EPSOrderItem(
                    order_id=order.id,
                    sku_id=sku.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal
                )
                db.session.add(item)
                
                expected_quantities[sku.id] += quantity
                expected_amounts[sku.id] += subtotal
        
        db.session.commit()
        
        # 获取SKU统计
        statistics = StatisticsService.get_sku_statistics()
        
        # 验证：统计结果数量应该等于SKU数量
        assert len(statistics) == num_skus, \
            f"Expected {num_skus} SKUs, got {len(statistics)}"
        
        # 验证：每个SKU的统计数量和金额应该正确
        for stat in statistics:
            sku_id = stat['sku_id']
            assert sku_id in expected_quantities, f"Unexpected SKU ID {sku_id}"
            
            # 验证总数量
            assert stat['total_quantity'] == expected_quantities[sku_id], \
                f"SKU {sku_id}: expected {expected_quantities[sku_id]} quantity, got {stat['total_quantity']}"
            
            # 验证总金额
            assert abs(stat['total_amount'] - expected_amounts[sku_id]) <= Decimal('0.01'), \
                f"SKU {sku_id}: expected {expected_amounts[sku_id]}, got {stat['total_amount']}"


# Feature: server-order-management, Property 16: 时间范围筛选正确性
@given(
    num_orders=st.integers(min_value=3, max_value=10),
    days_offset=st.integers(min_value=1, max_value=30)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_time_range_filtering_correctness(app, num_orders, days_offset):
    """
    对于任何时间范围筛选，返回的所有订单的创建时间都应该在指定的开始时间和结束时间之间
    验证需求: 5.2
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='REQ-TIME-FILTER',
            jira_case='JIRA-TIME',
            description='Test requirement for time filtering'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建不同时间的订单
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        orders = []
        
        for i in range(num_orders):
            # 创建订单，时间间隔为days_offset天
            order_time = base_time + timedelta(days=i * days_offset)
            
            order = EPSOrder(
                order_code=f'ORDER-TIME-{i}',
                requirement_id=requirement.id,
                supplier=f'Supplier-{i % 3}',
                total_amount=Decimal('1000.00'),
                created_at=order_time
            )
            db.session.add(order)
            orders.append((order, order_time))
        
        db.session.commit()
        
        # 选择一个时间范围（从第2个订单到倒数第2个订单）
        if num_orders >= 3:
            start_date = base_time + timedelta(days=1 * days_offset)
            end_date = base_time + timedelta(days=(num_orders - 2) * days_offset)
            
            # 计算期望在范围内的订单
            expected_orders = [
                order for order, order_time in orders
                if start_date <= order_time <= end_date
            ]
            
            # 获取供应商统计（带时间范围）
            statistics = StatisticsService.get_supplier_statistics(
                start_date=start_date,
                end_date=end_date
            )
            
            # 验证：统计中的订单总数应该等于期望的订单数
            total_order_count = sum(stat['order_count'] for stat in statistics)
            assert total_order_count == len(expected_orders), \
                f"Expected {len(expected_orders)} orders in range, got {total_order_count}"
            
            # 验证：统计的总金额应该等于期望订单的总金额
            expected_total = sum(order.total_amount for order in expected_orders)
            actual_total = sum(stat['total_amount'] for stat in statistics)
            assert abs(actual_total - expected_total) <= Decimal('0.01'), \
                f"Expected total {expected_total}, got {actual_total}"
        
        # 测试只有开始时间的情况
        start_date_only = base_time + timedelta(days=2 * days_offset)
        expected_orders_start = [
            order for order, order_time in orders
            if order_time >= start_date_only
        ]
        
        statistics_start = StatisticsService.get_supplier_statistics(start_date=start_date_only)
        total_count_start = sum(stat['order_count'] for stat in statistics_start)
        assert total_count_start == len(expected_orders_start), \
            f"Expected {len(expected_orders_start)} orders after start date, got {total_count_start}"
        
        # 测试只有结束时间的情况
        end_date_only = base_time + timedelta(days=(num_orders - 3) * days_offset)
        expected_orders_end = [
            order for order, order_time in orders
            if order_time <= end_date_only
        ]
        
        statistics_end = StatisticsService.get_supplier_statistics(end_date=end_date_only)
        total_count_end = sum(stat['order_count'] for stat in statistics_end)
        assert total_count_end == len(expected_orders_end), \
            f"Expected {len(expected_orders_end)} orders before end date, got {total_count_end}"


# Feature: server-order-management, Property 17: 统计数据导出往返一致性
@given(
    num_suppliers=st.integers(min_value=1, max_value=5),
    orders_per_supplier=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_csv_export_roundtrip_consistency(app, num_suppliers, orders_per_supplier):
    """
    对于任何统计数据，导出为CSV后重新解析应该得到等价的数据结构
    验证需求: 5.5
    """
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='REQ-EXPORT-CSV',
            jira_case='JIRA-EXPORT',
            description='Test requirement for CSV export'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建多个供应商的订单
        for supplier_idx in range(num_suppliers):
            supplier = f'Supplier-{supplier_idx}'
            
            for order_idx in range(orders_per_supplier):
                amount = Decimal(str((supplier_idx + 1) * (order_idx + 1) * 1000))
                
                order = EPSOrder(
                    order_code=f'ORDER-EXPORT-{supplier_idx}-{order_idx}',
                    requirement_id=requirement.id,
                    supplier=supplier,
                    total_amount=amount
                )
                db.session.add(order)
        
        db.session.commit()
        
        # 获取原始统计数据
        original_data = StatisticsService.get_supplier_statistics()
        
        # 导出为CSV
        fieldnames = ['supplier', 'total_amount', 'order_count']
        csv_content = StatisticsService.export_to_csv(original_data, fieldnames)
        
        # 从CSV导入
        imported_data = StatisticsService.import_from_csv(
            csv_content, 
            fieldnames,
            decimal_fields=['total_amount']
        )
        
        # 验证：导入的数据应该与原始数据等价
        assert len(imported_data) == len(original_data), \
            f"Expected {len(original_data)} records, got {len(imported_data)}"
        
        # 按供应商排序以便比较
        original_sorted = sorted(original_data, key=lambda x: x['supplier'])
        imported_sorted = sorted(imported_data, key=lambda x: x['supplier'])
        
        for orig, imp in zip(original_sorted, imported_sorted):
            assert orig['supplier'] == imp['supplier'], \
                f"Supplier mismatch: {orig['supplier']} != {imp['supplier']}"
            
            assert abs(orig['total_amount'] - imp['total_amount']) <= Decimal('0.01'), \
                f"Amount mismatch for {orig['supplier']}: {orig['total_amount']} != {imp['total_amount']}"
            
            assert orig['order_count'] == imp['order_count'], \
                f"Order count mismatch for {orig['supplier']}: {orig['order_count']} != {imp['order_count']}"


# Feature: server-order-management, Property 17: 统计数据导出往返一致性（Excel格式）
@given(
    num_budget_codes=st.integers(min_value=1, max_value=5),
    orders_per_budget=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_excel_export_roundtrip_consistency(app, num_budget_codes, orders_per_budget):
    """
    对于任何统计数据，导出为Excel后重新解析应该得到等价的数据结构
    验证需求: 5.5
    """
    try:
        import openpyxl
    except ImportError:
        pytest.skip("openpyxl not installed")
    
    with app.app_context():
        # 清理数据库
        db.session.query(BudgetAllocation).delete()
        db.session.query(EPSOrderItem).delete()
        db.session.query(EPSOrder).delete()
        db.session.query(Requirement).delete()
        db.session.commit()
        
        # 创建测试需求
        requirement = Requirement(
            requirement_code='REQ-EXPORT-EXCEL',
            jira_case='JIRA-EXPORT',
            description='Test requirement for Excel export'
        )
        db.session.add(requirement)
        db.session.commit()
        
        # 创建多个预算Code的订单
        for budget_idx in range(num_budget_codes):
            budget_code = f'BUDGET-{budget_idx}'
            
            for order_idx in range(orders_per_budget):
                amount = Decimal(str((budget_idx + 1) * (order_idx + 1) * 1000))
                
                order = EPSOrder(
                    order_code=f'ORDER-EXCEL-{budget_idx}-{order_idx}',
                    requirement_id=requirement.id,
                    supplier=f'Supplier-{budget_idx}',
                    total_amount=amount
                )
                db.session.add(order)
                db.session.flush()
                
                # 为订单分配100%到该预算Code
                allocation = BudgetAllocation(
                    order_id=order.id,
                    budget_code=budget_code,
                    allocation_percentage=Decimal('100'),
                    amount=amount
                )
                db.session.add(allocation)
        
        db.session.commit()
        
        # 获取原始统计数据
        original_data = StatisticsService.get_budget_statistics()
        
        # 导出为Excel
        fieldnames = ['budget_code', 'total_amount', 'order_count']
        excel_content = StatisticsService.export_to_excel(original_data, fieldnames, 'budget_stats')
        
        # 从Excel导入
        imported_data = StatisticsService.import_from_excel(
            excel_content,
            decimal_fields=['total_amount']
        )
        
        # 验证：导入的数据应该与原始数据等价
        assert len(imported_data) == len(original_data), \
            f"Expected {len(original_data)} records, got {len(imported_data)}"
        
        # 按预算Code排序以便比较
        original_sorted = sorted(original_data, key=lambda x: x['budget_code'])
        imported_sorted = sorted(imported_data, key=lambda x: x['budget_code'])
        
        for orig, imp in zip(original_sorted, imported_sorted):
            assert orig['budget_code'] == imp['budget_code'], \
                f"Budget code mismatch: {orig['budget_code']} != {imp['budget_code']}"
            
            assert abs(orig['total_amount'] - imp['total_amount']) <= Decimal('0.01'), \
                f"Amount mismatch for {orig['budget_code']}: {orig['total_amount']} != {imp['total_amount']}"
            
            assert orig['order_count'] == imp['order_count'], \
                f"Order count mismatch for {orig['budget_code']}: {orig['order_count']} != {imp['order_count']}"
