import os
from dotenv import load_dotenv


# 加载.env文件中的环境变量
load_dotenv()

class Settings:
    """应用配置类，从环境变量读取配置"""
    # 数据库连接URL，默认值用于开发环境
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:rootpassword@localhost:32769/test_db"
    )

# 创建全局配置实例
settings = Settings()
