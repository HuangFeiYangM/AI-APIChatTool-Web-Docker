# app/schemas/auth.py
"""
认证相关的Pydantic模式
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


# app/schemas/auth.py（补充）
class Token(BaseModel):
    """JWT令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    # 可选添加刷新令牌
    refresh_token: Optional[str] = Field(None, description="刷新令牌")



class TokenPayload(BaseModel):
    """JWT令牌负载模式"""
    sub: Optional[int] = Field(None, description="用户ID")
    exp: Optional[int] = Field(None, description="过期时间")
    

class LoginRequest(BaseModel):
    """登录请求模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "testuser",
                "password": "password123"
            }
        }


class RegisterRequest(BaseModel):
    """注册请求模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    confirm_password: str = Field(..., min_length=6, max_length=100, description="确认密码")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        # 只允许字母、数字、下划线
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证两次密码是否一致"""
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "newuser",
                "password": "password123",
                "confirm_password": "password123",
                "email": "user@example.com"
            }
        }


class ChangePasswordRequest(BaseModel):
    """修改密码请求模式"""
    current_password: str = Field(..., min_length=6, max_length=100, description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=100, description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证新密码是否一致"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        }


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    
    @validator('username')
    def validate_at_least_one(cls, v, values):
        """至少提供用户名或邮箱之一"""
        if v is None and values.get('email') is None:
            raise ValueError('必须提供用户名或邮箱')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "testuser",
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """重置密码请求模式"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=100, description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证密码是否一致"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('密码不匹配')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_123",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        }
