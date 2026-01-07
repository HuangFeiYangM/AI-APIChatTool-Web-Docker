# app/services/__init__.py
"""
服务层模块
提供所有业务服务
"""

# 导入所有服务类
from .auth_service import AuthService, get_auth_service
from .user_service import UserService
from .conversation_service import ConversationService
from .model_router import ModelRouterService, get_model_router_service
from .model_service import ModelService
from .message_service import MessageService, get_message_service

# 可选：如果有其他服务，继续导入

__all__ = [
    "AuthService",
    "get_auth_service",
    "UserService",
    "ConversationService", 
    "ModelRouterService",
    "get_model_router_service",
    "ModelService",
    "get_message_service"
]
