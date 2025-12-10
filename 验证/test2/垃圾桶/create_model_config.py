# create_model_config.py
import asyncio
import httpx
import json



async def create_deepseek_config():
    # 1. 获取认证令牌
    token = await get_auth_token("test2", "123456")
    if not token:
        print("❌ 认证失败")
        return
    
    headers = get_auth_headers(token)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 2. 创建deepseek-chat配置
        config_data = {
            "model_name": "deepseek-chat",
            "api_key": "sk-d35fc57d5206433bb336ea0fb2b5878b",  # 从.env获取
            "is_enabled": True,
            "temperature": 0.7,
            "max_tokens": 2048,
            "priority": 1
        }
        
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/models/config",
                headers=headers,
                json=config_data
            )
            
            print(f"配置创建响应: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ 模型配置创建成功: {response.json()}")
            else:
                print(f"❌ 配置创建失败: {response.text}")
                
                # 如果接口不存在，尝试使用备用路径
                print("尝试备用路径...")
                config_data["model"] = "deepseek-chat"
                response = await client.post(
                    "http://localhost:8000/api/v1/models/setup",
                    headers=headers,
                    json=config_data
                )
                print(f"备用路径响应: {response.status_code}, {response.text}")
                
        except Exception as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    asyncio.run(create_deepseek_config())
