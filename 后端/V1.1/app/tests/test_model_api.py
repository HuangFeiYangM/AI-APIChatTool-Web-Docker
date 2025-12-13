# test_model_api.py
import asyncio
import httpx
import json
from typing import Dict, Any

# 服务器地址
BASE_URL = "http://localhost:8000/api/v1"

async def get_auth_token(username: str, password: str) -> str:
    """获取认证令牌"""
    async with httpx.AsyncClient() as client:
        login_data = {
            "username": username,
            "password": password
        }
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json=login_data
            )
            response.raise_for_status()
            data = response.json()
            return data["access_token"]
        except Exception as e:
            print(f"登录失败: {e}")
            if response.status_code == 401:
                print("请检查用户名和密码是否正确")
            return None

def get_auth_headers(token: str) -> Dict[str, str]:
    """构造认证头部"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

async def test_get_available_models(token: str):
    """测试获取可用模型列表"""
    async with httpx.AsyncClient() as client:
        try:
            headers = get_auth_headers(token)
            response = await client.get(
                f"{BASE_URL}/models/available",
                headers=headers
            )
            
            print("\n=== 测试获取可用模型列表 ===")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                if data.get("success"):
                    models = data.get("data", [])
                    print(f"\n可用模型数量: {len(models)}")
                    for model in models:
                        print(f"- {model.get('model_name')} ({model.get('model_provider')})")
                        print(f"  描述: {model.get('description')}")
                        print(f"  最大Token数: {model.get('max_tokens')}")
                else:
                    print(f"错误: {data.get('message')}")
            else:
                print(f"错误响应: {response.text}")
                
        except Exception as e:
            print(f"请求失败: {e}")

async def test_chat_with_model(token: str, model_name: str = "gpt-3.5-turbo"):
    """测试与模型对话"""
    async with httpx.AsyncClient() as client:
        try:
            headers = get_auth_headers(token)
            chat_data = {
                "model": model_name,
                "message": "你好，请介绍一下你自己",
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": False
            }
            
            print(f"\n=== 测试与模型对话 ({model_name}) ===")
            response = await client.post(
                f"{BASE_URL}/models/chat",
                headers=headers,
                json=chat_data
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 显示对话结果
                if data.get("response"):
                    print(f"\n模型回复: {data.get('response')}")
                if data.get("model_used"):
                    print(f"使用的模型: {data.get('model_used')}")
                if data.get("tokens_used"):
                    print(f"消耗的Token数: {data.get('tokens_used')}")
            elif response.status_code == 503:
                print("注意: API密钥未配置或无效，这是预期行为")
                print(f"错误详情: {response.json().get('detail', 'API服务不可用')}")
            else:
                print(f"错误响应: {response.text}")
                
        except Exception as e:
            print(f"请求失败: {e}")

async def test_update_model_config(token: str):
    """测试更新模型配置"""
    async with httpx.AsyncClient() as client:
        try:
            # 首先获取一个模型ID
            headers = get_auth_headers(token)
            response = await client.get(
                f"{BASE_URL}/models/available",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    # 使用第一个模型的ID
                    model_id = data["data"][0].get("model_id")
                    
                    config_data = {
                        "model_id": model_id,
                        "is_enabled": True,
                        "temperature": 0.8,
                        "max_tokens": 3000,
                        "priority": 1
                    }
                    
                    print(f"\n=== 测试更新模型配置 (model_id: {model_id}) ===")
                    response = await client.post(
                        f"{BASE_URL}/models/config",
                        headers=headers,
                        json=config_data
                    )
                    
                    print(f"状态码: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
                    else:
                        print(f"错误响应: {response.text}")
                else:
                    print("无法获取模型列表")
            else:
                print("无法获取模型列表")
                
        except Exception as e:
            print(f"请求失败: {e}")

async def test_get_user_configs(token: str):
    """测试获取用户配置"""
    async with httpx.AsyncClient() as client:
        try:
            headers = get_auth_headers(token)
            
            print(f"\n=== 测试获取用户模型配置 ===")
            response = await client.get(
                f"{BASE_URL}/models/config",
                headers=headers
            )
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                if data.get("success"):
                    configs = data.get("data", [])
                    print(f"\n用户配置数量: {len(configs)}")
                    for config in configs:
                        print(f"- 模型ID: {config.get('model_id')}")
                        print(f"  模型名称: {config.get('model_name')}")
                        print(f"  是否启用: {config.get('is_enabled')}")
            else:
                print(f"错误响应: {response.text}")
                
        except Exception as e:
            print(f"请求失败: {e}")

async def test_get_api_usage(token: str):
    """测试获取API使用统计"""
    async with httpx.AsyncClient() as client:
        try:
            headers = get_auth_headers(token)
            
            print(f"\n=== 测试获取API使用统计 ===")
            response = await client.get(
                f"{BASE_URL}/models/usage?days=7",
                headers=headers
            )
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
            else:
                print(f"错误响应: {response.text}")
                
        except Exception as e:
            print(f"请求失败: {e}")

async def main():
    """主测试函数"""
    # 测试用户凭据 - 修改为您实际的测试用户
    USERNAME = "testuser"  # 替换为您的测试用户名
    PASSWORD = "testpassword"  # 替换为您的测试密码
    
    print("开始测试模型路由API...")
    print(f"服务器地址: {BASE_URL}")
    print(f"测试用户: {USERNAME}")
    
    # 1. 获取认证令牌
    print("\n1. 获取认证令牌...")
    token = await get_auth_token(USERNAME, PASSWORD)
    if not token:
        print("❌ 获取令牌失败，请检查用户名和密码")
        return
    
    print(f"✅ 令牌获取成功")
    
    # 2. 测试获取可用模型列表
    await test_get_available_models(token)
    
    # 3. 测试与模型对话（由于没有API密钥，预计会失败）
    await test_chat_with_model(token, "gpt-3.5-turbo")
    
    # 4. 测试更新模型配置
    await test_update_model_config(token)
    
    # 5. 测试获取用户配置
    await test_get_user_configs(token)
    
    # 6. 测试获取API使用统计
    await test_get_api_usage(token)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main())
