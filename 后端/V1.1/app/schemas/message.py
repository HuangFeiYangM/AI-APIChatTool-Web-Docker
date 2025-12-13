# app/schemas/message.py
"""
消息相关的Pydantic模式
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageBase(BaseModel):
    """消息基础模式"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., min_length=1, max_length=16000, description="消息内容")
    tokens_used: int = Field(0, ge=0, description="使用的token数")
    model_id: Optional[int] = Field(None, description="使用的模型ID")


class MessageCreate(MessageBase):
    """创建消息请求"""
    conversation_id: int = Field(..., description="对话ID")


class MessageInDBBase(BaseModel):
    """数据库中的消息基础模式"""
    message_id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="对话ID")
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    tokens_used: int = Field(..., description="使用的token数")
    model_id: Optional[int] = Field(None, description="使用的模型ID")
    is_deleted: bool = Field(False, description="是否删除")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class MessageResponse(MessageInDBBase):
    """消息响应"""
    pass


class MessageUpdate(BaseModel):
    """更新消息请求"""
    content: Optional[str] = Field(None, min_length=1, max_length=16000, description="消息内容")
    
    @validator('content')
    def validate_content(cls, v):
        """验证内容"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("消息内容不能为空")
        return v


class MessageListResponse(BaseModel):
    """消息列表响应"""
    messages: list[MessageResponse] = Field(..., description="消息列表")
    total: int = Field(..., description="总消息数")
    user_messages: int = Field(..., description="用户消息数")
    assistant_messages: int = Field(..., description="助手消息数")
    total_tokens: int = Field(..., description="总token数")


class MessageSearchRequest(BaseModel):
    """搜索消息请求"""
    keyword: Optional[str] = Field(None, description="关键词")
    role: Optional[str] = Field(None, pattern="^(user|assistant|system)$", description="角色")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(20, ge=1, le=100, description="每页记录数")


class MessageStats(BaseModel):
    """消息统计"""
    total_messages: int = Field(..., description="总消息数")
    user_messages: int = Field(..., description="用户消息数")
    assistant_messages: int = Field(..., description="助手消息数")
    total_tokens: int = Field(..., description="总token数")


class ChatCompletionRequest(BaseModel):
    """聊天完成请求（用于模型聊天）"""
    message: str = Field(..., min_length=1, max_length=4000, description="用户消息")
    conversation_id: Optional[int] = Field(None, description="对话ID（为空则创建新对话）")
    model: Optional[str] = Field(None, description="模型名称")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(500, ge=1, le=8000, description="最大token数")
    stream: bool = Field(False, description="是否流式输出")


# app/schemas/message.py - 在文件末尾添加

class MessageCreateRequest(BaseModel):
    """创建消息的API请求模型（适配现有API接口）"""
    content: str = Field(..., min_length=1, max_length=16000, description="消息内容")
    role: str = Field("user", description="消息角色: user, assistant, system")
    model_id: Optional[int] = Field(None, description="使用的模型ID（当role=assistant时必需）")
    tokens_used: Optional[int] = Field(0, ge=0, description="使用的token数")
    
    @validator('role')
    def validate_role(cls, v):
        """验证角色"""
        v = v.lower()
        if v not in ["user", "assistant", "system"]:
            raise ValueError("角色必须是 user, assistant 或 system")
        return v
    
    @validator('model_id')
    def validate_model_id(cls, v, values):
        """验证model_id"""
        role = values.get('role', 'user')
        if role == 'assistant' and v is None:
            raise ValueError("assistant消息必须提供model_id")
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """验证内容"""
        if not v or not v.strip():
            raise ValueError("消息内容不能为空")
        return v.strip()
