# scripts/init_db.py
"""
数据库初始化脚本
替代Alembic，用于创建表结构和插入基础数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import init_database, get_engine, Base
from app.utils.logger import setup_logging, get_logger
from app.config import settings

# 设置日志
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def create_tables():
    """创建所有表"""
    try:
        logger.info("开始创建数据库表...")
        
        # 导入所有模型以注册它们
        from app.models import User, Conversation, Message, SystemModel, UserModelConfig, ApiCallLog
        
        # 创建表
        Base.metadata.create_all(bind=get_engine())
        logger.info("✅ 数据库表创建完成")
        return True
    except Exception as e:
        logger.error(f"❌ 创建数据库表失败: {e}")
        return False


def insert_system_models():
    """插入系统默认模型配置"""
    try:
        from sqlalchemy.orm import Session
        from app.database import get_engine
        from app.models.system_model import SystemModel, ModelType
        
        engine = get_engine()
        with Session(engine) as session:
            # 检查是否已有数据
            existing = session.query(SystemModel).count()
            if existing > 0:
                logger.info("系统模型数据已存在，跳过插入")
                return True
            
            # 插入默认模型配置（与database_v2.0.txt一致）
            system_models = [
                SystemModel(
                    model_name="gpt-3.5-turbo",
                    model_provider="OpenAI",
                    model_type=ModelType.CHAT,
                    api_endpoint="https://api.openai.com/v1/chat/completions",
                    api_version="v1",
                    is_default=True,
                    description="OpenAI GPT-3.5 Turbo模型"
                ),
                SystemModel(
                    model_name="gpt-4",
                    model_provider="OpenAI",
                    model_type=ModelType.CHAT,
                    api_endpoint="https://api.openai.com/v1/chat/completions",
                    api_version="v1",
                    is_default=False,
                    description="OpenAI GPT-4模型"
                ),
                SystemModel(
                    model_name="deepseek-chat",
                    model_provider="DeepSeek",
                    model_type=ModelType.CHAT,
                    api_endpoint="https://api.deepseek.com/chat/completions",
                    api_version="v1",
                    is_default=False,
                    description="DeepSeek Chat模型"
                ),
                SystemModel(
                    model_name="deepseek-coder",
                    model_provider="DeepSeek",
                    model_type=ModelType.CHAT,
                    api_endpoint="https://api.deepseek.com/chat/completions",
                    api_version="v1",
                    is_default=False,
                    description="DeepSeek Coder模型"
                ),
                SystemModel(
                    model_name="ernie-bot",
                    model_provider="Baidu",
                    model_type=ModelType.CHAT,
                    api_endpoint="https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
                    api_version="v2",
                    is_default=False,
                    description="百度文心一言模型"
                ),
                SystemModel(
                    model_name="claude-3-sonnet",
                    model_provider="Anthropic",
                    model_type=ModelType.CHAT,
                    api_endpoint="https://api.anthropic.com/v1/messages",
                    api_version="2023-06-01",
                    is_default=False,
                    description="Anthropic Claude 3 Sonnet模型"
                ),
                SystemModel(
                    model_name="llama-3-8b",
                    model_provider="Meta",
                    model_type=ModelType.CHAT,
                    api_endpoint="https://api.replicate.com/v1/predictions",
                    api_version="v1",
                    is_default=False,
                    description="Meta Llama 3 8B模型"
                ),
            ]
            
            session.add_all(system_models)
            session.commit()
            logger.info(f"✅ 插入了 {len(system_models)} 个系统模型配置")
            return True
            
    except Exception as e:
        logger.error(f"❌ 插入系统模型数据失败: {e}")
        return False


def create_admin_user():
    """创建管理员用户（根据database_v2.0.txt）"""
    try:
        from sqlalchemy.orm import Session
        from app.database import get_engine
        from app.models.user import User
        import bcrypt
        
        engine = get_engine()
        with Session(engine) as session:
            # 检查管理员是否已存在
            admin = session.query(User).filter(User.username == "admin").first()
            if admin:
                logger.info("管理员用户已存在，跳过创建")
                return True
            
            # 创建管理员用户（密码：admin123）
            password = "admin123"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            
            admin_user = User(
                username="admin",
                password_hash=password_hash,
                email="admin@example.com",
                is_active=True,
                is_locked=False
            )
            
            session.add(admin_user)
            session.commit()
            logger.info("✅ 管理员用户创建完成 (用户名: admin, 密码: admin123)")
            return True
            
    except Exception as e:
        logger.error(f"❌ 创建管理员用户失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始数据库初始化...")
    logger.info(f"数据库: {settings.DATABASE_URL[:30]}...")
    logger.info("=" * 50)
    
    # 初始化数据库连接
    try:
        init_database()
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False
    
    # 创建表
    if not create_tables():
        return False
    
    # 插入系统模型数据
    if not insert_system_models():
        return False
    
    # 创建管理员用户
    if not create_admin_user():
        return False
    
    logger.info("=" * 50)
    logger.info("✅ 数据库初始化完成！")
    logger.info("=" * 50)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
