# app/config.py
"""
应用程序配置管理
基于pydantic的BaseSettings，支持环境变量和.env文件
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator, Field


class Settings(BaseSettings):
    """应用程序配置"""
    
    # 项目基本信息
    PROJECT_NAME: str = "多端大模型统一平台"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=True, description="调试模式")
    
    # API配置
    API_V1_STR: str = "/api/v1"
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    
    # 数据库配置（按项目说明.txt）
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3310/testdb1?charset=utf8mb4"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = Field(default=True, description="SQL日志开关")
    
    # JWT认证配置
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-1234567890abcdef",
        description="JWT密钥，生产环境必须更换"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # 安全配置
    PASSWORD_HASH_ROUNDS: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCK_TIME_MINUTES: int = 15
    
    # 模型API配置（可留空，用户自行配置）
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    WENXIN_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # 模型API端点
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    WENXIN_BASE_URL: str = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop"
    
    # 文件上传配置
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["txt", "pdf", "doc", "docx", "png", "jpg", "jpeg"]
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="允许跨域的源"
    )
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = Field(
        default=None, 
        description="日志文件路径，None表示使用默认路径（项目根目录/logs/app.log）"
    )
    ENABLE_CONSOLE: bool = Field(
        default=True, 
        description="是否启用控制台输出日志"
    )
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """验证数据库URL格式"""
        if not v:
            raise ValueError("DATABASE_URL不能为空")
        if not v.startswith(("mysql+pymysql://", "mysql://")):
            raise ValueError("数据库URL格式错误，必须是mysql+pymysql://")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """验证密钥强度"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY长度至少32位")
        return v
    
    

        
    
    # 大模型api=======================================================
    # 默认API密钥配置
    DEFAULT_API_KEYS: dict[str, str] = {
        "openai": "",
        "deepseek": "",
        "wenxin": ""
    }
    
    # 模型API端点配置
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    WENXIN_API_BASE: str = "https://api.wenxin.com"
    
    
    

#==================================================================== 
    class Config:
        env_file = ".env.example"  # 从.env文件读取配置
        env_file_encoding = "utf-8"
        case_sensitive = False  # 环境变量不区分大小写
# ===================================================================


# 创建全局配置实例
settings = Settings()

# 打印配置信息（仅调试模式）
if settings.DEBUG:
    print(f"✅ 配置加载完成:")
    print(f"   项目: {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"   数据库: {settings.DATABASE_URL[:30]}...")
    print(f"   调试模式: {settings.DEBUG}")
