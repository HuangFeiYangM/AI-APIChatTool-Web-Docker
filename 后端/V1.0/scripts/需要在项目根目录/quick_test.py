# quick_test.py
# 运行位置：/（根目录）
from sqlalchemy import create_engine

# 最简单的连接测试
engine = create_engine("mysql+pymysql://root:root@localhost:3310/testdb1")
try:
    with engine.connect() as conn:
        print("✅ 数据库连接成功")
except Exception as e:
    print(f"❌ 连接失败: {e}")
