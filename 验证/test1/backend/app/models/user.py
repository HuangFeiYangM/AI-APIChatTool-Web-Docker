from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship  # 添加这行
from sqlalchemy.sql import func
from app.database import Base

class UserStorage(Base):
    """用户存储表模型，对应数据库中的 user_storage 表"""
    __tablename__ = "user_storage"

    # 用户名作为主键
    user = Column(String(255), primary_key=True, index=True, comment="用户名")
    # 密码（明文存储，仅开发使用——生产环境应哈希加密）
    password = Column(String(255), nullable=False, comment="密码")
    # 是否使用 DeepSeek API
    deepseek_bool = Column(Boolean, default=False, comment="是否使用DeepSeek")
    # DeepSeek API 密钥（可选）
    deepseek_api = Column(String(255), nullable=True, comment="DeepSeek API密钥")
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # 更新时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 定义与 ConversationStorage 的一对多关系
    conversations = relationship("ConversationStorage", back_populates="user_ref")
