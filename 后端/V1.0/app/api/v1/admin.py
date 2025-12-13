# app/api/v1/admin.py
"""
管理员API路由
"""
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.admin import (
    UserFilter, UserUpdateRequest, SystemModelCreate, 
    SystemModelUpdate, ApiCallFilter, AdminActionRequest
)
from app.services.admin_service import get_admin_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["管理员"])


def verify_admin_permission(current_user: dict):
    """验证管理员权限"""
    # 这里可以根据你的需求设置管理员验证逻辑
    # 例如：检查用户名是否为admin，或者用户有admin角色
    if current_user.get("username") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )


@router.get("/users")
async def get_users(
    username: Optional[str] = Query(None, description="用户名"),
    email: Optional[str] = Query(None, description="邮箱"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    is_locked: Optional[bool] = Query(None, description="是否锁定"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="每页记录数"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        filters = {
            "username": username,
            "email": email,
            "is_active": is_active,
            "is_locked": is_locked,
            "skip": skip,
            "limit": limit
        }
        
        service = get_admin_service(db)
        result = service.get_users(filters)
        
        return {
            "success": True,
            "message": "获取用户列表成功",
            "data": result["users"],
            "total": result["total"],
            "active_count": result["active_count"],
            "locked_count": result["locked_count"]
        }
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户详情（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        user_detail = service.get_user_detail(user_id)
        
        if not user_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户 {user_id} 不存在"
            )
        
        return {
            "success": True,
            "message": "获取用户详情成功",
            "data": user_detail
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户详情失败: {str(e)}"
        )


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新用户信息（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        result = service.update_user(user_id, update_data.dict(exclude_none=True))
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}"
        )


@router.post("/users/{user_id}/lock")
async def lock_user(
    user_id: int,
    request_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    锁定用户账户（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        reason = request_data.get("reason", "管理员操作")
        lock_hours = request_data.get("lock_hours", 24)
        
        service = get_admin_service(db)
        result = service.lock_user(user_id, reason, lock_hours)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"锁定用户失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"锁定用户失败: {str(e)}"
        )


@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    解锁用户账户（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        result = service.unlock_user(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解锁用户失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解锁用户失败: {str(e)}"
        )


@router.get("/stats")
async def get_system_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取系统统计信息（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        stats = service.get_system_stats()
        
        return {
            "success": True,
            "message": "获取系统统计成功",
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统统计失败: {str(e)}"
        )


@router.get("/daily-stats")
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30, description="天数"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取每日统计信息（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        daily_stats = service.get_daily_stats(days)
        
        return {
            "success": True,
            "message": "获取每日统计成功",
            "data": daily_stats
        }
    except Exception as e:
        logger.error(f"获取每日统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取每日统计失败: {str(e)}"
        )


@router.get("/health")
async def get_system_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取系统健康状态（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        health_status = service.get_system_health()
        
        return {
            "success": True,
            "message": "获取系统健康状态成功",
            "data": health_status
        }
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统健康状态失败: {str(e)}"
        )


@router.get("/api-logs")
async def get_api_call_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    model_id: Optional[int] = Query(None, description="模型ID"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    is_success: Optional[bool] = Query(None, description="是否成功"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=1000, description="每页记录数"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取API调用日志（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        filters = {
            "user_id": user_id,
            "model_id": model_id,
            "start_date": start_date,
            "end_date": end_date,
            "is_success": is_success,
            "skip": skip,
            "limit": limit
        }
        
        service = get_admin_service(db)
        result = service.get_api_call_logs(filters)
        
        return {
            "success": True,
            "message": "获取API调用日志成功",
            "data": result["logs"],
            "total": result["total"]
        }
    except Exception as e:
        logger.error(f"获取API调用日志失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取API调用日志失败: {str(e)}"
        )


@router.get("/system-models")
async def get_system_models_admin(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有系统模型（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        from app.repositories.system_model_repository import SystemModelRepository
        repo = SystemModelRepository(db)
        models = repo.get_all()
        
        return {
            "success": True,
            "message": "获取系统模型成功",
            "data": models
        }
    except Exception as e:
        logger.error(f"获取系统模型失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统模型失败: {str(e)}"
        )


@router.post("/system-models")
async def create_system_model(
    model_data: SystemModelCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建系统模型（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        result = service.create_system_model(model_data.dict())
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "data": result["data"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建系统模型失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建系统模型失败: {str(e)}"
        )


@router.put("/system-models/{model_id}")
async def update_system_model(
    model_id: int,
    update_data: SystemModelUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新系统模型（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        result = service.update_system_model(model_id, update_data.dict(exclude_none=True))
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "data": result["data"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新系统模型失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新系统模型失败: {str(e)}"
        )


@router.delete("/system-models/{model_id}")
async def delete_system_model(
    model_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除系统模型（管理员）
    """
    verify_admin_permission(current_user)
    
    try:
        service = get_admin_service(db)
        result = service.delete_system_model(model_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除系统模型失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除系统模型失败: {str(e)}"
        )


@router.post("/action")
async def admin_action(
    action_request: AdminActionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    执行管理员操作（通用接口）
    """
    verify_admin_permission(current_user)
    
    try:
        action = action_request.action
        target_id = action_request.target_id
        
        # 这里可以根据action类型执行不同的操作
        # 例如：清除缓存、重置统计、清理旧数据等
        
        return {
            "success": True,
            "message": f"管理员操作 '{action}' 执行成功"
        }
    except Exception as e:
        logger.error(f"执行管理员操作失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行管理员操作失败: {str(e)}"
        )
