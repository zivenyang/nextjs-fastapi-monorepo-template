import pytest
from httpx import AsyncClient
from fastapi import status

from app.core.token_blacklist import logout_tokens

# 标记所有测试为异步和认证测试
pytestmark = [pytest.mark.asyncio, pytest.mark.auth, pytest.mark.api]


async def test_logout_success(client: AsyncClient, test_user_token):
    """测试用户成功登出"""
    # 先记录下当前黑名单长度
    initial_blacklist_length = len(logout_tokens)
    
    # 使用获取的令牌执行登出
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    # 验证响应状态码和内容
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "登出成功"
    
    # 验证黑名单长度增加了
    assert len(logout_tokens) > initial_blacklist_length


async def test_logout_invalid_token(client: AsyncClient):
    """测试使用无效令牌登出"""
    # 使用无效令牌
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer invalid.token.format"}
    )
    
    # 验证响应状态码是401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data


async def test_logout_missing_token(client: AsyncClient):
    """测试没有提供令牌的登出请求"""
    # 不提供Authorization头
    response = await client.post("/api/v1/auth/logout")
    
    # 验证响应状态码是401或422
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]


async def test_logout_wrong_token_type(client: AsyncClient, test_user_token):
    """测试使用错误令牌类型登出"""
    # 使用错误的令牌类型（不是Bearer）
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Basic {test_user_token}"}
    )
    
    # 验证响应状态码是401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    # FastAPI的OAuth2认证中间件会自动返回"Not authenticated"错误
    assert "detail" in data
    assert data["detail"] == "Not authenticated"


async def test_logout_twice(client: AsyncClient, test_user_token):
    """测试用户进行两次登出"""
    # 第一次登出
    await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    # 第二次使用相同令牌登出
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    # 验证响应状态码是401 Unauthorized（因为令牌已被注销）
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data
    assert "已失效" in data["detail"] or "无效" in data["detail"] 