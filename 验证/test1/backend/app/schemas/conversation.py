from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ConversationCreate(BaseModel):
    """创建对话时使用的数据模式"""
    id_conversation: int
    id_part: int
    user: str
    markdown: Optional[str] = None

class ConversationResponse(BaseModel):
    """返回对话信息时的数据模式"""
    id_conversation: int
    id_part: int
    user: str
    markdown: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ConversationUpdate(BaseModel):
    """更新对话时使用的数据模式"""
    markdown: Optional[str] = None
