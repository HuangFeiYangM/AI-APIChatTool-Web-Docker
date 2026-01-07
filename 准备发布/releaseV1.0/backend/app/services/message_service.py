# app/services/message_service.py
"""
消息服务层
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.models.message import Message, MessageRole
from app.models.conversation import Conversation
from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate, MessageResponse, MessageStats

logger = logging.getLogger(__name__)


class MessageService:
    """消息服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.message_repo = MessageRepository(db)
    
    def create_message(self, message_data: MessageCreate) -> Optional[Dict[str, Any]]:
        """
        创建新消息
        """
        try:
            # 检查对话是否存在
            conversation = self.db.query(Conversation).filter(
                Conversation.conversation_id == message_data.conversation_id,
                Conversation.is_deleted == False
            ).first()
            
            if not conversation:
                logger.warning(f"对话不存在: {message_data.conversation_id}")
                return None
            
            # 创建消息记录
            message_dict = message_data.dict(exclude_none=True)
            
            # 将字符串角色转换为枚举
            if isinstance(message_dict.get("role"), str):
                try:
                    message_dict["role"] = MessageRole(message_dict["role"].lower())
                except ValueError:
                    logger.warning(f"无效的角色: {message_dict.get('role')}, 使用默认值: user")
                    message_dict["role"] = MessageRole.user
            
            message = self.message_repo.create(message_dict)
            
            if not message:
                logger.error("创建消息失败")
                return None
            
            # 更新对话的更新时间
            conversation.updated_at = datetime.now()
            self.db.commit()
            
            return self._message_to_dict(message)
            
        except Exception as e:
            logger.error(f"创建消息异常: {e}", exc_info=True)
            self.db.rollback()
            return None
    
    def get_conversation_messages(
        self,
        conversation_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取对话的所有消息
        """
        try:
            messages = self.message_repo.get_conversation_messages(
                conversation_id=conversation_id,
                user_id=user_id,
                include_deleted=include_deleted,
                skip=skip,
                limit=limit
            )
            
            return [self._message_to_dict(msg) for msg in messages]
            
        except Exception as e:
            logger.error(f"获取对话消息异常: {e}", exc_info=True)
            return []
    
    def get_message(self, message_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        获取单个消息
        """
        try:
            message = self.message_repo.get_by_id(message_id)
            
            if not message:
                return None
            
            # 如果提供用户ID，验证权限
            if user_id:
                conversation = self.db.query(Conversation).filter(
                    Conversation.conversation_id == message.conversation_id,
                    Conversation.user_id == user_id
                ).first()
                
                if not conversation:
                    return None
            
            return self._message_to_dict(message)
            
        except Exception as e:
            logger.error(f"获取消息异常: {e}", exc_info=True)
            return None
    
    def update_message(
        self,
        message_id: int,
        update_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        更新消息
        """
        try:
            message = self.message_repo.get_by_id(message_id)
            
            if not message:
                return None
            
            # 如果提供用户ID，验证权限
            if user_id:
                conversation = self.db.query(Conversation).filter(
                    Conversation.conversation_id == message.conversation_id,
                    Conversation.user_id == user_id
                ).first()
                
                if not conversation:
                    return None
            
            # 不允许更新已删除的消息
            if message.is_deleted:
                return None
            
            # 准备更新数据
            valid_fields = ["content"]
            update_dict = {}
            
            for field in valid_fields:
                if field in update_data:
                    update_dict[field] = update_data[field]
            
            if not update_dict:
                return self._message_to_dict(message)
            
            updated_message = self.message_repo.update(message, update_dict)
            
            if not updated_message:
                return None
            
            return self._message_to_dict(updated_message)
            
        except Exception as e:
            logger.error(f"更新消息异常: {e}", exc_info=True)
            self.db.rollback()
            return None
    
    def delete_message(self, message_id: int, user_id: Optional[int] = None) -> bool:
        """
        删除消息（软删除）
        """
        try:
            message = self.message_repo.get_by_id(message_id)
            
            if not message:
                return False
            
            # 如果提供用户ID，验证权限
            if user_id:
                conversation = self.db.query(Conversation).filter(
                    Conversation.conversation_id == message.conversation_id,
                    Conversation.user_id == user_id
                ).first()
                
                if not conversation:
                    return False
            
            # 如果已经删除，返回成功
            if message.is_deleted:
                return True
            
            message.is_deleted = True
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"删除消息异常: {e}", exc_info=True)
            self.db.rollback()
            return False
    
    def restore_message(self, message_id: int, user_id: Optional[int] = None) -> bool:
        """
        恢复已删除的消息
        """
        try:
            message = self.message_repo.get_by_id(message_id)
            
            if not message:
                return False
            
            # 如果提供用户ID，验证权限
            if user_id:
                conversation = self.db.query(Conversation).filter(
                    Conversation.conversation_id == message.conversation_id,
                    Conversation.user_id == user_id
                ).first()
                
                if not conversation:
                    return False
            
            # 如果未删除，返回成功
            if not message.is_deleted:
                return True
            
            message.is_deleted = False
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"恢复消息异常: {e}", exc_info=True)
            self.db.rollback()
            return False
    
    def get_message_stats(self, conversation_id: int) -> Dict[str, Any]:
        """
        获取消息统计信息
        """
        try:
            stats = self.message_repo.get_message_stats_by_conversation(conversation_id)
            return stats
        except Exception as e:
            logger.error(f"获取消息统计异常: {e}", exc_info=True)
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "total_tokens": 0
            }
    
    def search_messages(
        self,
        conversation_id: int,
        keyword: Optional[str] = None,
        role: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索消息
        """
        try:
            messages = self.message_repo.search_messages(
                conversation_id=conversation_id,
                keyword=keyword,
                role=role,
                start_date=start_date,
                end_date=end_date,
                skip=skip,
                limit=limit
            )
            
            return [self._message_to_dict(msg) for msg in messages]
            
        except Exception as e:
            logger.error(f"搜索消息异常: {e}", exc_info=True)
            return []
    
    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
        """
        将Message对象转换为字典
        """
        return {
            "message_id": message.message_id,
            "conversation_id": message.conversation_id,
            "role": message.role.value,
            "content": message.content,
            "tokens_used": message.tokens_used,
            "model_id": message.model_id,
            "is_deleted": message.is_deleted,
            "created_at": message.created_at.isoformat() if message.created_at else None
        }


def get_message_service(db: Session) -> MessageService:
    """
    获取消息服务实例
    """
    return MessageService(db)
