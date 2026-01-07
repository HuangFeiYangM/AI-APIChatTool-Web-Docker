# app/api/health.py
"""
健康检查API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get("/")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "service": "multi-model-platform-backend",
        "timestamp": "2023-01-01T00:00:00Z"
    }


@router.get("/database")
async def database_health_check(db: Session = Depends(get_db)):
    """数据库连接检查"""
    try:
        # 执行简单的SQL查询
        result = db.execute(text("SELECT 1")).scalar()
        return {
            "status": "healthy",
            "database": "connected",
            "check_result": result
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
