# app/core/security.py
"""
安全相关功能模块
包含JWT令牌管理、密码哈希等安全功能
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.config import settings

# app/core/security.py - 在现有文件基础上添加
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto",bcrypt__ident="2b",bcrypt__rounds=12)


class TokenData(BaseModel):
    """JWT令牌数据模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否正确
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码到令牌中的数据
        expires_delta: 可选的过期时间增量
        
    Returns:
        str: JWT令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌创建失败: {str(e)}"
        )


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证JWT访问令牌
    
    Args:
        token: JWT令牌字符串
        
    Returns:
        Optional[Dict]: 令牌负载或None（如果无效）
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的令牌: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌验证失败: {str(e)}"
        )


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    获取令牌负载（不验证过期，仅解码）
    
    Args:
        token: JWT令牌字符串
        
    Returns:
        Optional[Dict]: 令牌负载或None
    """
    try:
        # 先尝试正常解码
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}  # 不验证过期
        )
        return payload
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    创建刷新令牌（比访问令牌有效期更长）
    
    Args:
        data: 要编码到令牌中的数据
        
    Returns:
        str: JWT刷新令牌
    """
    to_encode = data.copy()
    # 刷新令牌有效期更长，例如7天
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def generate_password_reset_token(email: str) -> str:
    """
    生成密码重置令牌
    
    Args:
        email: 用户邮箱
        
    Returns:
        str: 密码重置令牌
    """
    expires_delta = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60)
    data = {"sub": email, "type": "password_reset"}
    return create_access_token(data, expires_delta=expires_delta)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    验证密码重置令牌
    
    Args:
        token: 密码重置令牌
        
    Returns:
        Optional[str]: 邮箱地址或None
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "password_reset":
            return None
        email: str = payload.get("sub")
        return email
    except jwt.PyJWTError:
        return None


def is_password_strong(password: str) -> bool:
    """
    检查密码强度
    
    Args:
        password: 密码字符串
        
    Returns:
        bool: 密码是否足够强
    """
    # 密码长度至少8位
    if len(password) < 8:
        return False
    
    # 包含至少一个大写字母
    if not any(c.isupper() for c in password):
        return False
    
    # 包含至少一个小写字母
    if not any(c.islower() for c in password):
        return False
    
    # 包含至少一个数字
    if not any(c.isdigit() for c in password):
        return False
    
    # 包含至少一个特殊字符
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False
    
    return True


def sanitize_user_input(input_str: str, max_length: int = 1000) -> str:
    """
    清理用户输入，防止XSS攻击
    
    Args:
        input_str: 用户输入字符串
        max_length: 最大长度限制
        
    Returns:
        str: 清理后的字符串
    """
    if not input_str:
        return ""
    
    # 限制长度
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    # 移除危险的HTML标签和脚本
    dangerous_tags = [
        "<script>", "</script>", "<iframe>", "</iframe>", 
        "<object>", "</object>", "<embed>", "</embed>",
        "javascript:", "onclick=", "onload=", "onerror="
    ]
    
    for tag in dangerous_tags:
        input_str = input_str.replace(tag, "")
    
    # 转义HTML特殊字符
    input_str = (
        input_str.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
        .replace("/", "&#x2F;")
    )
    
    return input_str


def check_password_policy(password: str) -> Dict[str, Any]:
    """
    检查密码策略
    
    Args:
        password: 密码字符串
        
    Returns:
        Dict: 密码策略检查结果
    """
    result = {
        "is_valid": True,
        "errors": [],
        "strength": "weak"
    }
    
    # 检查长度
    if len(password) < 8:
        result["is_valid"] = False
        result["errors"].append("密码至少需要8个字符")
    
    # 检查大写字母
    if not any(c.isupper() for c in password):
        result["errors"].append("密码至少需要一个大写字母")
    
    # 检查小写字母
    if not any(c.islower() for c in password):
        result["errors"].append("密码至少需要一个小写字母")
    
    # 检查数字
    if not any(c.isdigit() for c in password):
        result["errors"].append("密码至少需要一个数字")
    
    # 检查特殊字符
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        result["errors"].append("密码至少需要一个特殊字符")
    
    # 如果有错误，标记为无效
    if result["errors"]:
        result["is_valid"] = False
    
    # 评估密码强度
    if len(password) >= 12 and len(result["errors"]) == 0:
        result["strength"] = "strong"
    elif len(password) >= 10:
        result["strength"] = "medium"
    else:
        result["strength"] = "weak"
    
    return result


def validate_email_format(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 邮箱格式是否正确
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_api_key() -> str:
    """
    生成API密钥
    
    Returns:
        str: API密钥
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
    return f"sk-{api_key}"


# 在core/__init__.py中添加导出
__all__ = [
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'verify_access_token',
    'get_token_payload',
    'create_refresh_token',
    'generate_password_reset_token',
    'verify_password_reset_token',
    'is_password_strong',
    'sanitize_user_input',
    'check_password_policy',
    'validate_email_format',
    'generate_api_key',
    'pwd_context',
    'TokenData'
]




#大模型api=======================================================

def generate_encryption_key(salt: bytes = None) -> bytes:
    """生成加密密钥"""
    if not salt:
        salt = os.urandom(16)
    
    password = settings.SECRET_KEY.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key, salt

def encrypt_api_key(api_key: str) -> bytes:
    """加密API密钥"""
    key, salt = generate_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(api_key.encode())
    # 将salt和加密数据一起存储
    return salt + encrypted

def decrypt_api_key(encrypted_data: bytes) -> str:
    """解密API密钥"""
    salt = encrypted_data[:16]
    encrypted = encrypted_data[16:]
    
    key, _ = generate_encryption_key(salt)
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)
    return decrypted.decode()
