import pytest
from httpx import AsyncClient
from fastapi import status

# 标记所有测试为异步和API测试
pytestmark = [pytest.mark.asyncio, pytest.mark.api]

# --- 获取当前用户信息测试 ---

async def test_read_current_user(client: AsyncClient, token_headers):
    """测试获取当前用户信息"""
    response = await client.get("/api/v1/users/me", headers=token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data

async def test_read_current_user_unauthorized(client: AsyncClient):
    """测试未经授权访问当前用户信息"""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- 获取用户列表测试 ---

async def test_read_users_superuser(client: AsyncClient, superuser_token_headers):
    """测试超级用户获取用户列表"""
    response = await client.get("/api/v1/users/", headers=superuser_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # 至少包含测试用户和超级用户

async def test_read_users_normal_user(client: AsyncClient, token_headers):
    """测试普通用户获取用户列表，应该被拒绝"""
    response = await client.get("/api/v1/users/", headers=token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_read_users_unauthorized(client: AsyncClient):
    """测试未经授权获取用户列表"""
    response = await client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- 获取特定用户信息测试 ---

async def test_read_user_by_id_self(client: AsyncClient, token_headers, test_user):
    """测试获取自己的用户信息"""
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email

async def test_read_user_by_id_superuser(client: AsyncClient, superuser_token_headers, test_user):
    """测试超级用户获取其他用户信息"""
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=superuser_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_user.id)

async def test_read_user_by_id_other_user(client: AsyncClient, token_headers, test_superuser):
    """测试普通用户获取其他用户信息，应该被拒绝"""
    response = await client.get(f"/api/v1/users/{test_superuser.id}", headers=token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_read_user_not_found(client: AsyncClient, superuser_token_headers):
    """测试获取不存在的用户信息"""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/users/{non_existent_id}", headers=superuser_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND 