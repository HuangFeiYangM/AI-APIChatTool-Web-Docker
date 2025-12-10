# app/database.py
"""
数据库连接和会话管理
使用SQLAlchemy ORM
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional
import logging

from app.config import settings

# 获取日志器
logger = logging.getLogger(__name__)

# SQLAlchemy基类
Base = declarative_base()

# 数据库引擎和会话工厂
_engine = None
_SessionLocal = None


def init_database() -> None:
    """
    初始化数据库连接
    注意：这个函数需要在应用启动时调用一次
    """
    global _engine, _SessionLocal
    
    try:
        logger.info("正在初始化数据库连接...")
        
        # 创建引擎，使用连接池
        _engine = create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_pre_ping=True,  # 每次连接前ping数据库
            echo=settings.DATABASE_ECHO,  # 输出SQL语句
            future=True,
            echo_pool=settings.DEBUG,  
        )
        
        # 创建会话工厂
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
            class_=Session,
            expire_on_commit=False,  # 提交后不使实例过期
        )
        
        # 注册事件监听器（必须在engine创建之后）
        _setup_event_listeners()
        
        logger.info(f"✅ 数据库连接初始化成功 (池大小: {settings.DATABASE_POOL_SIZE})")
        
        # 测试连接
        _test_connection()
        
    except Exception as e:
        logger.error(f"❌ 数据库连接初始化失败: {e}")
        raise


def _test_connection() -> None:
    """测试数据库连接是否正常"""
    if _engine is None:
        raise RuntimeError("数据库引擎未初始化")
    
    try:
        with _engine.connect() as conn:
            # 执行简单查询测试连接
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("✅ 数据库连接测试通过")
            else:
                logger.warning("⚠️ 数据库连接测试返回异常")
    except OperationalError as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 数据库连接测试异常: {e}")
        raise


def _setup_event_listeners() -> None:
    """设置数据库事件监听器"""
    if _engine is None:
        return
    
    @event.listens_for(_engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        """连接创建时的回调"""
        if settings.DEBUG:
            logger.debug(f"数据库连接创建")

    @event.listens_for(_engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """从连接池取出连接时的回调"""
        if settings.DEBUG:
            logger.debug(f"数据库连接取出")

    @event.listens_for(_engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        """连接放回连接池时的回调"""
        if settings.DEBUG:
            logger.debug(f"数据库连接放回")


def get_engine():
    """获取数据库引擎实例"""
    if _engine is None:
        raise RuntimeError("数据库引擎未初始化，请先调用init_database()")
    return _engine


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖函数
    用于FastAPI依赖注入
    """
    if _SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用init_database()")
    
    db: Optional[Session] = None
    try:
        db = _SessionLocal()
        logger.debug("数据库会话创建")
        yield db
    except SQLAlchemyError as e:
        logger.error(f"数据库会话异常: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()
            logger.debug("数据库会话关闭")


def create_tables() -> None:
    """
    创建所有表（仅在开发环境使用）
    注意：数据库已存在，此函数仅用于创建缺失的表
    """
    engine = get_engine()
    
    try:
        logger.info("正在检查并创建数据库表...")
        # 导入所有模型，确保它们被注册
        from app.models import user, conversation, message, system_model, user_model_config
        # 创建表（如果不存在）
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建/检查完成")
    except Exception as e:
        logger.error(f"❌ 数据库表创建失败: {e}")
        raise


def check_connection() -> bool:
    """
    检查数据库连接是否正常
    返回: True表示正常，False表示异常
    """
    try:
        _test_connection()
        return True
    except Exception:
        return False


# 移除模块末尾的自动初始化代码
# 改为在应用启动时显式调用init_database()
