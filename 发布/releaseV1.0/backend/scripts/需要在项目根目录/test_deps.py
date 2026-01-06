# test_deps.py
import sys
sys.path.insert(0, '.')

from app.dependencies import get_model_router_service
from app.database import get_db,init_database

# 测试依赖函数
try:
    init_database()
    db = next(get_db())
    service = get_model_router_service(db)
    print(f"✅ 依赖函数测试成功: {service}")
except Exception as e:
    print(f"❌ 依赖函数测试失败: {e}")
    import traceback
    traceback.print_exc()
