# app/services/auth_service.py
"""
认证服务 - 实现用户注册、登录、JWT管理等业务逻辑
对应详细设计中的程序1和程序2
"""
from typing import Optional, Dict, Any, Tuple,List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
# app/services/auth_service.py（修复部分）
from fastapi import Depends  # 添加这行
from app.database import get_db  # 添加这行

from app.repositories.user_repository import UserRepository
from app.repositories.login_attempt_repository import LoginAttemptRepository  # 添加这行

from app.schemas.auth import (
    LoginRequest, RegisterRequest, ChangePasswordRequest, 
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.schemas.user import UserCreate, UserUpdate

from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    verify_access_token, get_token_payload, create_refresh_token,
    generate_password_reset_token, verify_password_reset_token,
    is_password_strong
)

from app.exceptions import (
    AuthenticationError, UserAlreadyExistsError, 
    UserNotFoundError, InvalidPasswordError,
    AccountLockedError, InvalidTokenError
)


logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        """初始化认证服务"""
        self.db = db
        self.user_repo = UserRepository(db)
        self.login_attempt_repo = LoginAttemptRepository(db)  # 添加这行
    
    # def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
    #     """
    #     用户认证
    #     对应详细设计中的程序2：用户登录
    #     """
    #     try:
    #         # 1. 验证用户是否存在且未锁定
    #         user = self.user_repo.get_by_username(username)
    #         if not user:
    #             logger.warning(f"用户不存在: {username}")
    #             raise AuthenticationError("用户名或密码错误")
            
    #         if user.is_locked:
    #             logger.warning(f"用户账户被锁定: {username}")
    #             raise AccountLockedError("账户已被锁定")
            
    #         if not user.is_active:
    #             logger.warning(f"用户账户未启用: {username}")
    #             raise AuthenticationError("账户未启用")
            
    #         # 2. 验证密码
    #         if not verify_password(password, user.password_hash):
    #             # 记录失败尝试
    #             self._record_failed_attempt(username)
    #             logger.warning(f"密码验证失败: {username}")
    #             raise AuthenticationError("用户名或密码错误")
            
    #         # 3. 登录成功，重置失败计数并更新最后登录时间
    #         user.failed_login_attempts = 0
    #         user.last_login_at = datetime.now()
    #         self.db.commit()
            
    #         # 4. 创建访问令牌
    #         access_token = create_access_token(
    #             data={"sub": str(user.user_id)}
    #         )
            
    #         logger.info(f"用户登录成功: {username}")
            
    #         return {
    #             "access_token": access_token,
    #             "token_type": "bearer",
    #             "user_id": user.user_id,
    #             "username": user.username,
    #             "email": user.email
    #         }
            
    #     except Exception as e:
    #         logger.error(f"用户认证失败: {e}")
    #         raise
    
    
    # 改的用户认证方法，增加了登录尝试记录功能
    # def authenticate_user(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
    #     """
    #     用户认证
    #     对应详细设计中的程序2：用户登录
        
    #     Args:
    #         username: 用户名
    #         password: 密码
    #         ip_address: IP地址（可选，用于记录）
    #         user_agent: 用户代理（可选，用于记录）
    #     """
    #     try:
    #         # 1. 验证用户是否存在且未锁定
    #         user = self.user_repo.get_by_username(username)
    #         if not user:
    #             logger.warning(f"用户不存在: {username}")
    #             # 记录登录尝试（即使用户不存在也记录）
    #             self._record_login_attempt(username, False, ip_address, user_agent)
    #             raise AuthenticationError("用户名或密码错误")
            
    #         if user.is_locked:
    #             logger.warning(f"用户账户被锁定: {username}")
    #             # 记录登录尝试
    #             self._record_login_attempt(username, False, ip_address, user_agent)
    #             raise AccountLockedError("账户已被锁定")
            
    #         if not user.is_active:
    #             logger.warning(f"用户账户未启用: {username}")
    #             # 记录登录尝试
    #             self._record_login_attempt(username, False, ip_address, user_agent)
    #             raise AuthenticationError("账户未启用")
            
    #         # 2. 验证密码
    #         if not verify_password(password, user.password_hash):
    #             # 记录失败登录尝试
    #             self._record_login_attempt(username, False, ip_address, user_agent)
    #             # 记录失败尝试（更新users表）
    #             self._record_failed_attempt(username)
    #             logger.warning(f"密码验证失败: {username}")
    #             raise AuthenticationError("用户名或密码错误")
            
    #         # 3. 登录成功，重置失败计数并更新最后登录时间
    #         user.failed_login_attempts = 0
    #         user.last_login_at = datetime.now()
    #         self.db.commit()
            
    #         # 4. 记录成功登录尝试
    #         self._record_login_attempt(username, True, ip_address, user_agent)
            
    #         # 5. 创建访问令牌
    #         access_token = create_access_token(
    #             data={"sub": str(user.user_id)}
    #         )
            
    #         logger.info(f"用户登录成功: {username}")
            
    #         return {
    #             "access_token": access_token,
    #             "token_type": "bearer",
    #             "user_id": user.user_id,
    #             "username": user.username,
    #             "email": user.email
    #         }
            
    #     except Exception as e:
    #         logger.error(f"用户认证失败: {e}")
    #         raise
    
    # # 记录登录信息
    # def _record_login_attempt(self, username: str, is_success: bool, ip_address: str = None, user_agent: str = None) -> None:
    #     """记录登录尝试到 login_attempts 表"""
    #     try:
    #         # 获取默认的IP和User-Agent（如果未提供）
    #         if not ip_address:
    #             ip_address = "127.0.0.1"  # 默认值，实际应该从请求中获取
            
    #         if not user_agent:
    #             user_agent = "Unknown"  # 默认值
            
    #         # 记录到 login_attempts 表
    #         self.login_attempt_repo.record_attempt(
    #             username=username,
    #             ip_address=ip_address,
    #             user_agent=user_agent,
    #             is_success=is_success
    #         )
            
    #         logger.debug(f"记录登录尝试: username={username}, success={is_success}, ip={ip_address}")
            
    #     except Exception as e:
    #         logger.error(f"记录登录尝试失败: {e}")
    #         # 不抛出异常，避免影响主流程
    
    # def _record_failed_attempt(self, username: str) -> None:
    #     """记录失败登录尝试（更新users表）"""
    #     try:
    #         user = self.user_repo.get_by_username(username)
    #         if user:
    #             user.failed_login_attempts += 1
                
    #             # 如果失败次数达到5次，锁定账户30分钟
    #             if user.failed_login_attempts >= 5:
    #                 user.is_locked = True
    #                 user.locked_reason = "多次登录失败"
    #                 user.locked_until = datetime.now() + timedelta(minutes=30)
    #                 logger.warning(f"账户因多次登录失败被锁定: {username}")
                
    #             self.db.commit()
                
    #     except Exception as e:
    #         logger.error(f"记录失败登录尝试失败: {e}")
    
    def authenticate_user(self, username: str, password: str, 
                        ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        用户认证
        对应详细设计中的程序2：用户登录
        """
        try:
            # 1. 验证用户是否存在且未锁定
            user = self.user_repo.get_by_username(username)
            if not user:
                logger.warning(f"用户不存在: {username}")
                # 记录失败的登录尝试
                if ip_address:
                    self.login_attempt_repo.record_attempt(
                        username=username,
                        ip_address=ip_address,
                        user_agent=user_agent or "",
                        is_success=False
                    )
                raise AuthenticationError("用户名或密码错误")
            
            if user.is_locked:
                logger.warning(f"用户账户被锁定: {username}")
                # 记录失败的登录尝试
                if ip_address:
                    self.login_attempt_repo.record_attempt(
                        username=username,
                        ip_address=ip_address,
                        user_agent=user_agent or "",
                        is_success=False
                    )
                raise AuthenticationError("账户已被锁定")
            
            if not user.is_active:
                logger.warning(f"用户账户未启用: {username}")
                # 记录失败的登录尝试
                if ip_address:
                    self.login_attempt_repo.record_attempt(
                        username=username,
                        ip_address=ip_address,
                        user_agent=user_agent or "",
                        is_success=False
                    )
                raise AuthenticationError("账户未启用")
            
            # 2. 验证密码
            if not verify_password(password, user.password_hash):
                # 记录失败尝试
                self._record_failed_attempt(username, ip_address, user_agent)
                logger.warning(f"密码验证失败: {username}")
                raise AuthenticationError("用户名或密码错误")
            
            # 3. 登录成功，重置失败计数并更新最后登录时间
            user.failed_login_attempts = 0
            user.last_login_at = datetime.now()
            user.is_locked = False  # 解锁账户（如果之前被锁定）
            user.locked_reason = None
            user.locked_until = None
            self.db.commit()
            
            # 记录成功的登录尝试
            if ip_address:
                self.login_attempt_repo.record_attempt(
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent or "",
                    is_success=True
                )
            
            # 4. 创建访问令牌
            access_token = create_access_token(
                data={"sub": str(user.user_id)}
            )
            
            logger.info(f"用户登录成功: {username}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email
            }
            
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            raise
    
    
    
    def _record_failed_attempt(self, username: str, ip_address: str = None, user_agent: str = None) -> None:
        """记录失败登录尝试"""
        try:
            user = self.user_repo.get_by_username(username)
            if user:
                user.failed_login_attempts += 1
                
                # 如果失败次数达到5次，锁定账户30分钟
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                    user.locked_reason = "多次登录失败"
                    user.locked_until = datetime.now() + timedelta(minutes=30)
                    logger.warning(f"账户因多次登录失败被锁定: {username}")
                
                self.db.commit()
            
            # 记录到login_attempts表
            if ip_address:
                self.login_attempt_repo.record_attempt(
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent or "",
                    is_success=False
                )
                
        except Exception as e:
            logger.error(f"记录失败登录尝试失败: {e}")
    
    def get_login_attempts_by_username(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户的登录尝试记录
        
        Args:
            username: 用户名
            limit: 返回的最大记录数
            
        Returns:
            登录尝试记录列表
        """
        attempts = self.login_attempt_repo.get_recent_failed_attempts(username, minutes=1440)  # 24小时内
        return [
            {
                "attempt_id": attempt.attempt_id,
                "username": attempt.username,
                "ip_address": attempt.ip_address,
                "user_agent": attempt.user_agent,
                "is_success": attempt.is_success,
                "created_at": attempt.created_at.isoformat() if attempt.created_at else None
            }
            for attempt in attempts[:limit]
        ]
    
    
    
    
    
    
    
    
    
    
    def register_user(self, user_data: RegisterRequest) -> Dict[str, Any]:
        """
        用户注册
        对应详细设计中的程序1：用户注册
        """
        try:
            # 1. 检查用户名是否已存在
            existing_user = self.user_repo.get_by_username(user_data.username)
            if existing_user:
                logger.warning(f"用户名已存在: {user_data.username}")
                raise UserAlreadyExistsError("用户名已存在")
            
            # 2. 检查邮箱是否已存在（如果提供了邮箱）
            if user_data.email:
                existing_email = self.user_repo.get_by_email(user_data.email)
                if existing_email:
                    logger.warning(f"邮箱已存在: {user_data.email}")
                    raise UserAlreadyExistsError("邮箱已存在")
            
            # 3. 创建用户
            hashed_password = get_password_hash(user_data.password)
            
            user_db_data = {
                "username": user_data.username,
                "password_hash": hashed_password,
                "email": user_data.email,
                "is_active": True,
                "is_locked": False,
                "failed_login_attempts": 0
            }
            
            user = self.user_repo.create(user_db_data)
            logger.info(f"用户注册成功: {user_data.username}")
            
            # 4. 自动登录（可选）
            access_token = create_access_token(
                data={"sub": str(user.user_id)}
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.user_id,
                "username": user.username,
                "message": "注册成功"
            }
        
        except Exception as e:
            logger.error(f"用户注册失败: {e}")
            raise
    
    def change_password(
        self, 
        user_id: int, 
        password_data: ChangePasswordRequest
    ) -> bool:
        """修改密码"""
        try:
            # 1. 获取用户
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("用户不存在")
            
            # 2. 验证当前密码
            if not verify_password(password_data.current_password, user.password_hash):
                logger.warning(f"修改密码失败 - 当前密码错误: user_id={user_id}")
                raise InvalidPasswordError("当前密码错误")
            
            # 3. 更新密码
            new_hashed_password = get_password_hash(password_data.new_password)
            user.password_hash = new_hashed_password
            self.db.commit()
            
            logger.info(f"密码修改成功: user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            raise
    
    def logout(self, token: str) -> bool:
        """用户登出（在客户端删除令牌）"""
        try:
            # JWT是无状态的，通常客户端删除令牌即可
            # 这里可以记录登出日志或管理令牌黑名单（如果需要）
            payload = get_token_payload(token)
            if payload and 'sub' in payload:
                logger.info(f"用户登出: user_id={payload['sub']}")
            return True
        except Exception as e:
            logger.error(f"登出处理失败: {e}")
            return False
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """验证JWT令牌"""
        try:
            payload = verify_access_token(token)
            if not payload:
                raise InvalidTokenError("无效的令牌")
            
            # 检查用户是否存在且状态正常
            user_id = int(payload.get('sub'))
            user = self.user_repo.get_by_id(user_id)
            
            if not user:
                raise UserNotFoundError("用户不存在")
            
            if not user.is_active:
                raise AuthenticationError("账户未启用")
            
            if user.is_locked:
                raise AccountLockedError("账户已被锁定")
            
            return {
                "valid": True,
                "user_id": user.user_id,
                "username": user.username,
                "exp": payload.get('exp')
            }
            
        except Exception as e:
            logger.warning(f"令牌验证失败: {e}")
            raise InvalidTokenError(str(e))
    
    def refresh_token(self, token: str) -> Dict[str, Any]:
        """刷新访问令牌"""
        try:
            # 验证旧令牌
            payload = self.validate_token(token)
            
            # 创建新令牌
            new_token = create_access_token(
                data={"sub": str(payload['user_id'])}
            )
            
            logger.info(f"令牌刷新成功: user_id={payload['user_id']}")
            
            return {
                "access_token": new_token,
                "token_type": "bearer",
                "user_id": payload['user_id']
            }
            
        except Exception as e:
            logger.error(f"令牌刷新失败: {e}")
            raise
    
    
    
    def unlock_user_account(self, username: str, admin_user_id: int) -> bool:
        """解锁用户账户（管理员功能）"""
        try:
            user = self.user_repo.get_by_username(username)
            if not user:
                raise UserNotFoundError("用户不存在")
            
            if not user.is_locked:
                return True  # 账户未锁定
            
            user.is_locked = False
            user.locked_reason = None
            user.locked_until = None
            user.failed_login_attempts = 0
            self.db.commit()
            
            logger.info(f"管理员解锁用户账户: admin={admin_user_id}, user={username}")
            return True
            
        except Exception as e:
            logger.error(f"解锁用户账户失败: {e}")
            raise
    
    def get_user_by_token(self, token: str) -> Dict[str, Any]:
        """通过令牌获取用户信息"""
        try:
            payload = self.validate_token(token)
            user = self.user_repo.get_by_id(payload['user_id'])
            
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_locked": user.is_locked,
                "last_login_at": user.last_login_at,
                "created_at": user.created_at
            }
            
        except Exception as e:
            logger.error(f"通过令牌获取用户信息失败: {e}")
            raise


# 工厂函数，用于依赖注入
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:  # 修改这行
    """获取认证服务实例"""
    return AuthService(db)

