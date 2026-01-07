# app/models/conversation.py
"""
对话模型
对应数据库表：conversations
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Conversation(Base):
    """对话表模型"""
    __tablename__ = "conversations"
    __table_args__ = {
        'comment': '对话表'
    }

    conversation_id = Column(Integer, primary_key=True, index=True, comment='对话ID')
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    title = Column(String(200), comment='对话标题')
    model_id = Column(Integer, ForeignKey('system_models.model_id', ondelete='RESTRICT'), nullable=False, comment='使用的模型ID')
    total_tokens = Column(Integer, default=0, nullable=False, comment='总token数')
    message_count = Column(Integer, default=0, nullable=False, comment='消息数量')
    is_archived = Column(Boolean, default=False, nullable=False, comment='是否归档')
    is_deleted = Column(Boolean, default=False, nullable=False, comment='是否删除')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    # 关系定义
    user = relationship("User", back_populates="conversations")
    system_model = relationship("SystemModel", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    api_call_logs = relationship("ApiCallLog", back_populates="conversation")

    def __repr__(self):
        return f"<Conversation(conversation_id={self.conversation_id}, user_id={self.user_id}, title='{self.title}')>"

    def soft_delete(self):
        """软删除对话"""
        from datetime import datetime
        self.is_deleted = True
        self.deleted_at = datetime.now()
        self.updated_at = datetime.now()

    def restore(self):
        """恢复已删除的对话"""
        self.is_deleted = False
        self.deleted_at = None
        self.updated_at = datetime.now()

    def archive(self):
        """归档对话"""
        self.is_archived = True
        self.updated_at = datetime.now()

    def unarchive(self):
        """取消归档"""
        self.is_archived = False
        self.updated_at = datetime.now()

    def increment_message_count(self, tokens: int = 0):
        """增加消息计数和token数"""
        self.message_count += 1
        self.total_tokens += tokens
        self.updated_at = datetime.now()
