import pytest
from datetime import datetime, timedelta, UTC

from httpx import AsyncClient
from fastapi import status

# 标记所有测试为异步和认证测试
pytestmark = [pytest.mark.asyncio, pytest.mark.auth, pytest.mark.api]

# 移除无效导入
# from tests.utils.user import create_random_user_instance
# from tests.utils.auth import authenticate_user


async def test_logout_success(client: AsyncClient, test_user_token):
    """测试用户成功登出，并验证令牌失效"""
    # 移除对内存字典的检查
    # initial_blacklist_length = len(logout_tokens)
    
    token_header = {"Authorization": f"Bearer {test_user_token}"}
    
    # 1. 验证令牌在登出前是有效的 (可选但有帮助)
    response_before = await client.get("/api/v1/users/me", headers=token_header)
    assert response_before.status_code == status.HTTP_200_OK
    
    # 2. 执行登出
    response_logout = await client.post(
        "/api/v1/auth/logout",
        headers=token_header
    )
    
    # 验证登出响应状态码和内容
    assert response_logout.status_code == status.HTTP_200_OK
    data = response_logout.json()
    assert "detail" in data
    assert data["detail"] == "登出成功"
    
    # 移除对内存字典的检查
    # assert len(logout_tokens) > initial_blacklist_length
    
    # 3. 验证令牌在登出后是无效的
    response_after = await client.get("/api/v1/users/me", headers=token_header)
    assert response_after.status_code == status.HTTP_401_UNAUTHORIZED
    # 可以进一步检查错误详情，它应该提示令牌失效或需要认证
    error_data = response_after.json()
    assert "detail" in error_data
    # The detail might be 'Not authenticated', 'Token has expired', or 'Token is blacklisted' depending on the exact check order in deps.py
    # Checking for 401 is usually sufficient for API tests.


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
    assert "detail" in data # FastAPI/Starlette might return a default 401 detail


async def test_logout_missing_token(client: AsyncClient):
    """测试没有提供令牌的登出请求"""
    # 不提供Authorization头
    response = await client.post("/api/v1/auth/logout")
    
    # 验证响应状态码是401 Unauthorized (因为 get_current_user 依赖会失败)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_logout_wrong_token_type(client: AsyncClient, test_user_token):
    """测试使用错误令牌类型登出"""
    # 使用错误的令牌类型（不是Bearer）
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Basic {test_user_token}"}
    )
    
    # 验证响应状态码是401 Unauthorized
    # logout 接口本身不直接依赖 oauth2_scheme，所以它会处理请求
    # 但是解析 "Basic ..." 会失败，或者 decode_jwt_token 会失败
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data
    # 错误详情可能是 "无效的认证头" 或 "无效的令牌"


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
    # 修改断言以匹配 get_current_user 中抛出的实际错误信息
    # assert "无法验证凭据" in data["detail"] 
    # 使用 deps.py 中黑名单检查抛出的 InvalidTokenException 的 detail
    assert "认证令牌已失效 (已登出)" == data["detail"] 