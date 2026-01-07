# scripts/test_fix_api_logs.py (修复版本)
import sys
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)

def test_admin_login():
    """测试管理员登录"""
    print("尝试登录管理员账户...")
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if response.status_code != 200:
        print(f"登录失败: {response.status_code}")
        print(f"响应内容: {response.text}")
        return None
    
    data = response.json()
    print(f"✅ 登录成功")
    print(f"响应结构: {data}")
    
    # 从data字段中获取access_token
    if "data" in data and "access_token" in data["data"]:
        token = data["data"]["access_token"]
        print(f"✅ 从data字段获取token: {token[:20]}...")
        return token
    elif "access_token" in data:
        token = data["access_token"]
        print(f"✅ 直接从响应获取token: {token[:20]}...")
        return token
    else:
        print(f"❌ 无法从响应中获取token")
        print(f"完整响应: {data}")
        return None

def test_admin_endpoints():
    """测试所有管理员端点"""
    token = test_admin_login()
    if not token:
        print("❌ 无法获取token，跳过管理员端点测试")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/api/v1/admin/users", "用户列表"),
        ("/api/v1/admin/stats", "系统统计"),
        ("/api/v1/admin/health", "系统健康"),
        ("/api/v1/admin/api-logs", "API调用日志"),
    ]
    
    print("\n🔧 测试所有管理员端点...")
    all_passed = True
    
    for endpoint, description in endpoints:
        response = client.get(endpoint, headers=headers)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"   {status} {description}: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"      成功: {data.get('message', '请求成功')}")
            
            # 如果是API日志接口，显示详细信息
            if "api-logs" in endpoint:
                if "data" in data:
                    logs = data["data"]
                    if isinstance(logs, list):
                        print(f"      日志数量: {len(logs)}")
                    else:
                        print(f"      日志结构: {type(logs)}")
        elif response.status_code == 403:
            print(f"      权限不足 - 确保你是admin用户")
            all_passed = False
        else:
            all_passed = False
            print(f"      错误: {response.text[:200]}...")
    
    return all_passed

def test_api_logs_detailed():
    """详细测试API日志接口"""
    token = test_admin_login()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📋 详细测试API调用日志接口...")
    
    # 测试基础查询
    print("1. 测试基础查询（limit=10）...")
    response = client.get("/api/v1/admin/api-logs", 
                         headers=headers, 
                         params={"limit": 10})
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   响应结构: {data.keys()}")
        
        # 显示成功消息
        if "message" in data:
            print(f"   消息: {data['message']}")
        
        # 显示数据
        if "data" in data:
            logs = data["data"]
            if isinstance(logs, list):
                print(f"   成功获取 {len(logs)} 条日志")
                
                # 显示前几条日志的摘要
                for i, log in enumerate(logs[:3]):
                    if isinstance(log, dict):
                        print(f"   日志{i+1}: ID={log.get('log_id')}, "
                              f"用户={log.get('username')}, "
                              f"模型={log.get('model_name')}, "
                              f"Tokens={log.get('total_tokens')}")
            else:
                print(f"   数据字段不是列表类型: {type(logs)}")
                print(f"   数据内容: {logs}")
        
        return True
    elif response.status_code == 500:
        print(f"❌ 服务器内部错误 (500)")
        print(f"   错误信息: {response.text}")
        
        # 尝试获取更详细的错误信息
        try:
            error_detail = response.json()
            print(f"   错误详情: {error_detail}")
        except:
            pass
        
        return False
    else:
        print(f"❌ 非预期状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("管理员功能测试")
    print("=" * 50)
    
    try:
        # 测试登录
        print("\n[阶段1] 测试登录功能...")
        token = test_admin_login()
        if not token:
            print("❌ 登录失败，无法继续测试")
            sys.exit(1)
        
        # 测试所有管理员端点
        print("\n[阶段2] 测试所有管理员端点...")
        admin_ok = test_admin_endpoints()
        
        # 详细测试API日志接口
        print("\n[阶段3] 详细测试API调用日志接口...")
        logs_ok = test_api_logs_detailed()
        
        print("\n" + "=" * 50)
        print("测试结果总结:")
        print(f"   登录功能: ✅ 通过")
        print(f"   管理员端点: {'✅ 通过' if admin_ok else '❌ 失败'}")
        print(f"   API调用日志功能: {'✅ 通过' if logs_ok else '❌ 失败'}")
        print("=" * 50)
        
        if admin_ok and logs_ok:
            print("\n🎉 所有测试通过！管理员功能完整可用。")
        else:
            print("\n⚠️ 部分测试失败，需要进一步检查。")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
