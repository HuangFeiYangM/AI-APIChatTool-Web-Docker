# scripts/test_model_config.py
"""
测试模型配置管理API
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


async def test_model_config():
    """测试模型配置管理"""
    base_url = "http://localhost:8000"
    
    # 1. 登录
    async with httpx.AsyncClient() as client:
        login_data = {"username": "test2", "password": "123456"}
        response = await client.post(f"{base_url}/api/v1/auth/login", json=login_data)
        token = response.json()["data"]["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 获取配置列表
        print("📋 获取用户模型配置列表...")
        response = await client.get(f"{base_url}/api/v1/models/config", headers=headers)
        print(f"   状态码: {response.status_code}")
        print(f"   配置数量: {len(response.json()['data'])}")
        
        # 3. 获取单个模型配置（以deepseek-chat为例，model_id=3）
        print("\n🔍 获取DeepSeek模型配置...")
        response = await client.get(f"{base_url}/api/v1/models/config/3", headers=headers)
        print(f"   状态码: {response.status_code}")
        
        # 4. 更新配置
        print("\n✏️  更新模型配置...")
        update_data = {
            "model_id": 3,
            "priority": 10,
            "is_enabled": True
        }
        response = await client.post(f"{base_url}/api/v1/models/config", 
                                    json=update_data, headers=headers)
        print(f"   状态码: {response.status_code}")
        print(f"   结果: {response.json()}")
        
        # 5. 启用/禁用测试
        print("\n🔧 测试启用/禁用...")
        response = await client.post(f"{base_url}/api/v1/models/config/3/disable", headers=headers)
        print(f"   禁用: {response.status_code}")
        
        response = await client.post(f"{base_url}/api/v1/models/config/3/enable", headers=headers)
        print(f"   启用: {response.status_code}")
        
        print("\n✅ 模型配置管理测试完成！")


if __name__ == "__main__":
    asyncio.run(test_model_config())
