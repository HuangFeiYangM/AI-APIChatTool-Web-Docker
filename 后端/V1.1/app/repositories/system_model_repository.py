# app/repositories/system_model_repository.py
"""
系统模型配置Repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.system_model import SystemModel
from app.repositories.base import BaseRepository


class SystemModelRepository(BaseRepository[SystemModel]):
    """系统模型配置Repository"""
    
    def __init__(self, db: Session):
        super().__init__(SystemModel, db)
    
    def get_by_name(self, model_name: str) -> Optional[SystemModel]:
        """
        根据模型名称获取模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置实例或None
        """
        return self.db.query(SystemModel).filter(
            SystemModel.model_name == model_name
        ).first()
    
    def get_by_provider(self, provider: str) -> List[SystemModel]:
        """
        根据提供商获取模型配置
        
        Args:
            provider: 模型提供商
            
        Returns:
            模型配置列表
        """
        return self.db.query(SystemModel).filter(
            SystemModel.model_provider == provider
        ).all()
    
    def get_available_models(self) -> List[SystemModel]:
        """
        获取所有可用的模型
        
        Returns:
            可用模型列表
        """
        return self.db.query(SystemModel).filter(
            SystemModel.is_available == True
        ).order_by(SystemModel.model_name).all()
    
    def get_default_model(self) -> Optional[SystemModel]:
        """
        获取默认模型
        
        Returns:
            默认模型或None
        """
        return self.db.query(SystemModel).filter(
            SystemModel.is_default == True,
            SystemModel.is_available == True
        ).first()
    
    def get_chat_models(self) -> List[SystemModel]:
        """
        获取聊天类型的模型
        
        Returns:
            聊天模型列表
        """
        return self.db.query(SystemModel).filter(
            SystemModel.model_type == 'chat',
            SystemModel.is_available == True
        ).order_by(SystemModel.model_name).all()
    
    def update_model_availability(self, model_id: int, is_available: bool) -> bool:
        """
        更新模型可用性
        
        Args:
            model_id: 模型ID
            is_available: 是否可用
            
        Returns:
            是否更新成功
        """
        model = self.get(model_id)
        if model:
            model.is_available = is_available
            self.db.commit()
            return True
        return False
    
    def search_models(
        self,
        name_keyword: Optional[str] = None,
        provider: Optional[str] = None,
        model_type: Optional[str] = None,
        is_available: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SystemModel]:
        """
        搜索模型
        
        Args:
            name_keyword: 名称关键词
            provider: 提供商
            model_type: 模型类型
            is_available: 是否可用
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            模型列表
        """
        query = self.db.query(SystemModel)
        
        if name_keyword:
            query = query.filter(SystemModel.model_name.ilike(f"%{name_keyword}%"))
        
        if provider:
            query = query.filter(SystemModel.model_provider == provider)
        
        if model_type:
            query = query.filter(SystemModel.model_type == model_type)
        
        if is_available is not None:
            query = query.filter(SystemModel.is_available == is_available)
        
        query = query.order_by(
            SystemModel.is_default.desc(),
            SystemModel.model_provider,
            SystemModel.model_name
        )
        
        return query.offset(skip).limit(limit).all()
    
    def get_model_stats(self) -> Dict[str, Any]:
        """
        获取模型统计信息
        
        Returns:
            统计信息字典
        """
        from sqlalchemy import func
        
        total = self.count()
        
        available = self.db.query(SystemModel).filter(
            SystemModel.is_available == True
        ).count()
        
        providers = self.db.query(
            SystemModel.model_provider,
            func.count(SystemModel.model_id).label('count')
        ).group_by(SystemModel.model_provider).all()
        
        provider_stats = {provider: count for provider, count in providers}
        
        return {
            "total": total,
            "available": available,
            "providers": provider_stats
        }
