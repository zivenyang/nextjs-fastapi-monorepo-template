import pytest
from sqlmodel import select

from app.models.user import User, UserRole

# 标记所有测试为异步和数据库测试
pytestmark = [pytest.mark.asyncio, pytest.mark.db, pytest.mark.unit]

async def test_create_user(db_session):
    """测试创建用户"""
    # 创建新用户
    new_user = User(
        email="dbtest@example.com",
        username="dbtest",
        full_name="DB Test User",
        hashed_password="hashed_password",
        role=UserRole.USER
    )
    
    # 添加到数据库
    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)
    
    # 验证用户已创建并有ID
    assert new_user.id is not None
    assert new_user.email == "dbtest@example.com"
    
    # 从数据库查询验证
    query = select(User).where(User.email == "dbtest@example.com")
    result = await db_session.execute(query)
    db_user = result.scalar_one()
    
    assert db_user.id == new_user.id
    assert db_user.username == "dbtest"
    assert db_user.is_active == True
    assert db_user.is_superuser == False

async def test_user_role_enum(db_session):
    """测试用户角色枚举"""
    # 创建管理员用户
    admin_user = User(
        email="admin@dbtest.com",
        username="admintest",
        hashed_password="hashed_password",
        role=UserRole.ADMIN
    )
    
    # 创建访客用户
    guest_user = User(
        email="guest@dbtest.com",
        username="guesttest",
        hashed_password="hashed_password",
        role=UserRole.GUEST
    )
    
    # 添加到数据库
    db_session.add(admin_user)
    db_session.add(guest_user)
    await db_session.commit()
    
    # 查询并验证角色
    query = select(User).where(User.email == "admin@dbtest.com")
    result = await db_session.execute(query)
    db_admin = result.scalar_one()
    assert db_admin.role == UserRole.ADMIN
    
    query = select(User).where(User.email == "guest@dbtest.com")
    result = await db_session.execute(query)
    db_guest = result.scalar_one()
    assert db_guest.role == UserRole.GUEST

async def test_timestamps(db_session):
    """测试时间戳字段"""
    # 创建用户
    user = User(
        email="timestamp@test.com",
        username="timetest",
        hashed_password="hashed_password"
    )
    
    # 添加到数据库
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 验证创建时间已设置
    assert user.created_at is not None
    # 更新时间应为None，因为刚创建
    assert user.updated_at is None
    
    # 记录创建时间
    creation_time = user.created_at
    
    # 更新用户
    user.username = "updated_timetest"
    await db_session.commit()
    await db_session.refresh(user)
    
    # 验证更新时间已设置且不同于创建时间
    assert user.updated_at is not None
    assert user.created_at == creation_time  # 创建时间不变 