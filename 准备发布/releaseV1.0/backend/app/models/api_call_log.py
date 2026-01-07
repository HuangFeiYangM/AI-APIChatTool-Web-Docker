# app/models/api_call_log.py
"""
API调用日志模型
对应数据库表：api_call_logs
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship  # 添加这行
from sqlalchemy.sql import func

from app.database import Base


class ApiCallLog(Base):
    """API调用日志表模型"""
    __tablename__ = "api_call_logs"
    __table_args__ = {
        'comment': 'API调用日志表'
    }

    log_id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    model_id = Column(Integer, ForeignKey('system_models.model_id', ondelete='CASCADE'), nullable=False, comment='模型ID')
    conversation_id = Column(Integer, ForeignKey('conversations.conversation_id', ondelete='SET NULL'), comment='对话ID')
    endpoint = Column(String(255), nullable=False, comment='调用端点')
    request_tokens = Column(Integer, default=0, nullable=False, comment='请求token数')
    response_tokens = Column(Integer, default=0, nullable=False, comment='响应token数')
    total_tokens = Column(Integer, default=0, nullable=False, comment='总token数')
    response_time_ms = Column(Integer, comment='响应时间(毫秒)')
    status_code = Column(Integer, comment='状态码')
    is_success = Column(Boolean, default=True, nullable=False, comment='是否成功')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')

    # 关系定义
    user = relationship("User", back_populates="api_call_logs")
    system_model = relationship("SystemModel", back_populates="api_call_logs")
    conversation = relationship("Conversation", back_populates="api_call_logs")

    def __repr__(self):
        return f"<ApiCallLog(log_id={self.log_id}, user_id={self.user_id}, model_id={self.model_id})>"
