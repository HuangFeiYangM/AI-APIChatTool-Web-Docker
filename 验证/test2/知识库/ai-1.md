# 阶段1：建立基础数据层 - SQLAlchemy模型设计

## 1. 项目准备

首先确认目录结构已存在：
```
multi-model-platform-backend/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── system_model.py
│   │   └── user_model_config.py
│   ├── database.py
│   └── config.py
```

## 2. SQLAlchemy模型设计

### 2.1 用户模型 (`app/models/user.py`)

```python
# app/models/user.py
"""
用户模型
对应数据库表：users
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime

from app.database import Base


class User(Base):
    """用户表模型"""
    __tablename__ = "users"
    __table_args__ = {
        'comment': '用户表'
    }

    user_id = Column(Integer, primary_key=True, index=True, comment='用户ID')
    username = Column(String(255), nullable=False, unique=True, index=True, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    email = Column(String(255), unique=True, index=True, comment='邮箱')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    is_locked = Column(Boolean, default=False, nullable=False, comment='是否锁定')
    locked_reason = Column(String(500), comment='锁定原因')
    locked_until = Column(DateTime, comment='锁定到期时间')
    failed_login_attempts = Column(Integer, default=0, nullable=False, comment='登录失败次数')
    last_login_at = Column(DateTime, comment='最后登录时间')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    # 关系定义
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    user_model_configs = relationship("UserModelConfig", back_populates="user", cascade="all, delete-orphan")
    api_call_logs = relationship("ApiCallLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', email='{self.email}')>"

    def is_account_locked(self) -> bool:
        """检查账户是否被锁定"""
        if not self.is_locked:
            return False
        if self.locked_until and self.locked_until < datetime.now():
            return False  # 锁定已过期
        return True

    def increment_failed_attempts(self):
        """增加登录失败次数"""
        self.failed_login_attempts += 1
        self.updated_at = datetime.now()

    def reset_failed_attempts(self):
        """重置登录失败次数"""
        self.failed_login_attempts = 0
        self.is_locked = False
        self.locked_reason = None
        self.locked_until = None
        self.updated_at = datetime.now()

    def lock_account(self, reason: str, lock_hours: int = 24):
        """锁定账户"""
        from datetime import datetime, timedelta
        
        self.is_locked = True
        self.locked_reason = reason
        self.locked_until = datetime.now() + timedelta(hours=lock_hours)
        self.updated_at = datetime.now()

    def unlock_account(self):
        """解锁账户"""
        self.is_locked = False
        self.locked_reason = None
        self.locked_until = None
        self.failed_login_attempts = 0
        self.updated_at = datetime.now()
```

### 2.2 系统模型配置 (`app/models/system_model.py`)

```python
# app/models/system_model.py
"""
系统模型配置模型
对应数据库表：system_models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ModelType(enum.Enum):
    """模型类型枚举"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"


class SystemModel(Base):
    """系统模型配置表模型"""
    __tablename__ = "system_models"
    __table_args__ = {
        'comment': '系统模型配置表'
    }

    model_id = Column(Integer, primary_key=True, index=True, comment='模型ID')
    model_name = Column(String(50), nullable=False, unique=True, index=True, comment='模型名称')
    model_provider = Column(String(50), nullable=False, index=True, comment='模型提供商')
    model_type = Column(Enum(ModelType), default=ModelType.CHAT, nullable=False, comment='模型类型')
    api_endpoint = Column(String(255), nullable=False, comment='API端点')
    api_version = Column(String(20), comment='API版本')
    is_available = Column(Boolean, default=True, nullable=False, comment='是否可用')
    is_default = Column(Boolean, default=False, nullable=False, comment='是否默认模型')
    rate_limit_per_minute = Column(Integer, default=60, nullable=False, comment='每分钟请求限制')
    max_tokens = Column(Integer, default=4096, nullable=False, comment='最大token数')
    description = Column(Text, comment='模型描述')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    # 关系定义
    user_model_configs = relationship("UserModelConfig", back_populates="system_model", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="system_model")
    messages = relationship("Message", back_populates="system_model")
    api_call_logs = relationship("ApiCallLog", back_populates="system_model", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SystemModel(model_id={self.model_id}, model_name='{self.model_name}', provider='{self.model_provider}')>"

    @property
    def is_chat_model(self) -> bool:
        """检查是否为聊天模型"""
        return self.model_type == ModelType.CHAT

    def get_endpoint_url(self, custom_endpoint: str = None) -> str:
        """获取API端点URL"""
        return custom_endpoint or self.api_endpoint

    def validate_config(self) -> bool:
        """验证模型配置是否有效"""
        return all([
            self.model_name,
            self.model_provider,
            self.api_endpoint,
            self.rate_limit_per_minute > 0,
            self.max_tokens > 0
        ])
```

### 2.3 用户模型配置 (`app/models/user_model_config.py`)

```python
# app/models/user_model_config.py
"""
用户模型配置模型
对应数据库表：user_model_configs
"""
from sqlalchemy import Column, Integer, Boolean, DateTime, String, Text, DECIMAL, BLOB, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserModelConfig(Base):
    """用户模型配置表模型"""
    __tablename__ = "user_model_configs"
    __table_args__ = {
        'comment': '用户模型配置表'
    }

    config_id = Column(Integer, primary_key=True, index=True, comment='配置ID')
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    model_id = Column(Integer, ForeignKey('system_models.model_id', ondelete='CASCADE'), nullable=False, comment='模型ID')
    is_enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    api_key = Column(String(500), comment='API密钥')
    api_key_encrypted = Column(BLOB, comment='加密的API密钥')
    custom_endpoint = Column(String(255), comment='自定义端点')
    max_tokens = Column(Integer, comment='自定义最大token数')
    temperature = Column(DECIMAL(3, 2), default=0.7, nullable=False, comment='温度参数')
    priority = Column(Integer, default=0, nullable=False, comment='优先级')
    last_used_at = Column(DateTime, comment='最后使用时间')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    # 关系定义
    user = relationship("User", back_populates="user_model_configs")
    system_model = relationship("SystemModel", back_populates="user_model_configs")

    def __repr__(self):
        return f"<UserModelConfig(config_id={self.config_id}, user_id={self.user_id}, model_id={self.model_id})>"

    def is_active(self) -> bool:
        """检查配置是否激活"""
        return self.is_enabled and (self.api_key or self.api_key_encrypted)

    def update_last_used(self):
        """更新最后使用时间"""
        from datetime import datetime
        self.last_used_at = datetime.now()
        self.updated_at = datetime.now()

    def get_api_key(self, decrypt_func=None) -> str:
        """获取API密钥（支持解密）"""
        if self.api_key:
            return self.api_key
        elif self.api_key_encrypted and decrypt_func:
            return decrypt_func(self.api_key_encrypted)
        return None

    def set_api_key(self, api_key: str, encrypt_func=None):
        """设置API密钥（支持加密）"""
        if encrypt_func and api_key:
            self.api_key_encrypted = encrypt_func(api_key)
            self.api_key = None
        else:
            self.api_key = api_key
            self.api_key_encrypted = None
        self.updated_at = datetime.now()
```

### 2.4 对话模型 (`app/models/conversation.py`)

```python
# app/models/conversation.py
"""
对话模型
对应数据库表：conversations
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Conversation(Base):
    """对话表模型"""
    __tablename__ = "conversations"
    __table_args__ = {
        'comment': '对话表'
    }

    conversation_id = Column(Integer, primary_key=True, index=True, comment='对话ID')
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    title = Column(String(200), comment='对话标题')
    model_id = Column(Integer, ForeignKey('system_models.model_id', ondelete='RESTRICT'), nullable=False, comment='使用的模型ID')
    total_tokens = Column(Integer, default=0, nullable=False, comment='总token数')
    message_count = Column(Integer, default=0, nullable=False, comment='消息数量')
    is_archived = Column(Boolean, default=False, nullable=False, comment='是否归档')
    is_deleted = Column(Boolean, default=False, nullable=False, comment='是否删除')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    # 关系定义
    user = relationship("User", back_populates="conversations")
    system_model = relationship("SystemModel", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    api_call_logs = relationship("ApiCallLog", back_populates="conversation")

    def __repr__(self):
        return f"<Conversation(conversation_id={self.conversation_id}, user_id={self.user_id}, title='{self.title}')>"

    def soft_delete(self):
        """软删除对话"""
        from datetime import datetime
        self.is_deleted = True
        self.deleted_at = datetime.now()
        self.updated_at = datetime.now()

    def restore(self):
        """恢复已删除的对话"""
        self.is_deleted = False
        self.deleted_at = None
        self.updated_at = datetime.now()

    def archive(self):
        """归档对话"""
        self.is_archived = True
        self.updated_at = datetime.now()

    def unarchive(self):
        """取消归档"""
        self.is_archived = False
        self.updated_at = datetime.now()

    def increment_message_count(self, tokens: int = 0):
        """增加消息计数和token数"""
        self.message_count += 1
        self.total_tokens += tokens
        self.updated_at = datetime.now()
```

### 2.5 消息模型 (`app/models/message.py`)

```python
# app/models/message.py
"""
消息模型
对应数据库表：messages
"""
import enum
from sqlalchemy import Column, Integer, Text, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MessageRole(enum.Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """消息表模型"""
    __tablename__ = "messages"
    __table_args__ = {
        'comment': '消息表'
    }

    message_id = Column(Integer, primary_key=True, index=True, comment='消息ID')
    conversation_id = Column(Integer, ForeignKey('conversations.conversation_id', ondelete='CASCADE'), nullable=False, index=True, comment='对话ID')
    role = Column(Enum(MessageRole), nullable=False, comment='角色')
    content = Column(Text, nullable=False, comment='消息内容')
    tokens_used = Column(Integer, default=0, nullable=False, comment='使用的token数')
    model_id = Column(Integer, ForeignKey('system_models.model_id', ondelete='SET NULL'), comment='使用的模型ID')
    is_deleted = Column(Boolean, default=False, nullable=False, comment='是否删除')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')

    # 关系定义
    conversation = relationship("Conversation", back_populates="messages")
    system_model = relationship("SystemModel", back_populates="messages")

    def __repr__(self):
        return f"<Message(message_id={self.message_id}, conversation_id={self.conversation_id}, role='{self.role}')>"

    @property
    def is_user_message(self) -> bool:
        """检查是否为用户消息"""
        return self.role == MessageRole.USER

    @property
    def is_assistant_message(self) -> bool:
        """检查是否为助手消息"""
        return self.role == MessageRole.ASSISTANT

    @property
    def is_system_message(self) -> bool:
        """检查是否为系统消息"""
        return self.role == MessageRole.SYSTEM

    def soft_delete(self):
        """软删除消息"""
        self.is_deleted = True

    def restore(self):
        """恢复已删除的消息"""
        self.is_deleted = False

    def get_truncated_content(self, max_length: int = 100) -> str:
        """获取截断的内容用于显示"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
```

### 2.6 其他模型（根据需求）

```python
# app/models/api_call_log.py
"""
API调用日志模型
对应数据库表：api_call_logs
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class ApiCallLog(Base):
    """API调用日志表模型"""
    __tablename__ = "api_call_logs"
    __table_args__ = {
        'comment': 'API调用日志表'
    }

    log_id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    model_id = Column(Integer, ForeignKey('system_models.model_id', ondelete='CASCADE'), nullable=False, comment='模型ID')
    conversation_id = Column(Integer, ForeignKey('conversations.conversation_id', ondelete='SET NULL'), comment='对话ID')
    endpoint = Column(String(255), nullable=False, comment='调用端点')
    request_tokens = Column(Integer, default=0, nullable=False, comment='请求token数')
    response_tokens = Column(Integer, default=0, nullable=False, comment='响应token数')
    total_tokens = Column(Integer, default=0, nullable=False, comment='总token数')
    response_time_ms = Column(Integer, comment='响应时间(毫秒)')
    status_code = Column(Integer, comment='状态码')
    is_success = Column(Boolean, default=True, nullable=False, comment='是否成功')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')

    # 关系定义
    user = relationship("User", back_populates="api_call_logs")
    system_model = relationship("SystemModel", back_populates="api_call_logs")
    conversation = relationship("Conversation", back_populates="api_call_logs")

    def __repr__(self):
        return f"<ApiCallLog(log_id={self.log_id}, user_id={self.user_id}, model_id={self.model_id})>"
```

### 2.7 模型初始化文件 (`app/models/__init__.py`)

```python
# app/models/__init__.py
"""
数据库模型包
"""
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.system_model import SystemModel, ModelType
from app.models.user_model_config import UserModelConfig
from app.models.api_call_log import ApiCallLog

# 导出所有模型
__all__ = [
    'User',
    'Conversation', 
    'Message',
    'MessageRole',
    'SystemModel',
    'ModelType',
    'UserModelConfig',
    'ApiCallLog'
]
```

## 3. 数据库初始化脚本

创建数据库初始化脚本：

```python
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
```

## 4. 验证脚本

创建模型验证脚本：

```python
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
        
        # 导入所有模型
        from app.models import User, Conversation, Message, SystemModel, UserModelConfig, ApiCallLog
        
        # 获取元数据
        metadata = Base.metadata
        
        # 检查所有表
        tables = metadata.tables.keys()
        expected_tables = {'users', 'conversations', 'messages', 'system_models', 'user_model_configs', 'api_call_logs'}
        
        logger.info(f"期望的表: {sorted(expected_tables)}")
        logger.info(f"实际创建的表: {sorted(tables)}")
        
        # 验证表名
        missing_tables = expected_tables - set(tables)
        extra_tables = set(tables) - expected_tables
        
        if missing_tables:
            logger.error(f"❌ 缺失的表: {missing_tables}")
            return False
        
        if extra_tables:
            logger.warning(f"⚠️ 额外的表（可能是中间表）: {extra_tables}")
        
        logger.info("✅ 表创建验证通过")
        return True
        
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
            # 检查系统模型数据
            models = session.query(SystemModel).all()
            logger.info(f"系统模型数量: {len(models)}")
            
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
```

## 5. 使用说明

### 5.1 安装依赖

首先确保安装了必要的依赖（添加到 `requirements.txt`）：

```txt
sqlalchemy==2.0.28
pymysql==1.1.0
bcrypt==4.1.2
```

### 5.2 执行步骤

1. **初始化数据库**：
```bash
python scripts/init_db.py
```

2. **验证模型设计**：
```bash
python scripts/validate_models.py
```

### 5.3 模型测试示例

创建测试文件验证模型功能：

```python
# tests/test_models.py
"""
模型功能测试
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import init_database, get_engine
from app.models.user import User
from app.models.system_model import SystemModel, ModelType
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


class TestModels:
    """模型测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试设置"""
        init_database()
        self.engine = get_engine()
        yield
        # 清理
        
    def test_user_model(self):
        """测试用户模型"""
        with Session(self.engine) as session:
            # 创建测试用户
            user = User(
                username="testuser",
                password_hash="hashed_password",
                email="test@example.com"
            )
            
            # 测试账户锁定
            assert not user.is_account_locked()
            
            # 锁定账户
            user.lock_account("测试锁定", lock_hours=1)
            assert user.is_account_locked()
            assert user.is_locked
            assert user.locked_reason == "测试锁定"
            
            # 解锁账户
            user.unlock_account()
            assert not user.is_account_locked()
            assert not user.is_locked
            
            session.add(user)
            session.commit()
            
            # 验证保存
            retrieved = session.query(User).filter_by(username="testuser").first()
            assert retrieved is not None
            assert retrieved.email == "test@example.com"
    
    def test_system_model(self):
        """测试系统模型"""
        with Session(self.engine) as session:
            model = SystemModel(
                model_name="test-model",
                model_provider="TestProvider",
                model_type=ModelType.CHAT,
                api_endpoint="https://api.test.com/v1",
                description="测试模型"
            )
            
            assert model.is_chat_model
            assert model.validate_config()
            
            session.add(model)
            session.commit()
    
    def test_conversation_relations(self):
        """测试对话关系"""
        with Session(self.engine) as session:
            # 创建用户
            user = User(
                username="reluser",
                password_hash="hash",
                email="rel@example.com"
            )
            
            # 获取或创建系统模型
            model = session.query(SystemModel).first()
            if not model:
                model = SystemModel(
                    model_name="test-rel-model",
                    model_provider="Test",
                    model_type=ModelType.CHAT,
                    api_endpoint="https://test.com"
                )
                session.add(model)
            
            # 创建对话
            conversation = Conversation(
                user=user,
                system_model=model,
                title="测试对话"
            )
            
            # 创建消息
            message = Message(
                conversation=conversation,
                role=MessageRole.USER,
                content="Hello, world!",
                system_model=model
            )
            
            session.add_all([user, conversation, message])
            session.commit()
            
            # 验证关系
            assert len(user.conversations) == 1
            assert user.conversations[0].title == "测试对话"
            assert len(conversation.messages) == 1
            assert conversation.messages[0].content == "Hello, world!"
            
            # 测试软删除
            conversation.soft_delete()
            assert conversation.is_deleted
            assert conversation.deleted_at is not None


if __name__ == "__main__":
    # 快速测试
    test = TestModels()
    test.setup()
    
    print("测试用户模型...")
    test.test_user_model()
    
    print("测试系统模型...")
    test.test_system_model()
    
    print("测试对话关系...")
    test.test_conversation_relations()
    
    print("✅ 所有模型测试通过！")
```

## 6. 正确性验证要点

### 6.1 验证步骤

1. **表结构正确性**：
   - 表名与设计文档一致
   - 列名、数据类型、约束正确
   - 主键、外键、索引正确

2. **关系完整性**：
   - 一对多、多对一关系正确
   - 级联删除配置正确
   - 关系属性命名一致

3. **业务逻辑正确性**：
   - 自定义方法正常工作
   - 属性访问器正确
   - 验证逻辑正确

4. **性能考虑**：
   - 索引配置合理
   - 避免N+1查询
   - 合理使用延迟加载

### 6.2 常见问题检查

1. **循环导入问题**：模型之间相互引用时使用字符串类型引用
2. **关系配置错误**：确保`back_populates`参数正确对应
3. **数据类型不匹配**：确保Python类型与数据库类型匹配
4. **默认值问题**：确保函数默认值使用`func.now()`而非`datetime.now()`

这个模型设计完全基于你的 `database_v2.0.txt` 文件，并添加了有用的业务方法和验证逻辑。现在你可以开始进行阶段2的开发了。