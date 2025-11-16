from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import UserStorage
from app.schemas.user import UserCreate, UserResponse, UserLogin

# 创建认证相关路由
router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口
    - 检查用户名是否已存在
    - 创建新用户（密码明文存储，仅用于开发）
    """
    # 检查用户名是否已注册
    existing_user = db.query(UserStorage).filter(UserStorage.user == user_data.user).first()
    if existing_user:
        # 修改为 422 错误，并匹配 HTTPValidationError 格式
        raise HTTPException(status_code=422, detail=[{"loc": ["body", "user"], "msg": "用户名已存在", "type": "value_error"}])
    
    # 创建新用户实例
    new_user = UserStorage(
        user=user_data.user,
        password=user_data.password,  # 明文存储，仅开发使用
        deepseek_bool=user_data.deepseek_bool,
        deepseek_api=user_data.deepseek_api
    )
    
    # 保存到数据库
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口
    - 验证用户名和密码（开发阶段直接比较明文）
    - 返回登录结果和用户信息
    """
    # 查询用户
    user = db.query(UserStorage).filter(UserStorage.user == login_data.user).first()
    
    # 验证用户是否存在和密码是否正确（明文比较）
    if not user or user.password != login_data.password:
        # 修改为 422 错误，并匹配 HTTPValidationError 格式
        raise HTTPException(status_code=422, detail=[{"loc": ["body", "user"], "msg": "用户名或密码错误", "type": "value_error"}])
    
    # 修改成功响应为空，以匹配 OpenAPI
    return None

@router.get("/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    """根据用户名获取用户信息"""
    user = db.query(UserStorage).filter(UserStorage.user == username).first()
    if not user:
        # 修改为 422 错误，并匹配 HTTPValidationError 格式
        raise HTTPException(status_code=422, detail=[{"loc": ["path", "username"], "msg": "用户不存在", "type": "value_error"}])
    return user
