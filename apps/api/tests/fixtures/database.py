"""
数据库相关的测试fixtures。

提供数据库初始化、会话创建和清理的fixtures。
"""

import os
from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

# 确保测试环境变量设置
os.environ["ENVIRONMENT"] = "test"

from app.core.config import settings

# 验证测试环境设置
assert settings.TESTING is True, "测试环境未正确加载，请检查环境变量设置"

# 创建异步数据库引擎
engine = create_async_engine(
    str(settings.DATABASE_URL), 
    echo=settings.DEBUG, 
    future=True,
    poolclass=NullPool  # 禁用连接池，确保每个测试会话使用独立连接
)

# 创建会话工厂
TestSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest_asyncio.fixture(scope="session")
async def setup_database() -> AsyncGenerator[None, None]:
    """
    设置测试数据库。
    
    在测试会话开始前创建所有表，会话结束后清理数据库。
    使用session作用域确保在所有测试之前只执行一次。
    """
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
    """
    提供数据库会话。
    
    为每个测试函数提供独立的数据库会话，测试结束后自动回滚更改。
    使用function作用域确保每个测试获得一个新的会话实例。
    """
    async with TestSessionLocal() as session:
        yield session
        # 回滚所有更改
        await session.rollback() 