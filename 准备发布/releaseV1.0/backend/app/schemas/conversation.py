# app/schemas/conversation.py
"""
对话相关的Pydantic模式
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.schemas.message import MessageResponse


class ConversationBase(BaseModel):
    """对话基础模式"""
    title: Optional[str] = Field(None, max_length=200, description="对话标题")
    model_id: int = Field(..., description="使用的模型ID")


class ConversationCreate(ConversationBase):
    """创建对话请求"""
    title: Optional[str] = Field(None, max_length=200, description="对话标题")
    model_id: int = Field(..., description="使用的模型ID")
    
    @validator('title')
    def set_default_title(cls, v):
        """如果标题为空，设置为默认值"""
        if v is None or v.strip() == "":
            return "新对话"
        return v


class ConversationUpdate(BaseModel):
    """更新对话请求"""
    title: Optional[str] = Field(None, max_length=200, description="对话标题")
    is_archived: Optional[bool] = Field(None, description="是否归档")
    
    @validator('title')
    def validate_title(cls, v):
        """验证标题"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("标题不能为空字符串")
        return v


class ConversationInDBBase(BaseModel):
    """数据库中的对话基础模式"""
    conversation_id: int = Field(..., description="对话ID")
    user_id: int = Field(..., description="用户ID")
    title: str = Field(..., description="对话标题")
    model_id: int = Field(..., description="使用的模型ID")
    total_tokens: int = Field(0, description="总token数")
    message_count: int = Field(0, description="消息数量")
    is_archived: bool = Field(False, description="是否归档")
    is_deleted: bool = Field(False, description="是否删除")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class ConversationResponse(ConversationInDBBase):
    """对话响应"""
    pass


class ConversationWithMessages(ConversationResponse):
    """包含消息的对话响应"""
    messages: List[MessageResponse] = Field(default_factory=list, description="消息列表")


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationResponse] = Field(..., description="对话列表")
    total: int = Field(..., description="总对话数")
    active: int = Field(..., description="活跃对话数")
    archived: int = Field(..., description="归档对话数")
    total_tokens: int = Field(..., description="总token数")


class ConversationStats(BaseModel):
    """对话统计"""
    total: int = Field(..., description="总对话数")
    active: int = Field(..., description="活跃对话数（最近7天）")
    archived: int = Field(..., description="归档对话数")
    total_tokens: int = Field(..., description="总token数")


class DeleteConversationRequest(BaseModel):
    """删除对话请求"""
    permanently: bool = Field(False, description="是否永久删除")
    reason: Optional[str] = Field(None, max_length=500, description="删除原因")


class BulkConversationRequest(BaseModel):
    """批量操作对话请求"""
    conversation_ids: List[int] = Field(..., description="对话ID列表")
    
    @validator('conversation_ids')
    def validate_ids(cls, v):
        """验证ID列表"""
        if not v:
            raise ValueError("对话ID列表不能为空")
        if len(v) > 100:
            raise ValueError("一次最多操作100个对话")
        return v


class ConversationSearchRequest(BaseModel):
    """搜索对话请求"""
    keyword: Optional[str] = Field(None, description="关键词（搜索标题）")
    model_id: Optional[int] = Field(None, description="模型ID")
    is_archived: Optional[bool] = Field(None, description="是否归档")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(20, ge=1, le=100, description="每页记录数")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        """验证日期范围"""
        if 'start_date' in values and v and values['start_date']:
            if v < values['start_date']:
                raise ValueError("结束时间不能早于开始时间")
        return v


class ConversationExportRequest(BaseModel):
    """导出对话请求"""
    format: str = Field("json", pattern="^(json|txt|markdown)$", description="导出格式")
    include_messages: bool = Field(True, description="是否包含消息")
    include_metadata: bool = Field(True, description="是否包含元数据")
