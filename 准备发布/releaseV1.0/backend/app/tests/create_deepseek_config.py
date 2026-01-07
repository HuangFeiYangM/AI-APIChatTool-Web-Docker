# scripts/create_deepseek_config.py
# 运行 scripts/run_deepseek_test.py
"""
为test2用户创建DeepSeek模型配置的脚本
"""
import sys
import os
import logging

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import get_db, init_database
from app.repositories.user_repository import UserRepository
from app.repositories.system_model_repository import SystemModelRepository
from app.repositories.user_model_config_repository import UserModelConfigRepository
from app.core.security import encrypt_api_key

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_deepseek_config():
    """为test2用户创建DeepSeek模型配置"""
    try:
        # 初始化数据库
        init_database()
        
        # 获取数据库会话
        db_gen = get_db()
        db = next(db_gen)
        
        # 创建Repository实例
        user_repo = UserRepository(db)
        model_repo = SystemModelRepository(db)
        config_repo = UserModelConfigRepository(db)
        
        # 1. 查找test2用户
        test2_user = user_repo.get_by_username("test2")
        if not test2_user:
            logger.error("用户test2不存在")
            return False
        
        logger.info(f"找到用户: {test2_user.username} (ID: {test2_user.user_id})")
        
        # 2. 查找DeepSeek模型
        # 查找deepseek-chat模型
        deepseek_model = model_repo.get_by_name("deepseek-chat")
        if not deepseek_model:
            logger.error("DeepSeek-chat模型不存在")
            return False
        
        logger.info(f"找到模型: {deepseek_model.model_name} (ID: {deepseek_model.model_id})")
        
        # 3. 检查是否已有配置
        existing_config = config_repo.get_user_config_for_model(
            test2_user.user_id, 
            deepseek_model.model_id
        )
        
        # 你的DeepSeek API密钥
        DEEPSEEK_API_KEY = "sk-d35fc57d5206433bb336ea0fb2b5878b"
        
        # 加密API密钥
        encrypted_key = encrypt_api_key(DEEPSEEK_API_KEY)
        
        if existing_config:
            # 更新现有配置
            update_data = {
                "api_key_encrypted": encrypted_key,
                "api_key": None,  # 清文明文
                "is_enabled": True,
                "temperature": 0.7,
                "max_tokens": 2000,
                "priority": 1
            }
            config_repo.update(existing_config, update_data)
            logger.info("更新了DeepSeek模型配置")
        else:
            # 创建新配置
            config_data = {
                "user_id": test2_user.user_id,
                "model_id": deepseek_model.model_id,
                "api_key_encrypted": encrypted_key,
                "is_enabled": True,
                "temperature": 0.7,
                "max_tokens": 2000,
                "priority": 1
            }
            config_repo.create(config_data)
            logger.info("创建了DeepSeek模型配置")
        
        # 提交更改
        db.commit()
        
        # 验证配置
        new_config = config_repo.get_user_config_for_model(
            test2_user.user_id, 
            deepseek_model.model_id
        )
        
        if new_config and new_config.is_enabled:
            logger.info(f"✅ DeepSeek配置创建/更新成功!")
            logger.info(f"   用户ID: {test2_user.user_id}")
            logger.info(f"   模型ID: {deepseek_model.model_id}")
            logger.info(f"   配置ID: {new_config.config_id}")
            logger.info(f"   是否启用: {new_config.is_enabled}")
            return True
        else:
            logger.error("配置创建/更新失败")
            return False
            
    except Exception as e:
        logger.error(f"创建配置时出错: {e}", exc_info=True)
        return False
    finally:
        try:
            db.close()
        except:
            pass


def create_config_for_all_deepseek_models():
    """为test2用户配置所有DeepSeek模型"""
    try:
        # 初始化数据库
        init_database()
        
        # 获取数据库会话
        db_gen = get_db()
        db = next(db_gen)
        
        # 创建Repository实例
        user_repo = UserRepository(db)
        model_repo = SystemModelRepository(db)
        config_repo = UserModelConfigRepository(db)
        
        # 查找test2用户
        test2_user = user_repo.get_by_username("test2")
        if not test2_user:
            logger.error("用户test2不存在")
            return False
        
        # 查找所有DeepSeek模型
        deepseek_models = []
        all_models = model_repo.get_all()
        for model in all_models:
            if "deepseek" in model.model_name.lower():
                deepseek_models.append(model)
        
        if not deepseek_models:
            logger.error("没有找到DeepSeek模型")
            return False
        
        logger.info(f"找到 {len(deepseek_models)} 个DeepSeek模型")
        
        # 你的DeepSeek API密钥
        DEEPSEEK_API_KEY = "sk-d35fc57d5206433bb336ea0fb2b5878b"
        encrypted_key = encrypt_api_key(DEEPSEEK_API_KEY)
        
        for model in deepseek_models:
            logger.info(f"处理模型: {model.model_name}")
            
            # 检查是否已有配置
            existing_config = config_repo.get_user_config_for_model(
                test2_user.user_id, 
                model.model_id
            )
            
            if existing_config:
                # 更新现有配置
                update_data = {
                    "api_key_encrypted": encrypted_key,
                    "api_key": None,
                    "is_enabled": True,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "priority": 1
                }
                config_repo.update(existing_config, update_data)
                logger.info(f"   ✓ 更新了 {model.model_name} 配置")
            else:
                # 创建新配置
                config_data = {
                    "user_id": test2_user.user_id,
                    "model_id": model.model_id,
                    "api_key_encrypted": encrypted_key,
                    "is_enabled": True,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "priority": 1
                }
                config_repo.create(config_data)
                logger.info(f"   ✓ 创建了 {model.model_name} 配置")
        
        db.commit()
        logger.info("✅ 所有DeepSeek模型配置完成!")
        return True
        
    except Exception as e:
        logger.error(f"配置模型时出错: {e}", exc_info=True)
        return False
    finally:
        try:
            db.close()
        except:
            pass


if __name__ == "__main__":
    print("=" * 60)
    print("为test2用户创建DeepSeek模型配置")
    print("=" * 60)
    
    # 选择配置方式
    choice = input("请选择配置方式:\n1. 仅配置deepseek-chat模型\n2. 配置所有DeepSeek模型\n请选择 (1/2): ").strip()
    
    if choice == "1":
        success = create_deepseek_config()
    elif choice == "2":
        success = create_config_for_all_deepseek_models()
    else:
        print("❌ 无效的选择")
        success = False
    
    if success:
        print("\n✅ 配置完成! 现在可以运行测试脚本了。")
    else:
        print("\n❌ 配置失败，请检查错误信息。")
