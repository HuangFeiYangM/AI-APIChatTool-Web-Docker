from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """创建用户时使用的数据模式"""
    user: str  # 用户名
    password: str
    deepseek_bool: Optional[bool] = False
    deepseek_api: Optional[str] = None

class UserResponse(BaseModel):
    """返回用户信息时的数据模式"""
    user: str
    deepseek_bool: bool
    deepseek_api: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """用户登录数据模式"""
    user: str
    password: str
