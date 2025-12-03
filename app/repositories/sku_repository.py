"""
SKU数据访问层
"""
from decimal import Decimal
from typing import List, Optional

from app import db
from app.models.sku import SKU, PriceHistory


class SKURepository:
    """SKU数据访问仓库"""
    
    @staticmethod
    def create(sku_data: dict) -> SKU:
        """
        创建SKU
        
        Args:
            sku_data: SKU数据字典
            
        Returns:
            创建的SKU对象
            
        Raises:
            ValueError: 如果SKU编码已存在
        """
        # 检查SKU编码是否已存在
        existing = SKURepository.find_by_code(sku_data['sku_code'])
        if existing:
            raise ValueError(f"SKU编码 {sku_data['sku_code']} 已存在")
        
        sku = SKU(
            sku_code=sku_data['sku_code'],
            name=sku_data['name'],
            unit_price=sku_data['unit_price'],
            supplier=sku_data['supplier'],
            category=sku_data.get('category')
        )
        
        db.session.add(sku)
        db.session.commit()
        
        return sku
    
    @staticmethod
    def update(sku_id: int, sku_data: dict, changed_by: str = None) -> SKU:
        """
        更新SKU
        
        Args:
            sku_id: SKU ID
            sku_data: 更新的数据
            changed_by: 修改人
            
        Returns:
            更新后的SKU对象
            
        Raises:
            ValueError: 如果SKU不存在或编码重复
        """
        sku = SKURepository.find_by_id(sku_id)
        if not sku:
            raise ValueError(f"SKU ID {sku_id} 不存在")
        
        # 如果修改了SKU编码，检查新编码是否已存在
        if 'sku_code' in sku_data and sku_data['sku_code'] != sku.sku_code:
            existing = SKURepository.find_by_code(sku_data['sku_code'])
            if existing:
                raise ValueError(f"SKU编码 {sku_data['sku_code']} 已存在")
            sku.sku_code = sku_data['sku_code']
        
        # 如果修改了价格，记录价格历史
        if 'unit_price' in sku_data:
            new_price = Decimal(str(sku_data['unit_price']))
            if new_price != sku.unit_price:
                price_history = PriceHistory(
                    sku_id=sku.id,
                    old_price=sku.unit_price,
                    new_price=new_price,
                    changed_by=changed_by
                )
                db.session.add(price_history)
                sku.unit_price = new_price
        
        # 更新其他字段
        if 'name' in sku_data:
            sku.name = sku_data['name']
        if 'supplier' in sku_data:
            sku.supplier = sku_data['supplier']
        if 'category' in sku_data:
            sku.category = sku_data['category']
        
        db.session.commit()
        
        return sku
    
    @staticmethod
    def find_by_id(sku_id: int) -> Optional[SKU]:
        """
        按ID查询SKU
        
        Args:
            sku_id: SKU ID
            
        Returns:
            SKU对象或None
        """
        return db.session.get(SKU, sku_id)
    
    @staticmethod
    def find_by_code(sku_code: str) -> Optional[SKU]:
        """
        按编码查询SKU
        
        Args:
            sku_code: SKU编码
            
        Returns:
            SKU对象或None
        """
        return SKU.query.filter_by(sku_code=sku_code).first()
    
    @staticmethod
    def search(keyword: str = None, supplier: str = None) -> List[SKU]:
        """
        搜索SKU
        
        Args:
            keyword: 搜索关键字（匹配编码或名称）
            supplier: 供应商筛选
            
        Returns:
            SKU列表
        """
        query = SKU.query
        
        if keyword:
            keyword_filter = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    SKU.sku_code.like(keyword_filter),
                    SKU.name.like(keyword_filter)
                )
            )
        
        if supplier:
            query = query.filter(SKU.supplier.like(f"%{supplier}%"))
        
        return query.order_by(SKU.sku_code).all()
    
    @staticmethod
    def get_all() -> List[SKU]:
        """
        获取所有SKU
        
        Returns:
            SKU列表
        """
        return SKU.query.order_by(SKU.sku_code).all()
    
    @staticmethod
    def delete(sku_id: int) -> bool:
        """
        删除SKU
        
        Args:
            sku_id: SKU ID
            
        Returns:
            是否删除成功
        """
        sku = SKURepository.find_by_id(sku_id)
        if not sku:
            return False
        
        db.session.delete(sku)
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_price_history(sku_id: int) -> List[PriceHistory]:
        """
        获取SKU的价格历史
        
        Args:
            sku_id: SKU ID
            
        Returns:
            价格历史列表
        """
        return PriceHistory.query.filter_by(sku_id=sku_id).order_by(PriceHistory.changed_at.desc()).all()
