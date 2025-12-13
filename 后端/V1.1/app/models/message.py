# app/models/message.py
"""
消息模型
对应数据库表：messages
"""
import enum
from sqlalchemy import Column, Integer, Text, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MessageRole(enum.Enum):
    """消息角色枚举"""
    user = "user"
    assistant = "assistant"
    system = "system"


class Message(Base):
    """消息表模型"""
    __tablename__ = "messages"
    __table_args__ = {
        'comment': '消息表'
    }

    message_id = Column(Integer, primary_key=True, index=True, comment='消息ID')
    conversation_id = Column(Integer, ForeignKey('conversations.conversation_id', ondelete='CASCADE'), nullable=False, index=True, comment='对话ID')
    role = Column(Enum(MessageRole), nullable=False, comment='角色')
    content = Column(Text, nullable=False, comment='消息内容')
    tokens_used = Column(Integer, default=0, nullable=False, comment='使用的token数')
    model_id = Column(Integer, ForeignKey('system_models.model_id', ondelete='SET NULL'), comment='使用的模型ID')
    is_deleted = Column(Boolean, default=False, nullable=False, comment='是否删除')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')

    # 关系定义
    conversation = relationship("Conversation", back_populates="messages")
    system_model = relationship("SystemModel", back_populates="messages")

    def __repr__(self):
        return f"<Message(message_id={self.message_id}, conversation_id={self.conversation_id}, role='{self.role}')>"

    @property
    def is_user_message(self) -> bool:
        """检查是否为用户消息"""
        return self.role == MessageRole.user

    @property
    def is_assistant_message(self) -> bool:
        """检查是否为助手消息"""
        return self.role == MessageRole.assistant

    @property
    def is_system_message(self) -> bool:
        """检查是否为系统消息"""
        return self.role == MessageRole.system

    def soft_delete(self):
        """软删除消息"""
        self.is_deleted = True

    def restore(self):
        """恢复已删除的消息"""
        self.is_deleted = False

    def get_truncated_content(self, max_length: int = 100) -> str:
        """获取截断的内容用于显示"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
