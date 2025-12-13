# app/repositories/login_attempt_repository.py
"""
登录尝试Repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta

from app.models.login_attempt import LoginAttempt
from app.repositories.base import BaseRepository


class LoginAttemptRepository(BaseRepository[LoginAttempt]):
    """登录尝试Repository"""
    
    def __init__(self, db: Session):
        super().__init__(LoginAttempt, db)
    
    def record_attempt(
        self, 
        username: str, 
        ip_address: str, 
        user_agent: str, 
        is_success: bool
    ) -> LoginAttempt:
        """
        记录登录尝试
        
        Args:
            username: 用户名
            ip_address: IP地址
            user_agent: 用户代理
            is_success: 是否成功
            
        Returns:
            创建的登录尝试记录
        """
        # login_attempt = LoginAttempt(
        #     username=username,
        #     ip_address=ip_address,
        #     user_agent=user_agent,
        #     is_success=is_success
        # )
        # return self.create_from_instance(login_attempt)
        
        # 改为使用create方法，传递字典参数
        return self.create({
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "is_success": is_success
        })
    
    def get_recent_failed_attempts(
        self, 
        username: str, 
        minutes: int = 15
    ) -> List[LoginAttempt]:
        """
        获取指定用户最近的失败登录尝试
        
        Args:
            username: 用户名
            minutes: 时间范围（分钟）
            
        Returns:
            失败登录尝试列表
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return self.db.query(LoginAttempt).filter(
            and_(
                LoginAttempt.username == username,
                LoginAttempt.is_success == False,
                LoginAttempt.created_at >= cutoff_time
            )
        ).order_by(desc(LoginAttempt.created_at)).all()
    
    def count_recent_failed_attempts(
        self, 
        username: str, 
        minutes: int = 15
    ) -> int:
        """
        统计指定用户最近的失败登录次数
        
        Args:
            username: 用户名
            minutes: 时间范围（分钟）
            
        Returns:
            失败登录次数
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return self.db.query(LoginAttempt).filter(
            and_(
                LoginAttempt.username == username,
                LoginAttempt.is_success == False,
                LoginAttempt.created_at >= cutoff_time
            )
        ).count()
    
    def get_attempts_by_ip(
        self, 
        ip_address: str, 
        limit: int = 100
    ) -> List[LoginAttempt]:
        """
        按IP地址获取登录尝试
        
        Args:
            ip_address: IP地址
            limit: 返回的最大记录数
            
        Returns:
            登录尝试列表
        """
        return self.db.query(LoginAttempt).filter(
            LoginAttempt.ip_address == ip_address
        ).order_by(desc(LoginAttempt.created_at)).limit(limit).all()
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        获取登录统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        from sqlalchemy import func
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 总尝试次数
        total_attempts = self.db.query(func.count(LoginAttempt.attempt_id)).filter(
            LoginAttempt.created_at >= start_date
        ).scalar()
        
        # 成功次数
        successful_attempts = self.db.query(func.count(LoginAttempt.attempt_id)).filter(
            and_(
                LoginAttempt.created_at >= start_date,
                LoginAttempt.is_success == True
            )
        ).scalar()
        
        # 失败次数
        failed_attempts = self.db.query(func.count(LoginAttempt.attempt_id)).filter(
            and_(
                LoginAttempt.created_at >= start_date,
                LoginAttempt.is_success == False
            )
        ).scalar()
        
        # 成功率
        success_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": round(success_rate, 2),
            "period_days": days
        }
