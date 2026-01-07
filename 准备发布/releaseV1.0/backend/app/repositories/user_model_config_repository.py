# app/repositories/user_model_config_repository.py
"""
用户模型配置Repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime

from app.models.user_model_config import UserModelConfig
from app.repositories.base import BaseRepository


class UserModelConfigRepository(BaseRepository[UserModelConfig]):
    """用户模型配置Repository"""
    
    def __init__(self, db: Session):
        super().__init__(UserModelConfig, db)
    
    def get_user_config_for_model(
        self,
        user_id: int,
        model_id: int
    ) -> Optional[UserModelConfig]:
        """
        获取用户对特定模型的配置
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            
        Returns:
            用户模型配置或None
        """
        return self.db.query(UserModelConfig).filter(
            UserModelConfig.user_id == user_id,
            UserModelConfig.model_id == model_id
        ).first()
    
    def get_user_configs(self, user_id: int) -> List[UserModelConfig]:
        """
        获取用户的所有模型配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户模型配置列表
        """
        return self.db.query(UserModelConfig).filter(
            UserModelConfig.user_id == user_id
        ).options(
            joinedload(UserModelConfig.system_model)
        ).order_by(UserModelConfig.priority.desc()).all()
    
    def get_enabled_user_configs(self, user_id: int) -> List[UserModelConfig]:
        """
        获取用户启用的模型配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            启用的用户模型配置列表
        """
        return self.db.query(UserModelConfig).filter(
            UserModelConfig.user_id == user_id,
            UserModelConfig.is_enabled == True
        ).options(
            joinedload(UserModelConfig.system_model)
        ).order_by(UserModelConfig.priority.desc()).all()
    
    def update_last_used_time(self, config_id: int) -> bool:
        """
        更新最后使用时间
        
        Args:
            config_id: 配置ID
            
        Returns:
            是否更新成功
        """
        config = self.get_by_id(config_id)
        if config:
            config.last_used_at = datetime.now()
            self.db.commit()
            return True
        return False
    
    def enable_user_model(self, user_id: int, model_id: int) -> bool:
        """
        启用用户的模型
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            
        Returns:
            是否启用成功
        """
        config = self.get_user_config_for_model(user_id, model_id)
        if config:
            config.is_enabled = True
            self.db.commit()
            return True
        
        # 如果配置不存在，创建新的配置
        config_data = {
            "user_id": user_id,
            "model_id": model_id,
            "is_enabled": True
        }
        self.create(config_data)
        return True
    
    def disable_user_model(self, user_id: int, model_id: int) -> bool:
        """
        禁用用户的模型
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            
        Returns:
            是否禁用成功
        """
        config = self.get_user_config_for_model(user_id, model_id)
        if config:
            config.is_enabled = False
            self.db.commit()
            return True
        return False
    
    def update_model_priority(self, user_id: int, model_id: int, priority: int) -> bool:
        """
        更新模型优先级
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            priority: 优先级（数值越大优先级越高）
            
        Returns:
            是否更新成功
        """
        config = self.get_user_config_for_model(user_id, model_id)
        if config:
            config.priority = priority
            self.db.commit()
            return True
        return False
    
    def get_user_preferred_models(self, user_id: int) -> List[UserModelConfig]:
        """
        获取用户偏好的模型（按优先级排序）
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户模型配置列表（按优先级降序）
        """
        return self.db.query(UserModelConfig).filter(
            UserModelConfig.user_id == user_id,
            UserModelConfig.is_enabled == True
        ).order_by(UserModelConfig.priority.desc()).all()
    
    def update_api_key(
        self,
        user_id: int,
        model_id: int,
        api_key: Optional[str] = None
    ) -> bool:
        """
        更新用户的API密钥
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            api_key: API密钥（None表示清除密钥）
            
        Returns:
            是否更新成功
        """
        config = self.get_user_config_for_model(user_id, model_id)
        if config:
            config.api_key = api_key
            self.db.commit()
            return True
        return False
