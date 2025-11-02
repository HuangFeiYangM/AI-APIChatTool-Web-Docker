import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# 获取父目录路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# 导入应用和数据库相关
from app.main import app
from app.database import Base, get_db
from app.config import settings

# 使用SQLite内存数据库进行测试
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建所有表
Base.metadata.create_all(bind=engine)

def override_get_db():
    """覆盖依赖项，使用测试数据库"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# 应用依赖覆盖
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# 测试数据
TEST_USER = "testuser"
TEST_PASSWORD = "testpassword"
TEST_CONVERSATION_ID = 1
TEST_PART_ID = 1
TEST_MARKDOWN = "## Test Conversation\nThis is a test."

@pytest.fixture(autouse=True)
def cleanup_db():
    """每个测试后清理数据库，确保测试隔离"""
    db = TestingSessionLocal()
    try:
        # 删除所有数据，但保留表结构
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()

# 健康检查测试
def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "API Platform Backend"}

# 根路径测试
def test_root():
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "欢迎使用统一API管理平台后端服务"}

# 认证API测试
def test_register_success():
    """测试用户注册成功"""
    response = client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"] == TEST_USER
    assert "created_at" in data

def test_register_user_exists():
    """测试注册时用户名已存在"""
    # 先注册用户
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    # 尝试重复注册
    response = client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": "anotherpassword",
        "deepseek_bool": True,
        "deepseek_api": "sk-123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "用户名已存在"

def test_login_success():
    """测试用户登录成功"""
    # 先注册用户
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    # 登录
    response = client.post("/api/auth/login", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "登录成功"
    assert data["user"] == TEST_USER

def test_login_invalid_credentials():
    """测试登录时用户名或密码错误"""
    response = client.post("/api/auth/login", json={
        "user": "nonexistent",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"

def test_get_user_success():
    """测试获取用户信息成功"""
    # 先注册用户
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    response = client.get(f"/api/auth/{TEST_USER}")
    assert response.status_code == 200
    data = response.json()
    assert data["user"] == TEST_USER

def test_get_user_not_found():
    """测试获取不存在的用户信息"""
    response = client.get("/api/auth/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "用户不存在"

# 对话API测试
def test_get_user_conversations_success():
    """测试获取用户对话列表成功"""
    # 先注册用户并创建对话
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": TEST_PART_ID,
        "user": TEST_USER,
        "markdown": TEST_MARKDOWN
    })
    response = client.get("/api/conversations/", params={"user": TEST_USER})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id_conversation"] == TEST_CONVERSATION_ID

def test_get_user_conversations_user_not_found():
    """测试获取对话时用户不存在"""
    response = client.get("/api/conversations/", params={"user": "nonexistent"})
    assert response.status_code == 404
    assert response.json()["detail"] == "用户不存在"

def test_create_conversation_success():
    """测试创建对话成功"""
    # 先注册用户
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    response = client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": TEST_PART_ID,
        "user": TEST_USER,
        "markdown": TEST_MARKDOWN
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id_conversation"] == TEST_CONVERSATION_ID
    assert data["markdown"] == TEST_MARKDOWN

def test_create_conversation_user_not_found():
    """测试创建对话时用户不存在"""
    response = client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": TEST_PART_ID,
        "user": "nonexistent",
        "markdown": TEST_MARKDOWN
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "用户不存在"

def test_create_conversation_already_exists():
    """测试创建已存在的对话"""
    # 先注册用户并创建对话
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": TEST_PART_ID,
        "user": TEST_USER,
        "markdown": TEST_MARKDOWN
    })
    # 尝试重复创建
    response = client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": TEST_PART_ID,
        "user": TEST_USER,
        "markdown": "Different content"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "对话已存在"

def test_get_conversation_success():
    """测试获取特定对话成功"""
    # 先注册用户并创建对话
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": TEST_PART_ID,
        "user": TEST_USER,
        "markdown": TEST_MARKDOWN
    })
    response = client.get(f"/api/conversations/{TEST_CONVERSATION_ID}/{TEST_PART_ID}", params={"user": TEST_USER})
    assert response.status_code == 200
    data = response.json()
    assert data["id_conversation"] == TEST_CONVERSATION_ID
    assert data["markdown"] == TEST_MARKDOWN

def test_get_conversation_not_found():
    """测试获取不存在的对话"""
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    response = client.get("/api/conversations/999/1", params={"user": TEST_USER})
    assert response.status_code == 404
    assert response.json()["detail"] == "对话不存在"

def test_update_conversation_success():
    """测试更新对话成功"""
    # 先注册用户并创建对话
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": TEST_PART_ID,
        "user": TEST_USER,
        "markdown": TEST_MARKDOWN
    })
    updated_markdown = "## Updated Content\nThis is updated."
    response = client.put(
        f"/api/conversations/{TEST_CONVERSATION_ID}/{TEST_PART_ID}",
        params={"user": TEST_USER},
        json={"markdown": updated_markdown}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["markdown"] == updated_markdown

def test_update_conversation_not_found():
    """测试更新不存在的对话"""
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    response = client.put(
        "/api/conversations/999/1",
        params={"user": TEST_USER},
        json={"markdown": "New content"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "对话不存在"

def test_delete_conversation_success():
    """测试删除对话成功"""
    # 先注册用户并创建对话
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": TEST_PART_ID,
        "user": TEST_USER,
        "markdown": TEST_MARKDOWN
    })
    response = client.delete(
        f"/api/conversations/{TEST_CONVERSATION_ID}/{TEST_PART_ID}",
        params={"user": TEST_USER}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "对话删除成功"

def test_delete_conversation_not_found():
    """测试删除不存在的对话"""
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    response = client.delete("/api/conversations/999/1", params={"user": TEST_USER})
    assert response.status_code == 404
    assert response.json()["detail"] == "对话不存在"

def test_get_conversation_parts_success():
    """测试获取对话所有部分成功"""
    # 先注册用户并创建多个对话部分
    client.post("/api/auth/register", json={
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "deepseek_bool": False,
        "deepseek_api": None
    })
    client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": 1,
        "user": TEST_USER,
        "markdown": "Part 1"
    })
    client.post("/api/conversations/", json={
        "id_conversation": TEST_CONVERSATION_ID,
        "id_part": 2,
        "user": TEST_USER,
        "markdown": "Part 2"
    })
    response = client.get(f"/api/conversations/{TEST_CONVERSATION_ID}/parts", params={"user": TEST_USER})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(part["id_conversation"] == TEST_CONVERSATION_ID for part in data)

def test_get_conversation_parts_user_not_found():
    """测试获取对话部分时用户不存在"""
    response = client.get("/api/conversations/1/parts", params={"user": "nonexistent"})
    assert response.status_code == 404
    assert response.json()["detail"] == "用户不存在"
