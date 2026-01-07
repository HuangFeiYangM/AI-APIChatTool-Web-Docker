# scripts/direct_test_api.py
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"  # 你的FastAPI服务器地址

def test_login():
    """直接测试登录API"""
    print("🔑 测试管理员登录...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"响应结构: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get("success") and "data" in data:
            token = data["data"]["access_token"]
            print(f"✅ 登录成功，获取到token: {token[:20]}...")
            return token
        else:
            print(f"❌ 登录失败: {data.get('message', '未知错误')}")
            return None
    else:
        print(f"❌ HTTP错误: {response.text}")
        return None

def test_admin_endpoints(token):
    """测试管理员端点"""
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/api/v1/admin/users", "GET", "用户列表"),
        ("/api/v1/admin/stats", "GET", "系统统计"),
        ("/api/v1/admin/health", "GET", "系统健康"),
        ("/api/v1/admin/api-logs", "GET", "API调用日志"),
    ]
    
    print("\n🔧 测试管理员端点...")
    results = []
    
    for endpoint, method, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", headers=headers)
            else:
                continue
            
            status_emoji = "✅" if response.status_code == 200 else "❌"
            print(f"   {status_emoji} {description}: {response.status_code}")
            
            if response.status_code == 200:
                results.append(True)
                # 对于API日志，显示数据统计
                if "api-logs" in endpoint:
                    data = response.json()
                    if data.get("success"):
                        print(f"     日志数量: {len(data.get('data', []))}")
                        print(f"     总记录数: {data.get('total', 0)}")
            else:
                results.append(False)
                print(f"     错误: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ {description}: 请求失败 - {e}")
            results.append(False)
    
    return all(results)

def test_api_logs_detailed(token):
    """详细测试API调用日志"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📋 详细测试API调用日志...")
    
    # 测试基本查询
    print("1. 测试基础查询...")
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/api-logs",
        headers=headers,
        params={"limit": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功，状态码: {response.status_code}")
        
        if data.get("success"):
            logs = data.get("data", [])
            print(f"   获取到 {len(logs)} 条日志")
            print(f"   总记录数: {data.get('total', 0)}")
            
            # 显示日志详情
            for i, log in enumerate(logs[:3]):
                print(f"   日志{i+1}: 用户={log.get('username')}, "
                    f"模型={log.get('model_name')}, "
                    f"Tokens={log.get('total_tokens')}, "
                    f"成功={log.get('is_success')}")
            
            return True
        else:
            print(f"   ❌ 响应指示失败: {data.get('message')}")
            return False
    elif response.status_code == 500:
        print(f"   ❌ 服务器内部错误 (500)")
        print(f"   错误信息: {response.text}")
        return False
    else:
        print(f"   ❌ 非预期状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("直接API测试 - 管理员功能验证")
    print("=" * 50)
    
    try:
        # 1. 测试登录
        token = test_login()
        
        if not token:
            print("\n❌ 无法获取token，测试终止")
            exit(1)
        
        # 2. 测试所有管理员端点
        admin_endpoints_ok = test_admin_endpoints(token)
        
        # 3. 详细测试API日志
        api_logs_ok = test_api_logs_detailed(token)
        
        print("\n" + "=" * 50)
        print("测试结果总结:")
        print(f"   管理员端点功能: {'✅ 通过' if admin_endpoints_ok else '❌ 失败'}")
        print(f"   API调用日志功能: {'✅ 通过' if api_logs_ok else '❌ 失败'}")
        print("=" * 50)
        
        if admin_endpoints_ok and api_logs_ok:
            print("\n🎉 所有测试通过！管理员功能完整可用。")
        else:
            print("\n⚠️ 部分测试失败，需要进一步检查。")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到服务器 {BASE_URL}")
        print("   请确保FastAPI应用正在运行: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
