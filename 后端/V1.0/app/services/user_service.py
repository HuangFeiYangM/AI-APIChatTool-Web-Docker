# app/services/user_service.py
"""
用户服务
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """获取用户资料"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {}
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at
        }


def get_user_service(db: Session):
    """获取用户服务实例"""
    return UserService(db)
