import pytest
from datetime import datetime, timedelta, UTC
import time
from unittest.mock import patch, AsyncMock

from app.core.token_blacklist import add_to_blacklist, is_blacklisted
# 不再需要导入 jwt_cache_instance 进行清理

# 标记所有测试为单元测试
pytestmark = [pytest.mark.asyncio, pytest.mark.unit]

@pytest.fixture
def mock_jwt_cache():
    """Mock jwt_cache_instance"""
    cache_mock = AsyncMock()
    cache_mock.setex.return_value = True
    cache_mock.exists.return_value = False # 默认不存在
    with patch("app.core.token_blacklist.jwt_cache_instance", cache_mock):
         yield cache_mock

async def test_add_valid_token(mock_jwt_cache):
    """测试添加有效令牌到黑名单"""
    token_jti = "valid-jti-1"
    expires = timedelta(minutes=10)
    
    result = await add_to_blacklist(token_jti, expires)
    
    assert result is True
    mock_jwt_cache.setex.assert_called_once_with(
        token_jti, int(expires.total_seconds()), "1"
    )

async def test_add_expired_token(mock_jwt_cache):
    """测试尝试添加已过期令牌 (应跳过并返回True)"""
    token_jti = "expired-jti"
    expires = timedelta(minutes=-10) # 已过期

    result = await add_to_blacklist(token_jti, expires)

    assert result is True # 视为成功，因为它已经无效
    mock_jwt_cache.setex.assert_not_called() # 不应调用 setex

async def test_add_token_redis_error(mock_jwt_cache):
    """测试添加令牌时Redis出错"""
    token_jti = "error-jti"
    expires = timedelta(minutes=10)
    mock_jwt_cache.setex.side_effect = Exception("Redis connection error")

    result = await add_to_blacklist(token_jti, expires)

    assert result is False # 添加失败

async def test_is_blacklisted_false(mock_jwt_cache):
    """测试令牌不在黑名单中"""
    token_jti = "not-blacklisted-jti"
    mock_jwt_cache.exists.return_value = False # 模拟 Redis 返回不存在

    result = await is_blacklisted(token_jti)

    assert result is False
    mock_jwt_cache.exists.assert_called_once_with(token_jti)

async def test_is_blacklisted_true(mock_jwt_cache):
    """测试令牌在黑名单中"""
    token_jti = "is-blacklisted-jti"
    mock_jwt_cache.exists.return_value = True # 模拟 Redis 返回存在

    result = await is_blacklisted(token_jti)

    assert result is True
    mock_jwt_cache.exists.assert_called_once_with(token_jti)

async def test_is_blacklisted_redis_error(mock_jwt_cache):
    """测试检查黑名单时Redis出错 (应返回True)"""
    token_jti = "check-error-jti"
    mock_jwt_cache.exists.side_effect = Exception("Redis connection error")

    result = await is_blacklisted(token_jti)

    assert result is True # 出错时视为在黑名单中 