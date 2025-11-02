from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 数据库连接URL，从配置中读取
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类，用于定义数据模型
Base = declarative_base()

def get_db():
    """
    数据库会话依赖注入函数
    - 在每个请求中提供独立的数据库会话
    - 请求完成后自动关闭会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
