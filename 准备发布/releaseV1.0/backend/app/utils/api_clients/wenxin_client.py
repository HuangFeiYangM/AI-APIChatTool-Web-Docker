# app/utils/api_clients/wenxin_client.py
"""
文心一言 API 客户端
"""
import httpx
import json
from typing import Dict, Any, Optional
import logging

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class WenxinClient(BaseAPIClient):
    """文心一言 API 客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://aip.baidubce.com"):
        super().__init__(api_key=api_key, base_url=base_url)
        self.provider_name = "Wenxin"
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "ernie-bot",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """聊天补全"""
        # 文心一言 API 端点
        endpoint = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        
        # 转换消息格式为文心一言格式
        wenxin_messages = []
        for msg in messages:
            if msg["role"] == "user":
                wenxin_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                wenxin_messages.append({"role": "assistant", "content": msg["content"]})
        
        payload = {
            "messages": wenxin_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "access_token": self.api_key
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"文心一言 API 错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)


def create_wenxin_client(api_key: str, base_url: str = None) -> WenxinClient:
    """创建文心一言客户端"""
    if base_url:
        return WenxinClient(api_key=api_key, base_url=base_url)
    else:
        return WenxinClient(api_key=api_key)
