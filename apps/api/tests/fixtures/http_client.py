"""
HTTP客户端相关的测试fixtures。

提供用于发送HTTP请求的测试客户端。
"""

from typing import AsyncGenerator

import pytest_asyncio
import pytest # 导入 pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis_async # 导入 redis

from app.main import app as fastapi_app
from app.api.deps import get_db
# 不再需要导入 get_redis_client
# from app.core.redis_cache import get_redis_client
from app.core import redis_cache # 导入 redis_cache 模块

# __init__.py 会处理导入 redis_client fixture

@pytest_asyncio.fixture(scope="function")
async def client(
    db_session: AsyncSession, 
    redis_client: redis_async.Redis | None, # 依赖注入 redis_client fixture
    monkeypatch: pytest.MonkeyPatch # 添加 monkeypatch fixture 依赖
) -> AsyncGenerator[AsyncClient, None]:
    """
    提供HTTP测试客户端。
    
    创建一个配置好的AsyncClient实例，用于发送HTTP请求到FastAPI应用。
    重写数据库依赖，并使用 monkeypatch 直接修改 RedisCache 实例以使用测试 Redis 连接。
    
    Args:
        db_session: 数据库会话fixture
        redis_client: 测试 Redis 客户端 fixture
        monkeypatch: Pytest monkeypatch fixture
        
    Yields:
        AsyncClient: 配置好的HTTP测试客户端
    """
    # 替换数据库依赖注入
    async def override_get_db():
        yield db_session

    # --- 修改：不再覆盖 get_redis_client，而是直接 patch 实例 ---
    if redis_client:
        # 使用 monkeypatch 替换 jwt_cache_instance 内部的 redis 客户端引用
        # raising=False 避免在属性不存在时出错 (虽然这里我们知道它存在)
        monkeypatch.setattr(redis_cache.jwt_cache_instance, "_redis", redis_client, raising=False)
        # 如果 API 缓存实例也用到，同样替换
        if hasattr(redis_cache, 'api_cache_instance'):
             monkeypatch.setattr(redis_cache.api_cache_instance, "_redis", redis_client, raising=False)
        print("\nPatched RedisCache instances with test client.") # 调试日志
    else:
        # 如果 redis_client 为 None (连接失败或禁用)，可以选择跳过测试或让应用按预期失败
        print("\nRedis client fixture returned None, not patching instances.")
        # pytest.skip("Redis client unavailable for testing.") 
    # -------------------------------------------------------------

    # 应用数据库依赖覆盖
    original_overrides = fastapi_app.dependency_overrides.copy() # 保存原始覆盖
    fastapi_app.dependency_overrides[get_db] = override_get_db
    # 移除 get_redis_client 的覆盖
    # fastapi_app.dependency_overrides[get_redis_client] = override_get_redis_client 
    
    # 创建并提供测试客户端
    async with AsyncClient(
        base_url="http://test",
        transport=ASGITransport(app=fastapi_app)
    ) as test_client:
        yield test_client
    
    # 清除依赖覆盖，恢复原始状态
    fastapi_app.dependency_overrides = original_overrides
    # Monkeypatch 会自动撤销更改，无需手动处理 