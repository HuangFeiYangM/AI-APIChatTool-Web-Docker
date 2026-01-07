# app/exceptions.py（补充部分）
"""
自定义异常类
"""

# 认证相关异常
class AuthenticationError(Exception):
    """认证失败异常"""
    def __init__(self, message: str = "认证失败"):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExistsError(Exception):
    """用户已存在异常"""
    def __init__(self, message: str = "用户已存在"):
        self.message = message
        super().__init__(self.message)


class UserNotFoundError(Exception):
    """用户不存在异常"""
    def __init__(self, message: str = "用户不存在"):
        self.message = message
        super().__init__(self.message)


class InvalidPasswordError(Exception):
    """密码无效异常"""
    def __init__(self, message: str = "密码错误"):
        self.message = message
        super().__init__(self.message)


class AccountLockedError(Exception):
    """账户锁定异常"""
    def __init__(self, message: str = "账户已被锁定"):
        self.message = message
        super().__init__(self.message)


class InvalidTokenError(Exception):
    """令牌无效异常"""
    def __init__(self, message: str = "无效的令牌"):
        self.message = message
        super().__init__(self.message)




# API大模型相关异常

class ModelNotAvailableError(Exception):
    """模型不可用异常"""
    pass

class APIRequestError(Exception):
    """API请求异常"""
    pass

class InsufficientQuotaError(Exception):
    """API配额不足异常"""
    pass

class ModelConfigError(Exception):
    """模型配置异常"""
    pass

class RateLimitExceededError(Exception):
    """速率限制异常"""
    pass


# app/exceptions.py（补充部分）

# 对话管理相关异常

class ConversationNotFoundError(Exception):
    """对话不存在异常"""
    def __init__(self, message: str = "对话不存在"):
        self.message = message
        super().__init__(self.message)


class MessageNotFoundError(Exception):
    """消息不存在异常"""
    def __init__(self, message: str = "消息不存在"):
        self.message = message
        super().__init__(self.message)


class UnauthorizedError(Exception):
    """无权访问异常"""
    def __init__(self, message: str = "无权访问"):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """数据验证异常"""
    def __init__(self, message: str = "数据验证失败"):
        self.message = message
        super().__init__(self.message)


class BulkOperationError(Exception):
    """批量操作异常"""
    def __init__(self, message: str = "批量操作失败"):
        self.message = message
        super().__init__(self.message)


class ConversationArchivedError(Exception):
    """对话已归档异常"""
    def __init__(self, message: str = "对话已归档"):
        self.message = message
        super().__init__(self.message)


class ConversationDeletedError(Exception):
    """对话已删除异常"""
    def __init__(self, message: str = "对话已删除"):
        self.message = message
        super().__init__(self.message)


class RateLimitExceededError(Exception):
    """速率限制异常"""
    def __init__(self, message: str = "请求频率过高"):
        self.message = message
        super().__init__(self.message)
