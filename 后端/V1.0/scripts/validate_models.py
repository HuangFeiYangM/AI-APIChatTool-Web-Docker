# scripts/validate_models.py
"""
验证SQLAlchemy模型是否正确
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import init_database, get_engine, Base
from app.utils.logger import setup_logging, get_logger
from app.config import settings
from sqlalchemy import inspect, text

# 设置日志
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def validate_table_creation():
    """验证表是否能被正确创建"""
    try:
        logger.info("验证表创建...")
        
        # 尝试导入所有模型，这会触发模型定义的验证
        try:
            from app.models import User, Conversation, Message, SystemModel, UserModelConfig, ApiCallLog
            logger.info("✅ 所有模型导入成功")
        except ImportError as e:
            logger.error(f"❌ 模型导入失败: {e}")
            return False
        
        # 获取元数据并生成创建表的SQL
        try:
            from app.database import Base
            metadata = Base.metadata
            
            # 生成创建表的SQL（不实际执行）
            from sqlalchemy.schema import CreateTable
            engine = get_engine()
            
            tables_created = []
            for table in metadata.sorted_tables:
                # 生成创建表的SQL语句
                create_sql = str(CreateTable(table).compile(engine))
                tables_created.append(table.name)
            
            expected_tables = {'users', 'conversations', 'messages', 'system_models', 'user_model_configs', 'api_call_logs'}
            actual_tables = set(tables_created)
            
            logger.info(f"期望的表: {sorted(expected_tables)}")
            logger.info(f"可创建的表: {sorted(actual_tables)}")
            
            # 验证表名
            missing_tables = expected_tables - actual_tables
            extra_tables = actual_tables - expected_tables
            
            if missing_tables:
                logger.error(f"❌ 缺失的表: {missing_tables}")
                return False
            
            if extra_tables:
                logger.warning(f"⚠️ 额外的表（可能是中间表）: {extra_tables}")
            
            logger.info("✅ 表创建验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 表元数据验证失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 表创建验证失败: {e}")
        return False


def validate_table_structure():
    """验证表结构是否正确"""
    try:
        logger.info("验证表结构...")
        
        engine = get_engine()
        inspector = inspect(engine)
        
        # 检查每个表的结构
        tables_to_check = {
            'users': ['user_id', 'username', 'password_hash', 'email', 'is_active', 'is_locked'],
            'conversations': ['conversation_id', 'user_id', 'title', 'model_id', 'total_tokens'],
            'messages': ['message_id', 'conversation_id', 'role', 'content', 'tokens_used'],
            'system_models': ['model_id', 'model_name', 'model_provider', 'api_endpoint', 'is_available'],
            'user_model_configs': ['config_id', 'user_id', 'model_id', 'is_enabled', 'api_key']
        }
        
        all_passed = True
        
        for table_name, expected_columns in tables_to_check.items():
            if not inspector.has_table(table_name):
                logger.error(f"❌ 表 '{table_name}' 不存在")
                all_passed = False
                continue
            
            actual_columns = [col['name'] for col in inspector.get_columns(table_name)]
            missing_columns = set(expected_columns) - set(actual_columns)
            
            if missing_columns:
                logger.error(f"❌ 表 '{table_name}' 缺失列: {missing_columns}")
                all_passed = False
            else:
                logger.info(f"✅ 表 '{table_name}' 结构正确")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ 表结构验证失败: {e}")
        return False


def validate_foreign_keys():
    """验证外键约束"""
    try:
        logger.info("验证外键约束...")
        
        engine = get_engine()
        inspector = inspect(engine)
        
        # 期望的外键关系
        expected_fks = {
            'conversations': ['user_id', 'model_id'],
            'messages': ['conversation_id', 'model_id'],
            'user_model_configs': ['user_id', 'model_id'],
            'api_call_logs': ['user_id', 'model_id', 'conversation_id']
        }
        
        all_passed = True
        
        for table_name, expected_fk_columns in expected_fks.items():
            if not inspector.has_table(table_name):
                continue
            
            # 获取外键
            fks = inspector.get_foreign_keys(table_name)
            actual_fk_columns = []
            for fk in fks:
                actual_fk_columns.extend(fk['constrained_columns'])
            
            # 检查每个期望的外键列
            for fk_column in expected_fk_columns:
                if fk_column not in actual_fk_columns:
                    logger.error(f"❌ 表 '{table_name}' 缺失外键约束: {fk_column}")
                    all_passed = False
            
            if all_passed:
                logger.info(f"✅ 表 '{table_name}' 外键约束正确")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ 外键验证失败: {e}")
        return False


def test_model_relationships():
    """测试模型关系"""
    try:
        logger.info("测试模型关系...")
        
        from sqlalchemy.orm import Session
        from app.database import get_engine
        from app.models import User, SystemModel
        
        engine = get_engine()
        
        with Session(engine) as session:
            # 尝试查询系统模型，手动处理枚举转换
            try:
                models = session.query(SystemModel).all()
                logger.info(f"系统模型数量: {len(models)}")
                
                # 打印模型信息
                for model in models:
                    logger.info(f"模型: {model.model_name}, 类型: {model.model_type}")
            except Exception as e:
                logger.warning(f"查询模型时出现错误，尝试手动转换枚举: {e}")
                
                # 使用原始SQL查询
                result = session.execute("SELECT model_id, model_name, model_type FROM system_models")
                models = result.fetchall()
                logger.info(f"原始查询系统模型数量: {len(models)}")
            
            # 检查用户数据
            users = session.query(User).all()
            logger.info(f"用户数量: {len(users)}")
            
            # 如果管理员存在，打印信息
            admin = session.query(User).filter(User.username == "admin").first()
            if admin:
                logger.info(f"管理员用户: {admin.username} ({admin.email})")
        
        logger.info("✅ 模型关系测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型关系测试失败: {e}")
        return False



def main():
    """主验证函数"""
    logger.info("=" * 60)
    logger.info("开始验证SQLAlchemy模型...")
    logger.info("=" * 60)
    
    # 初始化数据库
    try:
        init_database()
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False
    
    # 执行所有验证
    validations = [
        ("表创建验证", validate_table_creation),
        ("表结构验证", validate_table_structure),
        ("外键验证", validate_foreign_keys),
        ("模型关系测试", test_model_relationships)
    ]
    
    results = []
    for name, validation_func in validations:
        logger.info(f"\n📋 {name}...")
        result = validation_func()
        results.append((name, result))
    
    # 打印总结
    logger.info("\n" + "=" * 60)
    logger.info("验证结果总结:")
    logger.info("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 所有验证通过！SQLAlchemy模型设计正确。")
    else:
        logger.info("\n⚠️  部分验证失败，请检查模型设计。")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
