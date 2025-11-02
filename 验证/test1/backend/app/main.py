from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, conversation

# 初始化FastAPI应用
app = FastAPI(
    title="统一API管理平台后端",
    description="为用户提供统一的大模型API调用接口",
    version="1.0.0"
)

# # 配置CORS中间件（允许前端跨域访问）
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 生产环境应限制为具体域名
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 更严格的 CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 只允许明确的前端地址
    allow_credentials=False,  # 禁用 credentials
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# 包含认证相关路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
# 包含对话管理相关路由
app.include_router(conversation.router, prefix="/api/conversations", tags=["对话"])

@app.get("/")
def root():
    """根路径，返回欢迎信息"""
    return {"message": "欢迎使用统一API管理平台后端服务"}

@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "API Platform Backend"}
