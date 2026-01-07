# test_database.py (放在app目录下)
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.database import init_database, get_engine
    
    print("✅ 导入成功")
    init_database()
    engine = get_engine()
    print(f"✅ 引擎: {engine}")
    
    # 检查SessionLocal
    import app.database as db_module
    print("database模块属性:", [attr for attr in dir(db_module) if not attr.startswith('_')])
    
    # 尝试获取SessionLocal
    if hasattr(db_module, 'SessionLocal'):
        SessionLocal = db_module.SessionLocal
        print(f"✅ 找到SessionLocal: {SessionLocal}")
    elif hasattr(db_module, '_SessionLocal'):
        SessionLocal = db_module._SessionLocal
        print(f"✅ 找到_SessionLocal: {SessionLocal}")
    else:
        print("❌ 没有找到SessionLocal或_SessionLocal")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
