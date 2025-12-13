# app/repositories/message_repository.py
"""
消息Repository
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta

from app.models.message import Message
from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """消息Repository"""
    
    def __init__(self, db: Session):
        super().__init__(Message, db)
    
    def get_conversation_messages(
        self,
        conversation_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        获取对话的所有消息
        
        Args:
            conversation_id: 对话ID
            user_id: 可选的用户ID（用于验证权限）
            include_deleted: 是否包含已删除的消息
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            消息列表
        """
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        )
        
        # 如果提供用户ID，验证对话属于该用户
        if user_id:
            query = query.join(Conversation).filter(
                Conversation.user_id == user_id
            )
        
        if not include_deleted:
            query = query.filter(Message.is_deleted == False)
        
        query = query.order_by(Message.created_at.asc())
        
        return query.offset(skip).limit(limit).all()
    
    def get_last_message(self, conversation_id: int) -> Optional[Message]:
        """
        获取对话的最后一条消息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            最后一条消息或None
        """
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).first()
    
    def get_message_count(self, conversation_id: int) -> int:
        """
        获取对话的消息数量
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            消息数量
        """
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
        ).count()
    
    def create_user_message(
        self,
        conversation_id: int,
        content: str,
        tokens_used: int = 0
    ) -> Message:
        """
        创建用户消息
        
        Args:
            conversation_id: 对话ID
            content: 消息内容
            tokens_used: 使用的token数
            
        Returns:
            创建的消息
        """
        from app.models.message import MessageRole
        
        message_data = {
            "conversation_id": conversation_id,
            "role": MessageRole.user,
            "content": content,
            "tokens_used": tokens_used,
            "model_id": None,  # 用户消息没有模型
            "is_deleted": False
        }
        
        return self.create(message_data)
    
    def create_assistant_message(
        self,
        conversation_id: int,
        content: str,
        model_id: int,
        tokens_used: int = 0
    ) -> Message:
        """
        创建助手消息
        
        Args:
            conversation_id: 对话ID
            content: 消息内容
            model_id: 使用的模型ID
            tokens_used: 使用的token数
            
        Returns:
            创建的消息
        """
        from app.models.message import MessageRole
        
        message_data = {
            "conversation_id": conversation_id,
            "role": MessageRole.assistant,
            "content": content,
            "tokens_used": tokens_used,
            "model_id": model_id,
            "is_deleted": False
        }
        
        return self.create(message_data)
    
    def get_message_stats_by_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """
        获取对话的消息统计信息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            统计信息字典
        """
        stats = self.db.query(
            Message.role,
            func.count(Message.message_id).label('count'),
            func.sum(Message.tokens_used).label('total_tokens')
        ).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
        ).group_by(Message.role).all()
        
        result = {
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "total_tokens": 0
        }
        
        for role, count, tokens in stats:
            if role.value == "user":
                result["user_messages"] = count
            elif role.value == "assistant":
                result["assistant_messages"] = count
            
            result["total_messages"] += count
            result["total_tokens"] += (tokens or 0)
        
        return result
    
    def search_messages(
        self,
        conversation_id: int,
        keyword: Optional[str] = None,
        role: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """
        搜索对话中的消息
        
        Args:
            conversation_id: 对话ID
            keyword: 关键词（在内容中搜索）
            role: 消息角色
            start_date: 开始日期
            end_date: 结束日期
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            匹配的消息列表
        """
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
        )
        
        if keyword:
            query = query.filter(Message.content.ilike(f"%{keyword}%"))
        
        if role:
            # 将字符串转换为枚举值
            from app.models.message import MessageRole
            query = query.filter(Message.role == getattr(MessageRole, role.upper(), role))
        
        if start_date:
            query = query.filter(Message.created_at >= start_date)
        
        if end_date:
            query = query.filter(Message.created_at <= end_date)
        
        query = query.order_by(Message.created_at.desc())
        
        return query.offset(skip).limit(limit).all()
    
    def soft_delete_messages(self, conversation_id: int) -> int:
        """
        软删除对话的所有消息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            删除的消息数量
        """
        result = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
        ).update({
            "is_deleted": True
        }, synchronize_session=False)
        
        self.db.commit()
        return result
    
    # admin
    # 在 MessageRepository 类中添加

    def count_by_date(self, date: datetime) -> int:
        """统计指定日期的消息数量"""
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        return self.db.query(func.count(Message.message_id)).filter(
            Message.created_at >= start_date,
            Message.created_at < end_date
        ).scalar() or 0