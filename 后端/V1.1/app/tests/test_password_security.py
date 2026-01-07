# app/tests/test_password_security.py
"""
密码安全模块的单元测试
测试密码哈希、验证、强度检测和策略检查
"""
import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    is_password_strong,
    check_password_policy,
)

# ============================================================================
# UNIT-02: 密码加密/验证函数测试
# ============================================================================

class TestPasswordFunctions:
    """测试密码相关函数"""
    
    def test_get_password_hash(self):
        """测试密码哈希生成"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # 哈希值应该是一个字符串
        assert isinstance(hashed, str)
        # 哈希值应该不是原始密码
        assert hashed != password
        # 哈希值应该以 bcrypt 标识开头（默认配置）
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """测试验证正确密码"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # 验证应该通过
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)
        
        # 错误密码应该验证失败
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """测试空密码验证"""
        password = ""
        hashed = get_password_hash("somepassword")
        
        # 空密码应该验证失败
        assert verify_password(password, hashed) is False
    
    def test_verify_password_invalid_hash(self):
        """测试无效哈希格式"""
        password = "TestPassword123!"
        invalid_hash = "invalid_hash_format"
        
        # 无效哈希应该返回 False
        assert verify_password(password, invalid_hash) is False
    
    def test_is_password_strong_strong_password(self):
        """测试强密码检测"""
        strong_passwords = [
            "StrongPass123!",
            "AnotherStrongPwd456@",
            "VeryLongPassword123!@#",
        ]
        
        for password in strong_passwords:
            assert is_password_strong(password) is True, f"Password {password} should be strong"
    
    def test_is_password_strong_weak_passwords(self):
        """测试弱密码检测"""
        weak_passwords = [
            "short",                    # 太短
            "NoSpecialChar123",         # 缺少特殊字符
            "noupper123!",              # 缺少大写字母
            "NOLOWER123!",              # 缺少小写字母
            "NoDigit!",                 # 缺少数字
            "12345678",                 # 只有数字
            "abcdefgh",                 # 只有小写字母
            "ABCDEFGH",                 # 只有大写字母
            "!@#$%^&*",                 # 只有特殊字符
        ]
        
        for password in weak_passwords:
            assert is_password_strong(password) is False, f"Password {password} should be weak"
    
    def test_check_password_policy_valid(self):
        """测试有效的密码策略检查"""
        valid_passwords = [
            "ValidPass123!",  # 长度12
            "Another123!@#",   # 长度11
        ]
        
        for password in valid_passwords:
            result = check_password_policy(password)
            assert result["is_valid"] is True, f"Password {password} should be valid"
            assert result["errors"] == [], f"Password {password} should have no errors"
    
    def test_check_password_policy_invalid(self):
        """测试无效的密码策略检查"""
        test_cases = [
            {
                "password": "short",  # 长度5
                "expected_errors": [
                    "密码至少需要8个字符",
                    "密码至少需要一个大写字母", 
                    "密码至少需要一个数字",
                    "密码至少需要一个特殊字符"
                ]
            },
            {
                "password": "NoSpecial123",  # 长度11
                "expected_errors": ["密码至少需要一个特殊字符"]
            },
            {
                "password": "nospecial123",  # 长度11
                "expected_errors": ["密码至少需要一个大写字母", "密码至少需要一个特殊字符"]
            },
            {
                "password": "TOOLONGPASSWORD123!@#",  # 长度22
                "expected_errors": ["密码最多16个字符", "密码至少需要一个小写字母"]
            },
        ]
        
        for case in test_cases:
            password = case["password"]
            expected_errors = case["expected_errors"]
            result = check_password_policy(password)
            
            assert result["is_valid"] is False, f"Password {password} should be invalid"
            # 检查是否包含所有预期的错误信息
            for expected_error in expected_errors:
                assert expected_error in result["errors"], f"Password {password} should have error: {expected_error}"
            # 检查错误数量是否匹配（可能有多余的错误）
            assert len(result["errors"]) == len(expected_errors), \
                f"Password {password} expected {len(expected_errors)} errors, got {len(result['errors'])}: {result['errors']}"
    
    def test_check_password_policy_strength_assessment_fixed(self):
        """测试密码强度评估（修正版）"""
        test_cases = [
            # 密码长度7，有错误（长度不足），长度<10 → weak
            {"password": "Short1!", "strength": "weak", "note": "长度7，有错误"},
            # 密码长度12，无错误，长度≥12且无错误 → strong
            {"password": "ValidPass12!", "strength": "strong", "note": "长度12，无错误"},
            # 密码长度13，无错误，长度≥12且无错误 → strong  
            {"password": "ValidPass123!", "strength": "strong", "note": "长度13，无错误"},
            # 密码长度22，有错误（超长），长度≥10 → medium
            {"password": "VeryLongValidPass123!", "strength": "medium", "note": "长度22，有错误但长度≥10"},
            # 密码长度16，无错误，长度≥12且无错误 → strong
            {"password": "VeryLongValid12!", "strength": "strong", "note": "长度16，无错误"},  # 修复：改为16字符密码
            # 密码长度11，无错误，长度≥10 → medium
            {"password": "Anoth123!@#", "strength": "medium", "note": "长度11，无错误"},
            # 密码长度9，无错误，长度<10 → weak
            {"password": "Pass12!@#", "strength": "weak", "note": "长度9，无错误但长度<10"},
        ]
        
        for case in test_cases:
            password = case["password"]
            expected_strength = case["strength"]
            note = case["note"]
            result = check_password_policy(password)
            
            assert result["strength"] == expected_strength, \
                f"Password '{password}' ({note}) should be {expected_strength}, got {result['strength']}. Errors: {result['errors']}"


# ============================================================================
# 集成测试：密码哈希与验证的集成
# ============================================================================

def test_password_hash_and_verify_integration():
    """测试密码哈希和验证的集成工作流"""
    test_passwords = [
        "MySecurePassword123!",
        "AnotherPassword456@",
        "Test123!@#",
    ]
    
    for password in test_passwords:
        # 生成哈希
        hashed = get_password_hash(password)
        
        # 验证正确密码
        assert verify_password(password, hashed) is True
        
        # 验证错误密码
        wrong_password = password + "wrong"
        assert verify_password(wrong_password, hashed) is False


# ============================================================================
# 边界条件测试（密码相关）
# ============================================================================

def test_password_edge_cases():
    """测试密码相关边界条件"""
    # 测试非常长的密码哈希（应该能处理）
    long_password = "a" * 1000
    hashed = get_password_hash(long_password)
    assert verify_password(long_password, hashed) is True
    
    # 测试包含特殊Unicode字符的密码
    unicode_password = "密码🔐123!"
    hashed = get_password_hash(unicode_password)
    assert verify_password(unicode_password, hashed) is True
    
    # 测试check_password_policy处理空密码
    result = check_password_policy("")
    assert result["is_valid"] is False
    assert "密码至少需要8个字符" in result["errors"]


# ============================================================================
# 性能测试（可选）
# ============================================================================

def test_password_hash_performance():
    """测试密码哈希性能（基本检查）"""
    import time
    password = "TestPassword123!"
    
    start = time.time()
    hashed = get_password_hash(password)
    end = time.time()
    
    # bcrypt 哈希应该需要一定时间（但不要太长）
    # 通常 bcrypt 工作因子为 12 时约 0.3-0.5 秒
    hash_time = end - start
    assert hash_time < 1.0, f"Password hashing took {hash_time:.2f} seconds, should be < 1.0"
    assert hash_time > 0.01, f"Password hashing took {hash_time:.2f} seconds, seems too fast for bcrypt"


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v"])
