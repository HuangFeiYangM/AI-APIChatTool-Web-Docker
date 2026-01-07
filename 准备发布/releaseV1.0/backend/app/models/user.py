# app/models/user.py
"""
用户模型
对应数据库表：users
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime

from app.database import Base


class User(Base):
    """用户表模型"""
    __tablename__ = "users"
    __table_args__ = {
        'comment': '用户表'
    }

    user_id = Column(Integer, primary_key=True, index=True, comment='用户ID')
    username = Column(String(255), nullable=False, unique=True, index=True, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    email = Column(String(255), unique=True, index=True, comment='邮箱')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    is_locked = Column(Boolean, default=False, nullable=False, comment='是否锁定')
    locked_reason = Column(String(500), comment='锁定原因')
    locked_until = Column(DateTime, comment='锁定到期时间')
    failed_login_attempts = Column(Integer, default=0, nullable=False, comment='登录失败次数')
    last_login_at = Column(DateTime, comment='最后登录时间')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    # 关系定义
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    user_model_configs = relationship("UserModelConfig", back_populates="user", cascade="all, delete-orphan")
    api_call_logs = relationship("ApiCallLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', email='{self.email}')>"

    def is_account_locked(self) -> bool:
        """检查账户是否被锁定"""
        if not self.is_locked:
            return False
        if self.locked_until and self.locked_until < datetime.now():
            return False  # 锁定已过期
        return True

    def increment_failed_attempts(self):
        """增加登录失败次数"""
        self.failed_login_attempts += 1
        self.updated_at = datetime.now()

    def reset_failed_attempts(self):
        """重置登录失败次数"""
        self.failed_login_attempts = 0
        self.is_locked = False
        self.locked_reason = None
        self.locked_until = None
        self.updated_at = datetime.now()

    def lock_account(self, reason: str, lock_hours: int = 24):
        """锁定账户"""
        from datetime import datetime, timedelta
        
        self.is_locked = True
        self.locked_reason = reason
        self.locked_until = datetime.now() + timedelta(hours=lock_hours)
        self.updated_at = datetime.now()

    def unlock_account(self):
        """解锁账户"""
        self.is_locked = False
        self.locked_reason = None
        self.locked_until = None
        self.failed_login_attempts = 0
        self.updated_at = datetime.now()
