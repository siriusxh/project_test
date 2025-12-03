"""
数据库种子数据脚本
创建示例SKU、需求和订单用于演示
"""
import sys
from decimal import Decimal
from datetime import datetime, timedelta

from app import create_app, db
from app.models import (
    SKU, PriceHistory,
    Requirement, Configuration, ConfigurationItem,
    EPSOrder, EPSOrderItem, BudgetAllocation
)


def create_sample_skus():
    """创建示例SKU数据"""
    print("创建示例SKU数据...")
    
    skus = [
        # Dell服务器
        {
            'sku_code': 'DELL-R740-001',
            'name': 'Dell PowerEdge R740 2U机架式服务器',
            'unit_price': Decimal('45000.00'),
            'supplier': 'Dell',
            'category': '服务器'
        },
        {
            'sku_code': 'DELL-R640-001',
            'name': 'Dell PowerEdge R640 1U机架式服务器',
            'unit_price': Decimal('38000.00'),
            'supplier': 'Dell',
            'category': '服务器'
        },
        {
            'sku_code': 'DELL-R740XD-001',
            'name': 'Dell PowerEdge R740XD 2U存储服务器',
            'unit_price': Decimal('52000.00'),
            'supplier': 'Dell',
            'category': '服务器'
        },
        
        # HP服务器
        {
            'sku_code': 'HP-DL380-001',
            'name': 'HP ProLiant DL380 Gen10 2U机架式服务器',
            'unit_price': Decimal('42000.00'),
            'supplier': 'HP',
            'category': '服务器'
        },
        {
            'sku_code': 'HP-DL360-001',
            'name': 'HP ProLiant DL360 Gen10 1U机架式服务器',
            'unit_price': Decimal('36000.00'),
            'supplier': 'HP',
            'category': '服务器'
        },
        
        # 联想服务器
        {
            'sku_code': 'LENOVO-SR650-001',
            'name': '联想ThinkSystem SR650 2U机架式服务器',
            'unit_price': Decimal('40000.00'),
            'supplier': 'Lenovo',
            'category': '服务器'
        },
        
        # 内存
        {
            'sku_code': 'MEM-DDR4-32G-001',
            'name': 'DDR4 32GB 2933MHz ECC内存',
            'unit_price': Decimal('1800.00'),
            'supplier': 'Dell',
            'category': '内存'
        },
        {
            'sku_code': 'MEM-DDR4-64G-001',
            'name': 'DDR4 64GB 2933MHz ECC内存',
            'unit_price': Decimal('3500.00'),
            'supplier': 'Dell',
            'category': '内存'
        },
        {
            'sku_code': 'MEM-DDR4-32G-HP',
            'name': 'HP DDR4 32GB 2933MHz ECC内存',
            'unit_price': Decimal('1750.00'),
            'supplier': 'HP',
            'category': '内存'
        },
        
        # 硬盘
        {
            'sku_code': 'HDD-SAS-2T-001',
            'name': 'SAS 2TB 7.2K RPM 3.5寸硬盘',
            'unit_price': Decimal('1200.00'),
            'supplier': 'Dell',
            'category': '硬盘'
        },
        {
            'sku_code': 'SSD-SATA-960G-001',
            'name': 'SATA SSD 960GB 2.5寸固态硬盘',
            'unit_price': Decimal('2800.00'),
            'supplier': 'Dell',
            'category': '硬盘'
        },
        {
            'sku_code': 'SSD-NVME-1T-001',
            'name': 'NVMe SSD 1TB PCIe固态硬盘',
            'unit_price': Decimal('3200.00'),
            'supplier': 'Dell',
            'category': '硬盘'
        },
        {
            'sku_code': 'HDD-SAS-4T-HP',
            'name': 'HP SAS 4TB 7.2K RPM 3.5寸硬盘',
            'unit_price': Decimal('2100.00'),
            'supplier': 'HP',
            'category': '硬盘'
        },
        
        # 网卡
        {
            'sku_code': 'NIC-10G-2P-001',
            'name': '双口万兆网卡 Intel X710',
            'unit_price': Decimal('2500.00'),
            'supplier': 'Dell',
            'category': '网卡'
        },
        {
            'sku_code': 'NIC-25G-2P-001',
            'name': '双口25G网卡 Mellanox ConnectX-4',
            'unit_price': Decimal('4500.00'),
            'supplier': 'Dell',
            'category': '网卡'
        },
        {
            'sku_code': 'NIC-10G-4P-HP',
            'name': 'HP 四口万兆网卡',
            'unit_price': Decimal('4200.00'),
            'supplier': 'HP',
            'category': '网卡'
        },
        
        # RAID卡
        {
            'sku_code': 'RAID-H730P-001',
            'name': 'Dell PERC H730P RAID卡 2GB缓存',
            'unit_price': Decimal('3800.00'),
            'supplier': 'Dell',
            'category': 'RAID卡'
        },
        {
            'sku_code': 'RAID-H740P-001',
            'name': 'Dell PERC H740P RAID卡 8GB缓存',
            'unit_price': Decimal('5500.00'),
            'supplier': 'Dell',
            'category': 'RAID卡'
        },
        
        # 电源
        {
            'sku_code': 'PSU-750W-001',
            'name': '750W 80Plus铂金电源',
            'unit_price': Decimal('1200.00'),
            'supplier': 'Dell',
            'category': '电源'
        },
        {
            'sku_code': 'PSU-1100W-001',
            'name': '1100W 80Plus铂金电源',
            'unit_price': Decimal('1800.00'),
            'supplier': 'Dell',
            'category': '电源'
        },
    ]
    
    created_skus = []
    for sku_data in skus:
        sku = SKU(**sku_data)
        db.session.add(sku)
        created_skus.append(sku)
    
    db.session.commit()
    print(f"  ✓ 创建了 {len(created_skus)} 个SKU")
    
    return created_skus


def create_sample_requirements(skus):
    """创建示例需求数据"""
    print("创建示例需求数据...")
    
    # 按供应商和类别组织SKU
    dell_server = next(s for s in skus if s.sku_code == 'DELL-R740-001')
    dell_memory = next(s for s in skus if s.sku_code == 'MEM-DDR4-32G-001')
    dell_ssd = next(s for s in skus if s.sku_code == 'SSD-SATA-960G-001')
    dell_nic = next(s for s in skus if s.sku_code == 'NIC-10G-2P-001')
    dell_raid = next(s for s in skus if s.sku_code == 'RAID-H730P-001')
    
    hp_server = next(s for s in skus if s.sku_code == 'HP-DL380-001')
    hp_memory = next(s for s in skus if s.sku_code == 'MEM-DDR4-32G-HP')
    hp_hdd = next(s for s in skus if s.sku_code == 'HDD-SAS-4T-HP')
    hp_nic = next(s for s in skus if s.sku_code == 'NIC-10G-4P-HP')
    
    # 需求1: 数据库服务器采购
    req1 = Requirement(
        requirement_code='REQ-2024-001',
        jira_case='INFRA-1234',
        description='数据库服务器采购 - 用于核心业务数据库集群扩容',
        status='approved'
    )
    db.session.add(req1)
    db.session.flush()
    
    # 配置方案1: Dell高性能配置
    config1 = Configuration(
        requirement_id=req1.id,
        config_name='Dell R740 高性能数据库配置',
        total_price=Decimal('0')  # 将在添加配置项后计算
    )
    db.session.add(config1)
    db.session.flush()
    
    # 配置项
    items1 = [
        ConfigurationItem(
            configuration_id=config1.id,
            sku_id=dell_server.id,
            quantity=2,
            unit_price=dell_server.unit_price,
            subtotal=dell_server.unit_price * 2
        ),
        ConfigurationItem(
            configuration_id=config1.id,
            sku_id=dell_memory.id,
            quantity=16,  # 每台服务器8条32GB内存
            unit_price=dell_memory.unit_price,
            subtotal=dell_memory.unit_price * 16
        ),
        ConfigurationItem(
            configuration_id=config1.id,
            sku_id=dell_ssd.id,
            quantity=8,  # 每台服务器4块SSD
            unit_price=dell_ssd.unit_price,
            subtotal=dell_ssd.unit_price * 8
        ),
        ConfigurationItem(
            configuration_id=config1.id,
            sku_id=dell_nic.id,
            quantity=2,
            unit_price=dell_nic.unit_price,
            subtotal=dell_nic.unit_price * 2
        ),
        ConfigurationItem(
            configuration_id=config1.id,
            sku_id=dell_raid.id,
            quantity=2,
            unit_price=dell_raid.unit_price,
            subtotal=dell_raid.unit_price * 2
        ),
    ]
    
    for item in items1:
        db.session.add(item)
    
    # 计算配置总价
    config1.total_price = sum(item.subtotal for item in items1)
    
    # 需求2: 应用服务器采购
    req2 = Requirement(
        requirement_code='REQ-2024-002',
        jira_case='INFRA-1235',
        description='应用服务器采购 - 用于Web应用集群',
        status='approved'
    )
    db.session.add(req2)
    db.session.flush()
    
    # 配置方案2: HP标准配置
    config2 = Configuration(
        requirement_id=req2.id,
        config_name='HP DL380 标准应用配置',
        total_price=Decimal('0')
    )
    db.session.add(config2)
    db.session.flush()
    
    items2 = [
        ConfigurationItem(
            configuration_id=config2.id,
            sku_id=hp_server.id,
            quantity=4,
            unit_price=hp_server.unit_price,
            subtotal=hp_server.unit_price * 4
        ),
        ConfigurationItem(
            configuration_id=config2.id,
            sku_id=hp_memory.id,
            quantity=16,  # 每台服务器4条32GB内存
            unit_price=hp_memory.unit_price,
            subtotal=hp_memory.unit_price * 16
        ),
        ConfigurationItem(
            configuration_id=config2.id,
            sku_id=hp_hdd.id,
            quantity=8,  # 每台服务器2块硬盘
            unit_price=hp_hdd.unit_price,
            subtotal=hp_hdd.unit_price * 8
        ),
        ConfigurationItem(
            configuration_id=config2.id,
            sku_id=hp_nic.id,
            quantity=4,
            unit_price=hp_nic.unit_price,
            subtotal=hp_nic.unit_price * 4
        ),
    ]
    
    for item in items2:
        db.session.add(item)
    
    config2.total_price = sum(item.subtotal for item in items2)
    
    # 需求3: 混合采购（Dell + HP）
    req3 = Requirement(
        requirement_code='REQ-2024-003',
        jira_case='INFRA-1236',
        description='混合服务器采购 - 用于开发测试环境',
        status='draft'
    )
    db.session.add(req3)
    db.session.flush()
    
    # Dell配置
    config3a = Configuration(
        requirement_id=req3.id,
        config_name='Dell R640 开发环境配置',
        total_price=Decimal('0')
    )
    db.session.add(config3a)
    db.session.flush()
    
    dell_r640 = next(s for s in skus if s.sku_code == 'DELL-R640-001')
    items3a = [
        ConfigurationItem(
            configuration_id=config3a.id,
            sku_id=dell_r640.id,
            quantity=2,
            unit_price=dell_r640.unit_price,
            subtotal=dell_r640.unit_price * 2
        ),
        ConfigurationItem(
            configuration_id=config3a.id,
            sku_id=dell_memory.id,
            quantity=8,
            unit_price=dell_memory.unit_price,
            subtotal=dell_memory.unit_price * 8
        ),
    ]
    
    for item in items3a:
        db.session.add(item)
    
    config3a.total_price = sum(item.subtotal for item in items3a)
    
    # HP配置
    config3b = Configuration(
        requirement_id=req3.id,
        config_name='HP DL360 测试环境配置',
        total_price=Decimal('0')
    )
    db.session.add(config3b)
    db.session.flush()
    
    hp_dl360 = next(s for s in skus if s.sku_code == 'HP-DL360-001')
    items3b = [
        ConfigurationItem(
            configuration_id=config3b.id,
            sku_id=hp_dl360.id,
            quantity=3,
            unit_price=hp_dl360.unit_price,
            subtotal=hp_dl360.unit_price * 3
        ),
        ConfigurationItem(
            configuration_id=config3b.id,
            sku_id=hp_memory.id,
            quantity=12,
            unit_price=hp_memory.unit_price,
            subtotal=hp_memory.unit_price * 12
        ),
    ]
    
    for item in items3b:
        db.session.add(item)
    
    config3b.total_price = sum(item.subtotal for item in items3b)
    
    db.session.commit()
    print(f"  ✓ 创建了 3 个需求和 4 个配置方案")
    
    return [req1, req2, req3]


def create_sample_orders(requirements):
    """创建示例订单数据"""
    print("创建示例订单数据...")
    
    req1, req2, req3 = requirements
    
    # 订单1: 基于需求1创建Dell订单
    order1 = EPSOrder(
        order_code='EPS-2024-001',
        requirement_id=req1.id,
        supplier='Dell',
        total_amount=Decimal('0'),  # 将在添加订单项后计算
        status='confirmed',
        created_at=datetime.utcnow() - timedelta(days=10)
    )
    db.session.add(order1)
    db.session.flush()
    
    # 从需求1的配置中获取订单项
    config1 = req1.configurations.first()
    order1_items = []
    for config_item in config1.items:
        order_item = EPSOrderItem(
            order_id=order1.id,
            sku_id=config_item.sku_id,
            quantity=config_item.quantity,
            unit_price=config_item.unit_price,
            subtotal=config_item.subtotal
        )
        db.session.add(order_item)
        order1_items.append(order_item)
    
    order1.total_amount = sum(item.subtotal for item in order1_items)
    
    # 预算分配
    budget1_allocations = [
        BudgetAllocation(
            order_id=order1.id,
            budget_code='BUDGET-2024-IT-001',
            allocation_percentage=Decimal('60.00'),
            amount=order1.total_amount * Decimal('0.60')
        ),
        BudgetAllocation(
            order_id=order1.id,
            budget_code='BUDGET-2024-IT-002',
            allocation_percentage=Decimal('40.00'),
            amount=order1.total_amount * Decimal('0.40')
        ),
    ]
    
    for allocation in budget1_allocations:
        db.session.add(allocation)
    
    # 订单2: 基于需求2创建HP订单
    order2 = EPSOrder(
        order_code='EPS-2024-002',
        requirement_id=req2.id,
        supplier='HP',
        total_amount=Decimal('0'),
        status='confirmed',
        created_at=datetime.utcnow() - timedelta(days=5)
    )
    db.session.add(order2)
    db.session.flush()
    
    config2 = req2.configurations.first()
    order2_items = []
    for config_item in config2.items:
        order_item = EPSOrderItem(
            order_id=order2.id,
            sku_id=config_item.sku_id,
            quantity=config_item.quantity,
            unit_price=config_item.unit_price,
            subtotal=config_item.subtotal
        )
        db.session.add(order_item)
        order2_items.append(order_item)
    
    order2.total_amount = sum(item.subtotal for item in order2_items)
    
    # 预算分配
    budget2_allocation = BudgetAllocation(
        order_id=order2.id,
        budget_code='BUDGET-2024-IT-003',
        allocation_percentage=Decimal('100.00'),
        amount=order2.total_amount
    )
    db.session.add(budget2_allocation)
    
    db.session.commit()
    print(f"  ✓ 创建了 2 个订单")
    
    return [order1, order2]


def create_sample_price_history(skus):
    """创建示例价格历史数据"""
    print("创建示例价格历史数据...")
    
    # 为几个SKU创建价格变更历史
    dell_server = next(s for s in skus if s.sku_code == 'DELL-R740-001')
    hp_server = next(s for s in skus if s.sku_code == 'HP-DL380-001')
    
    price_changes = [
        PriceHistory(
            sku_id=dell_server.id,
            old_price=Decimal('48000.00'),
            new_price=Decimal('45000.00'),
            changed_at=datetime.utcnow() - timedelta(days=30),
            changed_by='admin'
        ),
        PriceHistory(
            sku_id=hp_server.id,
            old_price=Decimal('44000.00'),
            new_price=Decimal('42000.00'),
            changed_at=datetime.utcnow() - timedelta(days=20),
            changed_by='admin'
        ),
    ]
    
    for change in price_changes:
        db.session.add(change)
    
    db.session.commit()
    print(f"  ✓ 创建了 {len(price_changes)} 条价格历史记录")


def seed_database(config_name='development'):
    """
    填充数据库种子数据
    
    Args:
        config_name: 配置名称 ('development', 'production', 'testing')
    """
    print(f"\n开始填充数据库种子数据 (配置: {config_name})...\n")
    
    # 创建应用实例
    app = create_app(config_name)
    
    with app.app_context():
        # 检查数据库是否已有数据
        if SKU.query.first() is not None:
            print("警告: 数据库已包含数据!")
            response = input("是否清空现有数据并重新填充? (yes/no): ")
            if response.lower() != 'yes':
                print("操作已取消")
                return
            
            # 清空所有数据
            print("\n清空现有数据...")
            db.session.query(BudgetAllocation).delete()
            db.session.query(EPSOrderItem).delete()
            db.session.query(EPSOrder).delete()
            db.session.query(ConfigurationItem).delete()
            db.session.query(Configuration).delete()
            db.session.query(Requirement).delete()
            db.session.query(PriceHistory).delete()
            db.session.query(SKU).delete()
            db.session.commit()
            print("  ✓ 数据已清空")
        
        # 创建示例数据
        skus = create_sample_skus()
        requirements = create_sample_requirements(skus)
        orders = create_sample_orders(requirements)
        create_sample_price_history(skus)
        
        # 显示统计信息
        print("\n数据库种子数据填充完成!")
        print("\n统计信息:")
        print(f"  - SKU数量: {SKU.query.count()}")
        print(f"  - 需求数量: {Requirement.query.count()}")
        print(f"  - 配置方案数量: {Configuration.query.count()}")
        print(f"  - 配置项数量: {ConfigurationItem.query.count()}")
        print(f"  - EPS订单数量: {EPSOrder.query.count()}")
        print(f"  - 订单项数量: {EPSOrderItem.query.count()}")
        print(f"  - 预算分配数量: {BudgetAllocation.query.count()}")
        print(f"  - 价格历史数量: {PriceHistory.query.count()}")
        
        print("\n示例数据概览:")
        print("\n需求列表:")
        for req in Requirement.query.all():
            print(f"  - {req.requirement_code} ({req.jira_case}): {req.description}")
            print(f"    状态: {req.status}, 配置方案数: {req.configurations.count()}")
        
        print("\n订单列表:")
        for order in EPSOrder.query.all():
            print(f"  - {order.order_code} ({order.supplier}): ¥{order.total_amount:,.2f}")
            print(f"    状态: {order.status}, 订单项数: {order.items.count()}, 预算分配数: {order.budget_allocations.count()}")


if __name__ == '__main__':
    # 从命令行参数获取配置名称
    config_name = sys.argv[1] if len(sys.argv) > 1 else 'development'
    
    # 填充种子数据
    seed_database(config_name)
