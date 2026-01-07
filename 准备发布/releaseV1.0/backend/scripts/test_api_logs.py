import sys
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import get_db
from app.models.user import User

client = TestClient(app)

def test_admin_login():
    """测试管理员登录"""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    print(f"Admin token: {token[:20]}...")
    return token

def test_api_call_logs(token):
    """测试获取API调用日志"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试1：获取所有日志
    response = client.get("/api/v1/admin/api-call-logs", headers=headers, params={"limit": 10})
    print(f"API调用日志响应状态: {response.status_code}")
    print(f"API调用日志响应内容: {response.json()}")
    assert response.status_code == 200
    
    # 测试2：带过滤条件的查询
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    response = client.get("/api/v1/admin/api-call-logs", headers=headers, params={
        "start_date": start_date.strftime("%Y-%m-%d"),
        "limit": 5
    })
    print(f"过滤查询响应状态: {response.status_code}")
    assert response.status_code == 200
    
    return True

if __name__ == "__main__":
    print("测试API调用日志接口...")
    try:
        token = test_admin_login()
        success = test_api_call_logs(token)
        if success:
            print("✅ API调用日志接口测试通过！")
        else:
            print("❌ API调用日志接口测试失败")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
