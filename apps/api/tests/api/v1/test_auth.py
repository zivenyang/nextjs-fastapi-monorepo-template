import pytest
from httpx import AsyncClient
from fastapi import status

# 标记所有测试为异步和认证测试
pytestmark = [pytest.mark.asyncio, pytest.mark.auth, pytest.mark.api]

# 假设我们的 FastAPI 应用实例在 apps.api.app.main.py 中定义为 `app`
# 我们需要一种方法来在测试中访问它，通常通过 conftest.py 设置
# 这里我们先假设可以通过某种方式获取到 app

# --- 注册测试 ---

async def test_register_success(client: AsyncClient):
    """测试用户成功注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com", 
            "password": "password123",
            "username": "newuser",
            "full_name": "New User"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data

async def test_register_existing_email(client: AsyncClient, test_user):
    """测试使用已存在的邮箱注册"""
    # 尝试使用已存在的测试用户邮箱注册
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "anotherpassword",
            "username": "another",
            "full_name": "Another User"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "已被注册" in data["detail"]

async def test_register_invalid_email(client: AsyncClient):
    """测试使用无效邮箱注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "notanemail",
            "password": "password123",
            "username": "invaliduser",
            "full_name": "Invalid User"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_register_weak_password(client: AsyncClient):
    """测试使用弱密码注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weakpass@example.com",
            "password": "123", # 低于最小长度要求
            "username": "weakuser",
            "full_name": "Weak User"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# --- 登录测试 ---

async def test_login_success(client: AsyncClient):
    """测试用户成功登录并获取令牌"""
    # 先注册一个新用户
    register_payload = {
        "email": "login@example.com", 
        "password": "password123",
        "username": "loginuser",
        "full_name": "Login User"
    }
    await client.post("/api/v1/auth/register", json=register_payload)

    # 登录
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "password123"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_login_with_existing_user(client: AsyncClient, test_user):
    """测试使用预设的测试用户登录"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data

async def test_login_incorrect_password(client: AsyncClient, test_user):
    """测试使用错误密码登录"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data

async def test_login_nonexistent_email(client: AsyncClient):
    """测试使用不存在的邮箱登录"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# 注意：这些测试现在会失败，因为对应的 API 还没有实现。
# 我们还需要设置一个 pytest fixture `client` 来提供 AsyncClient 实例。
# 这通常在 tests/conftest.py 文件中完成。 