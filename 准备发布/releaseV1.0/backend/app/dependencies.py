# app/dependencies.py
"""FastAPI依赖项"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.services.auth_service import AuthService, get_auth_service

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """获取当前认证用户的依赖项"""
    try:
        token = credentials.credentials
        result = auth_service.validate_token(token)
        
        if not result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": result["user_id"],
            "username": result["username"],
            "valid": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """获取当前活跃用户（已验证且账户正常）"""
    return current_user


def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """获取管理员用户（需要管理员权限）"""
    if current_user["username"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


# 修复：简化 get_model_router_service，移除类型注解
def get_model_router_service(db: Session = Depends(get_db)):
    """获取模型路由服务的依赖函数"""
    try:
        from app.services.model_router import ModelRouterService
        return ModelRouterService(db)
    except Exception as e:
        logger.error(f"获取模型路由服务失败: {e}")
        raise
