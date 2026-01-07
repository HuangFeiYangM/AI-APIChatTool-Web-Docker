# check_config.py
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("检查环境变量加载情况:")
print("=" * 50)

# 检查关键环境变量
env_vars = ["DATABASE_URL", "DEEPSEEK_API_KEY", "SECRET_KEY"]
for var in env_vars:
    value = os.getenv(var)
    if value:
        masked = value[:10] + "..." if len(value) > 10 else value
        print(f"✅ {var}: {masked}")
    else:
        print(f"❌ {var}: 未找到")

print("\n检查配置模块:")
print("=" * 50)

try:
    from app.config import settings
    print(f"✅ 配置模块加载成功")
    print(f"DEEPSEEK_API_KEY 是否存在: {'DEEPSEEK_API_KEY' in dir(settings)}")
    
    # 检查DEFAULT_API_KEYS
    if hasattr(settings, 'DEFAULT_API_KEYS'):
        keys = settings.DEFAULT_API_KEYS
        print(f"DEFAULT_API_KEYS 中的提供商: {list(keys.keys())}")
        if 'deepseek' in keys:
            print(f"✅ DeepSeek API密钥已配置: {keys['deepseek'][:20]}...")
        else:
            print(f"❌ DeepSeek 不在 DEFAULT_API_KEYS 中")
    else:
        print(f"❌ DEFAULT_API_KEYS 属性不存在")
        
except Exception as e:
    print(f"❌ 加载配置模块失败: {e}")
