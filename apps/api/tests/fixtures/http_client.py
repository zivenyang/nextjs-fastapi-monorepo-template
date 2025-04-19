"""
HTTP客户端相关的测试fixtures。

提供用于发送HTTP请求的测试客户端。
"""

from typing import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app as fastapi_app
from app.api.deps import get_db

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    提供HTTP测试客户端。
    
    创建一个配置好的AsyncClient实例，用于发送HTTP请求到FastAPI应用。
    重写数据库依赖，使其使用测试会话而不是真实数据库连接。
    
    Args:
        db_session: 数据库会话fixture
        
    Yields:
        AsyncClient: 配置好的HTTP测试客户端
    """
    # 替换数据库依赖注入
    async def override_get_db():
        yield db_session

    # 应用依赖覆盖
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    # 创建并提供测试客户端
    async with AsyncClient(
        base_url="http://test",
        transport=ASGITransport(app=fastapi_app)
    ) as test_client:
        yield test_client
    
    # 清除依赖覆盖
    fastapi_app.dependency_overrides.clear() 