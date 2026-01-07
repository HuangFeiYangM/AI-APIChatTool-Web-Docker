# scripts/simple_conversation_test.py
"""
简化对话API测试
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_simple():
    """简化测试"""
    base_url = "http://localhost:8000"
    
    # 1. 登录
    print("1. 用户登录...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        login_data = {
            "username": "test2",
            "password": "123456"
        }
        
        response = await client.post(f"{base_url}/api/v1/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"登录失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
        
        result = response.json()
        token = result["data"]["access_token"]
        print(f"登录成功，Token: {token[:30]}...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 2. 创建对话
        print("\n2. 创建对话...")
        conversation_data = {
            "title": "测试对话",
            "model_id": 3  # deepseek-chat
        }
        
        response = await client.post(
            f"{base_url}/api/v1/conversations", 
            json=conversation_data, 
            headers=headers
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"创建成功: {result['message']}")
            conversation_id = result["data"]["conversation_id"]
            print(f"对话ID: {conversation_id}")
        else:
            print(f"创建失败: {response.status_code}")
            print(f"响应: {response.text}")
            # 继续测试其他功能
        
        # 3. 获取对话列表
        print("\n3. 获取对话列表...")
        response = await client.get(f"{base_url}/api/v1/conversations", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"获取成功: 找到 {len(result['data']['conversations'])} 个对话")
        else:
            print(f"获取失败: {response.status_code}")
            print(f"响应: {response.text}")
        
        # 4. 获取对话统计
        print("\n4. 获取对话统计...")
        response = await client.get(f"{base_url}/api/v1/conversations/stats", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"统计信息: {result['data']}")
        else:
            print(f"获取统计失败: {response.status_code}")
            print(f"响应: {response.text}")
        
        return True


async def main():
    """主函数"""
    print("="*60)
    print("🧪 简化对话API测试")
    print("="*60)
    
    try:
        await test_simple()
        print("\n✅ 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
