# app/services/model_router.py
# 在文件顶部添加缺失的导入
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# 确保这些 Repository 类存在
from app.repositories.system_model_repository import SystemModelRepository
from app.repositories.user_model_config_repository import UserModelConfigRepository
from app.repositories.api_call_log_repository import ApiCallLogRepository
from app.exceptions import (
    ModelNotAvailableError, APIRequestError, 
    InsufficientQuotaError, ModelConfigError
)
from app.config import settings
from app.core.security import encrypt_api_key, decrypt_api_key

logger = logging.getLogger(__name__)



class ModelRouterService:
    """模型路由服务 - 对应详细设计中的程序4"""

    def __init__(self, db: Session):
        self.db = db
        self.system_model_repo = SystemModelRepository(db)
        self.user_config_repo = UserModelConfigRepository(db)
        self.api_log_repo = ApiCallLogRepository(db)
        
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
        对应详细设计中的算法：模型API路由
        """
        start_time = datetime.now()
        
        try:
            # 1. 获取模型配置
            system_model = self.system_model_repo.get_by_name(model_name)
            if not system_model or not system_model.is_available:
                raise ModelNotAvailableError(f"模型 '{model_name}' 不存在或未激活")
            
            logger.info(f"用户 {user_id} 请求模型 {model_name} (提供商: {system_model.model_provider})")

            # 2. 获取用户配置和API密钥
            api_key, custom_endpoint = self._get_user_api_config(user_id, system_model.model_id)
            if not api_key:
                raise ModelConfigError(f"未配置模型 '{model_name}' 的API密钥")

            # 3. 检查速率限制
            self._check_rate_limit(user_id, system_model.model_id)

            # 4. 构造请求数据
            # 获取正确的模型标识符
            model_identifier = self._get_model_identifier(model_name, system_model.model_provider)
            
            request_data = {
                "model": model_identifier,
                "messages": [{"role": "user", "content": message}],
                "temperature": temperature,
                "max_tokens": min(max_tokens, system_model.max_tokens or 2000),
                "stream": stream
            }

            # 5. 调用API（带重试机制）
            response_data = await self._call_model_api_with_retry(
                provider=system_model.model_provider,
                endpoint=custom_endpoint or system_model.api_endpoint,
                api_key=api_key,
                request_data=request_data,
                stream=stream
            )

            # 6. 提取响应内容
            response_text = self._extract_response_content(response_data, system_model.model_provider, stream)
            tokens_used = self._calculate_tokens_used(response_data, system_model.model_provider)

            # 7. 记录API调用日志
            self._log_api_call(
                user_id=user_id,
                model_id=system_model.model_id,
                conversation_id=conversation_id,
                endpoint=system_model.api_endpoint,
                request_tokens=self._estimate_tokens(message),
                response_tokens=tokens_used,
                start_time=start_time,
                is_success=True,
                status_code=200
            )

            # 8. 更新用户配置的最后使用时间
            self.user_config_repo.update_last_used_time(system_model.model_id)

            # 9. 返回结果
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                "response": response_text,
                "model_used": model_name,
                "tokens_used": tokens_used,
                "processing_time_ms": processing_time,
                "conversation_id": conversation_id or 0
            }

        except Exception as e:
            # 记录失败日志
            model_id = system_model.model_id if 'system_model' in locals() else 0
            endpoint = system_model.api_endpoint if 'system_model' in locals() else ""
            
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
        if system_model and system_model.model_provider in settings.DEFAULT_API_KEYS:
            api_key = settings.DEFAULT_API_KEYS[system_model.model_provider]
            return api_key, None
        
        return None, None

    def _check_rate_limit(self, user_id: int, model_id: int):
        """检查速率限制"""
        # 获取最近一分钟的调用次数
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_calls = self.api_log_repo.get_model_api_calls(
            model_id=model_id,
            start_date=one_minute_ago,
            limit=1000  # 足够大的数来统计
        )
        
        # 过滤当前用户的调用
        user_calls = [call for call in recent_calls if call.user_id == user_id]
        
        # 获取模型速率限制
        system_model = self.system_model_repo.get_by_id(model_id)
        rate_limit = system_model.rate_limit_per_minute if system_model else 60
        
        if len(user_calls) >= rate_limit:
            raise APIRequestError(f"速率限制：每分钟最多 {rate_limit} 次调用")

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
                    logger.warning(f"API调用失败，第{attempt+1}次重试，等待{wait_time}秒")
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
        import httpx
        
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
        import httpx
        
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
            self.user_config_repo.update(user_config, update_data)
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


def get_model_router_service(db: Session) -> ModelRouterService:
    """
    依赖注入函数 - 用于 FastAPI 依赖注入
    返回 ModelRouterService 实例
    """
    return ModelRouterService(db)
