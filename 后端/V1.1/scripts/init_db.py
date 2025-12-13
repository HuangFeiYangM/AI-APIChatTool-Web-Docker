# scripts/init_db.py
#!/usr/bin/env python3
"""
数据库初始化脚本 - 用于Docker容器启动时初始化数据库
"""
import os
import sys
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db(db_url, max_retries=30, retry_interval=2):
    """等待数据库连接就绪"""
    for i in range(max_retries):
        try:
            engine = create_engine(db_url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ 数据库连接成功")
            return True
        except OperationalError as e:
            if i < max_retries - 1:
                logger.warning(f"⏳ 等待数据库... ({i+1}/{max_retries}) - {e}")
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ 数据库连接失败: {e}")
                return False
    return False

def init_database():
    """初始化数据库"""
    # 从环境变量获取数据库URL
    db_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@mysql:3306/mysql8db?charset=utf8mb4")
    
    logger.info(f"🔗 连接数据库: {db_url.split('@')[1].split('?')[0] if '@' in db_url else db_url}")
    
    # 等待数据库就绪
    if not wait_for_db(db_url):
        sys.exit(1)
    
    try:
        # 创建SQLAlchemy引擎
        engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            echo=False
        )
        
        # 检查数据库是否已初始化
        with engine.connect() as conn:
            # 检查users表是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'mysql8db' 
                AND table_name = 'users'
            """))
            table_exists = result.scalar() > 0
            
            if table_exists:
                logger.info("✅ 数据库已初始化，跳过初始化步骤")
                return True
            
            logger.info("🔄 开始初始化数据库...")
            
            # 读取初始化SQL文件
            sql_file_path = "/docker-entrypoint-initdb.d/init_v1.0.sql"
            if os.path.exists(sql_file_path):
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # 按语句分割并执行
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for stmt in statements:
                    if stmt:  # 跳过空语句
                        try:
                            conn.execute(text(stmt))
                            conn.commit()
                        except Exception as e:
                            logger.warning(f"⚠️  执行语句时忽略错误: {e}")
                            conn.rollback()
                            continue
                
                logger.info("✅ 数据库初始化完成")
                return True
            else:
                logger.error(f"❌ SQL文件不存在: {sql_file_path}")
                return False
                
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 开始数据库初始化流程...")
    
    success = init_database()
    
    if success:
        logger.info("🎉 数据库初始化流程完成")
        sys.exit(0)
    else:
        logger.error("💥 数据库初始化流程失败")
        sys.exit(1)
