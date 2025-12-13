


项目结构：
multi-model-platform-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI应用入口
│   ├── config.py                  # 配置文件
│   ├── database.py                # 数据库连接和会话管理
│   ├── dependencies.py            # 依赖注入
│   ├── middleware.py              # 中间件
│   ├── exceptions.py              # 自定义异常
│   │
│   ├── api/                       # API路由层
│   │   ├── __init__.py
│   │   ├── v1/                    # API版本1
│   │   │   ├── __init__.py
│   │   │   ├── router.py         # 主路由注册
│   │   │   ├── auth.py           # 认证相关路由
│   │   │   ├── users.py          # 用户管理路由
│   │   │   ├── conversations.py  # 对话管理路由
│   │   │   ├── models.py         # 模型配置路由
│   │   │   └── admin.py          # 管理员路由
│   │   └── health.py             # 健康检查路由
│   │
│   ├── core/                      # 核心业务层
│   │   ├── __init__.py
│   │   ├── security.py           # 安全相关（JWT、密码加密）
│   │   ├── models.py             # Pydantic数据模型
│   │   └── constants.py          # 常量定义
│   │
│   ├── services/                  # 业务服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py       # 认证服务
│   │   ├── user_service.py       # 用户服务
│   │   ├── conversation_service.py  # 对话服务
│   │   ├── model_service.py      # 模型服务
│   │   ├── model_router.py       # 模型路由服务
│   │   └── admin_service.py      # 管理员服务
│   │
│   ├── repositories/              # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py               # 基础Repository
│   │   ├── user_repository.py    # 用户数据访问
│   │   ├── conversation_repository.py  # 对话数据访问
│   │   ├── message_repository.py # 消息数据访问
│   │   ├── model_repository.py   # 模型配置数据访问
│   │   └── user_model_config_repository.py  # 用户模型配置数据访问
│   │
│   ├── models/                    # SQLAlchemy数据库模型
│   │   ├── __init__.py
│   │   ├── user.py               # 用户模型
│   │   ├── conversation.py       # 对话模型
│   │   ├── message.py            # 消息模型
│   │   ├── system_model.py       # 系统模型配置
│   │   └── user_model_config.py  # 用户模型配置
│   │
│   ├── schemas/                   # Pydantic模式（请求/响应）
│   │   ├── __init__.py
│   │   ├── auth.py               # 认证相关模式
│   │   ├── user.py               # 用户相关模式
│   │   ├── conversation.py       # 对话相关模式
│   │   ├── message.py            # 消息相关模式
│   │   └── model.py              # 模型相关模式
│   │
│   ├── utils/                     # 工具函数
│   │   ├── __init__.py
│   │   ├── validators.py         # 数据验证器
│   │   ├── helpers.py            # 辅助函数
│   │   ├── logger.py             # 日志配置
│   │   └── api_clients/          # 第三方API客户端
│   │       ├── __init__.py
│   │       ├── base_client.py    # 基础API客户端
│   │       ├── openai_client.py  # OpenAI API客户端
│   │       ├── deepseek_client.py # DeepSeek API客户端
│   │       └── wenxin_client.py  # 文心一言API客户端
│   │
│   └── tests/                     # 测试目录
│       ├── __init__.py
│       ├── conftest.py           # 测试配置
│       ├── test_auth.py          # 认证测试
│       ├── test_users.py         # 用户测试
│       ├── test_conversations.py # 对话测试
│       └── test_models.py        # 模型测试
│
├── alembic/                       # 数据库迁移
│   ├── versions/                  # 迁移版本
│   ├── env.py
│   └── alembic.ini
│
├── scripts/                       # 脚本目录
│   ├── init_db.py                 # 数据库初始化脚本
│   ├── create_admin.py            # 创建管理员脚本
│   └── seed_data.py               # 种子数据脚本
│
├── .env                   # 环境变量示例
├── .gitignore                     # Git忽略文件
├── requirements.txt               # Python依赖
├── requirements-dev.txt           # 开发依赖
├── pyproject.toml                 # 项目配置
├── README.md                      # 项目说明
└── Dockerfile                     # Docker配置（可选）