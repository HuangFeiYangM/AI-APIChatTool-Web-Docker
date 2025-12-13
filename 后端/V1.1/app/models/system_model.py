# app/models/system_model.py
"""
系统模型配置模型
对应数据库表：system_models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ModelType(str, enum.Enum):
    """模型类型枚举"""
    chat = "chat"
    completion = "completion"
    embedding = "embedding"


class SystemModel(Base):
    """系统模型配置表模型"""
    __tablename__ = "system_models"
    __table_args__ = {
        'comment': '系统模型配置表'
    }

    model_id = Column(Integer, primary_key=True, index=True, comment='模型ID')
    model_name = Column(String(50), nullable=False, unique=True, index=True, comment='模型名称')
    model_provider = Column(String(50), nullable=False, index=True, comment='模型提供商')
    model_type = Column(Enum(ModelType), default=ModelType.chat, nullable=False, comment='模型类型')
    api_endpoint = Column(String(255), nullable=False, comment='API端点')
    api_version = Column(String(20), comment='API版本')
    is_available = Column(Boolean, default=True, nullable=False, comment='是否可用')
    is_default = Column(Boolean, default=False, nullable=False, comment='是否默认模型')
    rate_limit_per_minute = Column(Integer, default=60, nullable=False, comment='每分钟请求限制')
    max_tokens = Column(Integer, default=4096, nullable=False, comment='最大token数')
    description = Column(Text, comment='模型描述')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    # 关系定义
    user_model_configs = relationship("UserModelConfig", back_populates="system_model", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="system_model")
    messages = relationship("Message", back_populates="system_model")
    api_call_logs = relationship("ApiCallLog", back_populates="system_model", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SystemModel(model_id={self.model_id}, model_name='{self.model_name}', provider='{self.model_provider}')>"

    @property
    def is_chat_model(self) -> bool:
        """检查是否为聊天模型"""
        return self.model_type == ModelType.chat

    def get_endpoint_url(self, custom_endpoint: str = None) -> str:
        """获取API端点URL"""
        return custom_endpoint or self.api_endpoint

    def validate_config(self) -> bool:
        """验证模型配置是否有效"""
        return all([
            self.model_name,
            self.model_provider,
            self.api_endpoint,
            self.rate_limit_per_minute > 0,
            self.max_tokens > 0
        ])
