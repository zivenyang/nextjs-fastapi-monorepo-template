"""
用户相关的测试fixtures。

提供测试用户和超级用户实例，用于测试需要认证的API端点。
"""

import uuid
from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import get_password_hash

# 测试数据常量 - 普通用户
TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "testpassword"
}

# 测试数据常量 - 管理员用户
TEST_ADMIN = {
    "email": "admin@example.com",
    "username": "admin",
    "full_name": "Admin User",
    "password": "adminpassword"
}

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """
    创建测试用户。
    
    检查是否已存在测试用户，如果存在则返回现有用户，
    否则创建一个新的测试用户并返回。
    
    Args:
        db_session: 数据库会话fixture
        
    Returns:
        User: 测试用户实例
    """
    # 首先检查用户是否已存在
    result = await db_session.execute(select(User).where(User.email == TEST_USER["email"]))
    existing_user = result.scalars().first()
    
    if existing_user:
        return existing_user
    
    # 如果不存在则创建新用户
    user = User(
        id=uuid.uuid4(),
        email=TEST_USER["email"],
        username=TEST_USER["username"],
        full_name=TEST_USER["full_name"],
        hashed_password=get_password_hash(TEST_USER["password"]),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def test_superuser(db_session: AsyncSession) -> User:
    """
    创建测试超级用户。
    
    检查是否已存在测试超级用户，如果存在则返回现有用户，
    否则创建一个新的测试超级用户并返回。
    
    Args:
        db_session: 数据库会话fixture
        
    Returns:
        User: 测试超级用户实例
    """
    # 首先检查超级用户是否已存在
    result = await db_session.execute(select(User).where(User.email == TEST_ADMIN["email"]))
    existing_user = result.scalars().first()
    
    if existing_user:
        return existing_user
    
    # 如果不存在则创建新超级用户
    user = User(
        id=uuid.uuid4(),
        email=TEST_ADMIN["email"],
        username=TEST_ADMIN["username"],
        full_name=TEST_ADMIN["full_name"],
        hashed_password=get_password_hash(TEST_ADMIN["password"]),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user 