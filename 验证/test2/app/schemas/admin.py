# app/schemas/admin.py
"""
管理员相关的Pydantic模式
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    LOCKED = "locked"
    DISABLED = "disabled"


class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"
    ADMIN = "admin"


class UserFilter(BaseModel):
    """用户筛选条件"""
    username: Optional[str] = Field(None, description="用户名（模糊搜索）")
    email: Optional[str] = Field(None, description="邮箱（模糊搜索）")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    is_locked: Optional[bool] = Field(None, description="是否锁定")
    role: Optional[UserRole] = Field(None, description="用户角色")
    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(20, ge=1, le=100, description="每页记录数")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_locked: Optional[bool] = Field(None, description="是否锁定")
    locked_reason: Optional[str] = Field(None, max_length=500, description="锁定原因")
    locked_until: Optional[datetime] = Field(None, description="锁定到期时间")


class UserResponse(BaseModel):
    """用户响应"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    is_active: bool = Field(..., description="是否启用")
    is_locked: bool = Field(..., description="是否锁定")
    locked_reason: Optional[str] = Field(None, description="锁定原因")
    locked_until: Optional[datetime] = Field(None, description="锁定到期时间")
    failed_login_attempts: int = Field(..., description="登录失败次数")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    conversation_count: int = Field(0, description="对话数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class UserListResponse(BaseModel):
    """用户列表响应"""
    success: bool = Field(True, description="是否成功")
    message: str = Field(..., description="消息")
    data: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总用户数")
    active_count: int = Field(..., description="活跃用户数")
    locked_count: int = Field(..., description="锁定用户数")


class SystemModelCreate(BaseModel):
    """创建系统模型请求"""
    model_name: str = Field(..., min_length=1, max_length=50, description="模型名称")
    model_provider: str = Field(..., min_length=1, max_length=50, description="模型提供商")
    model_type: str = Field("chat", pattern="^(chat|completion|embedding)$", description="模型类型")
    api_endpoint: str = Field(..., description="API端点")
    api_version: Optional[str] = Field(None, description="API版本")
    is_available: bool = Field(True, description="是否可用")
    is_default: bool = Field(False, description="是否默认模型")
    rate_limit_per_minute: int = Field(60, ge=1, description="每分钟请求限制")
    max_tokens: int = Field(4096, ge=1, description="最大token数")
    description: Optional[str] = Field(None, description="模型描述")


class SystemModelUpdate(BaseModel):
    """更新系统模型请求"""
    model_name: Optional[str] = Field(None, min_length=1, max_length=50, description="模型名称")
    model_provider: Optional[str] = Field(None, min_length=1, max_length=50, description="模型提供商")
    model_type: Optional[str] = Field(None, pattern="^(chat|completion|embedding)$", description="模型类型")
    api_endpoint: Optional[str] = Field(None, description="API端点")
    api_version: Optional[str] = Field(None, description="API版本")
    is_available: Optional[bool] = Field(None, description="是否可用")
    is_default: Optional[bool] = Field(None, description="是否默认模型")
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, description="每分钟请求限制")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大token数")
    description: Optional[str] = Field(None, description="模型描述")


class SystemStats(BaseModel):
    """系统统计"""
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    locked_users: int = Field(..., description="锁定用户数")
    total_conversations: int = Field(..., description="总对话数")
    total_messages: int = Field(..., description="总消息数")
    total_api_calls: int = Field(..., description="总API调用数")
    total_tokens_used: int = Field(..., description="总token使用量")
    system_uptime: float = Field(..., description="系统运行时间（小时）")
    avg_response_time: float = Field(..., description="平均响应时间（毫秒）")
    api_success_rate: float = Field(..., description="API成功率")


class DailyStats(BaseModel):
    """每日统计"""
    date: str = Field(..., description="日期")
    new_users: int = Field(..., description="新用户数")
    active_users: int = Field(..., description="活跃用户数")
    conversation_count: int = Field(..., description="对话数")
    message_count: int = Field(..., description="消息数")
    api_call_count: int = Field(..., description="API调用数")
    tokens_used: int = Field(..., description="token使用量")


class SystemHealth(BaseModel):
    """系统健康状态"""
    status: str = Field(..., description="状态（healthy/warning/critical）")
    database: bool = Field(..., description="数据库连接状态")
    cache: bool = Field(..., description="缓存连接状态")
    api_endpoints: Dict[str, bool] = Field(..., description="API端点状态")
    disk_usage: float = Field(..., description="磁盘使用率")
    memory_usage: float = Field(..., description="内存使用率")
    cpu_usage: float = Field(..., description="CPU使用率")
    last_check: datetime = Field(..., description="最后检查时间")


class ApiCallFilter(BaseModel):
    """API调用筛选条件"""
    user_id: Optional[int] = Field(None, description="用户ID")
    model_id: Optional[int] = Field(None, description="模型ID")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    is_success: Optional[bool] = Field(None, description="是否成功")
    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(50, ge=1, le=1000, description="每页记录数")


class AdminActionRequest(BaseModel):
    """管理员操作请求"""
    action: str = Field(..., description="操作类型")
    target_id: int = Field(..., description="目标ID")
    reason: Optional[str] = Field(None, max_length=500, description="操作原因")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="附加数据")
