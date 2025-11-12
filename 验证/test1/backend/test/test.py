import sys
import os

# 添加父目录到Python路径 - 必须在所有导入之前
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models.user import UserStorage
from app.models.conversation import ConversationStorage
# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用测试数据库（与开发数据库相同，但测试后会清理数据）
TEST_DATABASE_URL = "mysql+pymysql://root:rootpassword@localhost:32768/test_db"

# 创建测试数据库引擎和会话
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 覆盖依赖项以使用测试数据库
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# 测试前置和后置处理
@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    # 每个测试前清空表（确保测试隔离）
    db = TestingSessionLocal()
    db.query(ConversationStorage).delete()
    db.query(UserStorage).delete()
    db.commit()
    db.close()
    yield
    # 测试后无需额外清理，因为每个测试前已清空

# 测试根路径和健康检查
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "欢迎使用统一API管理平台后端服务"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "API Platform Backend"}

# 认证相关测试
def test_register_user():
    user_data = {
        "user": "testuser",
        "password": "testpass",
        "deepseek_bool": True,
        "deepseek_api": "sk-test123"
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["user"] == "testuser"
    assert data["deepseek_bool"] == True
    assert data["deepseek_api"] == "sk-test123"

def test_register_duplicate_user():
    # 先注册用户
    user_data = {"user": "duplicate", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    # 尝试重复注册
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "用户名已存在"

def test_login_user():
    # 先注册用户
    user_data = {"user": "loginuser", "password": "loginpass"}
    client.post("/api/auth/register", json=user_data)
    # 登录测试
    login_data = {"user": "loginuser", "password": "loginpass"}
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "登录成功"
    assert data["user"] == "loginuser"

def test_login_invalid_user():
    login_data = {"user": "nonexistent", "password": "pass"}
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"

def test_get_user():
    # 先注册用户
    user_data = {"user": "getuser", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    # 获取用户信息
    response = client.get("/api/auth/getuser")
    assert response.status_code == 200
    data = response.json()
    assert data["user"] == "getuser"

def test_get_nonexistent_user():
    response = client.get("/api/auth/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "用户不存在"

# 对话管理相关测试
def test_create_conversation():
    # 先注册用户
    user_data = {"user": "convuser", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    # 创建对话
    conv_data = {
        "id_conversation": 1,
        "id_part": 1,
        "user": "convuser",
        "markdown": "Test conversation content"
    }
    response = client.post("/api/conversations/", json=conv_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id_conversation"] == 1
    assert data["id_part"] == 1
    assert data["user"] == "convuser"
    assert data["markdown"] == "Test conversation content"

def test_create_duplicate_conversation():
    # 先注册用户和创建对话
    user_data = {"user": "dupconv", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    conv_data = {"id_conversation": 1, "id_part": 1, "user": "dupconv"}
    client.post("/api/conversations/", json=conv_data)
    # 尝试重复创建
    response = client.post("/api/conversations/", json=conv_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "对话已存在"

def test_create_conversation_nonexistent_user():
    conv_data = {"id_conversation": 1, "id_part": 1, "user": "nouser"}
    response = client.post("/api/conversations/", json=conv_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "用户不存在"

def test_get_user_conversations():
    # 注册用户并创建对话
    user_data = {"user": "getconvuser", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    conv_data = {"id_conversation": 1, "id_part": 1, "user": "getconvuser"}
    client.post("/api/conversations/", json=conv_data)
    # 获取用户对话
    response = client.get("/api/conversations/", params={"user": "getconvuser"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user"] == "getconvuser"

def test_get_conversations_nonexistent_user():
    response = client.get("/api/conversations/", params={"user": "nouser"})
    assert response.status_code == 404
    assert response.json()["detail"] == "用户不存在"

def test_get_specific_conversation():
    # 注册用户并创建对话
    user_data = {"user": "specificuser", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    conv_data = {"id_conversation": 1, "id_part": 1, "user": "specificuser"}
    client.post("/api/conversations/", json=conv_data)
    # 获取特定对话
    response = client.get("/api/conversations/1/1", params={"user": "specificuser"})
    assert response.status_code == 200
    data = response.json()
    assert data["id_conversation"] == 1
    assert data["id_part"] == 1

def test_get_nonexistent_conversation():
    # 先注册用户
    user_data = {"user": "noconvuser", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    response = client.get("/api/conversations/999/999", params={"user": "noconvuser"})
    assert response.status_code == 404
    assert response.json()["detail"] == "对话不存在"

def test_update_conversation():
    # 注册用户并创建对话
    user_data = {"user": "updateuser", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    conv_data = {"id_conversation": 1, "id_part": 1, "user": "updateuser"}
    client.post("/api/conversations/", json=conv_data)
    # 更新对话
    update_data = {"markdown": "Updated content"}
    response = client.put("/api/conversations/1/1", params={"user": "updateuser"}, json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["markdown"] == "Updated content"

def test_update_nonexistent_conversation():
    user_data = {"user": "updatenone", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    update_data = {"markdown": "New content"}
    response = client.put("/api/conversations/1/1", params={"user": "updatenone"}, json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "对话不存在"

def test_delete_conversation():
    # 注册用户并创建对话
    user_data = {"user": "deleteuser", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    conv_data = {"id_conversation": 1, "id_part": 1, "user": "deleteuser"}
    client.post("/api/conversations/", json=conv_data)
    # 删除对话
    response = client.delete("/api/conversations/1/1", params={"user": "deleteuser"})
    assert response.status_code == 200
    assert response.json()["message"] == "对话删除成功"
    # 验证对话已删除
    get_response = client.get("/api/conversations/1/1", params={"user": "deleteuser"})
    assert get_response.status_code == 404

def test_delete_nonexistent_conversation():
    user_data = {"user": "deletenone", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    response = client.delete("/api/conversations/1/1", params={"user": "deletenone"})
    assert response.status_code == 404
    assert response.json()["detail"] == "对话不存在"

def test_get_conversation_parts():
    # 注册用户并创建多个对话部分
    user_data = {"user": "partsuser", "password": "pass"}
    client.post("/api/auth/register", json=user_data)
    conv_data1 = {"id_conversation": 1, "id_part": 1, "user": "partsuser"}
    conv_data2 = {"id_conversation": 1, "id_part": 2, "user": "partsuser"}
    client.post("/api/conversations/", json=conv_data1)
    client.post("/api/conversations/", json=conv_data2)
    # 获取对话所有部分
    response = client.get("/api/conversations/1/parts", params={"user": "partsuser"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(part["id_conversation"] == 1 for part in data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
