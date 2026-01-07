# app/api/v1/health.py
"""健康检查API路由"""
from fastapi import APIRouter
import time

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "multi-model-platform-backend"
    }


@router.get("/ping")
async def ping():
    """简单ping测试"""
    return {"message": "pong"}
