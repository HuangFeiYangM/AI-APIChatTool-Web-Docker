# debug_deepseek.py
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_deepseek_direct():
    """直接测试DeepSeek API"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("❌ 未找到DeepSeek API密钥")
        return
    
    print(f"🔑 API密钥: {api_key[:10]}...")
    
    endpoint = "https://api.deepseek.com/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "你好，请简单介绍一下你自己"}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": False
    }
    
    print(f"📤 发送请求到: {endpoint}")
    print(f"📝 请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(endpoint, headers=headers, json=payload)
            
            print(f"📥 响应状态码: {response.status_code}")
            print(f"📥 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API调用成功")
                print(f"📄 响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 提取回复
                if "choices" in data and len(data["choices"]) > 0:
                    message = data["choices"][0]["message"]
                    print(f"🤖 模型回复: {message['content'][:200]}...")
            else:
                print(f"❌ API调用失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            import traceback
            traceback.print_exc()

async def test_model_router():
    """测试模型路由服务"""
    import sys
    sys.path.append("..")
    
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.services.model_router import ModelRouterService
    
    # 创建数据库会话
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost:3311/testdb1?charset=utf8mb4")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 创建服务实例
        service = ModelRouterService(db)
        
        # 测试用户ID（假设test2的用户ID是34）
        user_id = 34
        model_name = "deepseek-chat"
        
        print(f"🧪 测试模型路由服务")
        print(f"👤 用户ID: {user_id}")
        print(f"🤖 模型: {model_name}")
        
        # 调用聊天功能
        result = await service.chat_completion(
            user_id=user_id,
            model_name=model_name,
            message="你好，请简单介绍一下你自己",
            temperature=0.7,
            max_tokens=500,
            stream=False
        )
        
        print(f"✅ 模型路由测试成功")
        print(f"📄 结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"❌ 模型路由测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 DeepSeek API调试")
    print("=" * 50)
    
    # 先直接测试API
    print("\n1. 直接测试DeepSeek API")
    asyncio.run(test_deepseek_direct())
    
    # 然后测试模型路由
    print("\n2. 测试模型路由服务")
    asyncio.run(test_model_router())
