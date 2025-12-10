# Schemas目录详解

# **Schemas目录详解**

`schemas/` 目录是FastAPI项目中**最关键**的部分之一，它直接决定了API的接口规范、数据验证和自动文档生成的质量。

## **1. 核心作用**

### **1.1 数据验证与转换**
- **自动验证**: FastAPI会在请求到达路由函数**之前**自动验证数据
- **类型转换**: 自动将请求数据转换为正确的Python类型（如字符串转整数）
- **数据清理**: 过滤掉不应该接收的字段

### **1.2 自动API文档生成**
- **Swagger UI**: 自动生成 `/docs` 页面的接口文档
- **OpenAPI规范**: 自动生成符合OpenAPI规范的API描述
- **请求/响应示例**: 根据模型定义自动显示示例数据

### **1.3 序列化与反序列化**
- **请求体**: 将JSON请求体反序列化为Python对象
- **响应体**: 将Python对象序列化为JSON响应
- **嵌套对象**: 支持复杂嵌套结构的序列化

## **2. 文件结构详解**

### **2.1 `user.py` - 用户相关模型**
```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

# 基础模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, 
                         pattern="^[a-zA-Z0-9_]+$",
                         description="用户名，3-50个字符，只允许字母、数字和下划线")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")

# 创建用户时的请求模型
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100,
                         description="密码，6-100个字符")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v

# 用户登录请求模型
class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

# 数据库中的用户模型（不返回密码）
class UserInDB(UserBase):
    user_id: int = Field(..., description="用户ID")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True  # 允许从ORM对象转换

# API响应中的用户模型
class UserResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# JWT令牌响应
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(86400, description="过期时间(秒)")
```

### **2.2 `chat.py` - 对话相关模型**
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# 消息角色枚举
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# 发送消息请求
class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000,
                        description="消息内容，1-10000个字符")
    model: str = Field(..., description="选择的模型名称")
    conversation_id: Optional[int] = Field(None, description="对话ID，为空时创建新对话")

# 单条消息响应
class MessageResponse(BaseModel):
    message_id: int
    role: MessageRole
    content: str
    tokens_used: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

# 对话响应（包含消息列表）
class ConversationResponse(BaseModel):
    conversation_id: int
    title: Optional[str]
    model_used: str
    message_count: int
    created_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True

# 对话列表响应（分页）
class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0

# 流式响应块（用于Server-Sent Events）
class StreamChunk(BaseModel):
    content: str
    is_final: bool = False
    conversation_id: Optional[int] = None
```

### **2.3 `config.py` - 配置相关模型**
```python
from pydantic import BaseModel, Field, validator
from typing import Optional

# 模型配置请求
class ModelConfigRequest(BaseModel):
    model_name: str = Field(..., description="模型名称")
    is_enabled: bool = Field(True, description="是否启用")
    api_key: Optional[str] = Field(None, description="API密钥")
    custom_endpoint: Optional[str] = Field(None, description="自定义API端点")
    temperature: float = Field(0.7, ge=0.0, le=2.0, 
                              description="温度参数，0.0-2.0")
    max_tokens: int = Field(2000, ge=1, le=16000, 
                           description="最大token数")

# 系统模型信息
class SystemModelInfo(BaseModel):
    model_id: int
    model_name: str
    model_provider: str
    api_endpoint: str
    is_available: bool
    is_default: bool
    max_tokens: int
    description: Optional[str]

# 用户配置响应
class UserConfigResponse(BaseModel):
    config_id: int
    model_name: str
    is_enabled: bool
    last_used_at: Optional[str]
    created_at: str
```

### **2.4 `response.py` - 通用响应模型**
```python
from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar
from enum import Enum

# 响应状态码枚举
class ResponseCode(int, Enum):
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

# 通用响应模型
class BaseResponse(BaseModel):
    code: int = Field(ResponseCode.SUCCESS, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[Any] = Field(None, description="响应数据")

# 成功响应
class SuccessResponse(BaseResponse):
    code: int = ResponseCode.SUCCESS
    message: str = "success"

# 错误响应
class ErrorResponse(BaseResponse):
    code: int = ResponseCode.BAD_REQUEST
    message: str = "error"
    error_detail: Optional[str] = Field(None, description="错误详情")

# 分页参数
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页大小，1-100")

# 带分页的响应
class PaginatedResponse(BaseResponse):
    data: Any = None
    pagination: dict = Field(default_factory=lambda: {
        "page": 1,
        "page_size": 20,
        "total": 0,
        "total_pages": 0
    })
```

## **3. 在路由中的使用示例**

### **3.1 基本使用**
```python
from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserResponse, TokenResponse
from app.schemas.response import SuccessResponse

router = APIRouter()

# POST请求：自动验证请求体
@router.post("/register", response_model=SuccessResponse)
async def register(user: UserCreate):
    # user已通过验证，可以直接使用
    # FastAPI会自动将返回值转换为SuccessResponse格式
    return SuccessResponse(data={"user_id": 1})

# 带响应模型的GET请求
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    # 自动序列化User对象为UserResponse
    return user_obj

# 多个响应模型
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    # 返回TokenResponse格式的数据
    return {"access_token": "xxx", "token_type": "bearer"}
```

### **3.2 嵌套响应**
```python
from app.schemas.chat import ConversationResponse, MessageResponse

@router.get("/conversations/{conversation_id}", 
            response_model=ConversationResponse)
async def get_conversation(conversation_id: int):
    # 返回的数据会自动按照嵌套模型序列化
    return {
        "conversation_id": 1,
        "title": "对话标题",
        "messages": [
            {"message_id": 1, "role": "user", "content": "你好"}
        ]
    }
```

## **4. FastAPI自动文档效果**

基于这些schema定义，FastAPI会自动生成：

### **4.1 Swagger UI界面**
- **参数验证规则**: 显示每个字段的验证要求（长度、格式等）
- **示例值**: 显示示例请求数据
- **响应模型**: 显示返回的数据结构
- **枚举值**: 显示所有可能的枚举选项

### **4.2 交互式API测试**
- **尝试功能**: 可以直接在浏览器中发送请求
- **自动填充**: 使用schema中的示例值自动填充表单
- **响应预览**: 直接查看响应的结构和数据

## **5. 最佳实践建议**

### **5.1 模型分离原则**
- **请求模型**: 以`Request`或`Create`结尾，用于接收数据
- **响应模型**: 以`Response`结尾，用于返回数据
- **数据库模型**: 继承自`Base`，用于数据库操作

### **5.2 字段验证策略**
```python
# 使用Field进行详细配置
class ExampleModel(BaseModel):
    # 基础验证
    name: str = Field(..., min_length=1, max_length=100)
    
    # 正则验证
    username: str = Field(..., pattern="^[a-z0-9_]+$")
    
    # 数值范围验证
    age: int = Field(..., ge=0, le=150)
    
    # 默认值
    is_active: bool = Field(True)
    
    # 可选字段
    description: Optional[str] = Field(None)
    
    # 自定义验证器
    @validator('name')
    def name_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('必须包含空格')
        return v.title()
```

### **5.3 性能优化**
- **避免过度嵌套**: 深度嵌套会影响序列化性能
- **使用`orm_mode`**: 启用`from_attributes=True`以直接从ORM对象转换
- **选择性暴露**: 响应模型只包含前端需要的字段

## **6. 错误处理示例**

```python
from fastapi import HTTPException
from pydantic import ValidationError

# FastAPI会自动处理验证错误
@router.post("/test")
async def test_endpoint(data: UserCreate):
    try:
        # 数据已自动验证
        return {"message": "成功"}
    except ValidationError as e:
        # 详细的错误信息会显示在API文档中
        raise HTTPException(
            status_code=422,
            detail={
                "errors": e.errors(),
                "body": e.json()
            }
        )
```

通过这种设计，你的API将拥有：
1. **完整的自动验证**
2. **清晰的接口文档**
3. **一致的数据格式**
4. **强大的类型提示**
5. **优秀的开发体验**

这种模式使得前后端协作更加顺畅，API维护更加容易。
