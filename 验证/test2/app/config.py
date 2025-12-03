from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/multi_model_platform"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # API配置
    OPENAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    WENXIN_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
