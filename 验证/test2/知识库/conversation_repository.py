# app/repositories/conversation_repository.py
"""
对话Repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta

from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """对话Repository"""
    
    def __init__(self, db: Session):
        super().__init__(Conversation, db)
    
    def get_user_conversations(
        self,
        user_id: int,
        include_deleted: bool = False,
        include_archived: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """
        获取用户的所有对话
        
        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的对话
            include_archived: 是否包含已归档的对话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            对话列表
        """
        query = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        )
        
        if not include_deleted:
            query = query.filter(Conversation.is_deleted == False)
        
        if not include_archived:
            query = query.filter(Conversation.is_archived == False)
        
        query = query.order_by(Conversation.created_at.desc())
        
        return query.offset(skip).limit(limit).all()
    
    def get_conversation_with_messages(
        self, 
        conversation_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Conversation]:
        """
        获取对话及其消息（预加载）
        
        Args:
            conversation_id: 对话ID
            user_id: 可选的用户ID（用于权限验证）
            
        Returns:
            对话实例或None
        """
        query = self.db.query(Conversation).options(
            joinedload(Conversation.messages)
        ).filter(Conversation.conversation_id == conversation_id)
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        return query.first()
    
    def get_recent_conversations(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 20
    ) -> List[Conversation]:
        """
        获取用户最近使用的对话
        
        Args:
            user_id: 用户ID
            days: 最近多少天
            limit: 返回的最大记录数
            
        Returns:
            最近对话列表
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
            Conversation.created_at >= cutoff_date
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()
    
    def soft_delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        软删除对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.is_deleted == False
        ).first()
        
        if conversation:
            conversation.soft_delete()
            self.db.commit()
            return True
        return False
    
    def restore_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        恢复已删除的对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            是否恢复成功
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.is_deleted == True
        ).first()
        
        if conversation:
            conversation.restore()
            self.db.commit()
            return True
        return False
    
    def archive_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        归档对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            是否归档成功
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
            Conversation.is_archived == False
        ).first()
        
        if conversation:
            conversation.archive()
            self.db.commit()
            return True
        return False
    
    def unarchive_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        取消归档对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            是否取消归档成功
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
            Conversation.is_archived == True
        ).first()
        
        if conversation:
            conversation.unarchive()
            self.db.commit()
            return True
        return False
    
    def get_conversation_stats(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的对话统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        # 总对话数
        total = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_deleted == False
        ).count()
        
        # 活跃对话数（最近7天有更新）
        cutoff_date = datetime.now() - timedelta(days=7)
        active = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
            Conversation.updated_at >= cutoff_date
        ).count()
        
        # 归档对话数
        archived = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
            Conversation.is_archived == True
        ).count()
        
        # 总token数
        total_tokens_result = self.db.query(
            func.sum(Conversation.total_tokens)
        ).filter(
            Conversation.user_id == user_id,
            Conversation.is_deleted == False
        ).first()
        
        total_tokens = total_tokens_result[0] or 0
        
        return {
            "total": total,
            "active": active,
            "archived": archived,
            "total_tokens": total_tokens
        }
