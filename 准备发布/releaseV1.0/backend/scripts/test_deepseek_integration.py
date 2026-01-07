# scripts/test_deepseek_integration_fixed.py
"""
测试DeepSeek API集成的完整脚本 - 修复登录响应问题
"""
import asyncio
import sys
import os
from pathlib import Path
import json
import time
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.database import init_database, get_db
from app.models.user import User
from app.models.system_model import SystemModel
from app.models.user_model_config import UserModelConfig
from app.utils.api_clients.deepseek_client import create_deepseek_client

async def test_login() -> str:
    """测试用户登录并获取JWT token - 修复版本"""
    print("🔐 测试用户登录...")
    
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "username": "test2",
        "password": "123456"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(login_url, json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"登录响应: {result}")  # 调试信息
                
                # 根据你的auth.py，token在data字段中
                if result.get("success") and "data" in result:
                    token = result["data"].get("access_token")
                    if token:
                        print(f"✅ 登录成功！Token: {token[:50]}...")
                        return token
                    else:
                        print("❌ 登录响应data中没有access_token")
                        print(f"data内容: {result['data']}")
                else:
                    print("❌ 登录响应格式不正确")
                    print(f"完整响应: {result}")
                return ""
            elif response.status_code == 401:
                print("❌ 登录失败: 用户名或密码错误")
                print(f"错误信息: {response.text}")
                return ""
            elif response.status_code == 423:
                print("❌ 登录失败: 账户被锁定")
                print(f"错误信息: {response.text}")
                return ""
            else:
                print(f"❌ 登录失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return ""
                
    except Exception as e:
        print(f"❌ 登录请求异常: {e}")
        import traceback
        traceback.print_exc()
        return ""

async def test_direct_api_call():
    """直接调用DeepSeek API测试"""
    print("\n🎯 直接调用DeepSeek API测试...")
    
    try:
        # 创建DeepSeek客户端
        client = create_deepseek_client(
            api_key="sk-d35fc57d5206433bb336ea0fb2b5878b"
        )
        
        # 测试连接
        print("1. 测试API连接...")
        connection_ok = await client.test_connection()
        if connection_ok:
            print("✅ API连接正常")
        else:
            print("❌ API连接失败")
            return False
        
        # 获取可用模型
        print("2. 获取可用模型列表...")
        try:
            models = await client.models()
            if models and "data" in models:
                print(f"✅ 可用模型: {', '.join([m['id'] for m in models['data']])}")
            else:
                print(f"✅ 获取模型列表成功")
        except Exception as e:
            print(f"⚠️  获取模型列表失败: {e}")
        
        # 发送测试消息
        print("3. 发送测试消息...")
        messages = [
            {"role": "user", "content": "你好，请简单介绍一下你自己，用中文回答。"}
        ]
        
        start_time = time.time()
        
        try:
            response = await client.chat_completion(
                messages=messages,
                model="deepseek-chat",
                temperature=0.7,
                max_tokens=500,
                stream=False
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response and "choices" in response:
                reply = response["choices"][0]["message"]["content"]
                usage = response.get("usage", {})
                
                print(f"✅ API调用成功！响应时间: {response_time:.0f}ms")
                print(f"🤖 模型回复: {reply[:100]}...")
                print(f"📊 Token使用: 输入={usage.get('prompt_tokens', 'N/A')}, "
                      f"输出={usage.get('completion_tokens', 'N/A')}")
                
                return True
            else:
                print(f"❌ API响应格式错误: {response}")
                return False
                
        except Exception as e:
            print(f"❌ API调用失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_backend_chat_api(token: str):
    """测试后端聊天API"""
    print(f"\n🚀 测试后端聊天API (需要token)...")
    
    if not token:
        print("❌ 无有效token，跳过后端API测试")
        return False
    
    chat_url = "http://localhost:8000/api/v1/models/chat"
    
    chat_data = {
        "message": "你好，请简单介绍一下你自己，用中文回答。",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            start_time = time.time()
            response = await client.post(
                chat_url,
                json=chat_data,
                headers=headers
            )
            response_time = (time.time() - start_time) * 1000
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")  # 调试信息
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 后端API调用成功！响应时间: {response_time:.0f}ms")
                
                # 根据你的API设计，响应可能在data字段中
                if "data" in result:
                    chat_response = result["data"]
                    print(f"🤖 回复: {chat_response.get('response', '')[:100]}...")
                    print(f"📊 对话ID: {chat_response.get('conversation_id')}")
                else:
                    print(f"🤖 回复: {result.get('response', '')[:100]}...")
                    print(f"📊 对话ID: {result.get('conversation_id')}")
                
                return True
            else:
                print(f"❌ 后端API调用失败: {response.status_code}")
                print(f"错误详情: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 后端API请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_config():
    """检查数据库配置"""
    print("\n🔍 检查数据库配置...")
    
    # 初始化数据库
    init_database()
    
    # 获取数据库会话
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 检查用户
        user = db.query(User).filter(User.username == "test2").first()
        if user:
            print(f"✅ 用户test2存在 (ID: {user.user_id}, 状态: {'活跃' if user.is_active else '禁用'})")
            
            # 验证密码
            from app.core.security import verify_password
            password_valid = verify_password("123456", user.password_hash)
            print(f"   密码验证: {'正确' if password_valid else '错误'}")
        else:
            print("❌ 用户test2不存在")
            return False
        
        # 检查模型
        model = db.query(SystemModel).filter(
            SystemModel.model_name == "deepseek-chat"
        ).first()
        if model:
            print(f"✅ DeepSeek模型存在 (ID: {model.model_id}, 名称: {model.model_name})")
        else:
            print("❌ DeepSeek模型不存在")
            return False
        
        # 检查用户模型配置
        config = db.query(UserModelConfig).filter(
            UserModelConfig.user_id == user.user_id,
            UserModelConfig.model_id == model.model_id
        ).first()
        
        if config:
            print(f"✅ 用户模型配置存在 (配置ID: {config.config_id})")
            print(f"   启用状态: {'已启用' if config.is_enabled else '禁用'}")
            print(f"   优先级: {config.priority}")
            print(f"   API密钥: {config.api_key[:10]}..." if config.api_key else "   API密钥: 未设置")
            return True
        else:
            print("❌ 用户模型配置不存在")
            return False
            
    except Exception as e:
        print(f"❌ 数据库查询错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            next(db_gen)  # 完成生成器
        except StopIteration:
            pass

async def test_health_check():
    """测试后端服务健康状态"""
    print("\n🏥 测试后端服务健康状态...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8000/health")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 后端服务健康: {result}")
                return True
            else:
                print(f"⚠️  后端服务异常: {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        print("请确保后端服务正在运行:")
        print("uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 DeepSeek API集成测试 - 修复版")
    print("=" * 60)
    
    # 首先测试后端服务是否运行
    health_ok = await test_health_check()
    if not health_ok:
        print("\n⚠️  后端服务未运行，无法继续测试")
        return
    
    # 检查数据库配置
    config_ok = check_database_config()
    if not config_ok:
        print("\n⚠️  数据库配置不完整，请先运行配置脚本:")
        print("python scripts/create_test_config.py")
        return
    
    # 测试直接API调用
    print("\n" + "=" * 40)
    print("测试1: 直接调用DeepSeek API")
    print("=" * 40)
    direct_result = await test_direct_api_call()
    
    # 测试登录
    print("\n" + "=" * 40)
    print("测试2: 用户登录")
    print("=" * 40)
    token = await test_login()
    
    # 测试后端API
    if token:
        print("\n" + "=" * 40)
        print("测试3: 后端聊天API")
        print("=" * 40)
        backend_result = await test_backend_chat_api(token)
    else:
        backend_result = False
        print("\n⚠️  无法获取token，跳过聊天API测试")
    
    # 测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"✅ 后端服务健康: {'是' if health_ok else '否'}")
    print(f"✅ 数据库配置: {'正确' if config_ok else '错误'}")
    print(f"✅ 直接API调用: {'成功' if direct_result else '失败'}")
    print(f"✅ 用户登录: {'成功' if token else '失败'}")
    print(f"✅ 后端API调用: {'成功' if backend_result else '失败'}")
    
    if direct_result and token and backend_result:
        print("\n🎉 所有测试通过！DeepSeek API集成正常。")
    else:
        print("\n⚠️  部分测试失败，请检查:")
        if not direct_result:
            print("  - 直接API调用失败：检查API密钥和网络连接")
        if not token:
            print("  - 登录失败：检查用户密码或后端服务响应格式")
        if not backend_result and token:
            print("  - 后端API调用失败：检查后端服务状态和配置")

if __name__ == "__main__":
    # 检查是否在项目根目录
    current_dir = Path(__file__).parent.parent
    if not (current_dir / "app").exists():
        print("❌ 请在项目根目录运行此脚本")
        print("运行示例: python scripts/test_deepseek_integration_fixed.py")
        sys.exit(1)
    
    asyncio.run(main())
