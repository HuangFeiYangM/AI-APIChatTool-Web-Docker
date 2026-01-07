# test_setup.py
# 启动：/（根目录）
"""测试配置文件"""
import sys
from pathlib import Path
from sqlalchemy import text  # 添加导入

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.database import init_database  # 新增：导入init_database

# 设置日志
setup_logging(log_level="DEBUG")
logger = get_logger(__name__)

def test_config():
    """测试配置加载"""
    logger.info("开始测试配置...")
    
    print(f"\n📋 配置信息:")
    print(f"   项目名称: {settings.PROJECT_NAME}")
    print(f"   版本: {settings.VERSION}")
    print(f"   调试模式: {settings.DEBUG}")
    print(f"   数据库URL: {settings.DATABASE_URL[:50]}...")
    print(f"   服务器: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"   API前缀: {settings.API_V1_STR}")
    print(f"   日志级别: {settings.LOG_LEVEL}")
    
    logger.info("配置测试完成 ✓")

def test_database():
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    try:
        # 第一步：初始化数据库
        init_database()
        
        # 第二步：测试连接
        from app.database import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                logger.info("✅ 数据库连接成功 ✓")
                return True
            else:
                logger.error("❌ 数据库连接测试返回异常")
                return False
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

def test_logger():
    """测试日志系统"""
    logger.debug("这是一条DEBUG消息")
    logger.info("这是一条INFO消息")
    logger.warning("这是一条WARNING消息")
    logger.error("这是一条ERROR消息")
    
    # 测试其他模块的日志
    from app.utils.logger import get_logger
    test_logger = get_logger("test.module")
    test_logger.info("这是来自test.module的日志")
    
    logger.info("日志系统测试完成 ✓")

if __name__ == "__main__":
    print("🔧 开始后端环境测试...\n")
    
    # 测试配置
    test_config()
    print()
    
    # 测试数据库
    if test_database():
        print()
        # 测试日志
        test_logger()
        print()
        print("🎉 所有测试完成！后端基础环境正常。")
        print("\n接下来可以运行: python -m uvicorn app.main:app --reload")
    else:
        print("\n❌ 数据库连接失败，请检查配置和MySQL服务")
