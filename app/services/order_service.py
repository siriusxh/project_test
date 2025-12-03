"""
订单服务
"""
from typing import List, Dict
from decimal import Decimal
from datetime import datetime

from app import db
from app.models.order import EPSOrder, EPSOrderItem, BudgetAllocation
from app.models.requirement import Requirement, Configuration, ConfigurationItem
from app.repositories.order_repository import OrderRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.configuration_repository import ConfigurationRepository


class OrderService:
    """订单服务"""
    
    @staticmethod
    def create_requirement(data: dict) -> Requirement:
        """
        创建新需求
        
        Args:
            data: 需求数据
            
        Returns:
            创建的需求对象
        """
        return RequirementRepository.create(data)
    
    @staticmethod
    def split_requirement_to_orders(requirement_id: int, supplier_mapping: Dict[int, str] = None) -> List[EPSOrder]:
        """
        将需求拆分为EPS订单（按供应商）
        
        Args:
            requirement_id: 需求ID
            supplier_mapping: 配置ID到供应商的映射，如果为None则从SKU获取供应商
            
        Returns:
            创建的订单列表
            
        Raises:
            ValueError: 如果需求不存在
        """
        requirement = RequirementRepository.find_by_id(requirement_id)
        if not requirement:
            raise ValueError(f"需求ID {requirement_id} 不存在")
        
        # 获取需求的所有配置
        configurations = ConfigurationRepository.find_by_requirement(requirement_id)
        if not configurations:
            raise ValueError(f"需求 {requirement_id} 没有配置方案")
        
        # 按供应商分组配置项
        supplier_items = {}  # {supplier: [(sku_id, quantity, unit_price), ...]}
        
        for config in configurations:
            for item in config.items:
                # 确定供应商
                if supplier_mapping and config.id in supplier_mapping:
                    supplier = supplier_mapping[config.id]
                else:
                    # 从SKU获取供应商
                    supplier = item.sku.supplier
                
                if supplier not in supplier_items:
                    supplier_items[supplier] = []
                
                supplier_items[supplier].append({
                    'sku_id': item.sku_id,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price
                })
        
        # 为每个供应商创建订单
        orders = []
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        
        for idx, (supplier, items) in enumerate(supplier_items.items()):
            # 生成订单编号
            order_code = f"EPS-{requirement.requirement_code}-{supplier[:3].upper()}-{timestamp}-{idx}"
            
            order_data = {
                'order_code': order_code,
                'requirement_id': requirement_id,
                'supplier': supplier
            }
            
            order = OrderRepository.create_with_items(order_data, items)
            orders.append(order)
        
        return orders
    
    @staticmethod
    def allocate_budget(order_id: int, budget_codes: List[Dict[str, any]]) -> List[BudgetAllocation]:
        """
        分配预算Code
        
        Args:
            order_id: 订单ID
            budget_codes: 预算Code列表，每项包含 {'budget_code': str, 'allocation_percentage': Decimal}
            
        Returns:
            创建的预算分配列表
            
        Raises:
            ValueError: 如果验证失败
        """
        # 验证预算分配
        OrderService.validate_budget_allocation(budget_codes)
        
        # 设置预算分配
        return OrderRepository.set_budget_allocations(order_id, budget_codes)
    
    @staticmethod
    def validate_budget_allocation(allocations: List[Dict[str, any]]) -> bool:
        """
        验证预算分配比例
        
        Args:
            allocations: 预算分配列表
            
        Returns:
            是否验证通过
            
        Raises:
            ValueError: 如果分配比例总和不为100%
        """
        if not allocations:
            raise ValueError("预算分配不能为空")
        
        total_percentage = Decimal('0')
        for alloc in allocations:
            percentage = alloc.get('allocation_percentage')
            if percentage is None:
                raise ValueError("预算分配必须包含allocation_percentage字段")
            
            percentage = Decimal(str(percentage))
            if percentage <= 0 or percentage > 100:
                raise ValueError(f"预算分配比例必须在0-100之间，当前为{percentage}%")
            
            total_percentage += percentage
        
        # 允许0.01的浮点误差
        if abs(total_percentage - Decimal('100')) > Decimal('0.01'):
            raise ValueError(f"预算分配比例总和必须为100%，当前为{total_percentage}%")
        
        return True
    
    @staticmethod
    def get_order_details(order_id: int) -> Dict:
        """
        获取订单详情
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单详情字典
            
        Raises:
            ValueError: 如果订单不存在
        """
        order = OrderRepository.find_by_id(order_id)
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        items = OrderRepository.get_items(order_id)
        budget_allocations = OrderRepository.get_budget_allocations(order_id)
        
        return {
            'order': order,
            'items': items,
            'budget_allocations': budget_allocations,
            'requirement': order.requirement
        }
    
    @staticmethod
    def calculate_budget_total(budget_code: str) -> Decimal:
        """
        计算预算Code的总支出
        
        Args:
            budget_code: 预算Code
            
        Returns:
            总支出金额
        """
        allocations = BudgetAllocation.query.filter_by(budget_code=budget_code).all()
        total = sum(alloc.amount for alloc in allocations)
        return Decimal(str(total))
