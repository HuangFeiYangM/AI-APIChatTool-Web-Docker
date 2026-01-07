# app/utils/api_clients/deepseek_client.py
"""
DeepSeek API客户端
"""
import httpx
import json
from typing import Dict, Any, Optional, AsyncGenerator
import logging
from datetime import datetime

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class DeepSeekClient(BaseAPIClient):
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        super().__init__(api_key=api_key, base_url=base_url)
        self.provider_name = "DeepSeek"
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天补全
        
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
        endpoint = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            if stream:
                return await self._stream_chat_completion(endpoint, payload, headers)
            else:
                return await self._chat_completion(endpoint, payload, headers)
                
        except Exception as e:
            logger.error(f"DeepSeek聊天请求失败: {e}")
            raise
    
    async def _chat_completion(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """非流式聊天补全"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"DeepSeek响应: {data}")
                return data
            else:
                error_msg = f"DeepSeek API错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def _stream_chat_completion(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> AsyncGenerator[str, None]:
        """流式聊天补全"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                endpoint,
                json=payload,
                headers=headers
            ) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # 移除"data: "前缀
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                yield chunk
                            except json.JSONDecodeError:
                                continue
                else:
                    error_msg = f"DeepSeek流式API错误: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
    
    async def models(self) -> Dict[str, Any]:
        """
        获取可用模型列表
        
        Returns:
            模型列表
        """
        endpoint = f"{self.base_url}/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"获取DeepSeek模型列表失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "deepseek-chat"
    ) -> float:
        """
        计算API调用成本
        
        Args:
            prompt_tokens: 提示token数
            completion_tokens: 补全token数
            model: 模型名称
            
        Returns:
            成本（美元）
        """
        # DeepSeek定价（示例，请根据实际定价调整）
        pricing = {
            "deepseek-chat": {
                "input": 0.00014 / 1000,  # $0.14 per 1K tokens
                "output": 0.00028 / 1000,  # $0.28 per 1K tokens
            },
            "deepseek-coder": {
                "input": 0.00028 / 1000,  # $0.28 per 1K tokens
                "output": 0.00056 / 1000,  # $0.56 per 1K tokens
            }
        }
        
        model_pricing = pricing.get(model, pricing["deepseek-chat"])
        input_cost = prompt_tokens * model_pricing["input"]
        output_cost = completion_tokens * model_pricing["output"]
        
        return input_cost + output_cost


# 工厂函数
def create_deepseek_client(api_key: str, base_url: str = None) -> DeepSeekClient:
    """
    创建DeepSeek客户端
    
    Args:
        api_key: API密钥
        base_url: 基础URL（可选）
        
    Returns:
        DeepSeekClient实例
    """
    if base_url:
        return DeepSeekClient(api_key=api_key, base_url=base_url)
    else:
        return DeepSeekClient(api_key=api_key)
