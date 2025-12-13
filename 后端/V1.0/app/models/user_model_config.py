# app/models/user_model_config.py
"""
用户模型配置模型
对应数据库表：user_model_configs
"""
from sqlalchemy import Column, Integer, Boolean, DateTime, String, Text, DECIMAL, BLOB, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserModelConfig(Base):
    """用户模型配置表模型"""
    __tablename__ = "user_model_configs"
    __table_args__ = {
        'comment': '用户模型配置表'
    }

    config_id = Column(Integer, primary_key=True, index=True, comment='配置ID')
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    model_id = Column(Integer, ForeignKey('system_models.model_id', ondelete='CASCADE'), nullable=False, comment='模型ID')
    is_enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    api_key = Column(String(500), comment='API密钥')
    api_key_encrypted = Column(BLOB, comment='加密的API密钥')
    custom_endpoint = Column(String(255), comment='自定义端点')
    max_tokens = Column(Integer, comment='自定义最大token数')
    temperature = Column(DECIMAL(3, 2), default=0.7, nullable=False, comment='温度参数')
    priority = Column(Integer, default=0, nullable=False, comment='优先级')
    last_used_at = Column(DateTime, comment='最后使用时间')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    # 关系定义
    user = relationship("User", back_populates="user_model_configs")
    system_model = relationship("SystemModel", back_populates="user_model_configs")

    def __repr__(self):
        return f"<UserModelConfig(config_id={self.config_id}, user_id={self.user_id}, model_id={self.model_id})>"

    def is_active(self) -> bool:
        """检查配置是否激活"""
        return self.is_enabled and (self.api_key or self.api_key_encrypted)

    def update_last_used(self):
        """更新最后使用时间"""
        from datetime import datetime
        self.last_used_at = datetime.now()
        self.updated_at = datetime.now()

    def get_api_key(self, decrypt_func=None) -> str:
        """获取API密钥（支持解密）"""
        if self.api_key:
            return self.api_key
        elif self.api_key_encrypted and decrypt_func:
            return decrypt_func(self.api_key_encrypted)
        return None

    def set_api_key(self, api_key: str, encrypt_func=None):
        """设置API密钥（支持加密）"""
        if encrypt_func and api_key:
            self.api_key_encrypted = encrypt_func(api_key)
            self.api_key = None
        else:
            self.api_key = api_key
            self.api_key_encrypted = None
        self.updated_at = datetime.now()
