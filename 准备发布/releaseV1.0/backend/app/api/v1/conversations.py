# app/api/v1/conversations.py
"""
对话管理API路由 - 修复版本
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.services.conversation_service import get_conversation_service
import logging
from app.schemas.message import MessageCreateRequest, MessageUpdate
from app.services.message_service import MessageService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["对话管理"])


@router.get("", response_model=Dict[str, Any])
async def get_conversations(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    include_archived: bool = Query(True, description="是否包含已归档的对话"),
    include_deleted: bool = Query(False, description="是否包含已删除的对话"),
    current_user: dict = Depends(get_current_user),  # 改为 dict 类型
    db: Session = Depends(get_db)
):
    """
    获取用户的对话列表
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        service = get_conversation_service(db)
        conversations = service.get_user_conversations(
            user_id=user_id,
            include_deleted=include_deleted,
            include_archived=include_archived,
            skip=skip,
            limit=limit
        )
        
        return {
            "success": True,
            "message": "获取对话列表成功",
            "data": {
                "conversations": conversations,
                "total": len(conversations),
                "skip": skip,
                "limit": limit
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话列表异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话列表失败: {str(e)}"
        )


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),  # 改为 dict 类型
    db: Session = Depends(get_db)
):
    """
    创建新对话
    请求格式：
    {
    "title": "关于AI的讨论",
    "model_id": 1
    }
        
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        title = conversation_data.get("title", "新对话")
        model_id = conversation_data.get("model_id")
        
        if not model_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供模型ID"
            )
        
        service = get_conversation_service(db)
        conversation = service.create_conversation(
            user_id=user_id,
            title=title,
            model_id=model_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建对话失败，请稍后重试"
            )
        
        return {
            "success": True,
            "message": "对话创建成功",
            "data": conversation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建对话异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建对话失败: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_conversation_stats(
    current_user: dict = Depends(get_current_user),  # 改为 dict 类型
    db: Session = Depends(get_db)
):
    """
    获取用户的对话统计信息
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        service = get_conversation_service(db)
        stats = service.get_conversation_stats(user_id)
        
        return {
            "success": True,
            "message": "获取对话统计成功",
            "data": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话统计异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话统计失败: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation_detail(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),  # 改为 dict 类型
    db: Session = Depends(get_db)
):
    """
    获取对话详情
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        service = get_conversation_service(db)
        conversation = service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限访问"
            )
        
        return {
            "success": True,
            "message": "获取对话详情成功",
            "data": conversation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话详情异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话详情失败: {str(e)}"
        )


@router.put("/{conversation_id}", response_model=Dict[str, Any])
async def update_conversation(
    conversation_id: int,
    update_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),  # 改为 dict 类型
    db: Session = Depends(get_db)
):
    """
    更新对话
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        title = update_data.get("title")
        is_archived = update_data.get("is_archived")
        
        service = get_conversation_service(db)
        conversation = service.update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title,
            is_archived=is_archived
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限修改"
            )
        
        return {
            "success": True,
            "message": "对话更新成功",
            "data": conversation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新对话失败: {str(e)}"
        )


@router.delete("/{conversation_id}", response_model=Dict[str, Any])
async def delete_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),  # 改为 dict 类型
    db: Session = Depends(get_db)
):
    """
    删除对话
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        service = get_conversation_service(db)
        success = service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限删除"
            )
        
        return {
            "success": True,
            "message": "对话删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除对话失败: {str(e)}"
        )


@router.post("/{conversation_id}/archive", response_model=Dict[str, Any])
async def archive_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),  # 改为 dict 类型
    db: Session = Depends(get_db)
):
    """
    归档对话
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        service = get_conversation_service(db)
        success = service.archive_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限归档"
            )
        
        return {
            "success": True,
            "message": "对话归档成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"归档对话异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"归档对话失败: {str(e)}"
        )


@router.post("/{conversation_id}/unarchive", response_model=Dict[str, Any])
async def unarchive_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),  # 改为 dict 类型
    db: Session = Depends(get_db)
):
    """
    取消归档对话
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        service = get_conversation_service(db)
        success = service.unarchive_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限取消归档"
            )
        
        return {
            "success": True,
            "message": "对话取消归档成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消归档对话异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消归档对话失败: {str(e)}"
        )






@router.get("/{conversation_id}/messages", response_model=Dict[str, Any])
@router.get("/{conversation_id}/messages", response_model=Dict[str, Any])
async def get_conversation_messages(
    conversation_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    include_deleted: bool = Query(False, description="是否包含已删除的消息"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取对话的消息列表
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        # 检查对话是否存在且属于当前用户
        conversation_service = get_conversation_service(db)
        conversation = conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限访问"
            )
        
        # 获取消息列表
        message_service = MessageService(db)
        messages = message_service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            include_deleted=include_deleted,
            skip=skip,
            limit=limit
        )
        
        # 获取消息统计
        stats = message_service.get_message_stats(conversation_id)
        
        return {
            "success": True,
            "message": "获取消息列表成功",
            "data": {
                "messages": messages,
                "total": stats.get("total_messages", 0),
                "user_messages": stats.get("user_messages", 0),
                "assistant_messages": stats.get("assistant_messages", 0),
                "total_tokens": stats.get("total_tokens", 0),
                "conversation_id": conversation_id,
                "skip": skip,
                "limit": limit
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话消息异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话消息失败: {str(e)}"
        )

# app/api/v1/conversations.py - 添加消息管理端点（在文件末尾添加）：
# @router.post("/{conversation_id}/messages", response_model=Dict[str, Any])
# async def create_message(
#     conversation_id: int,
#     message_data: Dict[str, Any],
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     在对话中创建新消息
    
#     测试方法：
    
#     1.输入要添加的对话的id/n
#     2.在Request body里输入这个：/n
#     {
#     "content": "你的消息内容",
#     "role": "user",
#     "model_id": 1
#     }
    

#     """
#     try:
#         user_id = current_user.get("user_id")
#         if not user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="用户信息无效"
#             )
        
#         # 检查对话是否存在且属于当前用户
#         conversation_service = get_conversation_service(db)
#         conversation = conversation_service.get_conversation(
#             conversation_id=conversation_id,
#             user_id=user_id
#         )
        
#         if not conversation:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="对话不存在或无权限访问"
#             )
        
#         # TODO: 这里需要添加消息服务的调用
#         # 暂时返回成功
#         return {
#             "success": True,
#             "message": "消息创建成功（待实现）",
#             "data": {
#                 "message_id": 0,
#                 "conversation_id": conversation_id,
#                 "content": message_data.get("content", ""),
#                 "role": message_data.get("role", "user")
#             }
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"创建消息异常: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"创建消息失败: {str(e)}"
#         )


# 在 conversations.py 中修改 create_message 端点
@router.post("/{conversation_id}/messages", response_model=Dict[str, Any])
async def create_message(
    conversation_id: int,
    message_data: MessageCreateRequest,  # 改用Pydantic模型
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    在对话中创建新消息
    
    请求格式：
    {
        "content": "你的消息内容",
        "role": "user",  # 可选：user, assistant, system
        "model_id": 1,   # 可选：当 role="assistant" 时指定使用的模型
        "tokens_used": 0  # 可选：使用的token数
    }
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        # 检查对话是否存在且属于当前用户
        conversation_service = get_conversation_service(db)
        conversation = conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限访问"
            )
        
        # 注意：这里使用 message_data.属性名，而不是 message_data.get('属性名')
        content = message_data.content  # 直接访问属性
        role = message_data.role
        model_id = message_data.model_id
        tokens_used = message_data.tokens_used
        
        # 如果是 assistant 消息，检查 model_id
        if role == "assistant" and not model_id:
            # 如果没传 model_id，使用对话的默认模型
            if "model_id" in conversation:
                model_id = conversation["model_id"]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="assistant消息必须提供model_id"
                )
        
        # 保存消息 - 注意这里调用的是 conversation_service 的 save_message 方法
        result = conversation_service.save_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            model_id=model_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": "消息创建成功",
            "data": result["data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建消息异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建消息失败: {str(e)}"
        )



# 在 conversations.py 中添加以下端点

@router.get("/{conversation_id}/messages/{message_id}", response_model=Dict[str, Any])
async def get_message_detail(
    conversation_id: int,
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取消息详情
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        # 验证对话权限
        conversation_service = get_conversation_service(db)
        conversation = conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限访问"
            )
        
        # 获取消息详情
        message_service = MessageService(db)
        message = message_service.get_message(message_id, user_id)
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="消息不存在"
            )
        
        return {
            "success": True,
            "message": "获取消息详情成功",
            "data": message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取消息详情异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取消息详情失败: {str(e)}"
        )


@router.put("/{conversation_id}/messages/{message_id}", response_model=Dict[str, Any])
async def update_message(
    conversation_id: int,
    message_id: int,
    update_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新消息内容
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        # 验证对话权限
        conversation_service = get_conversation_service(db)
        conversation = conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限访问"
            )
        
        # 验证更新数据
        content = update_data.get("content")
        if content is not None:
            if not content.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="消息内容不能为空"
                )
            update_data["content"] = content.strip()
        
        # 更新消息
        message_service = MessageService(db)
        updated_message = message_service.update_message(message_id, update_data, user_id)
        
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="消息不存在或无权限修改"
            )
        
        return {
            "success": True,
            "message": "消息更新成功",
            "data": updated_message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新消息异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新消息失败: {str(e)}"
        )


@router.delete("/{conversation_id}/messages/{message_id}", response_model=Dict[str, Any])
async def delete_message(
    conversation_id: int,
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除消息
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户信息无效"
            )
        
        # 验证对话权限
        conversation_service = get_conversation_service(db)
        conversation = conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在或无权限访问"
            )
        
        # 删除消息
        message_service = MessageService(db)
        success = message_service.delete_message(message_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="消息不存在或无权限删除"
            )
        
        return {
            "success": True,
            "message": "消息删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除消息异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除消息失败: {str(e)}"
        )
