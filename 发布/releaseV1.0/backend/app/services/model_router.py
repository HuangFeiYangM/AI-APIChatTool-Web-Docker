# app/services/model_router.py
"""
模型路由服务 - 对应详细设计中的程序4：模型API路由模块
负责处理与大模型API的通信，包括请求路由、重试、错误处理和对话后处理
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.security import decrypt_api_key, encrypt_api_key
from app.exceptions import (
    ModelNotAvailableError, APIRequestError,
    InsufficientQuotaError, ModelConfigError,
    ConversationNotFoundError
)
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.repositories.api_call_log_repository import ApiCallLogRepository
from app.repositories.system_model_repository import SystemModelRepository
from app.repositories.user_model_config_repository import UserModelConfigRepository
from app.services.conversation_service import ConversationService
from app.config import settings

logger = logging.getLogger(__name__)


class ModelRouterService:
    """模型路由服务 - 核心服务，处理所有模型API调用和对话管理"""

    def __init__(self, db: Session):
        self.db = db
        self.system_model_repo = SystemModelRepository(db)
        self.user_config_repo = UserModelConfigRepository(db)
        self.api_log_repo = ApiCallLogRepository(db)
        self.conversation_service = ConversationService(db)

        # 客户端配置
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0  # 秒

    async def chat_completion(
        self,
        user_id: int,
        model_name: str,
        message: str,
        conversation_id: Optional[int] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        聊天完成 - 主入口点
        对应详细设计中的算法：模型API路由 + 对话后处理
        """
        start_time = datetime.now()

        try:
            # 1. 验证用户输入
            self._validate_user_input(message, model_name, temperature, max_tokens)

            # 2. 获取模型配置
            system_model = self.system_model_repo.get_by_name(model_name)
            if not system_model or not system_model.is_available:
                raise ModelNotAvailableError(f"模型 '{model_name}' 不存在或未激活")

            logger.info(f"用户 {user_id} 请求聊天 | 模型: {model_name} | 提供商: {system_model.model_provider}")

            # 3. 获取用户配置和API密钥
            api_key, custom_endpoint = self._get_user_api_config(user_id, system_model.model_id)
            if not api_key:
                raise ModelConfigError(f"未配置模型 '{model_name}' 的API密钥")

            # 4. 检查速率限制
            self._check_rate_limit(user_id, system_model.model_id)

            # 5. 检查对话权限（如果提供了conversation_id）
            if conversation_id:
                self._validate_conversation_access(user_id, conversation_id)

            # 6. 构造请求数据
            model_identifier = self._get_model_identifier(model_name, system_model.model_provider)

            request_data = {
                "model": model_identifier,
                "messages": [{"role": "user", "content": message}],
                "temperature": temperature,
                "max_tokens": min(max_tokens, system_model.max_tokens or 2000),
                "stream": stream
            }

            # 7. 调用API（带重试机制）
            response_data = await self._call_model_api_with_retry(
                provider=system_model.model_provider,
                endpoint=custom_endpoint or system_model.api_endpoint,
                api_key=api_key,
                request_data=request_data,
                stream=stream
            )

            # 8. 提取响应内容
            response_text = self._extract_response_content(response_data, system_model.model_provider, stream)
            tokens_used = self._calculate_tokens_used(response_data, system_model.model_provider)
            prompt_tokens = self._estimate_tokens(message)
            completion_tokens = max(0, tokens_used - prompt_tokens)

            # 9. 记录API调用日志
            self._log_api_call(
                user_id=user_id,
                model_id=system_model.model_id,
                conversation_id=conversation_id,
                endpoint=system_model.api_endpoint,
                request_tokens=prompt_tokens,
                response_tokens=completion_tokens,
                start_time=start_time,
                is_success=True,
                status_code=200
            )

            # 10. 更新用户配置的最后使用时间
            self.user_config_repo.update_last_used_time(system_model.model_id)

            # 11. 对话后处理
            processing_result = await self._post_chat_processing(
                user_id=user_id,
                model_id=system_model.model_id,
                model_provider=system_model.model_provider,
                conversation_id=conversation_id,
                user_message=message,
                ai_response=response_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=tokens_used,
                start_time=start_time
            )

            # 12. 返回结果
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            result = {
                "response": response_text,
                "model_used": model_name,
                "tokens_used": tokens_used,
                "processing_time_ms": processing_time,
                "conversation_id": conversation_id or 0,
                "success": True
            }

            # 如果创建了新对话，返回对话ID
            if processing_result.get("new_conversation_id"):
                result["conversation_id"] = processing_result["new_conversation_id"]

            return result

        except Exception as e:
            # 记录失败日志
            model_id = locals().get('system_model', None)
            if model_id and hasattr(model_id, 'model_id'):
                model_id = model_id.model_id
            else:
                model_id = 0

            endpoint = locals().get('system_model', None)
            if endpoint and hasattr(endpoint, 'api_endpoint'):
                endpoint = endpoint.api_endpoint
            else:
                endpoint = ""

            self._log_api_call(
                user_id=user_id,
                model_id=model_id,
                conversation_id=conversation_id,
                endpoint=endpoint,
                request_tokens=self._estimate_tokens(message),
                response_tokens=0,
                start_time=start_time,
                is_success=False,
                status_code=500,
                error_message=str(e)
            )
            raise

    def _validate_user_input(self, message: str, model_name: str, temperature: float, max_tokens: int):
        """验证用户输入"""
        if not message or not message.strip():
            raise ValueError("消息内容不能为空")

        if len(message.strip()) > 10000:
            raise ValueError("消息内容过长，最多10000个字符")

        if temperature < 0 or temperature > 2:
            raise ValueError("温度参数必须在0到2之间")

        if max_tokens < 1 or max_tokens > 8192:
            raise ValueError("最大token数必须在1到8192之间")

        if not model_name or not model_name.strip():
            raise ValueError("模型名称不能为空")

    def _get_user_api_config(self, user_id: int, model_id: int) -> tuple[Optional[str], Optional[str]]:
        """获取用户的API配置"""
        # 首先检查用户个人配置
        user_config = self.user_config_repo.get_user_config_for_model(user_id, model_id)

        if user_config and user_config.is_enabled:
            # 获取API密钥（支持解密）
            api_key = None
            if user_config.api_key:
                api_key = user_config.api_key
            elif user_config.api_key_encrypted:
                try:
                    api_key = decrypt_api_key(user_config.api_key_encrypted)
                except Exception as e:
                    logger.error(f"API密钥解密失败: {e}")
                    raise ModelConfigError("API密钥解密失败")

            return api_key, user_config.custom_endpoint

        # 如果没有用户配置，使用系统默认
        system_model = self.system_model_repo.get_by_id(model_id)
        if system_model and system_model.model_provider.lower() in settings.DEFAULT_API_KEYS:
            api_key = settings.DEFAULT_API_KEYS[system_model.model_provider.lower()]
            return api_key, None

        return None, None

    def _check_rate_limit(self, user_id: int, model_id: int):
        """检查速率限制"""
        # 获取最近一分钟的调用次数
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_calls = self.api_log_repo.get_model_api_calls(
            model_id=model_id,
            start_date=one_minute_ago,
            limit=1000
        )

        # 过滤当前用户的调用
        user_calls = [call for call in recent_calls if call.user_id == user_id]

        # 获取模型速率限制
        system_model = self.system_model_repo.get_by_id(model_id)
        rate_limit = system_model.rate_limit_per_minute if system_model else 60

        if len(user_calls) >= rate_limit:
            raise APIRequestError(f"速率限制：每分钟最多 {rate_limit} 次调用")

    def _validate_conversation_access(self, user_id: int, conversation_id: int):
        """验证用户对对话的访问权限"""
        conversation = self.db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            raise ConversationNotFoundError("对话不存在或无权限访问")

        if conversation.is_deleted:
            raise ConversationNotFoundError("对话已被删除")

    def _get_model_identifier(self, model_name: str, provider: str) -> str:
        """根据模型名称和提供商获取正确的模型标识符"""
        model_name_lower = model_name.lower()

        if "deepseek" in model_name_lower:
            if "coder" in model_name_lower:
                return "deepseek-coder"
            else:
                return "deepseek-chat"
        elif "gpt-4" in model_name_lower:
            return "gpt-4"
        elif "ernie" in model_name_lower:
            return "ernie-bot"
        elif "claude" in model_name_lower:
            return "claude-3-sonnet"
        elif "llama" in model_name_lower:
            return "llama-3-8b"
        else:
            # 默认返回模型名称，或者GPT-3.5
            return model_name if model_name else "gpt-3.5-turbo"

    async def _call_model_api_with_retry(
        self,
        provider: str,
        endpoint: str,
        api_key: str,
        request_data: Dict[str, Any],
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用模型API（带重试机制）- 使用封装好的客户端类
        """
        last_exception = None

        # 转换供应商名称为小写，确保匹配
        provider_lower = provider.lower() if provider else ""

        for attempt in range(self.max_retries):
            try:
                # 根据供应商创建对应的客户端
                if provider_lower == "openai":
                    return await self._call_openai_via_client(
                        endpoint=endpoint,
                        api_key=api_key,
                        request_data=request_data,
                        stream=stream
                    )

                elif provider_lower == "deepseek":
                    return await self._call_deepseek_via_client(
                        endpoint=endpoint,
                        api_key=api_key,
                        request_data=request_data,
                        stream=stream
                    )

                elif provider_lower in ["baidu", "wenxin"]:
                    return await self._call_wenxin_api(
                        endpoint=endpoint,
                        api_key=api_key,
                        request_data=request_data,
                        stream=stream
                    )

                elif provider_lower == "anthropic":
                    # 暂时使用OpenAI兼容的API
                    return await self._call_openai_via_client(
                        endpoint=endpoint,
                        api_key=api_key,
                        request_data=request_data,
                        stream=stream
                    )

                else:
                    logger.warning(f"不支持的供应商: {provider} (小写: {provider_lower})")
                    # 尝试直接调用OpenAI兼容API
                    try:
                        return await self._call_openai_via_client(
                            endpoint=endpoint,
                            api_key=api_key,
                            request_data=request_data,
                            stream=stream
                        )
                    except Exception as fallback_e:
                        raise ModelNotAvailableError(f"不支持的供应商: {provider}")

            except (Exception) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(f"API调用失败，第{attempt + 1}次重试，等待{wait_time}秒")
                    await asyncio.sleep(wait_time)
                else:
                    if isinstance(e, (ModelNotAvailableError, APIRequestError, InsufficientQuotaError, ModelConfigError)):
                        raise
                    else:
                        raise APIRequestError(f"API请求失败，重试{self.max_retries}次后失败: {str(e)}")

        raise last_exception or APIRequestError("未知错误")

    async def _call_openai_via_client(
        self,
        endpoint: str,
        api_key: str,
        request_data: Dict[str, Any],
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用OpenAI兼容API（包括OpenAI、Anthropic等使用OpenAI格式的API）
        使用HTTPX直接调用
        """
        # 构建基础URL
        base_url = endpoint
        if "/chat/completions" in endpoint:
            base_url = endpoint[:endpoint.rfind("/chat/completions")]

        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        # 确保以/结尾
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        final_endpoint = f"{base_url}chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        logger.info(f"调用OpenAI兼容API: endpoint={final_endpoint}, model={request_data.get('model')}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    final_endpoint,
                    headers=headers,
                    json=request_data
                )

                if response.status_code == 200:
                    if stream:
                        # 处理流式响应
                        return await self._handle_stream_response(response)
                    else:
                        data = response.json()
                        logger.debug(f"OpenAI兼容API响应数据: {data}")
                        return data
                else:
                    error_text = response.text[:500] if response.text else "无错误信息"
                    logger.error(f"OpenAI兼容API错误 {response.status_code}: {error_text}")

                    # 根据状态码提供更具体的错误信息
                    if response.status_code == 401:
                        raise APIRequestError("API密钥无效或已过期")
                    elif response.status_code == 429:
                        raise APIRequestError("请求速率超限，请稍后重试")
                    elif response.status_code == 400:
                        # 尝试解析错误详情
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("error", {}).get("message", error_text)
                            raise APIRequestError(f"API请求错误: {error_msg}")
                        except:
                            raise APIRequestError(f"API请求错误: {error_text}")
                    else:
                        raise APIRequestError(f"API错误 ({response.status_code}): {error_text}")

            except httpx.TimeoutException:
                logger.error("OpenAI兼容API请求超时")
                raise APIRequestError("API请求超时，请稍后重试")
            except httpx.NetworkError:
                logger.error("OpenAI兼容API网络错误")
                raise APIRequestError("网络连接错误，请检查网络后重试")
            except Exception as e:
                logger.error(f"OpenAI兼容API调用异常: {e}")
                raise

    async def _call_deepseek_via_client(
        self,
        endpoint: str,
        api_key: str,
        request_data: Dict[str, Any],
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用DeepSeek API - 使用DeepSeek客户端
        """
        try:
            # 导入DeepSeek客户端
            from app.utils.api_clients.deepseek_client import create_deepseek_client

            # 构建基础URL
            base_url = endpoint
            if "/chat/completions" in endpoint:
                base_url = endpoint[:endpoint.rfind("/chat/completions")]

            # 创建DeepSeek客户端
            client = create_deepseek_client(
                api_key=api_key,
                base_url=base_url if base_url else None
            )

            logger.info(f"调用DeepSeek客户端: model={request_data.get('model')}")

            # 调用聊天补全
            result = await client.chat_completion(
                messages=request_data["messages"],
                model=request_data.get("model", "deepseek-chat"),
                temperature=request_data.get("temperature", 0.7),
                max_tokens=request_data.get("max_tokens", 2000),
                stream=stream
            )

            return result

        except ImportError:
            logger.warning("DeepSeek客户端未找到，使用OpenAI兼容方式调用")
            # 如果DeepSeek客户端不存在，回退到OpenAI兼容方式
            return await self._call_openai_via_client(endpoint, api_key, request_data, stream)
        except Exception as e:
            logger.error(f"DeepSeek客户端调用失败: {e}")
            raise

    async def _call_wenxin_api(
        self,
        endpoint: str,
        api_key: str,
        request_data: Dict[str, Any],
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用文心一言API（示例实现）
        """
        # 注意：文心一言API参数可能不同，这里需要根据实际文档调整
        headers = {
            "Content-Type": "application/json"
        }

        # 转换请求格式为文心一言格式
        wenxin_data = {
            "messages": request_data["messages"],
            "temperature": request_data.get("temperature", 0.7),
            "max_tokens": request_data.get("max_tokens", 2000)
        }

        logger.info(f"调用文心一言API: endpoint={endpoint}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # 注意：文心一言API可能需要不同的参数传递方式
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=wenxin_data,
                    params={"access_token": api_key}
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    error_text = response.text[:500] if response.text else "无错误信息"
                    logger.error(f"文心一言API错误 {response.status_code}: {error_text}")
                    raise APIRequestError(f"文心一言API错误: {error_text}")

            except httpx.TimeoutException:
                logger.error("文心一言API请求超时")
                raise APIRequestError("文心一言API请求超时")
            except httpx.NetworkError:
                logger.error("文心一言API网络错误")
                raise APIRequestError("网络连接错误")
            except Exception as e:
                logger.error(f"文心一言API调用异常: {e}")
                raise

    async def _handle_stream_response(self, response) -> Dict[str, Any]:
        """
        处理流式响应
        注意：这个方法应该返回与正常响应相同格式的数据
        """
        import httpx

        if isinstance(response, httpx.Response):
            # 处理HTTP响应
            content = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]  # 移除"data: "前缀
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                content += delta["content"]
                    except json.JSONDecodeError:
                        continue

            # 返回模拟的非流式响应结构
            return {
                "choices": [{
                    "message": {
                        "content": content,
                        "role": "assistant"
                    }
                }],
                "usage": {
                    "total_tokens": len(content) // 4  # 粗略估计
                }
            }
        else:
            # 处理其他类型的流式响应
            return response

    def _extract_response_content(self, response_data: Dict[str, Any], provider: str, stream: bool = False) -> str:
        """从响应中提取文本内容"""
        if stream:
            # 流式响应已在_handle_stream_response中处理
            return response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        provider_lower = provider.lower() if provider else ""

        if provider_lower in ["openai", "deepseek", "anthropic"]:
            # OpenAI格式的响应
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                elif "text" in choice:
                    return choice["text"]
            return ""
        elif provider_lower in ["baidu", "wenxin"]:
            # 文心一言格式
            return response_data.get("result", "")
        else:
            # 其他格式，尝试通用提取
            if "text" in response_data:
                return response_data["text"]
            elif "output" in response_data:
                return response_data["output"]
            else:
                return str(response_data)

    def _calculate_tokens_used(self, response_data: Dict[str, Any], provider: str) -> int:
        """计算使用的token数"""
        provider_lower = provider.lower() if provider else ""

        if provider_lower in ["openai", "deepseek", "anthropic"]:
            # OpenAI格式的使用统计
            return response_data.get("usage", {}).get("total_tokens", 0)
        elif provider_lower in ["baidu", "wenxin"]:
            # 文心一言可能不返回token数，这里估计
            result = self._extract_response_content(response_data, provider, False)
            return len(result) // 3  # 中文大概3个字符一个token
        else:
            # 其他模型，尝试通用方法
            if "usage" in response_data and "total_tokens" in response_data["usage"]:
                return response_data["usage"]["total_tokens"]
            elif "total_tokens" in response_data:
                return response_data["total_tokens"]
            else:
                return 0

    def _estimate_tokens(self, text: str) -> int:
        """粗略估计文本的token数"""
        if not text:
            return 0

        # 简单实现：英文约4字符1token，中文约1.5字符1token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)

    def _log_api_call(
        self,
        user_id: int,
        model_id: int,
        conversation_id: Optional[int],
        endpoint: str,
        request_tokens: int,
        response_tokens: int,
        start_time: datetime,
        is_success: bool,
        status_code: int,
        error_message: Optional[str] = None
    ):
        """记录API调用日志"""
        response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        self.api_log_repo.create_api_call(
            user_id=user_id,
            model_id=model_id,
            endpoint=endpoint,
            request_tokens=request_tokens,
            response_tokens=response_tokens,
            response_time_ms=response_time_ms,
            status_code=status_code,
            is_success=is_success,
            error_message=error_message,
            conversation_id=conversation_id
        )

    async def _post_chat_processing(
        self,
        user_id: int,
        model_id: int,
        model_provider: str,
        conversation_id: Optional[int],
        user_message: str,
        ai_response: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        对话后处理流程
        """
        result = {
            "success": True,
            "messages_saved": False,
            "conversation_updated": False,
            "quota_checked": False,
            "new_conversation_id": None
        }

        try:
            # 1. 检查用户配额（简化的实现）
            quota_result = self._check_user_quota(user_id, total_tokens)
            result["quota_checked"] = True

            if not quota_result["has_quota"]:
                logger.warning(f"用户{user_id}超出配额限制，但仍继续处理")

            # 2. 处理对话
            if conversation_id:
                # 更新现有对话
                result["conversation_updated"] = self._update_existing_conversation(
                    conversation_id=conversation_id,
                    user_message=user_message,
                    ai_response=ai_response,
                    total_tokens=total_tokens,
                    model_id=model_id
                )
            else:
                # 创建新对话
                new_conversation = self._create_new_conversation(
                    user_id=user_id,
                    model_id=model_id,
                    user_message=user_message,
                    ai_response=ai_response,
                    total_tokens=total_tokens
                )

                if new_conversation.get("success"):
                    result["new_conversation_id"] = new_conversation["conversation_id"]
                    result["conversation_updated"] = True

            # 3. 记录详细的使用统计
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # 记录详细的聊天完成日志
            self.api_log_repo.record_chat_completion(
                user_id=user_id,
                model_id=model_id,
                conversation_id=conversation_id or result.get("new_conversation_id"),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_time_ms=response_time_ms,
                is_success=True,
                cost=self._calculate_api_cost(total_tokens, model_provider)
            )

            result["messages_saved"] = True

            logger.info(
                f"✅ 对话处理完成 - 用户:{user_id}, "
                f"模型:{model_id}, token:{total_tokens}, "
                f"耗时:{response_time_ms}ms"
            )

            return result

        except Exception as e:
            logger.error(f"对话后处理失败: {e}")
            result["success"] = False
            return result

    def _check_user_quota(self, user_id: int, tokens_used: int) -> Dict[str, Any]:
        """检查用户配额（简化版本）"""
        try:
            # 这里可以添加更复杂的配额检查逻辑
            # 例如：检查每日限额、每月限额、特定模型限额等

            # 临时实现：总是返回有配额
            return {
                "has_quota": True,
                "message": "配额检查通过",
                "remaining_quota": 1000000  # 模拟剩余配额
            }
        except Exception as e:
            logger.error(f"配额检查失败: {e}")
            # 失败时默认允许使用
            return {
                "has_quota": True,
                "message": "配额系统暂时不可用",
                "remaining_quota": 1000000
            }

    def _update_existing_conversation(
        self,
        conversation_id: int,
        user_message: str,
        ai_response: str,
        total_tokens: int,
        model_id: Optional[int] = None
    ) -> bool:
        """更新现有对话"""
        try:
            # 保存用户消息
            user_msg_result = self.conversation_service.save_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message
            )

            # 保存AI回复
            ai_msg_result = self.conversation_service.save_message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_response,
                tokens_used=total_tokens,
                model_id=model_id
            )

            # 更新对话统计
            conversation = self.db.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()

            if conversation:
                conversation.message_count = (conversation.message_count or 0) + 2
                conversation.total_tokens = (conversation.total_tokens or 0) + total_tokens
                conversation.updated_at = datetime.now()

                # 如果标题是默认的"新对话"，根据第一条消息自动生成标题
                if conversation.title == "新对话" or conversation.title.startswith("New Conversation"):
                    title = self._extract_conversation_title(user_message)
                    if title:
                        conversation.title = title[:50]  # 限制标题长度

                self.db.commit()

            return all([
                user_msg_result.get("success"),
                ai_msg_result.get("success"),
                conversation is not None
            ])

        except Exception as e:
            logger.error(f"更新对话失败: {e}")
            self.db.rollback()
            return False

    def _create_new_conversation(
        self,
        user_id: int,
        model_id: int,
        user_message: str,
        ai_response: str,
        total_tokens: int
    ) -> Dict[str, Any]:
        """创建新对话"""
        try:
            # 自动生成标题
            title = self._extract_conversation_title(user_message)
            if not title:
                title = "新对话"

            # 创建对话
            conversation = Conversation(
                user_id=user_id,
                title=title[:50],  # 限制标题长度
                model_id=model_id,
                message_count=2,
                total_tokens=total_tokens,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

            # 保存消息
            self._update_existing_conversation(
                conversation_id=conversation.conversation_id,
                user_message=user_message,
                ai_response=ai_response,
                total_tokens=total_tokens,
                model_id=model_id
            )

            return {
                "success": True,
                "conversation_id": conversation.conversation_id,
                "title": conversation.title
            }

        except Exception as e:
            logger.error(f"创建新对话失败: {e}")
            self.db.rollback()
            return {"success": False, "message": str(e)}

    def _extract_conversation_title(self, message: str) -> str:
        """从消息中提取对话标题"""
        if not message:
            return "新对话"

        # 清理消息
        message = message.strip()

        # 移除换行符和多余空格
        title = ' '.join(message.split())

        # 如果消息太长，截取前30个字符
        if len(title) > 30:
            title = title[:30] + "..."

        return title

    def _calculate_api_cost(
        self,
        tokens_used: int,
        model_provider: str
    ) -> float:
        """计算API调用成本"""
        # 简化的成本计算，实际应根据各厂商定价
        pricing = {
            "openai": 0.002 / 1000,  # $0.002 per 1K tokens
            "deepseek": 0.00014 / 1000,  # $0.00014 per 1K tokens
            "wenxin": 0.012 / 1000,  # 文心一言定价
        }

        rate = pricing.get(model_provider.lower(), 0.001 / 1000)
        return tokens_used * rate

    # 其他业务方法
    def get_available_models(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取可用模型列表"""
        models = self.system_model_repo.get_available_models()

        result = []
        for model in models:
            model_info = {
                "model_id": model.model_id,
                "model_name": model.model_name,
                "model_provider": model.model_provider,
                "model_type": model.model_type,
                "api_endpoint": model.api_endpoint,
                "is_default": model.is_default,
                "rate_limit_per_minute": model.rate_limit_per_minute,
                "max_tokens": model.max_tokens,
                "description": model.description
            }

            if user_id:
                user_config = self.user_config_repo.get_user_config_for_model(user_id, model.model_id)
                if user_config:
                    model_info["user_config"] = {
                        "is_enabled": user_config.is_enabled,
                        "priority": user_config.priority,
                        "last_used_at": user_config.last_used_at
                    }

            result.append(model_info)

        return result

    def update_user_model_config(self, user_id: int, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户模型配置"""
        model_id = config_data.get("model_id")
        if not model_id:
            raise ModelConfigError("必须提供model_id")

        # 检查模型是否存在
        system_model = self.system_model_repo.get_by_id(model_id)
        if not system_model:
            raise ModelNotAvailableError(f"模型ID {model_id} 不存在")

        # 获取或创建配置
        user_config = self.user_config_repo.get_user_config_for_model(user_id, model_id)

        update_data = {}
        if "api_key" in config_data and config_data["api_key"]:
            # 加密存储API密钥
            encrypted_key = encrypt_api_key(config_data["api_key"])
            update_data["api_key_encrypted"] = encrypted_key
            update_data["api_key"] = None  # 清文明文

        if "custom_endpoint" in config_data:
            update_data["custom_endpoint"] = config_data["custom_endpoint"]

        if "is_enabled" in config_data:
            update_data["is_enabled"] = config_data["is_enabled"]

        if "priority" in config_data:
            update_data["priority"] = config_data["priority"]

        if "temperature" in config_data:
            update_data["temperature"] = config_data["temperature"]

        if "max_tokens" in config_data:
            update_data["max_tokens"] = config_data["max_tokens"]

        if user_config:
            # 更新现有配置
            for key, value in update_data.items():
                setattr(user_config, key, value)
            self.db.commit()
            message = "配置更新成功"
        else:
            # 创建新配置
            create_data = {
                "user_id": user_id,
                "model_id": model_id,
                **update_data
            }
            user_config = self.user_config_repo.create(create_data)
            message = "配置创建成功"

        return {
            "success": True,
            "message": message,
            "config_id": user_config.config_id
        }

    def get_api_usage_stats(
        self,
        user_id: Optional[int] = None,
        model_id: Optional[int] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """获取API使用统计"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        stats = self.api_log_repo.get_api_usage_stats(
            user_id=user_id,
            model_id=model_id,
            start_date=start_date,
            end_date=end_date
        )

        daily_stats = self.api_log_repo.get_daily_usage_stats(
            days=days,
            user_id=user_id,
            model_id=model_id
        )

        return {
            "stats": stats,
            "daily_stats": daily_stats,
            "period": f"最近{days}天"
        }

    def validate_api_key(self, model_id: int, api_key: str) -> Dict[str, Any]:
        """验证API密钥格式"""
        # 基础格式验证
        if not api_key or len(api_key) < 10:
            return {
                "valid": False,
                "message": "API密钥格式不正确"
            }

        # 根据不同提供商进行格式验证
        system_model = self.system_model_repo.get_by_id(model_id)
        if not system_model:
            return {
                "valid": False,
                "message": "模型不存在"
            }

        provider = system_model.model_provider.lower()

        if provider == "openai":
            if not api_key.startswith("sk-"):
                return {
                    "valid": False,
                    "message": "OpenAI API密钥格式应为 sk- 开头"
                }
        elif provider == "deepseek":
            if not api_key.startswith("sk-"):
                return {
                    "valid": False,
                    "message": "DeepSeek API密钥格式应为 sk- 开头"
                }

        return {
            "valid": True,
            "message": "API密钥格式正确"
        }

    def get_user_model_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有模型配置"""
        configs = self.user_config_repo.get_user_configs(user_id)

        result = []
        for config in configs:
            config_dict = {
                "config_id": config.config_id,
                "user_id": config.user_id,
                "model_id": config.model_id,
                "is_enabled": config.is_enabled,
                "has_api_key": bool(config.api_key or config.api_key_encrypted),
                "custom_endpoint": config.custom_endpoint,
                "max_tokens": config.max_tokens,
                "temperature": float(config.temperature) if config.temperature else None,
                "priority": config.priority,
                "last_used_at": config.last_used_at,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }

            # 获取模型名称
            system_model = self.system_model_repo.get_by_id(config.model_id)
            if system_model:
                config_dict["model_name"] = system_model.model_name
                config_dict["model_provider"] = system_model.model_provider

            result.append(config_dict)

        return result

    def delete_user_model_config(self, user_id: int, model_id: int) -> Dict[str, Any]:
        """删除用户模型配置"""
        user_config = self.user_config_repo.get_user_config_for_model(user_id, model_id)

        if not user_config:
            return {
                "success": False,
                "message": "配置不存在"
            }

        try:
            self.user_config_repo.delete(user_config.config_id)
            return {
                "success": True,
                "message": "配置删除成功"
            }
        except Exception as e:
            logger.error(f"删除配置失败: {e}")
            return {
                "success": False,
                "message": f"删除失败: {str(e)}"
            }

    def bulk_update_models(
        self,
        user_id: int,
        model_ids: List[int],
        is_enabled: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """批量更新模型配置"""
        results = []

        for model_id in model_ids:
            if is_enabled is not None:
                if is_enabled:
                    self.user_config_repo.enable_user_model(user_id, model_id)
                else:
                    self.user_config_repo.disable_user_model(user_id, model_id)

            if priority is not None:
                self.user_config_repo.update_model_priority(user_id, model_id, priority)

            results.append(model_id)

        return {
            "success": True,
            "message": f"批量更新成功，共处理 {len(results)} 个模型",
            "data": results
        }

    def enable_user_model(self, user_id: int, model_id: int) -> Dict[str, Any]:
        """启用用户的模型"""
        success = self.user_config_repo.enable_user_model(user_id, model_id)

        if success:
            return {
                "success": True,
                "message": f"已启用模型 {model_id}"
            }
        else:
            return {
                "success": False,
                "message": f"启用模型失败"
            }

    def disable_user_model(self, user_id: int, model_id: int) -> Dict[str, Any]:
        """禁用用户的模型"""
        success = self.user_config_repo.disable_user_model(user_id, model_id)

        if success:
            return {
                "success": True,
                "message": f"已禁用模型 {model_id}"
            }
        else:
            return {
                "success": False,
                "message": f"禁用模型失败"
            }


def get_model_router_service(db: Session) -> ModelRouterService:
    """
    依赖注入函数 - 用于 FastAPI 依赖注入
    返回 ModelRouterService 实例
    """
    return ModelRouterService(db)
