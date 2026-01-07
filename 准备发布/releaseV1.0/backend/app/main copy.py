# app/main.py
"""
FastAPI应用入口
"""
import sys
import os
import time
# 获取当前文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（app的父目录）
project_root = os.path.dirname(current_dir)

# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_database, create_tables
from app.middleware import setup_middleware
from app.api.v1.router import router as api_v1_router

# 配置日志
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler() if settings.ENABLE_CONSOLE else logging.NullHandler(),
        *([logging.FileHandler(settings.LOG_FILE)] if settings.LOG_FILE else []),
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（FastAPI 2.4+推荐）"""
    # 启动时
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} 正在启动...")
    
    try:
        # 初始化数据库
        init_database()
        logger.info("✅ 数据库连接初始化完成")
        
        # 创建表（如果不存在）
        if settings.DEBUG:
            create_tables()
            logger.info("✅ 数据库表检查完成")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise
    
    finally:
        # 关闭时
        logger.info(f"👋 {settings.PROJECT_NAME} 正在关闭...")


# 创建FastAPI应用（使用lifespan）
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="多模型平台后端API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,  # 使用lifespan管理器
)

# 设置CORS（应该在其他中间件之前）
app.add_middleware(
    CORSMiddleware,
    # allow_origins=settings.CORS_ORIGINS,
    allow_origins=["http://localhost:8080", "https://frp-shy.com:11687", "http://frp-shy.com:11687","http://127.0.0.1:8080"],  # 只保留这一个
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 设置其他中间件（顺序重要）
setup_middleware(app)

# 注册API路由
app.include_router(api_v1_router, prefix="/api/v1")

# 根路径
@app.get("/")
async def root():
    return {
        "message": "欢迎使用多模型平台API",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "api": "/api/v1"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    from app.database import check_connection
    db_status = check_connection()
    
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "timestamp": time.time(),
        "version": settings.VERSION
    }
