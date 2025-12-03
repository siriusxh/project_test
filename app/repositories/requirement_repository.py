"""
需求数据访问层
"""
from typing import List, Optional

from app import db
from app.models.requirement import Requirement, Configuration, ConfigurationItem


class RequirementRepository:
    """需求数据访问仓库"""
    
    @staticmethod
    def create(requirement_data: dict) -> Requirement:
        """
        创建需求
        
        Args:
            requirement_data: 需求数据字典
            
        Returns:
            创建的需求对象
            
        Raises:
            ValueError: 如果需求编码已存在
        """
        # 检查需求编码是否已存在
        existing = RequirementRepository.find_by_code(requirement_data['requirement_code'])
        if existing:
            raise ValueError(f"需求编码 {requirement_data['requirement_code']} 已存在")
        
        requirement = Requirement(
            requirement_code=requirement_data['requirement_code'],
            jira_case=requirement_data['jira_case'],
            description=requirement_data.get('description'),
            status=requirement_data.get('status', 'draft')
        )
        
        db.session.add(requirement)
        db.session.commit()
        
        return requirement
    
    @staticmethod
    def update(requirement_id: int, requirement_data: dict) -> Requirement:
        """
        更新需求
        
        Args:
            requirement_id: 需求ID
            requirement_data: 更新的数据
            
        Returns:
            更新后的需求对象
            
        Raises:
            ValueError: 如果需求不存在或编码重复
        """
        requirement = RequirementRepository.find_by_id(requirement_id)
        if not requirement:
            raise ValueError(f"需求ID {requirement_id} 不存在")
        
        # 如果修改了需求编码，检查新编码是否已存在
        if 'requirement_code' in requirement_data and requirement_data['requirement_code'] != requirement.requirement_code:
            existing = RequirementRepository.find_by_code(requirement_data['requirement_code'])
            if existing:
                raise ValueError(f"需求编码 {requirement_data['requirement_code']} 已存在")
            requirement.requirement_code = requirement_data['requirement_code']
        
        # 更新其他字段
        if 'jira_case' in requirement_data:
            requirement.jira_case = requirement_data['jira_case']
        if 'description' in requirement_data:
            requirement.description = requirement_data['description']
        if 'status' in requirement_data:
            requirement.status = requirement_data['status']
        
        db.session.commit()
        
        return requirement
    
    @staticmethod
    def find_by_id(requirement_id: int) -> Optional[Requirement]:
        """
        按ID查询需求
        
        Args:
            requirement_id: 需求ID
            
        Returns:
            需求对象或None
        """
        return db.session.get(Requirement, requirement_id)
    
    @staticmethod
    def find_by_code(requirement_code: str) -> Optional[Requirement]:
        """
        按编码查询需求
        
        Args:
            requirement_code: 需求编码
            
        Returns:
            需求对象或None
        """
        return Requirement.query.filter_by(requirement_code=requirement_code).first()
    
    @staticmethod
    def find_by_jira_case(jira_case: str) -> List[Requirement]:
        """
        按Jira Case查询需求
        
        Args:
            jira_case: Jira Case编号
            
        Returns:
            需求列表
        """
        return Requirement.query.filter_by(jira_case=jira_case).all()
    
    @staticmethod
    def get_all_with_filters(filters: dict = None) -> List[Requirement]:
        """
        带筛选条件查询需求
        
        Args:
            filters: 筛选条件字典
            
        Returns:
            需求列表
        """
        query = Requirement.query
        
        if filters:
            if 'jira_case' in filters:
                query = query.filter(Requirement.jira_case.like(f"%{filters['jira_case']}%"))
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
            if 'requirement_code' in filters:
                query = query.filter(Requirement.requirement_code.like(f"%{filters['requirement_code']}%"))
        
        return query.order_by(Requirement.created_at.desc()).all()
    
    @staticmethod
    def delete(requirement_id: int) -> bool:
        """
        删除需求
        
        Args:
            requirement_id: 需求ID
            
        Returns:
            是否删除成功
        """
        requirement = RequirementRepository.find_by_id(requirement_id)
        if not requirement:
            return False
        
        db.session.delete(requirement)
        db.session.commit()
        
        return True
