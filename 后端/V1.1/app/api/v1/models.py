# app/api/v1/models.py
from typing import Optional,  Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request,Body
from sqlalchemy.orm import Session
import logging

from app.dependencies import get_db, get_current_user
from app.schemas.model import (
    ChatRequest, ChatResponse, ModelConfigUpdateRequest,
    SystemModelOut, UserModelConfigCreateRequest, UserModelConfigOut, APIUsageStats,UserModelConfigCreate, UserModelConfigUpdate,  # 添加这些导入
    UserModelConfigListResponse, BulkConfigUpdateRequest  # 添加这些导入
)
from app.services.model_router import ModelRouterService
from app.exceptions import (
    ModelNotAvailableError, APIRequestError, 
    InsufficientQuotaError, ModelConfigError
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["模型"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_model(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    model_service: ModelRouterService = Depends(lambda db=Depends(get_db): ModelRouterService(db))  # 修复这里
):
    """
    与大模型对话
    对应详细设计中的程序3（模型对话模块）+ 程序4（模型路由模块）
    """
    try:
        # 记录请求日志
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"用户 {current_user['username']}({current_user['user_id']}) 请求聊天 | "
                    f"模型: {chat_request.model} | IP: {client_ip}")
        
        # 调用模型服务
        result = await model_service.chat_completion(
            user_id=current_user["user_id"],
            model_name=chat_request.model,
            message=chat_request.message,
            conversation_id=chat_request.conversation_id,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
            stream=chat_request.stream
        )
        
        return ChatResponse(**result)
        
    except ModelNotAvailableError as e:
        logger.warning(f"模型不可用: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelConfigError as e:
        logger.warning(f"模型配置错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InsufficientQuotaError as e:
        logger.warning(f"API配额不足: {e}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e)
        )
    except APIRequestError as e:
        logger.error(f"API请求错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="内部服务器错误"
        )


@router.get("/available")
async def get_available_models(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)  # 添加数据库依赖
):
    """
    获取当前系统可用的模型列表
    """
    try:
        from app.services.model_router import ModelRouterService
        model_service = ModelRouterService(db)
        models = model_service.get_available_models(current_user["user_id"])
        return {
            "success": True,
            "message": "获取成功",
            "data": models
        }
    except Exception as e:
        logger.error(f"获取可用模型失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模型列表失败"
        )


@router.post("/config")
async def update_model_config(
    config_request: ModelConfigUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)  # 添加数据库依赖
):
    """
    更新用户模型配置
    对应详细设计中的程序6（DeepSeek配置模块）
    """
    try:
        from app.services.model_router import ModelRouterService
        model_service = ModelRouterService(db)
        
        config_data = config_request.dict(exclude_none=True)
        
        result = model_service.update_user_model_config(
            user_id=current_user["user_id"],
            config_data=config_data
        )
        
        return result
        
    except ModelNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新模型配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新配置失败"
        )


@router.get("/config")
async def get_user_model_configs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)  # 修复：使用依赖注入而不是 next()
):
    """
    获取用户的所有模型配置
    """
    try:
        from app.repositories.user_model_config_repository import UserModelConfigRepository
        from app.repositories.system_model_repository import SystemModelRepository
        
        config_repo = UserModelConfigRepository(db)
        model_repo = SystemModelRepository(db)
        
        configs = config_repo.get_user_configs(current_user["user_id"])
        
        # 转换为响应格式
        config_list = []
        for config in configs:
            # 获取模型名称
            system_model = model_repo.get_by_id(config.model_id)
            model_name = system_model.model_name if system_model else None
            
            config_dict = {
                "config_id": config.config_id,
                "user_id": config.user_id,
                "model_id": config.model_id,
                "model_name": model_name,
                "is_enabled": config.is_enabled,
                "custom_endpoint": config.custom_endpoint,
                "max_tokens": config.max_tokens,
                "temperature": float(config.temperature) if config.temperature else None,
                "priority": config.priority,
                "last_used_at": config.last_used_at,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
            config_list.append(config_dict)
        
        return {
            "success": True,
            "message": "获取成功",
            "data": config_list
        }
    except Exception as e:
        logger.error(f"获取用户模型配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置失败"
        )


@router.get("/usage")
async def get_api_usage(
    model_id: Optional[int] = None,
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)  # 添加数据库依赖
):
    """
    获取API使用统计
    """
    try:
        from app.services.model_router import ModelRouterService
        model_service = ModelRouterService(db)
        
        stats = model_service.get_api_usage_stats(
            user_id=current_user["user_id"],
            model_id=model_id,
            days=days
        )
        
        return {
            "success": True,
            "message": "获取成功",
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取API使用统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计失败"
        )


@router.get("/system-models")
async def get_system_models(
    db: Session = Depends(get_db),  # 修复：使用依赖注入
    current_user: dict = Depends(get_current_user)
):
    """
    获取所有系统模型（管理员功能）
    """
    # 简单权限检查：这里假设只有admin用户可以访问
    if current_user["username"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    try:
        from app.repositories.system_model_repository import SystemModelRepository
        repo = SystemModelRepository(db)
        models = repo.get_all()
        
        return {
            "success": True,
            "message": "获取成功",
            "data": models
        }
    except Exception as e:
        logger.error(f"获取系统模型失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统模型失败"
        )


# 在 app/api/v1/models.py 中添加以下端点 2025.12.9-15:19

@router.get("/config/{model_id}")
async def get_user_model_config(
    model_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户对特定模型的配置
    """
    try:
        from app.services.model_service import ModelService
        model_service = ModelService(db)
        
        config = model_service.get_user_model_config(current_user["user_id"], model_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到该模型的配置"
            )
        
        return {
            "success": True,
            "message": "获取成功",
            "data": config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户模型配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置失败"
        )


@router.delete("/config/{model_id}")
async def delete_user_model_config(
    model_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除用户对特定模型的配置
    """
    try:
        from app.services.model_service import ModelService
        model_service = ModelService(db)
        
        result = model_service.delete_user_model_config(current_user["user_id"], model_id)
        
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
        logger.error(f"删除用户模型配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除配置失败"
        )


@router.post("/config/bulk-update")
async def bulk_update_model_configs(
    bulk_request: BulkConfigUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量更新模型配置
    """
    try:
        from app.services.model_service import ModelService
        model_service = ModelService(db)
        
        result = model_service.bulk_update_models(
            user_id=current_user["user_id"],
            model_ids=bulk_request.model_ids,
            is_enabled=bulk_request.is_enabled,
            priority=bulk_request.priority
        )
        
        return {
            "success": True,
            "message": result["message"],
            "data": result["data"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新模型配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新失败"
        )


@router.post("/config/{model_id}/enable")
async def enable_model_config(
    model_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    启用模型配置
    """
    try:
        from app.services.model_service import ModelService
        model_service = ModelService(db)
        
        result = model_service.enable_user_model(current_user["user_id"], model_id)
        
        return {
            "success": result["success"],
            "message": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启用模型配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启用失败"
        )


@router.post("/config/{model_id}/disable")
async def disable_model_config(
    model_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    禁用模型配置
    """
    try:
        from app.services.model_service import ModelService
        model_service = ModelService(db)
        
        result = model_service.disable_user_model(current_user["user_id"], model_id)
        
        return {
            "success": result["success"],
            "message": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁用模型配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="禁用失败"
        )


@router.post("/config/validate-api-key")
async def validate_api_key(
    validation_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    验证API密钥格式
    """
    try:
        from app.services.model_service import ModelService
        model_service = ModelService(db)
        
        model_id = validation_data.get("model_id")
        api_key = validation_data.get("api_key")
        
        if not model_id or not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供model_id和api_key"
            )
        
        result = model_service.validate_api_key(model_id, api_key)
        
        return {
            "success": True,
            "message": result["message"],
            "data": {"valid": result["valid"]}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证API密钥失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证失败"
        )


# app/api/v1/models.py - 在合适位置添加以下端点

@router.post("/config/create", response_model=Dict[str, Any])
async def create_model_config(
    config_request: UserModelConfigCreateRequest,  # 使用前面定义的请求模型
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建用户的大模型配置
    - 添加新的API密钥和配置
    - 验证API密钥格式
    - 检查模型是否存在
    """
    try:
        from app.services.model_service import ModelService
        model_service = ModelService(db)
        
        # 调用创建方法
        result = model_service.create_user_model_config(
            user_id=current_user["user_id"],
            config_data=config_request.dict()
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "data": result.get("data", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建模型配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建配置失败: {str(e)}"
        )


@router.get("/system-models/available")
async def get_available_system_models(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取系统支持的所有模型列表（普通用户版）
    - 返回所有系统预定义的模型
    - 标记用户是否已配置
    """
    try:
        from app.repositories.system_model_repository import SystemModelRepository
        from app.repositories.user_model_config_repository import UserModelConfigRepository
        
        system_repo = SystemModelRepository(db)
        config_repo = UserModelConfigRepository(db)
        
        # 获取所有系统模型
        system_models = system_repo.get_all()
        
        result = []
        for model in system_models:
            model_info = {
                "model_id": model.model_id,
                "model_name": model.model_name,
                "model_provider": model.model_provider,
                "model_type": model.model_type,
                "description": model.description,
                "max_tokens": model.max_tokens,
                "is_available": model.is_available,
                "is_default": model.is_default,
                "rate_limit": model.rate_limit_per_minute,
                "created_at": model.created_at
            }
            
            # 检查用户是否已配置
            user_config = config_repo.get_user_config_for_model(
                current_user["user_id"], 
                model.model_id
            )
            
            if user_config:
                model_info["has_config"] = True
                model_info["config_enabled"] = user_config.is_enabled
                model_info["last_used"] = user_config.last_used_at
            else:
                model_info["has_config"] = False
                model_info["config_enabled"] = False
                model_info["last_used"] = None
            
            result.append(model_info)
        
        # 按提供商分组
        grouped_models = {}
        for model in result:
            provider = model["model_provider"]
            if provider not in grouped_models:
                grouped_models[provider] = []
            grouped_models[provider].append(model)
        
        return {
            "success": True,
            "message": "获取系统模型列表成功",
            "data": {
                "models": result,
                "grouped_by_provider": grouped_models,
                "total": len(result)
            }
        }
        
    except Exception as e:
        logger.error(f"获取系统模型列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模型列表失败"
        )


# app/api/v1/models.py - 添加测试API密钥端点

@router.post("/config/test-api-key")
async def test_model_api_key(
    test_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    测试API密钥是否有效
    - 发送一个测试请求到API
    - 验证密钥是否有效
    """
    try:
        model_id = test_data.get("model_id")
        api_key = test_data.get("api_key")
        custom_endpoint = test_data.get("custom_endpoint")
        
        if not model_id or not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供model_id和api_key"
            )
        
        from app.repositories.system_model_repository import SystemModelRepository
        from app.services.model_router import ModelRouterService
        
        system_repo = SystemModelRepository(db)
        model_router = ModelRouterService(db)
        
        # 获取模型信息
        system_model = system_repo.get_by_id(model_id)
        if not system_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )
        
        # 构造测试消息
        test_message = "Hello, this is a test message. Please respond with 'OK' if you receive this."
        
        try:
            # 尝试调用API
            result = await model_router.chat_completion(
                user_id=current_user["user_id"],
                model_name=system_model.model_name,
                message=test_message,
                temperature=0.1,  # 使用低温度确保确定性响应
                max_tokens=10,
                stream=False
            )
            
            # 如果有响应，说明API密钥有效
            if result.get("response"):
                return {
                    "success": True,
                    "message": "API密钥测试通过",
                    "data": {
                        "model": system_model.model_name,
                        "provider": system_model.model_provider,
                        "test_result": "success",
                        "response_preview": result["response"][:100]
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "API密钥测试失败：无响应",
                    "data": {
                        "model": system_model.model_name,
                        "provider": system_model.model_provider,
                        "test_result": "failed"
                    }
                }
                
        except Exception as api_error:
            logger.warning(f"API密钥测试失败: {api_error}")
            return {
                "success": False,
                "message": f"API密钥测试失败: {str(api_error)}",
                "data": {
                    "model": system_model.model_name,
                    "provider": system_model.model_provider,
                    "test_result": "failed",
                    "error_detail": str(api_error)
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试API密钥异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试API密钥失败: {str(e)}"
        )
