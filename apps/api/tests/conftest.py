import asyncio
import os
import uuid
from typing import AsyncGenerator, Dict, Generator
from pathlib import Path

# 设置环境变量，指向测试环境
# 必须在导入应用之前设置
os.environ["ENVIRONMENT"] = "test"
# ENV_FILE不需要明确设置，config.py会根据ENVIRONMENT自动选择

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import select

# 修正导入路径
from app.main import app
from app.api.deps import get_db
from app.core.config import settings
from app.models.user import User
from app.core.security import get_password_hash, create_access_token

# 验证测试环境设置是否正确
assert settings.TESTING is True, "测试环境未正确加载，请检查环境变量设置"

# 使用环境变量中的数据库URL
# 设置poolclass=NullPool可以避免连接池共享导致的事务问题
from sqlalchemy.pool import NullPool
engine = create_async_engine(
    str(settings.DATABASE_URL), 
    echo=settings.DEBUG, 
    future=True,
    poolclass=NullPool  # 禁用连接池，确保每个测试会话使用独立连接
)

TestSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 我们使用pytest_asyncio代替pytest来提供异步事件循环
@pytest_asyncio.fixture(scope="session")
async def setup_database() -> AsyncGenerator[None, None]:
    """设置测试数据库"""
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)  # 先清空所有表
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # 清理数据库
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话"""
    async with TestSessionLocal() as session:
        yield session
        # 回滚所有更改
        await session.rollback()

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """提供测试客户端"""
    
    # 确保导入的是FastAPI应用实例
    from app.main import app as fastapi_app

    # 替换数据库依赖
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    # 创建并提供客户端
    async with AsyncClient(
        base_url="http://test",
        transport=ASGITransport(app=fastapi_app)
    ) as test_client:
        yield test_client
    
    # 清除依赖覆盖
    fastapi_app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session) -> User:
    """创建测试用户"""
    # 首先检查用户是否已存在
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    existing_user = result.scalars().first()
    
    if existing_user:
        return existing_user
    
    # 如果不存在则创建新用户
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def test_superuser(db_session) -> User:
    """创建测试超级用户"""
    # 首先检查超级用户是否已存在
    result = await db_session.execute(select(User).where(User.email == "admin@example.com"))
    existing_user = result.scalars().first()
    
    if existing_user:
        return existing_user
    
    # 如果不存在则创建新超级用户
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpassword"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def token_headers(test_user) -> Dict[str, str]:
    """获取带有测试用户令牌的认证头"""
    access_token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def superuser_token_headers(test_superuser) -> Dict[str, str]:
    """获取带有超级用户令牌的认证头"""
    access_token = create_access_token(subject=str(test_superuser.id))
    return {"Authorization": f"Bearer {access_token}"}

# 你可以在这里添加其他的 fixtures，比如数据库 session 的 fixture 等。 