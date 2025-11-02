from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ConversationStorage(Base):
    """对话储存表模型，对应数据库中的conversation_storage表"""
    __tablename__ = "conversation_storage"

    # 对话ID，复合主键的一部分
    id_conversation = Column(Integer, primary_key=True, index=True, comment="对话ID")
    # 对话部分ID，复合主键的一部分
    id_part = Column(Integer, primary_key=True, index=True, comment="对话部分ID")
    # 用户名，外键关联user_storage表
    user = Column(String(255), ForeignKey("user_storage.user"), nullable=False, comment="用户名")
    # Markdown内容
    markdown = Column(Text, nullable=True, comment="Markdown内容")
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # 更新时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 定义与UserStorage模型的多对一关系
    user_ref = relationship("UserStorage", back_populates="conversations")
