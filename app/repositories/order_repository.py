"""
订单数据访问层
"""
from typing import List, Optional
from decimal import Decimal

from app import db
from app.models.order import EPSOrder, EPSOrderItem, BudgetAllocation


class OrderRepository:
    """订单数据访问仓库"""
    
    @staticmethod
    def create(order_data: dict) -> EPSOrder:
        """
        创建订单
        
        Args:
            order_data: 订单数据字典
            
        Returns:
            创建的订单对象
            
        Raises:
            ValueError: 如果订单编号已存在
        """
        # 检查订单编号是否已存在
        existing = OrderRepository.find_by_code(order_data['order_code'])
        if existing:
            raise ValueError(f"订单编号 {order_data['order_code']} 已存在")
        
        order = EPSOrder(
            order_code=order_data['order_code'],
            requirement_id=order_data['requirement_id'],
            supplier=order_data['supplier'],
            total_amount=order_data['total_amount'],
            status=order_data.get('status', 'pending')
        )
        
        db.session.add(order)
        db.session.commit()
        
        return order
    
    @staticmethod
    def create_with_items(order_data: dict, items_data: List[dict]) -> EPSOrder:
        """
        创建订单及其订单项
        
        Args:
            order_data: 订单数据字典
            items_data: 订单项数据列表
            
        Returns:
            创建的订单对象
        """
        # 计算总金额
        total_amount = Decimal('0')
        for item_data in items_data:
            subtotal = Decimal(str(item_data['unit_price'])) * item_data['quantity']
            total_amount += subtotal
        
        order = EPSOrder(
            order_code=order_data['order_code'],
            requirement_id=order_data['requirement_id'],
            supplier=order_data['supplier'],
            total_amount=total_amount,
            status=order_data.get('status', 'pending')
        )
        
        db.session.add(order)
        db.session.flush()  # 获取order.id
        
        # 创建订单项
        for item_data in items_data:
            unit_price = Decimal(str(item_data['unit_price']))
            quantity = item_data['quantity']
            subtotal = unit_price * quantity
            
            item = EPSOrderItem(
                order_id=order.id,
                sku_id=item_data['sku_id'],
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal
            )
            db.session.add(item)
        
        db.session.commit()
        
        return order
    
    @staticmethod
    def update(order_id: int, order_data: dict) -> EPSOrder:
        """
        更新订单
        
        Args:
            order_id: 订单ID
            order_data: 更新的数据
            
        Returns:
            更新后的订单对象
            
        Raises:
            ValueError: 如果订单不存在或编号重复
        """
        order = OrderRepository.find_by_id(order_id)
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        # 如果修改了订单编号，检查新编号是否已存在
        if 'order_code' in order_data and order_data['order_code'] != order.order_code:
            existing = OrderRepository.find_by_code(order_data['order_code'])
            if existing:
                raise ValueError(f"订单编号 {order_data['order_code']} 已存在")
            order.order_code = order_data['order_code']
        
        # 更新其他字段
        if 'supplier' in order_data:
            order.supplier = order_data['supplier']
        if 'total_amount' in order_data:
            order.total_amount = order_data['total_amount']
        if 'status' in order_data:
            order.status = order_data['status']
        
        db.session.commit()
        
        return order
    
    @staticmethod
    def find_by_id(order_id: int) -> Optional[EPSOrder]:
        """
        按ID查询订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单对象或None
        """
        return db.session.get(EPSOrder, order_id)
    
    @staticmethod
    def find_by_code(order_code: str) -> Optional[EPSOrder]:
        """
        按编码查询订单
        
        Args:
            order_code: 订单编号
            
        Returns:
            订单对象或None
        """
        return EPSOrder.query.filter_by(order_code=order_code).first()
    
    @staticmethod
    def find_by_requirement(requirement_id: int) -> List[EPSOrder]:
        """
        按需求ID查询订单
        
        Args:
            requirement_id: 需求ID
            
        Returns:
            订单列表
        """
        return EPSOrder.query.filter_by(requirement_id=requirement_id).all()
    
    @staticmethod
    def find_by_budget_code(budget_code: str) -> List[EPSOrder]:
        """
        按预算Code查询订单
        
        Args:
            budget_code: 预算Code
            
        Returns:
            订单列表
        """
        # 查询包含该预算Code的所有订单
        allocations = BudgetAllocation.query.filter_by(budget_code=budget_code).all()
        order_ids = [alloc.order_id for alloc in allocations]
        
        if not order_ids:
            return []
        
        return EPSOrder.query.filter(EPSOrder.id.in_(order_ids)).all()
    
    @staticmethod
    def get_all_with_filters(filters: dict = None, page: int = 1, per_page: int = 20):
        """
        带筛选条件查询订单（支持分页）
        
        Args:
            filters: 筛选条件字典
            page: 页码（从1开始）
            per_page: 每页数量
            
        Returns:
            分页对象
        """
        from app.models.requirement import Requirement
        
        query = EPSOrder.query.join(Requirement, EPSOrder.requirement_id == Requirement.id)
        
        if filters:
            if 'requirement_id' in filters:
                query = query.filter(EPSOrder.requirement_id == filters['requirement_id'])
            if 'supplier' in filters:
                query = query.filter(EPSOrder.supplier.like(f"%{filters['supplier']}%"))
            if 'status' in filters:
                query = query.filter(EPSOrder.status == filters['status'])
            if 'order_code' in filters:
                query = query.filter(EPSOrder.order_code.like(f"%{filters['order_code']}%"))
            if 'jira_case' in filters:
                query = query.filter(Requirement.jira_case.like(f"%{filters['jira_case']}%"))
            if 'budget_code' in filters:
                # 通过预算分配表筛选
                query = query.join(BudgetAllocation, EPSOrder.id == BudgetAllocation.order_id)
                query = query.filter(BudgetAllocation.budget_code.like(f"%{filters['budget_code']}%"))
                query = query.distinct()
            
            # 排序
            sort_by = filters.get('sort_by', 'created_at_desc')
            if sort_by == 'created_at_asc':
                query = query.order_by(EPSOrder.created_at.asc())
            elif sort_by == 'created_at_desc':
                query = query.order_by(EPSOrder.created_at.desc())
            elif sort_by == 'total_amount_asc':
                query = query.order_by(EPSOrder.total_amount.asc())
            elif sort_by == 'total_amount_desc':
                query = query.order_by(EPSOrder.total_amount.desc())
            else:
                query = query.order_by(EPSOrder.created_at.desc())
        else:
            query = query.order_by(EPSOrder.created_at.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def delete(order_id: int) -> bool:
        """
        删除订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否删除成功
        """
        order = OrderRepository.find_by_id(order_id)
        if not order:
            return False
        
        db.session.delete(order)
        db.session.commit()
        
        return True
    
    @staticmethod
    def add_budget_allocation(order_id: int, budget_data: dict) -> BudgetAllocation:
        """
        添加预算分配
        
        Args:
            order_id: 订单ID
            budget_data: 预算分配数据
            
        Returns:
            创建的预算分配对象
            
        Raises:
            ValueError: 如果订单不存在
        """
        order = OrderRepository.find_by_id(order_id)
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        allocation_percentage = Decimal(str(budget_data['allocation_percentage']))
        amount = order.total_amount * allocation_percentage / Decimal('100')
        
        allocation = BudgetAllocation(
            order_id=order_id,
            budget_code=budget_data['budget_code'],
            allocation_percentage=allocation_percentage,
            amount=amount
        )
        
        db.session.add(allocation)
        db.session.commit()
        
        return allocation
    
    @staticmethod
    def set_budget_allocations(order_id: int, allocations_data: List[dict]) -> List[BudgetAllocation]:
        """
        设置订单的预算分配（替换现有分配）
        
        Args:
            order_id: 订单ID
            allocations_data: 预算分配数据列表
            
        Returns:
            创建的预算分配对象列表
            
        Raises:
            ValueError: 如果订单不存在或分配比例总和不为100%
        """
        order = OrderRepository.find_by_id(order_id)
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        # 验证分配比例总和
        total_percentage = sum(Decimal(str(alloc['allocation_percentage'])) for alloc in allocations_data)
        if abs(total_percentage - Decimal('100')) > Decimal('0.01'):
            raise ValueError(f"预算分配比例总和必须为100%，当前为{total_percentage}%")
        
        # 删除现有分配
        BudgetAllocation.query.filter_by(order_id=order_id).delete()
        
        # 创建新分配
        allocations = []
        total_allocated = Decimal('0')
        
        for idx, alloc_data in enumerate(allocations_data):
            allocation_percentage = Decimal(str(alloc_data['allocation_percentage']))
            
            # 对于最后一个分配，使用剩余金额以避免舍入误差
            if idx == len(allocations_data) - 1:
                amount = order.total_amount - total_allocated
            else:
                amount = order.total_amount * allocation_percentage / Decimal('100')
                total_allocated += amount
            
            allocation = BudgetAllocation(
                order_id=order_id,
                budget_code=alloc_data['budget_code'],
                allocation_percentage=allocation_percentage,
                amount=amount
            )
            db.session.add(allocation)
            allocations.append(allocation)
        
        db.session.commit()
        
        return allocations
    
    @staticmethod
    def get_budget_allocations(order_id: int) -> List[BudgetAllocation]:
        """
        获取订单的所有预算分配
        
        Args:
            order_id: 订单ID
            
        Returns:
            预算分配列表
        """
        return BudgetAllocation.query.filter_by(order_id=order_id).all()
    
    @staticmethod
    def get_items(order_id: int) -> List[EPSOrderItem]:
        """
        获取订单的所有订单项
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单项列表
        """
        return EPSOrderItem.query.filter_by(order_id=order_id).all()
