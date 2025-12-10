# app/api/v1/router.py
"""
API v1 主路由注册
"""
from fastapi import APIRouter
from app.api.v1 import auth, health, models,conversations, admin   # 导入其他模块 # 新增 models # 新增 conversations# 新增 admin

router = APIRouter()

# 注册子路由
router.include_router(auth.router)
router.include_router(health.router)
router.include_router(models.router)  # 新增这行
router.include_router(conversations.router) # 新增这行
router.include_router(admin.router)  # 新增这行


# 后续添加其他模块...
# router.include_router(users.router)
# router.include_router(conversations.router)
# router.include_router(models.router)
