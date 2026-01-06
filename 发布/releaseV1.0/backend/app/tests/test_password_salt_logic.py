# app/tests/test_password_salt_logic.py
"""
白盒测试：验证密码加密/验证函数的盐值生成逻辑
测试内容：验证盐值生成逻辑
测试方法：白盒测试
"""

import sys
import os
from pathlib import Path

# 将项目根目录添加到 Python 路径，以便导入模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.security import get_password_hash, verify_password


def test_bcrypt_salt_randomness():
    """
    测试步骤：
    1. 两次加密相同明文密码
    2. 检查生成的哈希值是否不同（由于盐值随机）
    3. 验证两个哈希值都能通过密码验证
    """
    print("🔍 开始执行白盒测试：验证 bcrypt 盐值生成逻辑")
    print("-" * 60)

    # 测试用明文密码
    test_password = "MySecureP@ssw0rd123!"

    # 1. 两次加密相同明文密码
    hash1 = get_password_hash(test_password)
    hash2 = get_password_hash(test_password)
    
    print(f"明文密码: {test_password}")
    print(f"第一次哈希值: {hash1[:60]}...")
    print(f"第二次哈希值: {hash2[:60]}...")
    print("-" * 60)

    # 2. 检查生成的哈希值是否不同
    if hash1 != hash2:
        print("✅ 预期结果 1: 两个哈希值确实不同（盐值部分不同）")
        print(f"   → 哈希1 盐值部分: {hash1[7:29]}")
        print(f"   → 哈希2 盐值部分: {hash2[7:29]}")
        assert hash1 != hash2, "错误：两个哈希值竟然相同！"
    else:
        print("❌ 预期结果 1: 两个哈希值应该不同，但实际相同！")
        assert False, "哈希值相同，盐值随机性测试失败！"

    # 3. 验证两个哈希值都能通过密码验证
    verify_result1 = verify_password(test_password, hash1)
    verify_result2 = verify_password(test_password, hash2)
    
    if verify_result1 and verify_result2:
        print("✅ 预期结果 2: 两个哈希值都能通过 bcrypt 验证")
    else:
        print("❌ 预期结果 2: 哈希值验证失败")
        print(f"   → 哈希1 验证结果: {verify_result1}")
        print(f"   → 哈希2 验证结果: {verify_result2}")
        assert False, "哈希值验证失败！"

    print("-" * 60)
    print("🎉 测试状态：✅ 全部通过")
    print("\n测试总结：")
    print("1. bcrypt 的 get_password_hash 函数每次调用都会生成不同的随机盐值。")
    print("2. 盐值被编码在哈希值字符串中（$2b$12$<salt><hash>）。")
    print("3. verify_password 函数能从哈希值中提取盐值并进行正确验证。")
    print("4. 该实现符合安全最佳实践，能有效防御彩虹表攻击。")

    return True


if __name__ == "__main__":
    try:
        success = test_bcrypt_salt_randomness()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 测试执行出错: {e}")
        sys.exit(1)
