# app/services/model_service.py
"""
模型配置服务 - 对应详细设计中的程序6：模型配置管理
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.repositories.system_model_repository import SystemModelRepository
from app.repositories.user_model_config_repository import UserModelConfigRepository

logger = logging.getLogger(__name__)


class ModelService:
    """模型配置管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.system_model_repo = SystemModelRepository(db)
        self.user_config_repo = UserModelConfigRepository(db)
    
    def get_available_models_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户可用的模型列表"""
        # 获取所有系统模型
        system_models = self.system_model_repo.get_available_models()
        
        result = []
        for model in system_models:
            model_info = {
                "model_id": model.model_id,
                "model_name": model.model_name,
                "model_provider": model.model_provider,
                "model_type": model.model_type,
                "description": model.description,
                "api_endpoint": model.api_endpoint,
                "max_tokens": model.max_tokens,
                "is_default": model.is_default,
                "is_available": model.is_available,
            }
            
            # 获取用户对该模型的配置
            user_config = self.user_config_repo.get_user_config_for_model(user_id, model.model_id)
            if user_config:
                model_info.update({
                    "is_enabled": user_config.is_enabled,
                    "has_api_key": bool(user_config.api_key or user_config.api_key_encrypted),
                    "priority": user_config.priority,
                    "last_used_at": user_config.last_used_at
                })
            else:
                model_info.update({
                    "is_enabled": False,
                    "has_api_key": False,
                    "priority": 0,
                    "last_used_at": None
                })
            
            result.append(model_info)
        
        return result
    
    def update_user_model_config(
        self, 
        user_id: int, 
        model_id: int, 
        config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新用户模型配置"""
        # 检查模型是否存在
        system_model = self.system_model_repo.get_by_id(model_id)
        if not system_model:
            return {
                "success": False,
                "message": f"模型ID {model_id} 不存在"
            }
        
        # 获取或创建用户配置
        user_config = self.user_config_repo.get_user_config_for_model(user_id, model_id)
        
        update_data = {}
        if "api_key" in config_data:
            update_data["api_key"] = config_data["api_key"]
        
        if "custom_endpoint" in config_data:
            update_data["custom_endpoint"] = config_data["custom_endpoint"]
        
        if "is_enabled" in config_data:
            update_data["is_enabled"] = config_data["is_enabled"]
        
        if "priority" in config_data:
            update_data["priority"] = config_data["priority"]
        
        if "max_tokens" in config_data:
            update_data["max_tokens"] = config_data["max_tokens"]
        
        if "temperature" in config_data:
            update_data["temperature"] = config_data["temperature"]
        
        if user_config:
            # 更新现有配置
            for key, value in update_data.items():
                setattr(user_config, key, value)
            self.db.commit()
            message = "配置更新成功"
        else:
            # 创建新配置
            create_data = {
                "user_id": user_id,
                "model_id": model_id,
                **update_data
            }
            user_config = self.user_config_repo.create(create_data)
            message = "配置创建成功"
        
        return {
            "success": True,
            "message": message,
            "config_id": user_config.config_id
        }
    
    def delete_user_model_config(self, user_id: int, model_id: int) -> Dict[str, Any]:
        """删除用户模型配置"""
        user_config = self.user_config_repo.get_user_config_for_model(user_id, model_id)
        
        if not user_config:
            return {
                "success": False,
                "message": "配置不存在"
            }
        
        self.user_config_repo.delete(user_config.config_id)
        
        return {
            "success": True,
            "message": "配置删除成功"
        }
    
    
    def get_user_model_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有模型配置（补充版本）"""
        configs = self.user_config_repo.get_user_configs(user_id)
        
        result = []
        for config in configs:
            config_dict = {
                "config_id": config.config_id,
                "user_id": config.user_id,
                "model_id": config.model_id,
                "model_name": config.system_model.model_name if config.system_model else None,
                "is_enabled": config.is_enabled,
                "has_api_key": bool(config.api_key or config.api_key_encrypted),
                "custom_endpoint": config.custom_endpoint,
                "max_tokens": config.max_tokens,
                "temperature": float(config.temperature) if config.temperature else None,
                "priority": config.priority,
                "last_used_at": config.last_used_at,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
            result.append(config_dict)
        
        return result
    
    def get_user_model_config(self, user_id: int, model_id: int) -> Optional[Dict[str, Any]]:
        """获取用户的特定模型配置"""
        config = self.user_config_repo.get_user_config_for_model(user_id, model_id)
        
        if not config:
            return None
        
        # 获取模型信息
        system_model = self.system_model_repo.get_by_id(model_id)
        
        return {
            "config_id": config.config_id,
            "user_id": config.user_id,
            "model_id": config.model_id,
            "model_name": system_model.model_name if system_model else None,
            "model_provider": system_model.model_provider if system_model else None,
            "is_enabled": config.is_enabled,
            "has_api_key": bool(config.api_key or config.api_key_encrypted),
            "custom_endpoint": config.custom_endpoint,
            "max_tokens": config.max_tokens,
            "temperature": float(config.temperature) if config.temperature else None,
            "priority": config.priority,
            "last_used_at": config.last_used_at,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
    
    def enable_user_model(self, user_id: int, model_id: int) -> Dict[str, Any]:
        """启用用户的模型"""
        success = self.user_config_repo.enable_user_model(user_id, model_id)
        
        if success:
            return {
                "success": True,
                "message": f"已启用模型 {model_id}"
            }
        else:
            return {
                "success": False,
                "message": f"启用模型失败"
            }
    
    def disable_user_model(self, user_id: int, model_id: int) -> Dict[str, Any]:
        """禁用用户的模型"""
        success = self.user_config_repo.disable_user_model(user_id, model_id)
        
        if success:
            return {
                "success": True,
                "message": f"已禁用模型 {model_id}"
            }
        else:
            return {
                "success": False,
                "message": f"禁用模型失败"
            }
            
    # 在此处添加新的方法
    def bulk_update_models(self, user_id: int, model_ids: List[int], 
                        is_enabled: Optional[bool] = None,
                        priority: Optional[int] = None) -> Dict[str, Any]:
        """批量更新模型配置"""
        results = []
        
        for model_id in model_ids:
            if is_enabled is not None:
                if is_enabled:
                    self.user_config_repo.enable_user_model(user_id, model_id)
                else:
                    self.user_config_repo.disable_user_model(user_id, model_id)
            
            if priority is not None:
                self.user_config_repo.update_model_priority(user_id, model_id, priority)
            
            results.append(model_id)
        
        return {
            "success": True,
            "message": f"批量更新成功，共处理 {len(results)} 个模型",
            "data": results
        }
    
    def validate_api_key(self, model_id: int, api_key: str) -> Dict[str, Any]:
        """验证API密钥格式（基础验证）"""
        # 基础格式验证
        if not api_key or len(api_key) < 10:
            return {
                "valid": False,
                "message": "API密钥格式不正确"
            }
        
        # 根据不同提供商进行格式验证
        system_model = self.system_model_repo.get_by_id(model_id)
        if not system_model:
            return {
                "valid": False,
                "message": "模型不存在"
            }
        
        provider = system_model.model_provider.lower()
        
        if provider == "openai":
            if not api_key.startswith("sk-"):
                return {
                    "valid": False,
                    "message": "OpenAI API密钥格式应为 sk- 开头"
                }
        elif provider == "deepseek":
            if not api_key.startswith("sk-"):
                return {
                    "valid": False,
                    "message": "DeepSeek API密钥格式应为 sk- 开头"
                }
        
        return {
            "valid": True,
            "message": "API密钥格式正确"
        }