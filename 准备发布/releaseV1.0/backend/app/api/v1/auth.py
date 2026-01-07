# app/api/v1/auth.py
"""
用户认证API路由
对应详细设计中的程序1（注册）和程序2（登录）
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status,Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.schemas.auth import (
    LoginRequest, RegisterRequest, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.auth_service import AuthService, get_auth_service
from app.dependencies import get_current_user  # 添加这行
from app.exceptions import (
    AuthenticationError, UserAlreadyExistsError,
    UserNotFoundError, InvalidPasswordError,
    AccountLockedError, InvalidTokenError
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()


@router.post("/login", response_model=Dict[str, Any])
async def login(
    login_data: LoginRequest,
    request: Request,  # 添加Request参数
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录
    - 验证用户名密码
    - 生成JWT令牌
    """
    try:
        
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        result = auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password,
            ip_address=client_ip,
            user_agent=user_agent
        )
        return {
            "success": True,
            "message": "登录成功",
            "data": result
        }
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"登录异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/register", response_model=Dict[str, Any])
async def register(
    register_data: RegisterRequest,
    request: Request,  # 添加Request参数
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户注册
    - 检查用户名/邮箱是否已存在
    - 创建新用户
    - 自动登录并返回令牌
    """
    try:
        
        # 直接调用，不要传递额外的参数
        result = auth_service.register_user(register_data)
        
        
        
        return {
            "success": True,
            "message": "注册成功",
            "data": result
        }
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"注册异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登出
    - 客户端应删除令牌
    - 服务端可记录日志
    """
    try:
        token = credentials.credentials
        success = auth_service.logout(token)
        return {
            "success": success,
            "message": "登出成功" if success else "登出处理失败"
        }
    except Exception as e:
        logger.error(f"登出异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(
    
    auth_service: AuthService = Depends(get_auth_service),  # 直接使用 auth_service 依赖
    credentials: HTTPAuthorizationCredentials = Depends(security)  # 提取 token
):
    """
    获取当前登录用户信息
    - 需要有效的JWT令牌
    """
    try:
        token = credentials.credentials
        user_info = auth_service.get_user_by_token(token)
        return {
            "success": True,
            "data": user_info
        }
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取用户信息异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/change-password", response_model=Dict[str, Any])
async def change_password(
    password_data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    修改密码
    - 需要有效的JWT令牌
    - 验证当前密码
    - 更新为新密码
    """
    try:
        token = credentials.credentials
        payload = auth_service.validate_token(token)
        
        if not payload["valid"]:
            raise InvalidTokenError("无效的令牌")
        
        success = auth_service.change_password(
            user_id=payload["user_id"],
            password_data=password_data
        )
        
        return {
            "success": success,
            "message": "密码修改成功" if success else "密码修改失败"
        }
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except InvalidPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"修改密码异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )


@router.post("/refresh-token", response_model=Dict[str, Any])
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    刷新访问令牌
    - 使用旧令牌获取新令牌
    """
    try:
        token = credentials.credentials
        result = auth_service.refresh_token(token)
        
        return {
            "success": True,
            "data": result
        }
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"刷新令牌异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )


@router.post("/forgot-password", response_model=Dict[str, Any])
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    忘记密码 - 请求重置
    - 发送重置链接到邮箱（实际开发中）
    - 这里只返回重置令牌用于演示
    """
    try:
        # 在实际应用中，这里会：
        # 1. 验证用户存在
        # 2. 生成重置令牌
        # 3. 发送重置链接到用户邮箱
        
        # 示例：直接返回提示
        return {
            "success": True,
            "message": "重置链接已发送到您的邮箱（演示）",
            "data": {
                "instruction": "请检查您的邮箱，点击重置链接"
            }
        }
        
    except Exception as e:
        logger.error(f"忘记密码处理异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置密码请求失败"
        )


@router.post("/reset-password", response_model=Dict[str, Any])
async def reset_password(
    reset_data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    重置密码
    - 验证重置令牌
    - 更新密码
    """
    try:
        # 在实际应用中，这里会验证重置令牌并更新密码
        # 示例：模拟成功
        return {
            "success": True,
            "message": "密码重置成功（演示）"
        }
        
    except Exception as e:
        logger.error(f"重置密码异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置失败"
        )


@router.get("/validate-token", response_model=Dict[str, Any])
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    验证令牌有效性
    """
    try:
        token = credentials.credentials
        result = auth_service.validate_token(token)
        
        return {
            "success": True,
            "data": result
        }
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"验证令牌异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌验证失败"
        )



# 新增API：获取登录尝试记录
@router.get("/login-attempts/{username}", response_model=Dict[str, Any])
async def get_login_attempts(
    username: str,
    auth_service: AuthService = Depends(get_auth_service),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    获取用户登录尝试记录（需要管理员权限）
    """
    try:
        token = credentials.credentials
        payload = auth_service.validate_token(token)
        
        # 检查权限（这里简化为检查是否是管理员，您可以根据需要实现更复杂的权限检查）
        # 实际应用中，您可能需要检查用户角色
        user_info = auth_service.get_user_by_token(token)
        
        # 只有管理员或用户自己可以查看登录记录
        if user_info["username"] != username and user_info["username"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此用户的登录记录"
            )
        
        attempts = auth_service.get_login_attempts_by_username(username)
        
        return {
            "success": True,
            "data": attempts,
            "count": len(attempts)
        }
        
    except Exception as e:
        logger.error(f"获取登录尝试记录异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取登录尝试记录失败"
        )