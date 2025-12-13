# app/utils/api_clients/base_client.py
"""
API客户端基类
定义通用的API调用接口、重试机制、错误处理等
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """API客户端基类 - 所有具体API客户端的父类"""
    
    def __init__(self, api_key: str, base_url: str = None):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL（可选）
        """
        self.api_key = api_key
        self.base_url = base_url
        self.provider_name = "Base"  # 子类应该覆盖这个
        
        # 通用配置
        self.timeout = 30.0  # 请求超时时间（秒）
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1.0  # 重试延迟（秒）
        
        # 请求统计
        self.total_requests = 0
        self.failed_requests = 0
        
        logger.debug(f"初始化 {self.provider_name} 客户端")
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: list,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天补全 - 抽象方法，必须由子类实现
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            **kwargs: 其他参数
            
        Returns:
            响应数据
        """
        pass
    
    async def _make_request_with_retry(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str],
        payload: Dict[str, Any] = None,
        stream: bool = False
    ) -> httpx.Response:
        """
        带重试机制的HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: 端点URL
            headers: 请求头
            payload: 请求数据
            stream: 是否流式
            
        Returns:
            httpx.Response对象
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self.total_requests += 1
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "POST":
                        if stream:
                            response = await client.stream(
                                "POST",
                                endpoint,
                                headers=headers,
                                json=payload
                            )
                        else:
                            response = await client.post(
                                endpoint,
                                headers=headers,
                                json=payload
                            )
                    elif method.upper() == "GET":
                        response = await client.get(endpoint, headers=headers)
                    else:
                        raise ValueError(f"不支持的HTTP方法: {method}")
                    
                    # 检查响应状态
                    response.raise_for_status()
                    
                    logger.debug(f"请求成功: {endpoint} (尝试次数: {attempt+1})")
                    return response
                    
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"请求超时: {endpoint}, 尝试 {attempt+1}/{self.max_retries}")
                
            except httpx.HTTPStatusError as e:
                # HTTP错误状态码，通常不需要重试（除非是5xx）
                if 500 <= e.response.status_code < 600:
                    last_exception = e
                    logger.warning(f"服务器错误 ({e.response.status_code}): {endpoint}")
                else:
                    # 客户端错误（4xx）不应该重试
                    self.failed_requests += 1
                    logger.error(f"客户端错误 ({e.response.status_code}): {endpoint}")
                    raise
                    
            except httpx.NetworkError as e:
                last_exception = e
                logger.warning(f"网络错误: {endpoint}, 尝试 {attempt+1}/{self.max_retries}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"请求异常: {endpoint}, 错误: {e}")
                
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                await asyncio.sleep(wait_time)
        
        # 所有重试都失败
        self.failed_requests += 1
        error_msg = f"请求失败，重试 {self.max_retries} 次后仍失败: {endpoint}"
        logger.error(error_msg)
        
        if last_exception:
            raise last_exception
        else:
            raise Exception(error_msg)
    
    def _build_headers(self, extra_headers: Dict[str, str] = None) -> Dict[str, str]:
        """
        构建请求头
        
        Args:
            extra_headers: 额外的请求头
            
        Returns:
            请求头字典
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if extra_headers:
            headers.update(extra_headers)
            
        return headers
    
    def _get_endpoint(self, path: str) -> str:
        """
        获取完整的端点URL
        
        Args:
            path: 路径
            
        Returns:
            完整的URL
        """
        if self.base_url:
            # 确保base_url以/结尾，path不以/开头
            base = self.base_url.rstrip('/')
            path = path.lstrip('/')
            return f"{base}/{path}"
        else:
            return path
    
    async def _handle_stream_response(
        self, 
        response: httpx.Response
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理流式响应
        
        Args:
            response: httpx响应对象
            
        Yields:
            每个chunk的数据
        """
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]  # 移除"data: "前缀
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    yield chunk
                except json.JSONDecodeError:
                    logger.warning(f"无法解析流式数据: {data[:100]}")
                    continue
    
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = None
    ) -> float:
        """
        计算API调用成本（默认实现，子类可以覆盖）
        
        Args:
            prompt_tokens: 提示token数
            completion_tokens: 补全token数
            model: 模型名称
            
        Returns:
            成本（美元）
        """
        # 默认实现返回0，子类应该提供具体的定价
        logger.debug(f"成本计算未实现: {self.provider_name}")
        return 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取客户端统计信息
        
        Returns:
            统计信息字典
        """
        success_rate = 0
        if self.total_requests > 0:
            success_rate = 1 - (self.failed_requests / self.total_requests)
        
        return {
            "provider": self.provider_name,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat()
        }
    
    def _log_request(
        self, 
        endpoint: str, 
        model: str, 
        messages_count: int
    ) -> None:
        """
        记录请求日志
        
        Args:
            endpoint: 端点
            model: 模型名称
            messages_count: 消息数量
        """
        logger.info(
            f"[{self.provider_name}] 请求: model={model}, "
            f"messages={messages_count}, endpoint={endpoint}"
        )
    
    def _log_response(
        self, 
        response_data: Dict[str, Any], 
        response_time_ms: float
    ) -> None:
        """
        记录响应日志
        
        Args:
            response_data: 响应数据
            response_time_ms: 响应时间（毫秒）
        """
        if "usage" in response_data:
            usage = response_data["usage"]
            logger.info(
                f"[{self.provider_name}] 响应: "
                f"tokens={usage.get('total_tokens', 'N/A')}, "
                f"time={response_time_ms:.0f}ms"
            )
    
    async def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            是否连接成功
        """
        try:
            # 尝试一个简单的请求，比如列出模型
            if hasattr(self, 'models'):
                await self.models()
                logger.info(f"[{self.provider_name}] 连接测试成功")
                return True
            else:
                logger.warning(f"[{self.provider_name}] 连接测试跳过（未实现models方法）")
                return False
                
        except Exception as e:
            logger.error(f"[{self.provider_name}] 连接测试失败: {e}")
            return False
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.provider_name}Client(requests={self.total_requests})"
    
    def __repr__(self) -> str:
        """详细表示"""
        return f"{self.__class__.__name__}(api_key=..., base_url={self.base_url})"
