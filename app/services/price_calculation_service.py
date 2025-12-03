"""
价格计算服务
"""
from decimal import Decimal
from typing import List, Dict

from app.models.requirement import Configuration, ConfigurationItem
from app.repositories.sku_repository import SKURepository


class PriceCalculationService:
    """价格计算服务"""
    
    @staticmethod
    def calculate_configuration_price(configuration_items: List[Dict]) -> Decimal:
        """
        计算配置总价
        
        Args:
            configuration_items: 配置项列表，每项包含 {'sku_id': int, 'quantity': int}
            
        Returns:
            配置总价
        """
        total_price = Decimal('0')
        
        for item in configuration_items:
            sku_id = item['sku_id']
            quantity = item['quantity']
            
            # 获取当前SKU价格
            unit_price = PriceCalculationService.get_current_sku_price(sku_id)
            if unit_price is None:
                raise ValueError(f"SKU ID {sku_id} 不存在")
            
            # 计算小计
            subtotal = PriceCalculationService.calculate_item_subtotal(unit_price, quantity)
            total_price += subtotal
        
        return total_price
    
    @staticmethod
    def calculate_item_subtotal(unit_price: Decimal, quantity: int) -> Decimal:
        """
        计算单项小计
        
        Args:
            unit_price: 单价
            quantity: 数量
            
        Returns:
            小计金额
        """
        if isinstance(unit_price, (int, float, str)):
            unit_price = Decimal(str(unit_price))
        
        return unit_price * quantity
    
    @staticmethod
    def get_current_sku_price(sku_id: int) -> Decimal:
        """
        获取当前SKU价格
        
        Args:
            sku_id: SKU ID
            
        Returns:
            当前单价，如果SKU不存在返回None
        """
        sku = SKURepository.find_by_id(sku_id)
        if not sku:
            return None
        
        return sku.unit_price
    
    @staticmethod
    def recalculate_configuration_total(configuration: Configuration) -> Decimal:
        """
        重新计算配置总价（基于配置项）
        
        Args:
            configuration: 配置对象
            
        Returns:
            重新计算的总价
        """
        total_price = Decimal('0')
        
        for item in configuration.items:
            total_price += item.subtotal
        
        return total_price
    
    @staticmethod
    def validate_configuration_price(configuration: Configuration) -> bool:
        """
        验证配置总价是否正确
        
        Args:
            configuration: 配置对象
            
        Returns:
            总价是否正确
        """
        calculated_total = PriceCalculationService.recalculate_configuration_total(configuration)
        return abs(calculated_total - configuration.total_price) < Decimal('0.01')
