# apps/api/tests/fixtures/redis.py
import pytest_asyncio
import redis.asyncio as redis_async
from app.core.config import settings # 导入应用配置

@pytest_asyncio.fixture(scope="function") # function scope 保证每个测试都有新连接
async def redis_client() -> redis_async.Redis | None:
    """
    提供一个连接到测试 Redis 的客户端，并在测试结束后关闭连接。
    """
    if not settings.REDIS_ENABLED:
         yield None # 如果 Redis 未启用，则不提供客户端
         return

    client = None
    try:
        client = redis_async.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            # 重要：测试时可能需要使用不同的 DB，避免污染开发/生产数据
            db=settings.REDIS_DB + 1 if settings.REDIS_DB is not None else 1, 
            password=settings.REDIS_PASSWORD or None,
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        await client.ping() # 确认连接
        print("\nConnected to Test Redis DB") # 添加日志，方便调试
        yield client # 提供给测试使用
    except Exception as e:
         # 如果连接失败，可以抛出异常或返回 None，取决于你希望测试如何处理
         print(f"\n测试 Redis 连接失败: {e}")
         yield None # 或者 pytest.skip("Redis 连接失败")
    finally:
        if client:
            try:
                # 在 redis-py 4.2+ 中，aclose() 是推荐的，用于关闭连接池
                await client.aclose() 
                # print("Test Redis Client Closed.") # 添加日志
            except Exception as close_e:
                print(f"\n关闭测试 Redis 客户端时出错: {close_e}") 