# app/schemas/model.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    WENXIN = "wenxin"


class ModelType(str, Enum):
    """模型类型枚举"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"


# 聊天请求
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="用户输入")
    model: str = Field(..., description="模型标识符")
    conversation_id: Optional[int] = Field(None, description="对话ID")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度")
    max_tokens: Optional[int] = Field(2000, gt=0, le=8192, description="最大token数")
    stream: Optional[bool] = Field(False, description="是否流式输出")


# 聊天响应
class ChatResponse(BaseModel):
    response: str = Field(..., description="模型回复")
    conversation_id: int = Field(..., description="对话ID")
    model_used: str = Field(..., description="使用的模型")
    tokens_used: Optional[int] = Field(None, description="消耗的token数")
    processing_time_ms: Optional[int] = Field(None, description="处理时间(ms)")


# 模型配置更新请求
class ModelConfigUpdateRequest(BaseModel):
    model_id: int = Field(..., description="模型ID")
    api_key: Optional[str] = Field(None, min_length=10, max_length=500, description="API密钥")
    custom_endpoint: Optional[str] = Field(None, description="自定义端点")
    is_enabled: bool = Field(True, description="是否启用")
    priority: int = Field(0, ge=0, le=100, description="优先级")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="默认温度")
    max_tokens: Optional[int] = Field(None, gt=0, le=32768, description="默认最大token数")


# 系统模型输出
class SystemModelOut(BaseModel):
    model_id: int
    model_name: str
    model_provider: str
    model_type: str
    api_endpoint: str
    api_version: Optional[str]
    is_available: bool
    is_default: bool
    rate_limit_per_minute: int
    max_tokens: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 用户模型配置输出
class UserModelConfigOut(BaseModel):
    config_id: int
    user_id: int
    model_id: int
    model_name: Optional[str] = None  # 通过关系获取
    is_enabled: bool
    custom_endpoint: Optional[str]
    max_tokens: Optional[int]
    temperature: Optional[float]
    priority: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# API调用统计
class APIUsageStats(BaseModel):
    total_calls: int
    total_request_tokens: int
    total_response_tokens: int
    total_tokens: int
    avg_response_time: float
    success_rate: float


# 每日使用统计
class DailyUsageStats(BaseModel):
    date: str
    call_count: int
    total_tokens: int
    success_rate: float


# 在 app/schemas/model.py 末尾添加

class UserModelConfigCreate(BaseModel):
    """创建用户模型配置请求"""
    model_id: int = Field(..., description="模型ID")
    api_key: Optional[str] = Field(None, min_length=10, max_length=500, description="API密钥")
    custom_endpoint: Optional[str] = Field(None, description="自定义端点")
    is_enabled: bool = Field(True, description="是否启用")
    priority: int = Field(0, ge=0, le=100, description="优先级")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="默认温度")
    max_tokens: Optional[int] = Field(None, gt=0, le=32768, description="默认最大token数")


class UserModelConfigUpdate(BaseModel):
    """更新用户模型配置请求"""
    api_key: Optional[str] = Field(None, min_length=10, max_length=500, description="API密钥")
    custom_endpoint: Optional[str] = Field(None, description="自定义端点")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    priority: Optional[int] = Field(None, ge=0, le=100, description="优先级")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="默认温度")
    max_tokens: Optional[int] = Field(None, gt=0, le=32768, description="默认最大token数")


class UserModelConfigListResponse(BaseModel):
    """用户模型配置列表响应"""
    success: bool = Field(True, description="是否成功")
    message: str = Field(..., description="消息")
    data: List[UserModelConfigOut] = Field(..., description="配置列表")
    total: int = Field(..., description="总数")


class BulkConfigUpdateRequest(BaseModel):
    """批量更新配置请求"""
    model_ids: List[int] = Field(..., description="模型ID列表")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    priority: Optional[int] = Field(None, ge=0, le=100, description="优先级")
    
    @validator('model_ids')
    def validate_model_ids(cls, v):
        if not v:
            raise ValueError("模型ID列表不能为空")
        if len(v) > 20:
            raise ValueError("一次最多操作20个模型")
        return v