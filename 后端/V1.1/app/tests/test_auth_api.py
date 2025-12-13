#!/usr/bin/env python3
"""
用户认证API测试脚本 - 修复导入问题版本
"""

import sys
import os
import json
import time
from typing import Dict, Any, Optional
import subprocess
import requests
import atexit

# ====== 路径设置和导入修复 ======
# 获取当前测试文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))  # app/tests
app_dir = os.path.dirname(current_dir)  # app
project_root = os.path.dirname(app_dir)  # 项目根目录

# 将所有可能的路径添加到sys.path
sys.path.insert(0, project_root)
sys.path.insert(0, app_dir)
sys.path.insert(0, current_dir)

print(f"当前目录: {current_dir}")
print(f"app目录: {app_dir}")
print(f"项目根目录: {project_root}")
print(f"Python路径: {sys.path[:3]}")

# 尝试导入必要的模块
try:
    from fastapi.testclient import TestClient
    from fastapi import status
    import uvicorn
    
    print("✅ FastAPI相关模块导入成功")
except ImportError as e:
    print(f"❌ FastAPI模块导入失败: {e}")
    sys.exit(1)

# ====== 测试配置 ======
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
TEST_USER = {
    "username": "test1",
    "password": "1234567",
    "email": "test1@example.com"
}
NEW_USER = {
    "username": "new_test_user",
    "password": "NewPass123!",
    "confirm_password": "NewPass123!",
    "email": "new_test@example.com"
}
INVALID_USER = {
    "username": "nonexistent",
    "password": "wrongpassword"
}

# ====== 测试状态 ======
test_state = {
    "access_token": None,
    "user_id": None,
    "server_process": None
}

# ====== 服务器管理 ======
def start_test_server():
    """启动测试服务器"""
    print("🚀 启动测试服务器...")
    
    # 使用subprocess启动服务器
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{project_root}{os.pathsep}{app_dir}"
    
    # 运行服务器命令
    server_cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload", "false"
    ]
    
    try:
        # 启动服务器进程
        process = subprocess.Popen(
            server_cmd,
            cwd=project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        test_state["server_process"] = process
        
        # 等待服务器启动
        print("⏳ 等待服务器启动...")
        max_wait = 30
        for i in range(max_wait):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=1)
                if response.status_code == 200:
                    print("✅ 测试服务器启动成功")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            if i % 5 == 0:
                print(f"等待服务器启动... ({i+1}/{max_wait}秒)")
        
        print("❌ 服务器启动超时")
        return False
        
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        return False

def stop_test_server():
    """停止测试服务器"""
    print("🛑 停止测试服务器...")
    
    if test_state["server_process"]:
        try:
            test_state["server_process"].terminate()
            test_state["server_process"].wait(timeout=10)
            print("✅ 测试服务器已停止")
        except subprocess.TimeoutExpired:
            test_state["server_process"].kill()
            print("⚠️  强制停止测试服务器")
        except Exception as e:
            print(f"❌ 停止服务器失败: {e}")

# ====== 测试辅助函数 ======
def make_request(method, endpoint, json_data=None, headers=None, expected_status=None):
    """发送HTTP请求并处理响应"""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=json_data, headers=headers)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        
        if expected_status and response.status_code != expected_status:
            print(f"⚠️  状态码不匹配: 期望 {expected_status}, 实际 {response.status_code}")
            return None
        
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误 {e.response.status_code}: {e.response.text}")
        if expected_status and e.response.status_code == expected_status:
            return None
        raise
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        raise
    except Exception as e:
        print(f"请求处理异常: {e}")
        raise

def print_response(response_data, title="响应"):
    """打印响应数据"""
    print(f"\n{'='*60}")
    print(f"{title}:")
    print(f"{'='*60}")
    if response_data:
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
    else:
        print("无响应数据")

# ====== 测试函数 ======
def test_health_check():
    """测试健康检查端点"""
    print("\n🧪 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print_response(data, "健康检查响应")
    
    assert response.status_code == 200
    assert data["status"] in ["healthy", "degraded"]
    print("✅ 健康检查测试通过")
    return True  # 添加这行

def test_login_success():
    """测试登录成功"""
    print("\n🧪 测试登录成功...")
    
    data = make_request("POST", "/auth/login", json_data={
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    })
    
    print_response(data, "登录成功响应")
    
    assert data["success"] == True
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["username"] == TEST_USER["username"]
    
    test_state["access_token"] = data["data"]["access_token"]
    test_state["user_id"] = data["data"]["user_id"]
    
    print("✅ 登录成功测试通过")
    return True

def test_login_invalid_credentials():
    """测试登录 - 无效凭据"""
    print("\n🧪 测试登录无效凭据...")
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={
                "username": INVALID_USER["username"],
                "password": INVALID_USER["password"]
            }
        )
        
        print(f"状态码: {response.status_code}")
        
        # 应该是401未授权
        assert response.status_code == 401
        print("✅ 登录无效凭据测试通过")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("✅ 登录无效凭据测试通过")
            return True
        else:
            print(f"❌ 期望401但得到 {e.response.status_code}")
            return False

def test_login_wrong_password():
    """测试登录 - 错误密码"""
    print("\n🧪 测试登录错误密码...")
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": "wrong_password"
            }
        )
        
        print(f"状态码: {response.status_code}")
        
        # 应该是401未授权
        assert response.status_code == 401
        print("✅ 登录错误密码测试通过")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("✅ 登录错误密码测试通过")
            return True
        else:
            print(f"❌ 期望401但得到 {e.response.status_code}")
            return False

def test_register_success():
    """测试注册成功"""
    print("\n🧪 测试注册成功...")
    
    data = make_request("POST", "/auth/register", json_data=NEW_USER)
    
    print_response(data, "注册成功响应")
    
    assert data["success"] == True
    assert "access_token" in data["data"]
    assert data["message"] == "注册成功"
    
    print("✅ 注册成功测试通过")
    return True

def test_register_existing_username():
    """测试注册 - 用户名已存在"""
    print("\n🧪 测试注册用户名已存在...")
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json={
                "username": TEST_USER["username"],
                "password": "SomePass123!",
                "confirm_password": "SomePass123!",
                "email": "newemail@example.com"
            }
        )
        
        print(f"状态码: {response.status_code}")
        
        # 应该是400错误请求
        assert response.status_code == 400
        print("✅ 注册用户名已存在测试通过")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print("✅ 注册用户名已存在测试通过")
            return True
        else:
            print(f"❌ 期望400但得到 {e.response.status_code}")
            return False

def test_get_current_user_with_token():
    """测试获取当前用户 - 有效令牌"""
    print("\n🧪 测试获取当前用户（有效令牌）...")
    
    if not test_state["access_token"]:
        print("⚠️  没有可用的令牌，先执行登录测试")
        return False
    
    headers = {"Authorization": f"Bearer {test_state['access_token']}"}
    data = make_request("GET", "/auth/me", headers=headers)
    
    print_response(data, "获取用户信息响应")
    
    assert data["success"] == True
    assert data["data"]["username"] == TEST_USER["username"]
    
    print("✅ 获取当前用户测试通过")
    return True

def test_get_current_user_without_token():
    """测试获取当前用户 - 无令牌"""
    print("\n🧪 测试获取当前用户（无令牌）...")
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/auth/me")
        
        print(f"状态码: {response.status_code}")
        
        # 应该是403禁止访问
        assert response.status_code == 403
        print("✅ 获取当前用户（无令牌）测试通过")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("✅ 获取当前用户（无令牌）测试通过")
            return True
        else:
            print(f"❌ 期望403但得到 {e.response.status_code}")
            return False

def test_validate_token_success():
    """测试验证令牌 - 成功"""
    print("\n🧪 测试验证令牌成功...")
    
    if not test_state["access_token"]:
        print("⚠️  没有可用的令牌，先执行登录测试")
        return False
    
    headers = {"Authorization": f"Bearer {test_state['access_token']}"}
    data = make_request("GET", "/auth/validate-token", headers=headers)
    
    print_response(data, "验证令牌响应")
    
    assert data["success"] == True
    assert data["data"]["valid"] == True
    
    print("✅ 验证令牌成功测试通过")
    return True

def test_validate_token_invalid():
    """测试验证令牌 - 无效令牌"""
    print("\n🧪 测试验证令牌（无效令牌）...")
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/auth/validate-token",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        print(f"状态码: {response.status_code}")
        
        # 应该是401未授权
        assert response.status_code == 401
        print("✅ 验证令牌（无效令牌）测试通过")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("✅ 验证令牌（无效令牌）测试通过")
            return True
        else:
            print(f"❌ 期望401但得到 {e.response.status_code}")
            return False

def test_refresh_token_success():
    """测试刷新令牌 - 成功"""
    print("\n🧪 测试刷新令牌成功...")
    
    if not test_state["access_token"]:
        print("⚠️  没有可用的令牌，先执行登录测试")
        return False
    
    headers = {"Authorization": f"Bearer {test_state['access_token']}"}
    data = make_request("POST", "/auth/refresh-token", headers=headers)
    
    print_response(data, "刷新令牌响应")
    
    assert data["success"] == True
    assert "access_token" in data["data"]
    
    print("✅ 刷新令牌成功测试通过")
    return True

def test_logout_success():
    """测试登出 - 成功"""
    print("\n🧪 测试登出成功...")
    
    if not test_state["access_token"]:
        print("⚠️  没有可用的令牌，先执行登录测试")
        return False
    
    headers = {"Authorization": f"Bearer {test_state['access_token']}"}
    data = make_request("POST", "/auth/logout", headers=headers)
    
    print_response(data, "登出响应")
    
    assert data["success"] == True
    
    print("✅ 登出成功测试通过")
    return True

def test_forgot_password():
    """测试忘记密码"""
    print("\n🧪 测试忘记密码...")
    
    data = make_request("POST", "/auth/forgot-password", json_data={
        "username": TEST_USER["username"],
        "email": TEST_USER["email"]
    })
    
    print_response(data, "忘记密码响应")
    
    assert data["success"] == True
    
    print("✅ 忘记密码测试通过")
    return True

def test_get_login_attempts():
    """测试获取登录尝试记录"""
    print("\n🧪 测试获取登录尝试记录...")
    
    if not test_state["access_token"]:
        print("⚠️  没有可用的令牌，先执行登录测试")
        return False
    
    headers = {"Authorization": f"Bearer {test_state['access_token']}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/auth/login-attempts/{TEST_USER['username']}",
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        
        # 可能是200、403或401
        assert response.status_code in [200, 403, 401]
        print("✅ 获取登录尝试记录测试通过")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [200, 403, 401]:
            print("✅ 获取登录尝试记录测试通过")
            return True
        else:
            print(f"❌ 期望200/403/401但得到 {e.response.status_code}")
            return False

def test_change_password_success():
    """测试修改密码 - 成功"""
    print("\n🧪 测试修改密码成功...")
    
    # 先登录获取令牌
    login_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    
    if login_response.status_code != 200:
        print("❌ 登录失败，无法测试修改密码")
        return False
    
    token = login_response.json()["data"]["access_token"]
    
    # 修改密码
    headers = {"Authorization": f"Bearer {token}"}
    password_data = {
        "current_password": TEST_USER["password"],
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    }
    
    data = make_request("POST", "/auth/change-password", 
                        json_data=password_data, headers=headers)
    
    print_response(data, "修改密码响应")
    
    assert data["success"] == True
    
    # 测试用新密码登录
    new_login_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json={
            "username": TEST_USER["username"],
            "password": "NewPassword123!"
        }
    )
    
    assert new_login_response.status_code == 200
    
    # 改回原密码
    new_token = new_login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {new_token}"}
    reset_password_data = {
        "current_password": "NewPassword123!",
        "new_password": TEST_USER["password"],
        "confirm_password": TEST_USER["password"]
    }
    
    reset_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/change-password",
        json=reset_password_data,
        headers=headers
    )
    
    assert reset_response.status_code == 200
    
    print("✅ 修改密码成功测试通过")
    return True

# ====== 主测试运行器 ======
def run_all_tests():
    """运行所有测试"""
    print(f"{'='*70}")
    print("🚀 开始运行API测试")
    print(f"{'='*70}")
    
    # 注册退出处理
    atexit.register(stop_test_server)
    
    # 启动测试服务器
    if not start_test_server():
        print("❌ 无法启动测试服务器，测试终止")
        return False
    
    # 等待服务器完全启动
    time.sleep(2)
    
    # 测试列表
    tests = [
        ("健康检查", test_health_check),
        ("登录成功", test_login_success),
        ("登录-无效凭据", test_login_invalid_credentials),
        ("登录-错误密码", test_login_wrong_password),
        ("注册成功", test_register_success),
        ("注册-用户名已存在", test_register_existing_username),
        ("获取用户-有效令牌", test_get_current_user_with_token),
        ("获取用户-无令牌", test_get_current_user_without_token),
        ("验证令牌-成功", test_validate_token_success),
        ("验证令牌-无效", test_validate_token_invalid),
        ("刷新令牌-成功", test_refresh_token_success),
        ("登出-成功", test_logout_success),
        ("忘记密码", test_forgot_password),
        ("获取登录尝试记录", test_get_login_attempts),
        ("修改密码-成功", test_change_password_success),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    # 运行测试
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"运行测试: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                failed += 1
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - 异常: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60)
        time.sleep(1)  # 避免请求过于频繁
    
    # 停止服务器
    stop_test_server()
    
    # 输出结果
    print(f"{'='*70}")
    print(f"📊 测试完成统计:")
    print(f"   总测试数: {len(tests)}")
    print(f"   通过: {passed}")
    print(f"   失败: {failed}")
    print(f"   跳过: {skipped}")
    print(f"{'='*70}")
    
    if failed == 0:
        print("🎉 恭喜！所有测试通过！")
    else:
        print(f"⚠️  有 {failed} 个测试失败，请检查问题")
    
    return failed == 0

if __name__ == "__main__":
    try:
        # 检查必要的环境
        print("🔍 检查测试环境...")
        print(f"Python版本: {sys.version}")
        print(f"工作目录: {os.getcwd()}")
        
        # 运行测试
        success = run_all_tests()
        
        # 返回退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n🛑 测试被用户中断")
        stop_test_server()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行异常: {e}")
        import traceback
        traceback.print_exc()
        stop_test_server()
        sys.exit(1)
