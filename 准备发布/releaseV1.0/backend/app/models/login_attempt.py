# app/models/login_attempt.py
"""
登录尝试模型
对应数据库表：login_attempts
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


class LoginAttempt(Base):
    """登录尝试表模型"""
    __tablename__ = "login_attempts"
    __table_args__ = {
        'comment': '登录尝试表'
    }

    attempt_id = Column(Integer, primary_key=True, index=True, comment='尝试ID')
    username = Column(String(255), nullable=False, index=True, comment='用户名')
    ip_address = Column(String(45), nullable=False, index=True, comment='IP地址')
    user_agent = Column(Text, comment='用户代理')
    is_success = Column(Boolean, default=False, nullable=False, comment='是否成功')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')

    def __repr__(self):
        return f"<LoginAttempt(attempt_id={self.attempt_id}, username='{self.username}', is_success={self.is_success})>"
