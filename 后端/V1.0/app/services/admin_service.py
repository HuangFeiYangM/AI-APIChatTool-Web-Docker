# app/services/admin_service.py
"""
管理员服务层
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import psutil
import platform
import os

from app.repositories.user_repository import UserRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.system_model_repository import SystemModelRepository
from app.repositories.user_model_config_repository import UserModelConfigRepository
from app.repositories.api_call_log_repository import ApiCallLogRepository

logger = logging.getLogger(__name__)


class AdminService:
    """管理员服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.system_model_repo = SystemModelRepository(db)
        self.user_config_repo = UserModelConfigRepository(db)
        self.api_call_repo = ApiCallLogRepository(db)
    
    def get_users(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户列表（带筛选）"""
        users = self.user_repo.search_users(
            username=filters.get("username"),
            email=filters.get("email"),
            is_active=filters.get("is_active"),
            is_locked=filters.get("is_locked"),
            skip=filters.get("skip", 0),
            limit=filters.get("limit", 20)
        )
        
        # 获取统计数据
        total_users = self.user_repo.count()
        active_users = self.user_repo.get_active_users()
        locked_users = self.user_repo.get_locked_users()
        
        # 转换响应格式
        user_list = []
        for user in users:
            # 获取用户的对话数量
            conversation_count = self.conversation_repo.get_user_conversation_count(user.user_id)
            
            user_list.append({
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_locked": user.is_locked,
                "locked_reason": user.locked_reason,
                "locked_until": user.locked_until,
                "failed_login_attempts": user.failed_login_attempts,
                "last_login_at": user.last_login_at,
                "conversation_count": conversation_count,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            })
        
        return {
            "users": user_list,
            "total": total_users,
            "active_count": len(active_users),
            "locked_count": len(locked_users)
        }
    
    def get_user_detail(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户详情"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        # 获取用户的对话
        conversations = self.conversation_repo.get_user_conversations(
            user_id, include_deleted=False, include_archived=True, limit=10
        )
        
        # 获取用户的模型配置
        configs = self.user_config_repo.get_user_configs(user_id)
        
        # 获取用户的API调用统计
        api_stats = self.api_call_repo.get_user_api_stats(user_id, days=30)
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_locked": user.is_locked,
            "locked_reason": user.locked_reason,
            "locked_until": user.locked_until,
            "failed_login_attempts": user.failed_login_attempts,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "conversations": [
                {
                    "conversation_id": conv.conversation_id,
                    "title": conv.title,
                    "model_id": conv.model_id,
                    "total_tokens": conv.total_tokens,
                    "message_count": conv.message_count,
                    "created_at": conv.created_at
                }
                for conv in conversations
            ],
            "model_configs": [
                {
                    "config_id": config.config_id,
                    "model_id": config.model_id,
                    "is_enabled": config.is_enabled,
                    "priority": config.priority,
                    "last_used_at": config.last_used_at
                }
                for config in configs
            ],
            "api_stats": api_stats
        }
    
    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户信息"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {
                "success": False,
                "message": f"用户 {user_id} 不存在"
            }
        
        # 更新用户信息
        for key, value in update_data.items():
            if value is not None:
                setattr(user, key, value)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"用户 {user.username} 更新成功"
        }
    
    def lock_user(self, user_id: int, reason: str, lock_hours: int = 24) -> Dict[str, Any]:
        """锁定用户账户"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {
                "success": False,
                "message": f"用户 {user_id} 不存在"
            }
        
        user.lock_account(reason, lock_hours)
        self.db.commit()
        
        return {
            "success": True,
            "message": f"用户 {user.username} 已锁定，锁定原因：{reason}"
        }
    
    def unlock_user(self, user_id: int) -> Dict[str, Any]:
        """解锁用户账户"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {
                "success": False,
                "message": f"用户 {user_id} 不存在"
            }
        
        user.unlock_account()
        self.db.commit()
        
        return {
            "success": True,
            "message": f"用户 {user.username} 已解锁"
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        # 用户统计
        user_stats = self.user_repo.get_user_stats()
        
        # 对话统计
        total_conversations = self.conversation_repo.count()
        
        # 消息统计
        total_messages = self.message_repo.count()
        
        # API调用统计
        api_stats = self.api_call_repo.get_overall_stats(days=30)
        
        # 系统运行时间
        system_uptime = psutil.boot_time()
        uptime_hours = (datetime.now().timestamp() - system_uptime) / 3600
        
        return {
            "total_users": user_stats.get("total", 0),
            "active_users": user_stats.get("active", 0),
            "locked_users": user_stats.get("locked", 0),
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_api_calls": api_stats.get("total_calls", 0),
            "total_tokens_used": api_stats.get("total_tokens", 0),
            "system_uptime": round(uptime_hours, 2),
            "avg_response_time": api_stats.get("avg_response_time", 0),
            "api_success_rate": api_stats.get("success_rate", 0)
        }
    
    # def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
    #     """获取每日统计信息"""
    #     end_date = datetime.now()
    #     start_date = end_date - timedelta(days=days)
        
    #     daily_stats = []
    #     current_date = start_date
        
    #     while current_date <= end_date:
    #         date_str = current_date.strftime("%Y-%m-%d")
            
    #         # 获取该日期的统计数据
    #         new_users = self.user_repo.count_users_by_date(current_date)
    #         active_users = self.user_repo.count_active_users_by_date(current_date)
    #         conversation_count = self.conversation_repo.count_by_date(current_date)
    #         message_count = self.message_repo.count_by_date(current_date)
    #         api_stats = self.api_call_repo.get_stats_by_date(current_date)
            
    #         daily_stats.append({
    #             "date": date_str,
    #             "new_users": new_users,
    #             "active_users": active_users,
    #             "conversation_count": conversation_count,
    #             "message_count": message_count,
    #             "api_call_count": api_stats.get("call_count", 0),
    #             "tokens_used": api_stats.get("total_tokens", 0)
    #         })
            
    #         current_date += timedelta(days=1)
        
    #     return daily_stats
    
    
    # 修改 app/services/admin_service.py 中的 get_system_stats 方法

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            # 用户统计
            total_users = self.user_repo.count()
            active_users = len(self.user_repo.get_active_users())
            locked_users = len(self.user_repo.get_locked_users())
            
            # 对话统计
            total_conversations = self.conversation_repo.count()
            
            # 消息统计
            total_messages = self.message_repo.count()
            
            # API调用统计 - 改为使用我们现有的方法
            api_stats = self.get_overall_api_stats(days=30)
            
            # 系统运行时间
            import time
            try:
                import psutil
                system_uptime = psutil.boot_time()
                uptime_hours = (time.time() - system_uptime) / 3600
            except:
                uptime_hours = 0
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "locked_users": locked_users,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "total_api_calls": api_stats.get("total_calls", 0),
                "total_tokens_used": api_stats.get("total_tokens", 0),
                "system_uptime": round(uptime_hours, 2),
                "avg_response_time": api_stats.get("avg_response_time", 0),
                "api_success_rate": api_stats.get("success_rate", 0)
            }
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}", exc_info=True)
            return {
                "total_users": 0,
                "active_users": 0,
                "locked_users": 0,
                "total_conversations": 0,
                "total_messages": 0,
                "total_api_calls": 0,
                "total_tokens_used": 0,
                "system_uptime": 0,
                "avg_response_time": 0,
                "api_success_rate": 0
            }

    
    # def get_system_health(self) -> Dict[str, Any]:
    #     """获取系统健康状态"""
    #     try:
    #         # 检查数据库连接
    #         db_status = self.db.execute("SELECT 1").scalar() == 1
            
    #         # 检查系统资源
    #         disk_usage = psutil.disk_usage('/').percent
    #         memory_usage = psutil.virtual_memory().percent
    #         cpu_usage = psutil.cpu_percent(interval=0.1)
            
    #         # 检查API端点状态（这里需要根据实际配置检查）
    #         api_endpoints = {
    #             "openai": self._check_api_endpoint("https://api.openai.com/v1/models"),
    #             "deepseek": self._check_api_endpoint("https://api.deepseek.com/chat/completions"),
    #             "database": db_status
    #         }
            
    #         # 确定整体状态
    #         status = "healthy"
    #         if disk_usage > 90 or memory_usage > 90 or cpu_usage > 90:
    #             status = "warning"
    #         if not db_status or disk_usage > 95 or memory_usage > 95:
    #             status = "critical"
            
    #         return {
    #             "status": status,
    #             "database": db_status,
    #             "cache": True,  # 这里假设缓存正常
    #             "api_endpoints": api_endpoints,
    #             "disk_usage": round(disk_usage, 2),
    #             "memory_usage": round(memory_usage, 2),
    #             "cpu_usage": round(cpu_usage, 2),
    #             "last_check": datetime.now()
    #         }
    #     except Exception as e:
    #         logger.error(f"检查系统健康状态失败: {e}")
    #         return {
    #             "status": "critical",
    #             "database": False,
    #             "cache": False,
    #             "api_endpoints": {},
    #             "disk_usage": 0,
    #             "memory_usage": 0,
    #             "cpu_usage": 0,
    #             "last_check": datetime.now()
    #         }
    
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态（修复版本，移除外部API检查）"""
        try:
            from datetime import datetime
            
            # 检查数据库连接
            db_status = False
            try:
                db_status = self.db.execute("SELECT 1").scalar() == 1
            except:
                db_status = False
            
            # 检查系统资源（如果有psutil）
            try:
                import psutil
                disk_usage = psutil.disk_usage('/').percent
                memory_usage = psutil.virtual_memory().percent
                cpu_usage = psutil.cpu_percent(interval=0.1)
            except ImportError:
                # 如果没有安装psutil，使用默认值
                disk_usage = 0
                memory_usage = 0
                cpu_usage = 0
            
            # 确定整体状态
            status = "healthy"
            if not db_status:
                status = "critical"
            elif disk_usage > 90 or memory_usage > 90 or cpu_usage > 90:
                status = "warning"
            
            # 只检查数据库，不检查外部API
            api_endpoints = {
                "database": db_status,
            }
            
            return {
                "status": status,
                "database": db_status,
                "cache": True,  # 这里假设缓存正常
                "api_endpoints": api_endpoints,
                "disk_usage": round(disk_usage, 2),
                "memory_usage": round(memory_usage, 2),
                "cpu_usage": round(cpu_usage, 2),
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"检查系统健康状态失败: {e}", exc_info=True)
            return {
                "status": "critical",
                "database": False,
                "cache": False,
                "api_endpoints": {},
                "disk_usage": 0,
                "memory_usage": 0,
                "cpu_usage": 0,
                "last_check": datetime.now().isoformat()
            }

    
    
    
    def _check_api_endpoint(self, endpoint: str) -> bool:
        """检查API端点状态（简化版本）"""
        try:
            import requests
            response = requests.get(endpoint, timeout=5)
            return response.status_code == 200 or response.status_code == 401  # 401表示需要API密钥，但端点存在
        except:
            return False
    
    def get_api_call_logs(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """获取API调用日志"""
        logs = self.api_call_repo.search_logs(
            user_id=filters.get("user_id"),
            model_id=filters.get("model_id"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            is_success=filters.get("is_success"),
            skip=filters.get("skip", 0),
            limit=filters.get("limit", 50)
        )
        
        total = self.api_call_repo.count_logs(
            user_id=filters.get("user_id"),
            model_id=filters.get("model_id"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            is_success=filters.get("is_success")
        )
        
        log_list = []
        for log in logs:
            log_list.append({
                "log_id": log.log_id,
                "user_id": log.user_id,
                "username": log.user.username if log.user else None,
                "model_id": log.model_id,
                "model_name": log.system_model.model_name if log.system_model else None,
                "conversation_id": log.conversation_id,
                "endpoint": log.endpoint,
                "request_tokens": log.request_tokens,
                "response_tokens": log.response_tokens,
                "total_tokens": log.total_tokens,
                "response_time_ms": log.response_time_ms,
                "status_code": log.status_code,
                "is_success": log.is_success,
                "error_message": log.error_message,
                "created_at": log.created_at
            })
        
        return {
            "logs": log_list,
            "total": total
        }
    
    def create_system_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建系统模型"""
        # 检查模型名称是否已存在
        existing = self.system_model_repo.get_by_name(model_data["model_name"])
        if existing:
            return {
                "success": False,
                "message": f"模型名称 '{model_data['model_name']}' 已存在"
            }
        
        model = self.system_model_repo.create(model_data)
        
        return {
            "success": True,
            "message": "模型创建成功",
            "data": {
                "model_id": model.model_id,
                "model_name": model.model_name
            }
        }
    
    def update_system_model(self, model_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新系统模型"""
        model = self.system_model_repo.get_by_id(model_id)
        if not model:
            return {
                "success": False,
                "message": f"模型 {model_id} 不存在"
            }
        
        # 如果更新了模型名称，检查是否重复
        if "model_name" in update_data and update_data["model_name"] != model.model_name:
            existing = self.system_model_repo.get_by_name(update_data["model_name"])
            if existing and existing.model_id != model_id:
                return {
                    "success": False,
                    "message": f"模型名称 '{update_data['model_name']}' 已存在"
                }
        
        updated_model = self.system_model_repo.update(model, update_data)
        
        return {
            "success": True,
            "message": "模型更新成功",
            "data": {
                "model_id": updated_model.model_id,
                "model_name": updated_model.model_name
            }
        }
    
    def delete_system_model(self, model_id: int) -> Dict[str, Any]:
        """删除系统模型"""
        model = self.system_model_repo.get_by_id(model_id)
        if not model:
            return {
                "success": False,
                "message": f"模型 {model_id} 不存在"
            }
        
        # 检查是否有用户在使用此模型
        user_configs = self.user_config_repo.db.query(self.user_config_repo.model).filter(
            self.user_config_repo.model.model_id == model_id
        ).count()
        
        if user_configs > 0:
            return {
                "success": False,
                "message": f"无法删除模型，有 {user_configs} 个用户正在使用此模型"
            }
        
        self.system_model_repo.delete(model_id)
        
        return {
            "success": True,
            "message": "模型删除成功"
        }

    # 添加这个方法到 AdminService 类中
    def get_overall_api_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取整体API调用统计（简化版本）"""
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 使用正确的模型
            from app.models.api_call_log import ApiCallLog
            
            result = self.db.query(
                func.count(ApiCallLog.log_id).label('total_calls'),
                func.sum(ApiCallLog.total_tokens).label('total_tokens'),
                func.avg(ApiCallLog.response_time_ms).label('avg_response_time'),
                func.avg(func.cast(ApiCallLog.is_success, func.Integer)).label('success_rate')
            ).filter(
                ApiCallLog.created_at >= start_date,
                ApiCallLog.created_at <= end_date
            ).first()
            
            if result and result[0]:
                return {
                    "total_calls": result[0] or 0,
                    "total_tokens": result[1] or 0,
                    "avg_response_time": float(result[2] or 0),
                    "success_rate": float(result[3] or 0) * 100 if result[3] else 0
                }
            else:
                return {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "avg_response_time": 0,
                    "success_rate": 0
                }
        except Exception as e:
            logger.error(f"获取API统计失败: {e}", exc_info=True)
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "avg_response_time": 0,
                "success_rate": 0
            }
    
    

def get_admin_service(db: Session):
    """获取管理员服务实例"""
    return AdminService(db)
