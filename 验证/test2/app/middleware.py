# app/middleware.py
"""
应用程序中间件
"""
import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.security import verify_access_token, get_token_payload

# 获取日志器
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 对于认证请求，不记录密码信息
        log_safe = True
        if "/auth/login" in url or "/auth/register" in url:
            log_safe = False  # 这些端点的请求体可能包含敏感信息
        
        # 记录请求信息
        if log_safe:
            logger.info(f"← 请求: {method} {url} | IP: {client_ip} | UA: {user_agent[:50]}...")
        else:
            logger.info(f"← 请求: {method} {url} | IP: {client_ip}")
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            status_code = response.status_code
            response_size = response.headers.get("content-length", "unknown")
            
            logger.info(
                f"→ 响应: {method} {url} | "
                f"状态: {status_code} | "
                f"时间: {process_time:.3f}s | "
                f"大小: {response_size}"
            )
            
            # 添加X-Process-Time头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录异常信息
            process_time = time.time() - start_time
            logger.error(
                f"❌ 异常: {method} {url} | "
                f"错误: {str(e)} | "
                f"时间: {process_time:.3f}s"
            )
            raise


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """认证中间件（可选，主要用于统计或额外检查）"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # 检查认证头
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # 使用get_token_payload而不是verify_access_token，因为verify_access_token会抛出异常
                # 我们只是想在中间件中获取用户信息，但不阻止请求
                payload = get_token_payload(token)
                if payload:
                    # 将用户信息添加到请求状态
                    request.state.user_id = payload.get("sub")
                    request.state.username = payload.get("username")
                    logger.debug(f"用户已验证: {request.state.username}")
            except Exception:
                # 令牌无效，但继续处理（由端点依赖项处理）
                pass
        
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # 添加安全相关的HTTP头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 如果是HTTPS环境，添加更多安全头
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """异常处理中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await call_next(request)
        except Exception as e:
            # 记录详细异常信息
            logger.error(f"未处理异常: {type(e).__name__}: {str(e)}", exc_info=True)
            
            # 根据异常类型返回适当的错误响应
            from fastapi import HTTPException
            from starlette.exceptions import HTTPException as StarletteHTTPException
            
            if isinstance(e, (HTTPException, StarletteHTTPException)):
                raise e
            
            # 对于其他异常，返回500错误
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "服务器内部错误",
                    "message": str(e) if settings.DEBUG else "请稍后重试"
                }
            )


def setup_middleware(app: FastAPI) -> None:
    """
    设置应用程序中间件
    注意：中间件的顺序很重要，先添加的先执行（请求时），但响应时顺序相反
    """
    
    # 1. 异常处理中间件（应该在最外层，最先捕获异常）
    app.add_middleware(ExceptionHandlingMiddleware)
    
    # 2. 认证中间件（在日志之前，以便日志可以记录用户信息）
    app.add_middleware(AuthenticationMiddleware)
    
    # 3. 日志中间件
    app.add_middleware(LoggingMiddleware)
    
    # 4. 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 5. CORS中间件已经在main.py中单独添加，因为它需要特定的配置
    
    logger.info("✅ 中间件配置完成")
