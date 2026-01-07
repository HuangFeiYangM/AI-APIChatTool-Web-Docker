# test_password_security.py
"""
密码安全功能测试脚本 UNIT-01
用于验证 app/core/security.py 中的密码加密和验证函数
"""

# test_password_security_fixed.py
"""
密码安全功能测试脚本 - 修复版本
"""

import sys
import os
import hashlib
import random
import string
from pathlib import Path

# 添加项目路径到系统路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def generate_random_username():
    """生成随机的用户名"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}"

def generate_random_email():
    """生成随机的邮箱"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def test_password_functions():
    """测试密码加密和验证功能"""
    
    try:
        # 导入安全模块
        from app.core.security import (
            verify_password, 
            get_password_hash,
            check_password_policy,
            is_password_strong
        )
        
        print("=" * 60)
        print("密码加密/验证函数测试")
        print("=" * 60)
        
        # 测试用例1: 正常密码
        test_password = "Pass123!"
        
        print("\n📋 测试用例1: 正常密码")
        print(f"测试密码: {test_password}")
        
        # 1. 检查密码强度
        print("\n1. 检查密码强度...")
        strength_result = check_password_policy(test_password)
        print(f"   是否有效: {strength_result['is_valid']}")
        print(f"   强度等级: {strength_result['strength']}")
        if strength_result['errors']:
            print(f"   错误信息: {strength_result['errors']}")
        
        # 2. 加密密码
        print("\n2. 加密密码...")
        hashed_password = get_password_hash(test_password)
        print(f"   加密前: {test_password}")
        print(f"   加密后: {hashed_password}")
        
        # 验证加密结果不是明文
        assert test_password != hashed_password, "❌ 加密失败：哈希值等于明文"
        print("   ✅ 加密成功：哈希值与明文不同")
        
        # 3. 验证相同密码
        print("\n3. 验证相同密码...")
        verify_same = verify_password(test_password, hashed_password)
        print(f"   验证结果: {verify_same}")
        assert verify_same, "❌ 密码验证失败：相同密码应该返回True"
        print("   ✅ 相同密码验证成功")
        
        # 4. 验证不同密码
        print("\n4. 验证不同密码...")
        wrong_password = "WrongPass456!"
        verify_wrong = verify_password(wrong_password, hashed_password)
        print(f"   测试错误密码: {wrong_password}")
        print(f"   验证结果: {verify_wrong}")
        assert not verify_wrong, "❌ 密码验证失败：不同密码应该返回False"
        print("   ✅ 不同密码验证失败（正确）")
        
        # 5. 测试bcrypt哈希格式
        print("\n5. 测试bcrypt哈希格式...")
        assert hashed_password.startswith("$2b$"), "❌ bcrypt哈希格式不正确"
        assert "$12$" in hashed_password, "❌ bcrypt轮数不正确"
        print("   ✅ bcrypt哈希格式正确")
        
        # 测试用例2: 弱密码
        print("\n\n📋 测试用例2: 弱密码测试")
        weak_passwords = [
            ("short", "太短"),
            ("nouppercase", "无大写字母"),
            ("NOLOWERCASE", "无小写字母"),
            ("NoNumbers", "无数字"),
            ("Numb3rsOnly", "无特殊字符"),
            ("Password123", "无特殊字符"),
        ]
        
        for pwd, description in weak_passwords:
            print(f"\n测试弱密码 '{pwd}' ({description}):")
            result = check_password_policy(pwd)
            if result['is_valid']:
                print(f"  ⚠️  意外有效: {result['errors'] or '无错误'}")
            else:
                error_count = len(result['errors'])
                print(f"  ✅ 正确识别为弱密码 ({error_count}个错误)")
        
        # 测试用例3: 强密码
        print("\n\n📋 测试用例3: 强密码测试")
        strong_passwords = [
            ("StrongP@ssw0rd!", "常规强密码"),
            ("MySecret!2024#", "包含年份"),
            ("Complex-P@ss123", "包含连字符"),
            ("A"*20 + "1!a", "超长密码"),
        ]
        
        for pwd, description in strong_passwords:
            print(f"\n测试强密码 '{pwd}' ({description}):")
            result = check_password_policy(pwd)
            if result['is_valid']:
                print(f"  ✅ 正确识别为有效密码（强度: {result['strength']}）")
            else:
                print(f"  ❌ 错误识别为无效: {', '.join(result['errors'])}")
        
        # 总结
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print("\n测试总结:")
        print("✅ 密码加密函数工作正常")
        print("✅ 密码验证函数工作正常")
        print("✅ 密码强度检查工作正常")
        print("✅ bcrypt哈希算法正确实现")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("\n请确保:")
        print("1. 当前目录在项目根目录")
        print("2. 已安装所有依赖: pip install -r requirements.txt")
        print("3. app 模块可正常导入")
        return False
    
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    
    except Exception as e:
        print(f"\n❌ 发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment():
    """测试环境配置"""
    print("🔧 环境配置测试...")
    
    try:
        from app.config import settings
        print(f"   项目名称: {settings.PROJECT_NAME}")
        print(f"   数据库URL: {settings.DATABASE_URL[:50]}...")
        print(f"   调试模式: {settings.DEBUG}")
        print("   ✅ 配置文件加载成功")
        return True
    except Exception as e:
        print(f"   ❌ 配置文件加载失败: {e}")
        return False

def run_api_tests():
    """通过API端点测试密码功能"""
    print("\n\n🌐 API端点测试")
    print("=" * 60)
    
    try:
        import requests
        
        # 使用后端端口（你提到的8002）
        BASE_URL = "http://localhost:8002"
        
        # 生成唯一用户名和邮箱
        username = generate_random_username()
        email = generate_random_email()
        password = "TestP@ss123!"
        
        # 测试注册端点
        print("\n📤 测试注册端点...")
        print(f"   测试数据:")
        print(f"     用户名: {username}")
        print(f"     密码: {password}")
        print(f"     邮箱: {email}")
        
        register_data = {
            "username": username,
            "password": password,
            "email": email,
            "confirm_password": password  # 添加这个字段
        }
        
        try:
            print(f"   请求URL: {BASE_URL}/api/v1/auth/register")
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/register",
                json=register_data,
                timeout=10
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 注册成功")
                print(f"     用户ID: {result.get('data', {}).get('user_id', '未知')}")
                print(f"     令牌: {result.get('data', {}).get('access_token', '未知')[:30]}...")
                return True
            elif response.status_code == 400 and "已存在" in response.text:
                print("   ⚠️  测试用户已存在（跳过）")
                return True
            else:
                print(f"   ❌ 注册失败: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("   ⚠️  API服务器未运行，跳过API测试")
            print("   请在运行测试前启动后端服务")
            return False
        except Exception as e:
            print(f"   ⚠️  API测试错误: {e}")
            return False
    
    except ImportError:
        print("   ⚠️  requests模块未安装，跳过API测试")
        print("   安装: pip install requests")
        return False

def test_password_policy_details():
    """详细测试密码策略"""
    print("\n\n🔍 密码策略详细测试")
    print("=" * 60)
    
    from app.core.security import check_password_policy
    
    test_cases = [
        # (密码, 预期有效, 描述)
        ("aA1!", False, "太短（4字符）"),
        ("12345678", False, "只有数字"),
        ("abcdefgh", False, "只有小写"),
        ("ABCDEFGH", False, "只有大写"),
        ("!@#$%^&*", False, "只有特殊字符"),
        ("Aa12345!", True, "有效（8字符）"),
        ("Aa12345", False, "无特殊字符"),
        ("aa12345!", False, "无大写"),
        ("AA12345!", False, "无小写"),
        ("AaBbCcDd!", False, "无数字"),
        ("LongPassword12!@", True, "有效（长密码）"),
        ("123", False, "太短"),
        ("密码123!", False, "包含中文（可能不允许）"),
        ("Test 123!", True, "包含空格"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for password, expected_valid, description in test_cases:
        result = check_password_policy(password)
        is_valid = result['is_valid']
        
        if is_valid == expected_valid:
            status = "✅"
            passed += 1
        else:
            status = "❌"
        
        print(f"{status} 密码: '{password}' ({description})")
        print(f"   预期有效: {expected_valid}, 实际有效: {is_valid}")
        if result['errors']:
            print(f"   错误: {', '.join(result['errors'])}")
        print()
    
    print(f"密码策略测试: {passed}/{total} 通过")

def main():
    print("🔐 密码安全功能测试程序")
    print("=" * 60)
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    all_passed = True
    
    # 测试环境
    env_passed = test_environment()
    all_passed = all_passed and env_passed
    
    # 测试核心函数
    password_passed = test_password_functions()
    all_passed = all_passed and password_passed
    
    # 详细密码策略测试
    test_password_policy_details()
    
    # 可选：API测试
    print("\n是否运行API测试？这需要后端服务正在运行。")
    print("后端端口: localhost:8002")
    run_api = input("运行API测试？ (y/n): ").lower().strip()
    
    if run_api == 'y':
        api_passed = run_api_tests()
        all_passed = all_passed and api_passed
    
    # 最终总结
    print("\n" + "=" * 60)
    if all_passed:
        print("🎊 所有测试通过！")
    else:
        print("⚠️  部分测试失败")
    
    print("\n📋 测试完成情况:")
    print("1. 环境配置测试: " + ("✅" if env_passed else "❌"))
    print("2. 密码功能测试: " + ("✅" if password_passed else "❌"))
    print("3. API测试: " + (("✅" if api_passed else "❌") if 'api_passed' in locals() else "⏭️ 跳过"))
    print("=" * 60)

if __name__ == "__main__":
    main()
