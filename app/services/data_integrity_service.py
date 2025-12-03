"""
数据完整性服务
"""
import re
from decimal import Decimal
from typing import Dict, Any, Optional, List

from app import db
from app.exceptions import (
    ValidationError, 
    BusinessLogicError, 
    ReferentialIntegrityError,
    ForeignKeyError
)
from app.models.sku import SKU, PriceHistory
from app.models.requirement import Requirement, Configuration, ConfigurationItem
from app.models.order import EPSOrder, EPSOrderItem, BudgetAllocation


class DataIntegrityService:
    """数据完整性服务类"""
    
    @staticmethod
    def check_requirement_dependencies(requirement_id: int) -> Dict[str, Any]:
        """
        检查需求的依赖关系
        
        Args:
            requirement_id: 需求ID
            
        Returns:
            包含依赖信息的字典
            
        Raises:
            ReferentialIntegrityError: 如果存在依赖关系
        """
        requirement = Requirement.query.get(requirement_id)
        if not requirement:
            raise ValidationError(f"需求ID {requirement_id} 不存在")
        
        # 检查关联的订单
        orders = EPSOrder.query.filter_by(requirement_id=requirement_id).all()
        
        dependencies = {
            'has_dependencies': len(orders) > 0,
            'orders_count': len(orders),
            'orders': [order.to_dict() for order in orders]
        }
        
        if dependencies['has_dependencies']:
            raise ReferentialIntegrityError(
                f"需求 {requirement.requirement_code} 存在 {len(orders)} 个关联订单，无法删除",
                entity_type='requirement',
                entity_id=requirement_id,
                dependent_count=len(orders)
            )
        
        return dependencies
    
    @staticmethod
    def cascade_delete_requirement(requirement_id: int) -> Dict[str, int]:
        """
        级联删除需求及其所有关联数据
        
        Args:
            requirement_id: 需求ID
            
        Returns:
            删除统计信息
        """
        requirement = Requirement.query.get(requirement_id)
        if not requirement:
            raise ValidationError(f"需求ID {requirement_id} 不存在")
        
        stats = {
            'configurations': 0,
            'configuration_items': 0,
            'orders': 0,
            'order_items': 0,
            'budget_allocations': 0
        }
        
        # 删除关联的订单
        orders = EPSOrder.query.filter_by(requirement_id=requirement_id).all()
        for order in orders:
            # 删除订单项
            order_items = EPSOrderItem.query.filter_by(order_id=order.id).all()
            stats['order_items'] += len(order_items)
            for item in order_items:
                db.session.delete(item)
            
            # 删除预算分配
            budget_allocations = BudgetAllocation.query.filter_by(order_id=order.id).all()
            stats['budget_allocations'] += len(budget_allocations)
            for allocation in budget_allocations:
                db.session.delete(allocation)
            
            db.session.delete(order)
            stats['orders'] += 1
        
        # 删除配置
        configurations = Configuration.query.filter_by(requirement_id=requirement_id).all()
        for config in configurations:
            # 删除配置项
            config_items = ConfigurationItem.query.filter_by(configuration_id=config.id).all()
            stats['configuration_items'] += len(config_items)
            for item in config_items:
                db.session.delete(item)
            
            db.session.delete(config)
            stats['configurations'] += 1
        
        # 删除需求本身
        db.session.delete(requirement)
        db.session.commit()
        
        return stats
    
    @staticmethod
    def archive_price_change(sku_id: int, old_price: Decimal, new_price: Decimal, 
                           changed_by: Optional[str] = None) -> PriceHistory:
        """
        记录价格变更历史
        
        Args:
            sku_id: SKU ID
            old_price: 旧价格
            new_price: 新价格
            changed_by: 修改人
            
        Returns:
            价格历史记录
        """
        sku = SKU.query.get(sku_id)
        if not sku:
            raise ValidationError(f"SKU ID {sku_id} 不存在")
        
        price_history = PriceHistory(
            sku_id=sku_id,
            old_price=old_price,
            new_price=new_price,
            changed_by=changed_by
        )
        
        db.session.add(price_history)
        db.session.commit()
        
        return price_history
    
    @staticmethod
    def validate_foreign_keys(entity_type: str, data: Dict[str, Any]) -> bool:
        """
        验证外键关系
        
        Args:
            entity_type: 实体类型 ('order', 'configuration', 'configuration_item', 'order_item')
            data: 包含外键的数据字典
            
        Returns:
            验证是否通过
            
        Raises:
            ForeignKeyError: 如果外键不存在
        """
        if entity_type == 'order':
            # 验证需求ID
            requirement_id = data.get('requirement_id')
            if requirement_id:
                requirement = Requirement.query.get(requirement_id)
                if not requirement:
                    raise ForeignKeyError(
                        f"需求ID {requirement_id} 不存在",
                        foreign_key_field='requirement_id',
                        foreign_key_value=requirement_id
                    )
        
        elif entity_type == 'configuration':
            # 验证需求ID
            requirement_id = data.get('requirement_id')
            if requirement_id:
                requirement = Requirement.query.get(requirement_id)
                if not requirement:
                    raise ForeignKeyError(
                        f"需求ID {requirement_id} 不存在",
                        foreign_key_field='requirement_id',
                        foreign_key_value=requirement_id
                    )
        
        elif entity_type == 'configuration_item':
            # 验证配置ID
            configuration_id = data.get('configuration_id')
            if configuration_id:
                configuration = Configuration.query.get(configuration_id)
                if not configuration:
                    raise ForeignKeyError(
                        f"配置ID {configuration_id} 不存在",
                        foreign_key_field='configuration_id',
                        foreign_key_value=configuration_id
                    )
            
            # 验证SKU ID
            sku_id = data.get('sku_id')
            if sku_id:
                sku = SKU.query.get(sku_id)
                if not sku:
                    raise ForeignKeyError(
                        f"SKU ID {sku_id} 不存在",
                        foreign_key_field='sku_id',
                        foreign_key_value=sku_id
                    )
        
        elif entity_type == 'order_item':
            # 验证订单ID
            order_id = data.get('order_id')
            if order_id:
                order = EPSOrder.query.get(order_id)
                if not order:
                    raise ForeignKeyError(
                        f"订单ID {order_id} 不存在",
                        foreign_key_field='order_id',
                        foreign_key_value=order_id
                    )
            
            # 验证SKU ID
            sku_id = data.get('sku_id')
            if sku_id:
                sku = SKU.query.get(sku_id)
                if not sku:
                    raise ForeignKeyError(
                        f"SKU ID {sku_id} 不存在",
                        foreign_key_field='sku_id',
                        foreign_key_value=sku_id
                    )
        
        elif entity_type == 'budget_allocation':
            # 验证订单ID
            order_id = data.get('order_id')
            if order_id:
                order = EPSOrder.query.get(order_id)
                if not order:
                    raise ForeignKeyError(
                        f"订单ID {order_id} 不存在",
                        foreign_key_field='order_id',
                        foreign_key_value=order_id
                    )
        
        return True
    
    @staticmethod
    def validate_budget_code_format(budget_code: str) -> bool:
        """
        验证预算Code格式
        
        Args:
            budget_code: 预算Code
            
        Returns:
            验证是否通过
            
        Raises:
            ValidationError: 如果格式无效
        """
        if not budget_code or not budget_code.strip():
            raise ValidationError("预算Code不能为空", field='budget_code')
        
        # 预算Code格式规则：
        # - 长度在3-50个字符之间
        # - 只能包含字母、数字、连字符和下划线
        # - 必须以字母或数字开头
        if len(budget_code) < 3 or len(budget_code) > 50:
            raise ValidationError(
                "预算Code长度必须在3-50个字符之间",
                field='budget_code'
            )
        
        pattern = r'^[A-Za-z0-9][A-Za-z0-9\-_]*$'
        if not re.match(pattern, budget_code):
            raise ValidationError(
                "预算Code格式无效，只能包含字母、数字、连字符和下划线，且必须以字母或数字开头",
                field='budget_code'
            )
        
        return True
    
    @staticmethod
    def validate_form_input(form_type: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        验证表单输入
        
        Args:
            form_type: 表单类型 ('sku', 'requirement', 'configuration', 'order', 'budget')
            data: 表单数据
            
        Returns:
            错误字典，键为字段名，值为错误消息列表
            
        Raises:
            ValidationError: 如果验证失败
        """
        errors = {}
        
        if form_type == 'sku':
            # SKU编码验证
            if not data.get('sku_code') or not data['sku_code'].strip():
                errors['sku_code'] = ['SKU编码不能为空']
            elif len(data['sku_code']) > 50:
                errors['sku_code'] = ['SKU编码长度不能超过50个字符']
            
            # 名称验证
            if not data.get('name') or not data['name'].strip():
                errors['name'] = ['名称不能为空']
            elif len(data['name']) > 200:
                errors['name'] = ['名称长度不能超过200个字符']
            
            # 单价验证
            if 'unit_price' not in data:
                errors['unit_price'] = ['单价不能为空']
            else:
                try:
                    price = Decimal(str(data['unit_price']))
                    if price <= 0:
                        errors['unit_price'] = ['单价必须大于0']
                    elif price > Decimal('999999.99'):
                        errors['unit_price'] = ['单价不能超过999999.99']
                except (ValueError, TypeError, Exception):
                    errors['unit_price'] = ['单价格式无效']
            
            # 供应商验证
            if not data.get('supplier') or not data['supplier'].strip():
                errors['supplier'] = ['供应商不能为空']
            elif len(data['supplier']) > 100:
                errors['supplier'] = ['供应商名称长度不能超过100个字符']
        
        elif form_type == 'requirement':
            # 需求编码验证
            if not data.get('requirement_code') or not data['requirement_code'].strip():
                errors['requirement_code'] = ['需求编码不能为空']
            elif len(data['requirement_code']) > 50:
                errors['requirement_code'] = ['需求编码长度不能超过50个字符']
            
            # Jira Case验证
            if not data.get('jira_case') or not data['jira_case'].strip():
                errors['jira_case'] = ['Jira Case不能为空']
            elif len(data['jira_case']) > 50:
                errors['jira_case'] = ['Jira Case长度不能超过50个字符']
        
        elif form_type == 'order':
            # 订单编码验证
            if not data.get('order_code') or not data['order_code'].strip():
                errors['order_code'] = ['订单编码不能为空']
            elif len(data['order_code']) > 50:
                errors['order_code'] = ['订单编码长度不能超过50个字符']
            
            # 需求ID验证
            if not data.get('requirement_id'):
                errors['requirement_id'] = ['需求ID不能为空']
            
            # 供应商验证
            if not data.get('supplier') or not data['supplier'].strip():
                errors['supplier'] = ['供应商不能为空']
        
        elif form_type == 'budget':
            # 预算Code验证
            if not data.get('budget_code') or not data['budget_code'].strip():
                errors['budget_code'] = ['预算Code不能为空']
            else:
                try:
                    DataIntegrityService.validate_budget_code_format(data['budget_code'])
                except ValidationError as e:
                    errors['budget_code'] = [e.message]
            
            # 分配比例验证
            if 'allocation_percentage' not in data:
                errors['allocation_percentage'] = ['分配比例不能为空']
            else:
                try:
                    percentage = Decimal(str(data['allocation_percentage']))
                    if percentage <= 0 or percentage > 100:
                        errors['allocation_percentage'] = ['分配比例必须在0-100之间']
                except (ValueError, TypeError):
                    errors['allocation_percentage'] = ['分配比例格式无效']
        
        elif form_type == 'configuration':
            # 配置名称验证
            if not data.get('config_name') or not data['config_name'].strip():
                errors['config_name'] = ['配置名称不能为空']
            elif len(data['config_name']) > 100:
                errors['config_name'] = ['配置名称长度不能超过100个字符']
            
            # 需求ID验证
            if not data.get('requirement_id'):
                errors['requirement_id'] = ['需求ID不能为空']
        
        if errors:
            # 构造错误消息
            error_messages = []
            for field, messages in errors.items():
                error_messages.extend(messages)
            raise ValidationError('; '.join(error_messages))
        
        return errors
    
    @staticmethod
    def verify_association_consistency(entity_type: str, entity_id: int) -> Dict[str, Any]:
        """
        验证关联数据查询一致性
        
        Args:
            entity_type: 实体类型 ('requirement', 'order')
            entity_id: 实体ID
            
        Returns:
            关联数据字典
            
        Raises:
            ValidationError: 如果实体不存在
            BusinessLogicError: 如果关联数据不一致
        """
        if entity_type == 'requirement':
            requirement = Requirement.query.get(entity_id)
            if not requirement:
                raise ValidationError(f"需求ID {entity_id} 不存在")
            
            # 获取所有关联数据
            configurations = Configuration.query.filter_by(requirement_id=entity_id).all()
            orders = EPSOrder.query.filter_by(requirement_id=entity_id).all()
            
            # 验证配置的外键一致性
            for config in configurations:
                if config.requirement_id != entity_id:
                    raise BusinessLogicError(
                        f"配置 {config.id} 的需求ID不一致"
                    )
                
                # 验证配置项的外键一致性
                items = ConfigurationItem.query.filter_by(configuration_id=config.id).all()
                for item in items:
                    if item.configuration_id != config.id:
                        raise BusinessLogicError(
                            f"配置项 {item.id} 的配置ID不一致"
                        )
                    
                    # 验证SKU存在
                    sku = SKU.query.get(item.sku_id)
                    if not sku:
                        raise BusinessLogicError(
                            f"配置项 {item.id} 引用的SKU {item.sku_id} 不存在"
                        )
            
            # 验证订单的外键一致性
            for order in orders:
                if order.requirement_id != entity_id:
                    raise BusinessLogicError(
                        f"订单 {order.order_code} 的需求ID不一致"
                    )
            
            return {
                'requirement': requirement.to_dict(),
                'configurations': [c.to_dict() for c in configurations],
                'orders': [o.to_dict() for o in orders]
            }
        
        elif entity_type == 'order':
            order = EPSOrder.query.get(entity_id)
            if not order:
                raise ValidationError(f"订单ID {entity_id} 不存在")
            
            # 验证需求存在
            requirement = Requirement.query.get(order.requirement_id)
            if not requirement:
                raise BusinessLogicError(
                    f"订单 {order.order_code} 引用的需求 {order.requirement_id} 不存在"
                )
            
            # 获取订单项
            order_items = EPSOrderItem.query.filter_by(order_id=entity_id).all()
            for item in order_items:
                if item.order_id != entity_id:
                    raise BusinessLogicError(
                        f"订单项 {item.id} 的订单ID不一致"
                    )
                
                # 验证SKU存在
                sku = SKU.query.get(item.sku_id)
                if not sku:
                    raise BusinessLogicError(
                        f"订单项 {item.id} 引用的SKU {item.sku_id} 不存在"
                    )
            
            # 获取预算分配
            budget_allocations = BudgetAllocation.query.filter_by(order_id=entity_id).all()
            for allocation in budget_allocations:
                if allocation.order_id != entity_id:
                    raise BusinessLogicError(
                        f"预算分配 {allocation.id} 的订单ID不一致"
                    )
            
            return {
                'order': order.to_dict(),
                'requirement': requirement.to_dict(),
                'order_items': [item.to_dict() for item in order_items],
                'budget_allocations': [alloc.to_dict() for alloc in budget_allocations]
            }
        
        raise ValidationError(f"不支持的实体类型: {entity_type}")
