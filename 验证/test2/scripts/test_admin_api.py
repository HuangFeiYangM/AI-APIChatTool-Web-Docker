# scripts/test_admin_api.py
"""
测试管理员API功能
"""
import asyncio
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


async def test_admin_api():
    """测试管理员API"""
    base_url = "http://localhost:8000"
    
    # 1. 管理员登录
    async with httpx.AsyncClient() as client:
        print("🔐 管理员登录...")
        login_data = {"username": "admin", "password": "admin123"}
        
        try:
            response = await client.post(f"{base_url}/api/v1/auth/login", json=login_data)
            if response.status_code != 200:
                print(f"❌ 管理员登录失败: {response.status_code}")
                print(f"响应: {response.text}")
                return
            
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"✅ 管理员登录成功，Token: {token[:50]}...")
        except Exception as e:
            print(f"❌ 管理员登录异常: {e}")
            return
        
        # 2. 获取系统统计
        print("\n📊 获取系统统计...")
        response = await client.get(f"{base_url}/api/v1/admin/stats", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"   总用户数: {data.get('total_users', 0)}")
            print(f"   活跃用户: {data.get('active_users', 0)}")
            print(f"   总对话数: {data.get('total_conversations', 0)}")
        
        # 3. 获取用户列表
        print("\n👥 获取用户列表...")
        response = await client.get(f"{base_url}/api/v1/admin/users", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   用户数量: {len(data['data'])}")
            print(f"   总用户数: {data['total']}")
        
        # 4. 获取系统健康状态
        print("\n🏥 获取系统健康状态...")
        response = await client.get(f"{base_url}/api/v1/admin/health", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"   状态: {data.get('status')}")
            print(f"   数据库: {'✅' if data.get('database') else '❌'}")
            print(f"   CPU使用率: {data.get('cpu_usage')}%")
        
        # 5. 获取API调用日志
        print("\n📝 获取API调用日志...")
        response = await client.get(f"{base_url}/api/v1/admin/api-logs", headers=headers, params={"limit": 5})
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   日志数量: {len(data['data'])}")
            print(f"   总日志数: {data['total']}")
        
        # 6. 获取系统模型列表
        print("\n🤖 获取系统模型列表...")
        response = await client.get(f"{base_url}/api/v1/admin/system-models", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   模型数量: {len(data['data'])}")
            for model in data['data'][:3]:  # 只显示前3个
                print(f"     - {model.get('model_name')} ({model.get('model_provider')})")
        
        # 7. 测试普通用户无法访问管理员接口
        print("\n🔒 测试普通用户权限...")
        
        # 普通用户登录
        user_login_data = {"username": "test2", "password": "123456"}
        response = await client.post(f"{base_url}/api/v1/auth/login", json=user_login_data)
        if response.status_code == 200:
            user_token = response.json()["data"]["access_token"]
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            response = await client.get(f"{base_url}/api/v1/admin/stats", headers=user_headers)
            if response.status_code == 403:
                print("   ✅ 普通用户无法访问管理员接口（权限正确）")
            else:
                print(f"   ❌ 权限检查失败: {response.status_code}")
        
        print("\n🎉 管理员功能测试完成！")


if __name__ == "__main__":
    asyncio.run(test_admin_api())
