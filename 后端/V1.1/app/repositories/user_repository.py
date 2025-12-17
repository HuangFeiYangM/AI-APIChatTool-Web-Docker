# app/repositories/user_repository.py
"""
用户Repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户Repository"""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户实例或None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            用户实例或None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_active_users(self) -> List[User]:
        """
        获取所有活跃用户
        
        Returns:
            活跃用户列表
        """
        return self.db.query(User).filter(
            User.is_active == True,
            User.is_locked == False
        ).all()
    
    def get_locked_users(self) -> List[User]:
        """
        获取所有被锁定的用户
        
        Returns:
            被锁定的用户列表
        """
        return self.db.query(User).filter(User.is_locked == True).all()
    
    def search_users(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_locked: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        搜索用户
        
        Args:
            username: 用户名（模糊搜索）
            email: 邮箱（模糊搜索）
            is_active: 是否活跃
            is_locked: 是否锁定
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            用户列表
        """
        query = self.db.query(User)
        
        if username:
            query = query.filter(User.username.ilike(f"%{username}%"))
        
        if email:
            query = query.filter(User.email.ilike(f"%{email}%"))
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_locked is not None:
            query = query.filter(User.is_locked == is_locked)
        
        query = query.order_by(User.created_at.desc())
        
        return query.offset(skip).limit(limit).all()
    
    def authenticate_user(self, username: str, password_hash: str) -> Optional[User]:
        """
        验证用户凭据
        
        Args:
            username: 用户名
            password_hash: 密码哈希
            
        Returns:
            验证成功的用户或None
        """
        return self.db.query(User).filter(
            and_(
                User.username == username,
                User.password_hash == password_hash,
                User.is_active == True,
                User.is_locked == False
            )
        ).first()
    
    def update_last_login(self, user_id: int) -> bool:
        """
        更新用户最后登录时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否更新成功
        """
        user = self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now()
            self.db.commit()
            return True
        return False
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        获取用户统计信息
        
        Returns:
            统计信息字典
        """
        # 修正：直接使用datetime.now()
        today = datetime.now().date()
        
        total_users = self.count()
        
        active_users = self.db.query(User).filter(
            User.is_active == True,
            User.is_locked == False
        ).count()
        
        locked_users = self.db.query(User).filter(
            User.is_locked == True
        ).count()
        
        # 修正：使用func.date()进行日期比较
        today_users = self.db.query(User).filter(
            func.date(User.created_at) == today
        ).count()
        
        return {
            "total": total_users,
            "active": active_users,
            "locked": locked_users,
            "today_new": today_users
        }
        
        
    # admin
    # 在 UserRepository 类中添加

    def count_users_by_date(self, date: datetime) -> int:
        """统计指定日期的用户数量"""
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        return self.db.query(func.count(User.user_id)).filter(
            User.created_at >= start_date,
            User.created_at < end_date
        ).scalar() or 0


    def count_active_users_by_date(self, date: datetime) -> int:
        """统计指定日期的活跃用户数量"""
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        return self.db.query(func.count(User.user_id)).filter(
            User.is_active == True,
            User.is_locked == False,
            User.last_login_at >= start_date,
            User.last_login_at < end_date
        ).scalar() or 0
