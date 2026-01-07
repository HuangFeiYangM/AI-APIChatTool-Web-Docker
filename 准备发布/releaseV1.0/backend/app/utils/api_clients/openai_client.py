# app/utils/api_clients/openai_client.py
"""
OpenAI API客户端
"""
import httpx
import json
from typing import Dict, Any, Optional, AsyncGenerator
import logging
from datetime import datetime

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseAPIClient):
    """OpenAI API客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com"):
        super().__init__(api_key=api_key, base_url=base_url)
        self.provider_name = "OpenAI"
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
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
            logger.error(f"OpenAI聊天请求失败: {e}")
            raise
    
    async def _chat_completion(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"OpenAI响应: {data}")
                return data
            else:
                error_msg = f"OpenAI API错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def _stream_chat_completion(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> AsyncGenerator[str, None]:
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
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                yield chunk
                            except json.JSONDecodeError:
                                continue
                else:
                    error_msg = f"OpenAI流式API错误: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)


def create_openai_client(api_key: str, base_url: str = None) -> OpenAIClient:
    if base_url:
        return OpenAIClient(api_key=api_key, base_url=base_url)
    else:
        return OpenAIClient(api_key=api_key)
