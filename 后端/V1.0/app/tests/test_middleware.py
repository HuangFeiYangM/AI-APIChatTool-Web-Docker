# app/tests/test_middleware.py
"""
中间件测试
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import pytest

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_logging_middleware():
    """测试日志中间件是否正常工作"""
    response = client.get("/")
    assert response.status_code == 200
    
    # 检查是否包含X-Process-Time头
    assert "X-Process-Time" in response.headers


def test_cors_middleware():
    """测试CORS中间件是否正常工作"""
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        }
    )
    
    # CORS预检请求应该返回200
    assert response.status_code in [200, 204]
    assert "access-control-allow-origin" in response.headers


def test_security_headers():
    """测试安全头中间件是否添加了正确的头"""
    response = client.get("/")
    
    # 检查安全头
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


def test_exception_handling():
    """测试异常处理中间件"""
    # 创建一个会抛出异常的端点来测试
    @app.get("/test-exception")
    async def test_exception():
        raise ValueError("测试异常")
    
    response = client.get("/test-exception")
    
    # 异常应该被捕获并返回500
    assert response.status_code == 500
    assert "detail" in response.json()
