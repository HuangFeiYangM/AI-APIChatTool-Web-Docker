# app/tests/test_all_repositories.py
import sys
import os
from pathlib import Path



# 修正路径 - 向上三级到项目根目录 (test2)
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # 到test2目录
sys.path.insert(0, str(project_root))

print(f"项目根目录: {project_root}")
print(f"Python路径: {sys.path[0]}")

import pytest
from datetime import datetime, timedelta
from app.models.system_model import ModelType

try:
    from app.database import init_database, get_engine, Base
    
    # 先初始化数据库，这样才能访问_SessionLocal
    init_database()
    
    # 导入_SessionLocal
    import app.database as db_module
    
    # 检查_SessionLocal是否存在
    if hasattr(db_module, '_SessionLocal'):
        SessionLocal = db_module._SessionLocal
        print("✅ 使用_SessionLocal")
    elif hasattr(db_module, 'SessionLocal'):
        SessionLocal = db_module.SessionLocal
        print("✅ 使用SessionLocal")
    else:
        raise AttributeError("database模块中没有SessionLocal或_SessionLocal")
    
    from app.repositories import (
        UserRepository, ConversationRepository, MessageRepository,
        SystemModelRepository, UserModelConfigRepository, ApiCallLogRepository
    )
    
    print("✅ 所有导入成功")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("尝试动态导入...")
    
    # 尝试动态导入
    sys.path.insert(0, str(project_root))
    
    try:
        import app.database as database
        import app.repositories as repositories
        
        # 初始化数据库
        database.init_database()
        
        # 获取SessionLocal
        if hasattr(database, '_SessionLocal'):
            SessionLocal = database._SessionLocal
        elif hasattr(database, 'SessionLocal'):
            SessionLocal = database.SessionLocal
        else:
            raise AttributeError("database模块中没有SessionLocal或_SessionLocal")
        
        # 设置别名
        init_database = database.init_database
        get_engine = database.get_engine
        Base = database.Base  # 从database导入Base
        
        UserRepository = repositories.UserRepository
        ConversationRepository = repositories.ConversationRepository
        MessageRepository = repositories.MessageRepository
        SystemModelRepository = repositories.SystemModelRepository
        UserModelConfigRepository = repositories.UserModelConfigRepository
        ApiCallLogRepository = repositories.ApiCallLogRepository
        
        print("✅ 动态导入成功")
    except Exception as e2:
        print(f"❌ 动态导入失败: {e2}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@pytest.fixture(scope="function")
def db_session():
    """数据库会话fixture"""
    # 确保数据库已初始化
    init_database()
    engine = get_engine()
    
    # 创建表（如果不存在）
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestCompleteRepositories:
    """完整测试所有Repository"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_session):
        """每个测试前后的设置和清理"""
        self.db = db_session
        
        # 创建Repository实例
        self.user_repo = UserRepository(self.db)
        self.conv_repo = ConversationRepository(self.db)
        self.msg_repo = MessageRepository(self.db)
        self.model_repo = SystemModelRepository(self.db)
        self.config_repo = UserModelConfigRepository(self.db)
        self.log_repo = ApiCallLogRepository(self.db)
        
        # 清理旧数据
        self._cleanup_data()
        
        # 创建一个基础的测试模型，供所有测试使用
        self.base_model = self._create_base_test_model()
        
        yield
        
        # 测试后清理
        self._cleanup_data()
    
    # def _create_base_test_model(self):
    #     """创建基础的测试模型"""
    #     return self.model_repo.create({
    #         "model_name": "base-test-model",
    #         "model_provider": "TestProvider",
    #         "model_type": "chat",
    #         "api_endpoint": "https://test.com/api/v1",
    #         "is_available": True,
    #         "description": "基础测试模型"
    #     })
    
    # def _create_base_test_model(self):
    #     """创建基础的测试模型"""
    #     return self.model_repo.create({
    #         "model_name": "base-test-model",
    #         "model_provider": "TestProvider",
    #         "model_type": ModelType.chat.value,  # 使用枚举值而不是字符串
    #         "api_endpoint": "https://test.com/api/v1",
    #         "is_available": True,
    #         "description": "基础测试模型"
    # })
    
    def _create_base_test_model(self):
        """创建基础的测试模型"""
        return self.model_repo.create({
            "model_name": "base-test-model",
            "model_provider": "TestProvider",
            "model_type": ModelType.chat,  # 注意：小写
            "api_endpoint": "https://test.com/api/v1",
            "is_available": True,
            "description": "基础测试模型"
    })
    
    def _cleanup_data(self):
        """清理测试数据"""
        from app.models import (
            ApiCallLog, UserModelConfig, Message, Conversation, User, SystemModel
        )
        
        try:
            # 注意删除顺序（外键约束）
            # 先删除有外键依赖的表
            self.db.query(ApiCallLog).delete()
            self.db.query(Message).delete()
            self.db.query(Conversation).delete()
            self.db.query(UserModelConfig).delete()
            self.db.query(User).delete()
            
            # 删除测试模型（保留基础模型）
            self.db.query(SystemModel).filter(
                SystemModel.model_name.like("%test%")
            ).delete(synchronize_session=False)
            
            self.db.commit()
        except Exception as e:
            print(f"清理数据时出错: {e}")
            self.db.rollback()
    
    # 测试方法保持不变...
    def test_user_repository_operations(self):
        """测试UserRepository"""
        # 创建用户
        user_data = {
            "username": "test_user_1",
            "password_hash": "hashed_pwd_123",
            "email": "test1@example.com"
        }
        user = self.user_repo.create(user_data)
        
        # 测试获取
        user_by_id = self.user_repo.get_by_id(user.user_id)
        assert user_by_id.username == "test_user_1"
        
        user_by_name = self.user_repo.get_by_username("test_user_1")
        assert user_by_name.email == "test1@example.com"
        
        # 测试搜索
        users = self.user_repo.search_users(username="test_user")
        assert len(users) == 1
        
        # 测试统计
        stats = self.user_repo.get_user_stats()
        assert stats["total"] >= 1
        
        print("✅ UserRepository测试通过")
        
        
    
    # ... 其他测试方法保持不变 ...
    
    
    def test_conversation_repository_operations(self):
        """测试ConversationRepository"""
        # 先创建一个用户
        user_data = {
            "username": "conv_test_user",
            "password_hash": "hashed_pwd_123",
            "email": "conv_test@example.com"
        }
        user = self.user_repo.create(user_data)
        
        # 创建对话
        conv_data = {
            "user_id": user.user_id,
            "title": "测试对话",
            "model_id": self.base_model.model_id,
            "total_tokens": 0,
            "message_count": 0
        }
        conversation = self.conv_repo.create(conv_data)
        
        # 测试获取用户对话
        user_conversations = self.conv_repo.get_user_conversations(user.user_id)
        assert len(user_conversations) == 1
        assert user_conversations[0].title == "测试对话"
        
        # 测试获取对话详情
        conv_with_messages = self.conv_repo.get_conversation_with_messages(
            conversation.conversation_id, 
            user.user_id
        )
        assert conv_with_messages is not None
        
        # 测试软删除
        result = self.conv_repo.soft_delete_conversation(
            conversation.conversation_id, 
            user.user_id
        )
        assert result is True
        
        # 测试统计
        stats = self.conv_repo.get_conversation_stats(user.user_id)
        assert stats["total"] == 0  # 已软删除，不计入
        
        print("✅ ConversationRepository测试通过")
    
    def test_message_repository_operations(self):
        """测试MessageRepository"""
        # 先创建用户和对话
        user_data = {
            "username": "msg_test_user",
            "password_hash": "hashed_pwd_123",
            "email": "msg_test@example.com"
        }
        user = self.user_repo.create(user_data)
        
        conv_data = {
            "user_id": user.user_id,
            "title": "消息测试对话",
            "model_id": self.base_model.model_id
        }
        conversation = self.conv_repo.create(conv_data)
        
        # 创建消息
        user_message = self.msg_repo.create_user_message(
            conversation.conversation_id,
            "你好，这是一个测试消息"
        )
        
        assistant_message = self.msg_repo.create_assistant_message(
            conversation.conversation_id,
            "你好！我是助手，很高兴为你服务。",
            self.base_model.model_id
        )
        
        # 测试获取对话消息
        messages = self.msg_repo.get_conversation_messages(conversation.conversation_id)
        assert len(messages) == 2
        
        # 测试获取最后一条消息
        last_message = self.msg_repo.get_last_message(conversation.conversation_id)
        assert last_message.role.value == "assistant"
        
        # 测试消息统计
        stats = self.msg_repo.get_message_stats_by_conversation(conversation.conversation_id)
        assert stats["total_messages"] == 2
        assert stats["user_messages"] == 1
        assert stats["assistant_messages"] == 1
        
        print("✅ MessageRepository测试通过")
    
    def test_system_model_repository_operations(self):
        """测试SystemModelRepository"""
        # 创建模型
        model_data = {
            "model_name": "test-model-1",
            "model_provider": "TestProvider",
            "model_type": "chat",
            "api_endpoint": "https://test.com/api/v1",
            "is_available": True,
            "description": "测试模型"
        }
        model = self.model_repo.create(model_data)
        
        # 测试获取
        model_by_id = self.model_repo.get_by_id(model.model_id)
        assert model_by_id.model_name == "test-model-1"
        
        model_by_name = self.model_repo.get_by_name("test-model-1")
        assert model_by_name.model_provider == "TestProvider"
        
        # 测试获取可用模型
        available_models = self.model_repo.get_available_models()
        assert len(available_models) >= 2  # 至少包含基础模型和新创建的模型
        
        # 测试搜索
        models = self.model_repo.search_models(provider="TestProvider")
        assert len(models) >= 2
        
        print("✅ SystemModelRepository测试通过")
    
    def test_user_model_config_repository_operations(self):
        """测试UserModelConfigRepository"""
        # 先创建用户
        user_data = {
            "username": "config_test_user",
            "password_hash": "hashed_pwd_123",
            "email": "config_test@example.com"
        }
        user = self.user_repo.create(user_data)
        
        # 创建用户模型配置
        config_data = {
            "user_id": user.user_id,
            "model_id": self.base_model.model_id,
            "is_enabled": True,
            "priority": 10
        }
        config = self.config_repo.create(config_data)
        
        # 测试获取用户配置
        user_config = self.config_repo.get_user_config_for_model(
            user.user_id, 
            self.base_model.model_id
        )
        assert user_config is not None
        assert user_config.is_enabled == True
        
        # 测试获取用户所有配置
        user_configs = self.config_repo.get_user_configs(user.user_id)
        assert len(user_configs) == 1
        
        # 测试启用/禁用模型
        result = self.config_repo.disable_user_model(user.user_id, self.base_model.model_id)
        assert result is True
        
        disabled_config = self.config_repo.get_user_config_for_model(
            user.user_id, 
            self.base_model.model_id
        )
        assert disabled_config.is_enabled == False
        
        # 测试更新优先级
        self.config_repo.update_model_priority(user.user_id, self.base_model.model_id, 5)
        updated_config = self.config_repo.get_user_config_for_model(
            user.user_id, 
            self.base_model.model_id
        )
        assert updated_config.priority == 5
        
        print("✅ UserModelConfigRepository测试通过")
    
    def test_api_call_log_repository_operations(self):
        """测试ApiCallLogRepository"""
        # 先创建用户
        user_data = {
            "username": "log_test_user",
            "password_hash": "hashed_pwd_123",
            "email": "log_test@example.com"
        }
        user = self.user_repo.create(user_data)
        
        # 创建对话
        conv_data = {
            "user_id": user.user_id,
            "title": "日志测试对话",
            "model_id": self.base_model.model_id
        }
        conversation = self.conv_repo.create(conv_data)
        
        # 创建API调用日志
        log_data = {
            "user_id": user.user_id,
            "model_id": self.base_model.model_id,
            "conversation_id": conversation.conversation_id,
            "endpoint": "/api/chat",
            "request_tokens": 100,
            "response_tokens": 200,
            "total_tokens": 300,
            "response_time_ms": 1500,
            "status_code": 200,
            "is_success": True
        }
        log = self.log_repo.create(log_data)
        
        # 测试获取
        log_by_id = self.log_repo.get_by_id(log.log_id)
        assert log_by_id.endpoint == "/api/chat"
        
        # 测试获取用户日志
        user_logs = self.log_repo.get_user_api_calls(user.user_id, limit=10)
        assert len(user_logs) == 1
        
        # 测试获取模型日志
        model_logs = self.log_repo.get_model_api_calls(self.base_model.model_id, limit=10)
        assert len(model_logs) == 1
        
        # 测试统计
        stats = self.log_repo.get_api_usage_stats(
            user_id=user.user_id,
            model_id=self.base_model.model_id
        )
        assert stats["total_calls"] == 1
        assert stats["success_rate"] == 1.0
        
        print("✅ ApiCallLogRepository测试通过")










def run_all_tests():
    """手动运行所有测试"""
    print("🔧 开始完整Repository测试...")
    
    try:
        # 使用已经导入的模块
        init_database()
        engine = get_engine()
        
        # 创建表
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            # 创建测试实例
            test = TestCompleteRepositories()
            test.db = db
            
            # 清理数据
            test._cleanup_data()
            
            # 创建基础模型
            test.model_repo = SystemModelRepository(db)
            test.base_model = test._create_base_test_model()
            
            # 创建其他Repository实例
            test.user_repo = UserRepository(db)
            test.conv_repo = ConversationRepository(db)
            test.msg_repo = MessageRepository(db)
            test.config_repo = UserModelConfigRepository(db)
            test.log_repo = ApiCallLogRepository(db)
            
            print("\n=== 测试UserRepository ===")
            test.test_user_repository_operations()
            
            print("\n=== 测试ConversationRepository ===")
            test.test_conversation_repository_operations()
            
            print("\n=== 测试MessageRepository ===")
            test.test_message_repository_operations()
            
            print("\n=== 测试SystemModelRepository ===")
            test.test_system_model_repository_operations()
            
            print("\n=== 测试UserModelConfigRepository ===")
            test.test_user_model_config_repository_operations()
            
            print("\n=== 测试ApiCallLogRepository ===")
            test.test_api_call_log_repository_operations()
            
            print("\n🎉 所有Repository测试通过！")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
