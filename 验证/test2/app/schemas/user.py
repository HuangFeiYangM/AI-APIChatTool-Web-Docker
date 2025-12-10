# app/schemas/user.py
"""
用户相关的Pydantic模式
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    
    
class UserCreate(UserBase):
    """创建用户模式"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    

class UserUpdate(BaseModel):
    """更新用户模式"""
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    is_active: Optional[bool] = Field(None, description="是否启用")
    
    
class UserInDB(UserBase):
    """数据库用户模式"""
    user_id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否启用")
    is_locked: bool = Field(..., description="是否锁定")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True  # 兼容SQLAlchemy模型
        

class UserPublic(UserBase):
    """公开用户模式（不包含敏感信息）"""
    user_id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True
        

class UserStats(BaseModel):
    """用户统计信息模式"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    conversation_count: int = Field(0, description="对话数量")
    message_count: int = Field(0, description="消息数量")
    total_tokens: int = Field(0, description="总token数")
    last_active: Optional[datetime] = Field(None, description="最后活跃时间")
    

class UserSearchParams(BaseModel):
    """用户搜索参数模式"""
    username: Optional[str] = Field(None, description="用户名关键词")
    email: Optional[str] = Field(None, description="邮箱关键词")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    is_locked: Optional[bool] = Field(None, description="是否锁定")
    skip: int = Field(default=0, ge=0, description="跳过的记录数")
    limit: int = Field(default=100, ge=1, le=1000, description="返回的最大记录数")
    

class LoginAttemptCreate(BaseModel):
    """创建登录尝试记录模式"""
    username: str = Field(..., description="用户名")
    ip_address: str = Field(..., description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    is_success: bool = Field(..., description="是否成功")
