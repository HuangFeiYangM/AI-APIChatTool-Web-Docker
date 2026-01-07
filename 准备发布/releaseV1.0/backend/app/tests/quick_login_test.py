# quick_login_test.py
import httpx
import asyncio

async def test_login():
    async with httpx.AsyncClient() as client:
        login_data = {
            "username": "test2",
            "password": "123456"  # 请确认密码
        }
        
        print("测试登录接口...")
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data
        )
        
        print(f"状态码: {response.status_code}")
        print(f"完整响应: {response.text}")
        
        # 尝试解析JSON
        try:
            data = response.json()
            print(f"JSON解析成功: {data}")
            print(f"响应键: {list(data.keys())}")
        except:
            print("响应不是有效的JSON")

if __name__ == "__main__":
    asyncio.run(test_login())
