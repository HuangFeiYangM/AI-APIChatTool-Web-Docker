# app/services/conversation_service.py
"""
对话服务层 - 修复版本
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.conversation import (
    ConversationCreate, ConversationUpdate, 
    ConversationResponse, ConversationWithMessages,
    ConversationStats
)
from app.schemas.message import MessageResponse
from app.exceptions import ConversationNotFoundError, UnauthorizedError
from app.database import get_db

logger = logging.getLogger(__name__)


class ConversationService:
    """对话服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.conversation_repo = ConversationRepository(db)
    
    def create_conversation(
        self, 
        user_id: int, 
        title: str,
        model_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        创建新对话 - 简化版本
        """
        try:
            logger.info(f"尝试创建对话 - 用户ID: {user_id}, 标题: {title}, 模型ID: {model_id}")
            
            # 准备数据
            conversation_data = {
                "user_id": user_id,
                "title": title if title and title.strip() else "新对话",
                "model_id": model_id,
                "total_tokens": 0,
                "message_count": 0,
                "is_archived": False,
                "is_deleted": False
            }
            
            # 创建对话
            conversation = self.conversation_repo.create(conversation_data)
            
            if not conversation:
                logger.error("创建对话失败: repository返回None")
                return None
            
            logger.info(f"对话创建成功 - ID: {conversation.conversation_id}")
            
            # 转换为字典
            return {
                "conversation_id": conversation.conversation_id,
                "title": conversation.title,
                "user_id": conversation.user_id,
                "model_id": conversation.model_id,
                "total_tokens": conversation.total_tokens,
                "message_count": conversation.message_count,
                "is_archived": conversation.is_archived,
                "is_deleted": conversation.is_deleted,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"创建对话异常: {e}", exc_info=True)
            return None
    
    def get_user_conversations(
        self,
        user_id: int,
        include_deleted: bool = False,
        include_archived: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取用户的所有对话 - 简化版本
        """
        try:
            logger.info(f"获取用户对话 - 用户ID: {user_id}")
            
            conversations = self.conversation_repo.get_user_conversations(
                user_id, include_deleted, include_archived, skip, limit
            )
            
            if not conversations:
                logger.info(f"用户 {user_id} 没有对话记录")
                return []
            
            # 转换为字典列表
            result = []
            for conv in conversations:
                conv_dict = {
                    "conversation_id": conv.conversation_id,
                    "title": conv.title,
                    "user_id": conv.user_id,
                    "model_id": conv.model_id,
                    "total_tokens": conv.total_tokens,
                    "message_count": conv.message_count,
                    "is_archived": conv.is_archived,
                    "is_deleted": conv.is_deleted,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
                }
                result.append(conv_dict)
            
            logger.info(f"找到 {len(result)} 个对话")
            return result
            
        except Exception as e:
            logger.error(f"获取用户对话异常: {e}", exc_info=True)
            return []
    
    def get_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个对话 - 简化版本
        """
        try:
            logger.info(f"获取对话详情 - 对话ID: {conversation_id}, 用户ID: {user_id}")
            
            conversation = self.conversation_repo.get_by_id(conversation_id)
            
            if not conversation:
                logger.warning(f"对话不存在: {conversation_id}")
                return None
            
            if conversation.user_id != user_id:
                logger.warning(f"无权访问对话: 用户 {user_id} 尝试访问对话 {conversation_id} (属于用户 {conversation.user_id})")
                return None
            
            if conversation.is_deleted:
                logger.warning(f"对话已被删除: {conversation_id}")
                return None
            
            # 转换为字典
            return {
                "conversation_id": conversation.conversation_id,
                "title": conversation.title,
                "user_id": conversation.user_id,
                "model_id": conversation.model_id,
                "total_tokens": conversation.total_tokens,
                "message_count": conversation.message_count,
                "is_archived": conversation.is_archived,
                "is_deleted": conversation.is_deleted,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"获取对话详情异常: {e}", exc_info=True)
            return None
    
    def update_conversation(
        self,
        conversation_id: int,
        user_id: int,
        title: Optional[str] = None,
        is_archived: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        更新对话 - 简化版本
        """
        try:
            logger.info(f"更新对话 - 对话ID: {conversation_id}, 用户ID: {user_id}")
            
            conversation = self.conversation_repo.get_by_id(conversation_id)
            
            if not conversation:
                logger.warning(f"对话不存在: {conversation_id}")
                return None
            
            if conversation.user_id != user_id:
                logger.warning(f"无权更新对话: 用户 {user_id} 尝试更新对话 {conversation_id}")
                return None
            
            if conversation.is_deleted:
                logger.warning(f"对话已被删除，无法更新: {conversation_id}")
                return None
            
            # 准备更新数据
            update_data = {}
            if title is not None:
                update_data["title"] = title.strip() if title else "新对话"
            if is_archived is not None:
                update_data["is_archived"] = is_archived
            
            # 如果没有要更新的数据，直接返回当前对话
            if not update_data:
                logger.info("没有要更新的数据")
                return self.get_conversation(conversation_id, user_id)
            
            # 更新对话
            updated_conv = self.conversation_repo.update(conversation, update_data)
            
            if not updated_conv:
                logger.error("更新对话失败")
                return None
            
            logger.info(f"对话更新成功: {conversation_id}")
            
            # 转换为字典
            return {
                "conversation_id": updated_conv.conversation_id,
                "title": updated_conv.title,
                "user_id": updated_conv.user_id,
                "model_id": updated_conv.model_id,
                "total_tokens": updated_conv.total_tokens,
                "message_count": updated_conv.message_count,
                "is_archived": updated_conv.is_archived,
                "is_deleted": updated_conv.is_deleted,
                "created_at": updated_conv.created_at.isoformat() if updated_conv.created_at else None,
                "updated_at": updated_conv.updated_at.isoformat() if updated_conv.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"更新对话异常: {e}", exc_info=True)
            return None
    
    def delete_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """
        删除对话 - 简化版本
        """
        try:
            logger.info(f"删除对话 - 对话ID: {conversation_id}, 用户ID: {user_id}")
            
            success = self.conversation_repo.soft_delete_conversation(conversation_id, user_id)
            
            if success:
                logger.info(f"对话删除成功: {conversation_id}")
            else:
                logger.warning(f"对话删除失败: {conversation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除对话异常: {e}", exc_info=True)
            return False
    
    def archive_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """
        归档对话 - 简化版本
        """
        try:
            logger.info(f"归档对话 - 对话ID: {conversation_id}, 用户ID: {user_id}")
            
            success = self.conversation_repo.archive_conversation(conversation_id, user_id)
            
            if success:
                logger.info(f"对话归档成功: {conversation_id}")
            else:
                logger.warning(f"对话归档失败: {conversation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"归档对话异常: {e}", exc_info=True)
            return False
    
    def unarchive_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """
        取消归档对话 - 简化版本
        """
        try:
            logger.info(f"取消归档对话 - 对话ID: {conversation_id}, 用户ID: {user_id}")
            
            success = self.conversation_repo.unarchive_conversation(conversation_id, user_id)
            
            if success:
                logger.info(f"对话取消归档成功: {conversation_id}")
            else:
                logger.warning(f"对话取消归档失败: {conversation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"取消归档对话异常: {e}", exc_info=True)
            return False
    
    def get_conversation_stats(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取对话统计 - 简化版本
        """
        try:
            logger.info(f"获取对话统计 - 用户ID: {user_id}")
            
            stats = self.conversation_repo.get_conversation_stats(user_id)
            
            return {
                "total": stats.get("total", 0),
                "active": stats.get("active", 0),
                "archived": stats.get("archived", 0),
                "total_tokens": stats.get("total_tokens", 0)
            }
            
        except Exception as e:
            logger.error(f"获取对话统计异常: {e}", exc_info=True)
            return {
                "total": 0,
                "active": 0,
                "archived": 0,
                "total_tokens": 0
            }


def get_conversation_service(db: Session):
    """
    获取对话服务实例
    """
    return ConversationService(db)
