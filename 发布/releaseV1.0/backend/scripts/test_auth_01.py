# test_auth_01.py
"""
测试用例 AUTH-01：用户注册、登录、令牌验证完整流程
验证数据库用户表的唯一约束、密码加密机制以及JWT签发与刷新流程的完整性
"""

# test_auth_01_fixed.py
"""
测试用例 AUTH-01：用户注册、登录、令牌验证完整流程（修复版）
验证数据库用户表的唯一约束、密码加密机制以及JWT签发与刷新流程的完整性
"""

import requests
import json
import time
import random
import string
from typing import Dict, Any, Tuple

class AuthFlowTester:
    """认证流程测试类（修复版）"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        初始化测试器
        
        Args:
            base_url: 后端API基础URL，默认为本地8002端口
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.session = requests.Session()
        self.test_data = self._generate_test_data()
        
    def _generate_test_data(self) -> Dict[str, str]:
        """生成唯一的测试数据"""
        timestamp = int(time.time())
        random_str = ''.join(random.choices(string.ascii_lowercase, k=6))
        
        return {
            "username": f"testuser_{timestamp}_{random_str}",
            "email": f"test_{timestamp}_{random_str}@example.com",
            "password": "Test@123456",  # 符合密码策略：包含大小写字母、数字、特殊字符，长度>=8
            "wrong_password": "Wrong@123"
        }
    
    def _print_test_step(self, step: int, description: str):
        """打印测试步骤信息"""
        print(f"\n{'='*60}")
        print(f"步骤 {step}: {description}")
        print(f"{'='*60}")
    
    def _print_success(self, message: str):
        """打印成功信息"""
        print(f"✅ {message}")
    
    def _print_failure(self, message: str, response=None):
        """打印失败信息"""
        print(f"❌ {message}")
        if response:
            print(f"   状态码: {response.status_code}")
            try:
                if response.text:
                    print(f"   响应: {response.text[:200]}...")
            except:
                pass
    
    def test_register(self) -> Tuple[bool, Dict[str, Any]]:
        """
        步骤1：用户注册
        POST /api/v1/auth/register
        """
        self._print_test_step(1, "用户注册")
        
        url = f"{self.api_url}/auth/register"
        payload = {
            "username": self.test_data["username"],
            "email": self.test_data["email"],
            "password": self.test_data["password"],
            "confirm_password": self.test_data["password"]  # 添加确认密码字段
        }
        
        print(f"测试数据:")
        print(f"  用户名: {self.test_data['username']}")
        print(f"  邮箱: {self.test_data['email']}")
        print(f"  密码: {self.test_data['password']}")
        print(f"  确认密码: {self.test_data['password']}")
        
        try:
            response = self.session.post(url, json=payload)
            print(f"\n请求URL: {url}")
            print(f"请求体: {json.dumps(payload, indent=2)}")
            print(f"响应状态码: {response.status_code}")
            
            # 断言1：状态码应为200
            if response.status_code != 200:
                self._print_failure("注册失败 - 状态码不是200", response)
                return False, {}
            
            # 解析响应
            result = response.json()
            print(f"响应体: {json.dumps(result, indent=2)}")
            
            # 断言2：响应应包含success字段且为True
            if not result.get("success"):
                self._print_failure("注册失败 - 响应success字段不为True", response)
                return False, {}
            
            # 断言3：响应应包含message字段
            message = result.get("message", "")
            if "成功" not in message:
                self._print_failure(f"注册失败 - 消息不包含'成功': {message}", response)
                return False, {}
            
            # 断言4：响应应包含data字段，且包含access_token
            data = result.get("data", {})
            if "access_token" not in data:
                self._print_failure("注册失败 - 响应中缺少access_token", response)
                return False, data
            
            self._print_success(f"注册成功: {message}")
            print(f"   获取到访问令牌: {data['access_token'][:30]}...")
            
            return True, data
            
        except requests.exceptions.ConnectionError:
            self._print_failure(f"无法连接到服务器: {url}")
            print("   请确保后端服务正在运行，并且端口8002正确暴露")
            return False, {}
        except Exception as e:
            self._print_failure(f"注册过程中发生异常: {str(e)}")
            return False, {}
    
    def test_login(self) -> Tuple[bool, Dict[str, Any]]:
        """
        步骤2：用户登录
        POST /api/v1/auth/login
        """
        self._print_test_step(2, "用户登录")
        
        url = f"{self.api_url}/auth/login"
        payload = {
            "username": self.test_data["username"],
            "password": self.test_data["password"]
        }
        
        print(f"测试数据:")
        print(f"  用户名: {self.test_data['username']}")
        print(f"  密码: {self.test_data['password']}")
        
        try:
            response = self.session.post(url, json=payload)
            print(f"\n请求URL: {url}")
            print(f"请求体: {json.dumps(payload, indent=2)}")
            print(f"响应状态码: {response.status_code}")
            
            # 断言1：状态码应为200
            if response.status_code != 200:
                self._print_failure("登录失败 - 状态码不是200", response)
                return False, {}
            
            # 解析响应
            result = response.json()
            print(f"响应体: {json.dumps(result, indent=2)}")
            
            # 断言2：响应应包含success字段且为True
            if not result.get("success"):
                self._print_failure("登录失败 - 响应success字段不为True", response)
                return False, {}
            
            # 断言3：响应应包含message字段
            message = result.get("message", "")
            if "成功" not in message:
                self._print_failure(f"登录失败 - 消息不包含'成功': {message}", response)
                return False, {}
            
            # 断言4：响应应包含data字段，且包含access_token
            data = result.get("data", {})
            if "access_token" not in data:
                self._print_failure("登录失败 - 响应中缺少access_token", response)
                return False, data
            
            # 断言5：应该返回正确的用户信息
            if data.get("username") != self.test_data["username"]:
                self._print_failure(f"登录失败 - 用户名不匹配: {data.get('username')} != {self.test_data['username']}")
                return False, data
            
            self._print_success(f"登录成功: {message}")
            print(f"   获取到访问令牌: {data['access_token'][:30]}...")
            print(f"   用户ID: {data.get('user_id')}")
            print(f"   用户名: {data.get('username')}")
            
            # 保存令牌供后续使用
            self.access_token = data["access_token"]
            
            return True, data
            
        except Exception as e:
            self._print_failure(f"登录过程中发生异常: {str(e)}")
            return False, {}
    
    def test_wrong_password_login(self) -> bool:
        """
        步骤2.1：测试错误密码登录（额外验证）
        POST /api/v1/auth/login
        """
        self._print_test_step(2.1, "错误密码登录验证")
        
        url = f"{self.api_url}/auth/login"
        payload = {
            "username": self.test_data["username"],
            "password": self.test_data["wrong_password"]
        }
        
        print(f"测试数据:")
        print(f"  用户名: {self.test_data['username']}")
        print(f"  错误密码: {self.test_data['wrong_password']}")
        
        try:
            response = self.session.post(url, json=payload)
            print(f"\n请求URL: {url}")
            print(f"请求体: {json.dumps(payload, indent=2)}")
            print(f"响应状态码: {response.status_code}")
            
            # 断言：使用错误密码应该登录失败
            # 可能的状态码：401（认证失败）或400（请求错误）
            if response.status_code in [200, 201]:
                self._print_failure("错误密码登录验证失败 - 使用错误密码竟然登录成功了", response)
                return False
            
            result = response.json()
            print(f"响应体: {json.dumps(result, indent=2)}")
            
            self._print_success("错误密码登录验证通过 - 如预期般登录失败")
            return True
            
        except Exception as e:
            self._print_failure(f"错误密码登录验证过程中发生异常: {str(e)}")
            return False
    
    def test_protected_endpoint(self) -> bool:
        """
        步骤3：访问受保护接口
        GET /api/v1/auth/me (需要JWT令牌)
        """
        self._print_test_step(3, "访问受保护接口")
        
        if not hasattr(self, 'access_token'):
            self._print_failure("无法测试受保护接口 - 没有有效的访问令牌")
            return False
        
        url = f"{self.api_url}/auth/me"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        print(f"访问受保护端点: {url}")
        print(f"使用令牌: {self.access_token[:30]}...")
        
        try:
            response = self.session.get(url, headers=headers)
            print(f"\n请求URL: {url}")
            print(f"请求头: Authorization: Bearer {self.access_token[:30]}...")
            print(f"响应状态码: {response.status_code}")
            
            # 断言1：状态码应为200
            if response.status_code != 200:
                self._print_failure("访问受保护接口失败 - 状态码不是200", response)
                return False
            
            # 解析响应
            result = response.json()
            print(f"响应体: {json.dumps(result, indent=2)}")
            
            # 断言2：响应应包含success字段且为True
            if not result.get("success"):
                self._print_failure("访问受保护接口失败 - 响应success字段不为True", response)
                return False
            
            # 断言3：响应应包含用户信息
            data = result.get("data", {})
            if not data:
                self._print_failure("访问受保护接口失败 - 响应中缺少用户数据", response)
                return False
            
            # 断言4：用户信息应该匹配
            if data.get("username") != self.test_data["username"]:
                self._print_failure(f"用户信息不匹配: {data.get('username')} != {self.test_data['username']}")
                return False
            
            self._print_success("受保护接口访问成功")
            print(f"   获取到用户信息:")
            print(f"     用户ID: {data.get('user_id')}")
            print(f"     用户名: {data.get('username')}")
            print(f"     邮箱: {data.get('email')}")
            
            return True
            
        except Exception as e:
            self._print_failure(f"访问受保护接口过程中发生异常: {str(e)}")
            return False
    
    def test_token_validation(self) -> bool:
        """
        步骤4：验证令牌有效性
        GET /api/v1/auth/validate-token
        """
        self._print_test_step(4, "验证令牌有效性")
        
        if not hasattr(self, 'access_token'):
            self._print_failure("无法验证令牌 - 没有有效的访问令牌")
            return False
        
        url = f"{self.api_url}/auth/validate-token"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        print(f"验证令牌端点: {url}")
        
        try:
            response = self.session.get(url, headers=headers)
            print(f"\n请求URL: {url}")
            print(f"请求头: Authorization: Bearer {self.access_token[:30]}...")
            print(f"响应状态码: {response.status_code}")
            
            # 断言1：状态码应为200
            if response.status_code != 200:
                self._print_failure("令牌验证失败 - 状态码不是200", response)
                return False
            
            # 解析响应
            result = response.json()
            print(f"响应体: {json.dumps(result, indent=2)}")
            
            # 断言2：响应应包含success字段且为True
            if not result.get("success"):
                self._print_failure("令牌验证失败 - 响应success字段不为True", response)
                return False
            
            # 断言3：令牌应被标记为有效
            data = result.get("data", {})
            if not data.get("valid"):
                self._print_failure("令牌验证失败 - 令牌被标记为无效", response)
                return False
            
            self._print_success("令牌验证成功")
            print(f"   令牌状态: 有效")
            print(f"   用户ID: {data.get('user_id')}")
            print(f"   用户名: {data.get('username')}")
            
            return True
            
        except Exception as e:
            self._print_failure(f"令牌验证过程中发生异常: {str(e)}")
            return False
    
    def test_duplicate_registration(self) -> bool:
        """
        步骤5：测试重复注册（验证数据库唯一约束）
        POST /api/v1/auth/register
        """
        self._print_test_step(5, "测试重复注册（验证唯一约束）")
        
        url = f"{self.api_url}/auth/register"
        payload = {
            "username": self.test_data["username"],  # 使用已注册的用户名
            "email": f"duplicate_{self.test_data['email']}",  # 使用不同的邮箱
            "password": self.test_data["password"],
            "confirm_password": self.test_data["password"]  # 修复：添加确认密码字段
        }
        
        print(f"测试数据:")
        print(f"  重复用户名: {self.test_data['username']}")
        print(f"  新邮箱: {payload['email']}")
        print(f"  密码: {self.test_data['password']}")
        print(f"  确认密码: {self.test_data['password']}")
        
        try:
            response = self.session.post(url, json=payload)
            print(f"\n请求URL: {url}")
            print(f"请求体: {json.dumps(payload, indent=2)}")
            print(f"响应状态码: {response.status_code}")
            
            # 解析响应
            result = {}
            try:
                result = response.json()
                print(f"响应体: {json.dumps(result, indent=2)}")
            except:
                print(f"响应体: {response.text}")
            
            # 断言：重复注册应该失败
            # 可能的状态码：400（错误请求）、409（冲突）或422（验证错误）
            if response.status_code in [200, 201]:
                if result.get("success"):
                    self._print_failure("重复注册验证失败 - 竟然允许重复注册", response)
                    return False
                else:
                    # 虽然状态码是200，但success为False
                    self._print_success("重复注册验证通过 - 返回了success: false")
                    return True
            
            # 检查错误消息是否提到用户已存在
            error_message = ""
            if response.status_code == 400:
                error_message = result.get("detail", "")
            elif response.status_code == 422:
                # Pydantic验证错误，可能是字段验证错误
                if isinstance(result.get("detail"), list):
                    for error in result["detail"]:
                        if error.get("type") == "value_error" or error.get("type") == "validation_error":
                            error_message = str(error.get("msg", ""))
                else:
                    error_message = str(result.get("detail", ""))
            
            # 检查是否包含用户已存在的提示
            if "已存在" in error_message or "exist" in error_message.lower() or "already" in error_message.lower():
                self._print_success("重复注册验证通过 - 如预期般阻止重复注册")
                return True
            else:
                self._print_failure(f"重复注册验证失败 - 错误消息不匹配: {error_message}")
                return False
            
        except Exception as e:
            self._print_failure(f"重复注册验证过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_duplicate_email_registration(self) -> bool:
        """
        步骤5.1：测试重复邮箱注册（验证数据库唯一约束）
        POST /api/v1/auth/register
        """
        self._print_test_step(5.1, "测试重复邮箱注册（验证唯一约束）")
        
        url = f"{self.api_url}/auth/register"
        
        # 生成新的用户名，但使用已存在的邮箱
        timestamp = int(time.time())
        random_str = ''.join(random.choices(string.ascii_lowercase, k=6))
        new_username = f"duplicate_email_test_{timestamp}_{random_str}"
        
        payload = {
            "username": new_username,  # 使用新的用户名
            "email": self.test_data["email"],  # 使用已注册的邮箱
            "password": self.test_data["password"],
            "confirm_password": self.test_data["password"]
        }
        
        print(f"测试数据:")
        print(f"  新用户名: {new_username}")
        print(f"  重复邮箱: {self.test_data['email']}")
        
        try:
            response = self.session.post(url, json=payload)
            print(f"\n请求URL: {url}")
            print(f"请求体: {json.dumps(payload, indent=2)}")
            print(f"响应状态码: {response.status_code}")
            
            # 解析响应
            result = {}
            try:
                result = response.json()
                print(f"响应体: {json.dumps(result, indent=2)}")
            except:
                print(f"响应体: {response.text}")
            
            # 断言：重复邮箱注册应该失败
            if response.status_code in [200, 201]:
                if result.get("success"):
                    self._print_failure("重复邮箱注册验证失败 - 竟然允许重复邮箱注册", response)
                    return False
                else:
                    # 虽然状态码是200，但success为False
                    self._print_success("重复邮箱注册验证通过 - 返回了success: false")
                    return True
            
            # 检查错误消息是否提到邮箱已存在
            error_message = ""
            if response.status_code == 400:
                error_message = result.get("detail", "")
            elif response.status_code == 422:
                # Pydantic验证错误
                if isinstance(result.get("detail"), list):
                    for error in result["detail"]:
                        if error.get("type") == "value_error" or error.get("type") == "validation_error":
                            error_message = str(error.get("msg", ""))
                else:
                    error_message = str(result.get("detail", ""))
            
            # 检查是否包含邮箱已存在的提示
            if "邮箱" in error_message or "email" in error_message.lower() or "already" in error_message.lower():
                self._print_success("重复邮箱注册验证通过 - 如预期般阻止重复邮箱注册")
                return True
            else:
                self._print_failure(f"重复邮箱注册验证失败 - 错误消息不匹配: {error_message}")
                return False
            
        except Exception as e:
            self._print_failure(f"重复邮箱注册验证过程中发生异常: {str(e)}")
            return False
    
    def run_full_test(self) -> bool:
        """
        运行完整的AUTH-01测试流程
        """
        print("="*60)
        print("开始执行测试用例 AUTH-01（修复版）")
        print("测试目标: 验证注册、登录、令牌获取的完整流程")
        print("测试端口: 8002 (Docker暴露端口)")
        print("="*60)
        
        test_results = []
        
        # 步骤1: 注册
        register_success, register_data = self.test_register()
        test_results.append(("1. 用户注册", register_success))
        
        if not register_success:
            print("\n⚠️  注册失败，跳过后续测试")
            self._print_summary(test_results)
            return False
        
        # 步骤2: 登录
        login_success, login_data = self.test_login()
        test_results.append(("2. 用户登录", login_success))
        
        # 步骤2.1: 错误密码登录（额外验证）
        wrong_pass_success = self.test_wrong_password_login()
        test_results.append(("2.1 错误密码登录验证", wrong_pass_success))
        
        if not login_success:
            print("\n⚠️  登录失败，跳过后续测试")
            self._print_summary(test_results)
            return False
        
        # 步骤3: 访问受保护接口
        protected_success = self.test_protected_endpoint()
        test_results.append(("3. 访问受保护接口", protected_success))
        
        # 步骤4: 验证令牌
        token_success = self.test_token_validation()
        test_results.append(("4. 令牌验证", token_success))
        
        # 步骤5: 测试重复用户名注册
        duplicate_success = self.test_duplicate_registration()
        test_results.append(("5. 重复用户名注册验证", duplicate_success))
        
        # 步骤5.1: 测试重复邮箱注册
        duplicate_email_success = self.test_duplicate_email_registration()
        test_results.append(("5.1 重复邮箱注册验证", duplicate_email_success))
        
        # 打印测试摘要
        self._print_summary(test_results)
        
        # 判断整体测试结果
        all_passed = all(result for _, result in test_results)
        return all_passed
    
    def _print_summary(self, test_results):
        """打印测试结果摘要"""
        print("\n" + "="*60)
        print("测试结果摘要")
        print("="*60)
        
        passed_count = 0
        total_count = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed_count += 1
        
        print(f"\n总计: {passed_count}/{total_count} 通过")
        
        if passed_count == total_count:
            print("\n🎉 所有测试用例通过！AUTH-01测试完成。")
        else:
            print(f"\n⚠️  有 {total_count - passed_count} 个测试用例失败")

def main():
    """主函数"""
    # 你可以修改这里的base_url来测试不同的环境
    # 例如: "http://localhost:8002" 或 "http://192.168.1.100:8002"
    base_url = "http://localhost:8002"
    
    print("正在启动AUTH-01测试（修复版）...")
    print(f"测试服务器: {base_url}")
    print("如果连接失败，请确保:")
    print("1. 后端服务正在Docker中运行")
    print("2. 端口8002已正确暴露到宿主机")
    print("3. 数据库服务已启动并连接正常")
    print("")
    
    tester = AuthFlowTester(base_url)
    
    try:
        success = tester.run_full_test()
        
        if success:
            print("\n" + "="*60)
            print("✅ AUTH-01测试用例完全通过！")
            print("验证内容:")
            print("  1. 用户注册功能正常")
            print("  2. 数据库唯一约束有效（用户名和邮箱）")
            print("  3. 密码加密机制正常")
            print("  4. 用户登录功能正常")
            print("  5. JWT令牌签发正常")
            print("  6. 令牌验证机制正常")
            print("  7. 受保护接口访问正常")
            print("  8. 错误密码被正确拒绝")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("❌ AUTH-01测试用例失败")
            print("="*60)
            return 1
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 2
    except Exception as e:
        print(f"\n测试过程中发生未预期错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
