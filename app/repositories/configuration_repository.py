"""
配置数据访问层
"""
from decimal import Decimal
from typing import List, Optional

from app import db
from app.models.requirement import Configuration, ConfigurationItem
from app.models.sku import SKU


class ConfigurationRepository:
    """配置数据访问仓库"""
    
    @staticmethod
    def create(configuration_data: dict) -> Configuration:
        """
        创建配置
        
        Args:
            configuration_data: 配置数据字典
            
        Returns:
            创建的配置对象
        """
        configuration = Configuration(
            requirement_id=configuration_data['requirement_id'],
            config_name=configuration_data['config_name'],
            total_price=configuration_data['total_price']
        )
        
        db.session.add(configuration)
        db.session.commit()
        
        return configuration
    
    @staticmethod
    def create_with_items(configuration_data: dict, items_data: List[dict]) -> Configuration:
        """
        创建配置及其配置项
        
        Args:
            configuration_data: 配置数据字典
            items_data: 配置项数据列表
            
        Returns:
            创建的配置对象
        """
        # 计算总价
        total_price = Decimal('0')
        for item_data in items_data:
            subtotal = Decimal(str(item_data['unit_price'])) * item_data['quantity']
            total_price += subtotal
        
        configuration = Configuration(
            requirement_id=configuration_data['requirement_id'],
            config_name=configuration_data['config_name'],
            total_price=total_price
        )
        
        db.session.add(configuration)
        db.session.flush()  # 获取configuration.id
        
        # 创建配置项
        for item_data in items_data:
            unit_price = Decimal(str(item_data['unit_price']))
            quantity = item_data['quantity']
            subtotal = unit_price * quantity
            
            item = ConfigurationItem(
                configuration_id=configuration.id,
                sku_id=item_data['sku_id'],
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal
            )
            db.session.add(item)
        
        db.session.commit()
        
        return configuration
    
    @staticmethod
    def update(configuration_id: int, configuration_data: dict) -> Configuration:
        """
        更新配置
        
        Args:
            configuration_id: 配置ID
            configuration_data: 更新的数据
            
        Returns:
            更新后的配置对象
            
        Raises:
            ValueError: 如果配置不存在
        """
        configuration = ConfigurationRepository.find_by_id(configuration_id)
        if not configuration:
            raise ValueError(f"配置ID {configuration_id} 不存在")
        
        if 'config_name' in configuration_data:
            configuration.config_name = configuration_data['config_name']
        if 'total_price' in configuration_data:
            configuration.total_price = configuration_data['total_price']
        
        db.session.commit()
        
        return configuration
    
    @staticmethod
    def find_by_id(configuration_id: int) -> Optional[Configuration]:
        """
        按ID查询配置
        
        Args:
            configuration_id: 配置ID
            
        Returns:
            配置对象或None
        """
        return db.session.get(Configuration, configuration_id)
    
    @staticmethod
    def find_by_requirement(requirement_id: int) -> List[Configuration]:
        """
        按需求ID查询配置
        
        Args:
            requirement_id: 需求ID
            
        Returns:
            配置列表
        """
        return Configuration.query.filter_by(requirement_id=requirement_id).all()
    
    @staticmethod
    def delete(configuration_id: int) -> bool:
        """
        删除配置
        
        Args:
            configuration_id: 配置ID
            
        Returns:
            是否删除成功
        """
        configuration = ConfigurationRepository.find_by_id(configuration_id)
        if not configuration:
            return False
        
        db.session.delete(configuration)
        db.session.commit()
        
        return True
    
    @staticmethod
    def add_item(configuration_id: int, item_data: dict) -> ConfigurationItem:
        """
        添加配置项
        
        Args:
            configuration_id: 配置ID
            item_data: 配置项数据
            
        Returns:
            创建的配置项对象
            
        Raises:
            ValueError: 如果配置不存在
        """
        configuration = ConfigurationRepository.find_by_id(configuration_id)
        if not configuration:
            raise ValueError(f"配置ID {configuration_id} 不存在")
        
        unit_price = Decimal(str(item_data['unit_price']))
        quantity = item_data['quantity']
        subtotal = unit_price * quantity
        
        item = ConfigurationItem(
            configuration_id=configuration_id,
            sku_id=item_data['sku_id'],
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal
        )
        
        db.session.add(item)
        
        # 更新配置总价
        configuration.total_price += subtotal
        
        db.session.commit()
        
        return item
    
    @staticmethod
    def get_items(configuration_id: int) -> List[ConfigurationItem]:
        """
        获取配置的所有配置项
        
        Args:
            configuration_id: 配置ID
            
        Returns:
            配置项列表
        """
        return ConfigurationItem.query.filter_by(configuration_id=configuration_id).all()
    
    @staticmethod
    def delete_item(item_id: int) -> bool:
        """
        删除配置项
        
        Args:
            item_id: 配置项ID
            
        Returns:
            是否删除成功
        """
        item = db.session.get(ConfigurationItem, item_id)
        if not item:
            return False
        
        # 更新配置总价
        configuration = ConfigurationRepository.find_by_id(item.configuration_id)
        if configuration:
            configuration.total_price -= item.subtotal
        
        db.session.delete(item)
        db.session.commit()
        
        return True
