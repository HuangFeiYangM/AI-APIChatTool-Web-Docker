# scripts/create_test_config.py
"""
为test2用户创建DeepSeek模型配置 - 修复导入问题
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入必要的模块
from app.config import settings
from app.database import get_db, init_database
from app.models.user import User
from app.models.system_model import SystemModel
from app.models.user_model_config import UserModelConfig
from app.core.security import get_password_hash

def create_test_config():
    """为test2用户创建DeepSeek模型配置"""
    # 先初始化数据库
    print("正在初始化数据库连接...")
    init_database()
    
    # 使用get_db的生成器模式获取数据库会话
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        print("1. 查找test2用户...")
        
        # 查找test2用户
        user = db.query(User).filter(User.username == "test2").first()
        if not user:
            print("❌ 找不到test2用户，正在创建...")
            
            # 创建test2用户
            user = User(
                username="test2",
                password_hash=get_password_hash("123456"),
                email="test2@example.com",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ 创建test2用户成功，ID: {user.user_id}")
        else:
            print(f"✅ 找到test2用户，ID: {user.user_id}")
        
        print("\n2. 查找DeepSeek模型...")
        
        # 查找deepseek-chat模型
        model = db.query(SystemModel).filter(
            SystemModel.model_name == "deepseek-chat",
            SystemModel.model_provider == "DeepSeek"
        ).first()
        
        if not model:
            # 创建deepseek-chat模型配置
            model = SystemModel(
                model_name="deepseek-chat",
                model_provider="DeepSeek",
                model_type="chat",
                api_endpoint="https://api.deepseek.com/chat/completions",
                api_version="v1",
                is_available=True,
                is_default=False,
                rate_limit_per_minute=60,
                max_tokens=4096,
                description="DeepSeek Chat模型"
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            print(f"✅ 创建deepseek-chat模型成功，ID: {model.model_id}")
        else:
            print(f"✅ 找到deepseek-chat模型，ID: {model.model_id}")
        
        print("\n3. 为用户test2配置DeepSeek API...")
        
        # 检查是否已有配置
        existing_config = db.query(UserModelConfig).filter(
            UserModelConfig.user_id == user.user_id,
            UserModelConfig.model_id == model.model_id
        ).first()
        
        if existing_config:
            # 更新现有配置
            existing_config.api_key = "sk-d35fc57d5206433bb336ea0fb2b5878b"
            existing_config.is_enabled = True
            existing_config.priority = 10
            existing_config.temperature = 0.7
            existing_config.max_tokens = 2000
            db.commit()
            print(f"✅ 更新用户配置成功，配置ID: {existing_config.config_id}")
        else:
            # 创建新配置
            config = UserModelConfig(
                user_id=user.user_id,
                model_id=model.model_id,
                is_enabled=True,
                api_key="sk-d35fc57d5206433bb336ea0fb2b5878b",
                custom_endpoint="https://api.deepseek.com",
                max_tokens=2000,
                temperature=0.7,
                priority=10
            )
            db.add(config)
            db.commit()
            db.refresh(config)
            print(f"✅ 创建用户配置成功，配置ID: {config.config_id}")
        
        print("\n🎉 所有配置完成！")
        print(f"用户: {user.username} (ID: {user.user_id})")
        print(f"模型: {model.model_name} (ID: {model.model_id})")
        print(f"API密钥已设置")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置过程出错: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        try:
            next(db_gen)  # 完成生成器
        except StopIteration:
            pass

if __name__ == "__main__":
    create_test_config()
