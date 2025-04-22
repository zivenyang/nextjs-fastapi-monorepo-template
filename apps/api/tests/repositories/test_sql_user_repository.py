import pytest
from unittest.mock import AsyncMock, MagicMock # 导入 Mock 工具
from uuid import uuid4
from typing import List

from sqlmodel.ext.asyncio.session import AsyncSession # 导入类型

from app.repositories.sql.user_repository import SQLUserRepository
from app.models.user import User, UserProfile

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

# --- Fixture for Mock Session (与 test_user_service.py 类似) ---
@pytest.fixture
def mock_db_session() -> MagicMock:
    session = MagicMock(spec=AsyncSession)
    # get 是一个协程
    session.get = AsyncMock()
    # execute 是一个协程
    mock_execute = AsyncMock()
    session.execute = mock_execute
    # execute await 后的结果是一个 *同步* MagicMock
    mock_result = MagicMock()
    # 这个 mock_result 有 *同步* 方法 scalar_one_or_none 和 scalars().all()
    mock_result.scalar_one_or_none = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all = MagicMock()
    mock_result.scalars.return_value = mock_scalars # scalars() 返回 mock_scalars
    mock_execute.return_value = mock_result # execute await 后返回 mock_result

    # add 是同步调用
    session.add = MagicMock()

    return session

# --- Unit Tests for SQLUserRepository ---

async def test_get_by_id_found(mock_db_session: MagicMock):
    """测试 get_by_id 找到用户"""
    test_id = uuid4()
    expected_user = User(id=test_id, email="found@example.com", hashed_password="hash")

    # 配置 mock session 的 get() 方法返回值
    mock_db_session.get.return_value = expected_user

    repository = SQLUserRepository(session=mock_db_session)
    found_user = await repository.get_by_id(user_id=test_id)

    assert found_user == expected_user
    # 确认 session.get 被正确调用
    mock_db_session.get.assert_awaited_once_with(User, test_id)
    # 确认 execute 没有被调用 (因为我们用了 get)
    mock_db_session.execute.assert_not_awaited()

async def test_get_by_id_not_found(mock_db_session: MagicMock):
    """测试 get_by_id 未找到用户"""
    test_id = uuid4()
    # 配置 mock session 的 get() 方法返回值 为 None
    mock_db_session.get.return_value = None

    repository = SQLUserRepository(session=mock_db_session)
    found_user = await repository.get_by_id(user_id=test_id)

    assert found_user is None
    mock_db_session.get.assert_awaited_once_with(User, test_id)
    mock_db_session.execute.assert_not_awaited()

# 接下来添加 get_by_email, list_users, create 等方法的测试...

async def test_get_by_email_found(mock_db_session: MagicMock):
    """测试 get_by_email 找到用户"""
    test_email = "found@example.com"
    expected_user = User(id=uuid4(), email=test_email, hashed_password="hashed")
    # 配置 mock_result 的 scalar_one_or_none() 同步方法的返回值
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = expected_user

    repository = SQLUserRepository(session=mock_db_session)
    found_user = await repository.get_by_email(email=test_email)

    assert found_user == expected_user
    mock_db_session.execute.assert_awaited_once() # 确认 execute 被调用
    # 确认结果处理方法被调用
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()
    mock_db_session.get.assert_not_awaited() # 确认 get 没被调用

async def test_get_by_email_not_found(mock_db_session: MagicMock):
    """测试 get_by_email 未找到用户"""
    test_email = "notfound@example.com"
    # 配置 mock_result 的 scalar_one_or_none() 返回 None
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    repository = SQLUserRepository(session=mock_db_session)
    found_user = await repository.get_by_email(email=test_email)

    assert found_user is None
    mock_db_session.execute.assert_awaited_once()
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()
    mock_db_session.get.assert_not_awaited()

async def test_get_profile_by_user_id_found(mock_db_session: MagicMock):
    """测试 get_profile_by_user_id 找到资料"""
    user_id = uuid4()
    expected_profile = UserProfile(id=uuid4(), user_id=user_id, bio="Test Bio")
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = expected_profile

    repository = SQLUserRepository(session=mock_db_session)
    found_profile = await repository.get_profile_by_user_id(user_id=user_id)

    assert found_profile == expected_profile
    mock_db_session.execute.assert_awaited_once()
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()

async def test_get_profile_by_user_id_not_found(mock_db_session: MagicMock):
    """测试 get_profile_by_user_id 未找到资料"""
    user_id = uuid4()
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    repository = SQLUserRepository(session=mock_db_session)
    found_profile = await repository.get_profile_by_user_id(user_id=user_id)

    assert found_profile is None
    mock_db_session.execute.assert_awaited_once()
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()

async def test_list_users(mock_db_session: MagicMock):
    """测试 list_users"""
    expected_users = [
        User(id=uuid4(), email="user1@example.com", hashed_password="hash1"),
        User(id=uuid4(), email="user2@example.com", hashed_password="hash2"),
    ]
    # 配置 scalars().all() 的返回值
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = expected_users

    repository = SQLUserRepository(session=mock_db_session)
    users = await repository.list_users(skip=0, limit=10)

    assert users == expected_users
    mock_db_session.execute.assert_awaited_once() # 确认 execute 被调用
    # 确认结果处理方法链被调用
    mock_db_session.execute.return_value.scalars.assert_called_once()
    mock_db_session.execute.return_value.scalars.return_value.all.assert_called_once()

async def test_list_users_empty(mock_db_session: MagicMock):
    """测试 list_users 返回空列表"""
    # 配置 scalars().all() 的返回值为空列表
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = []

    repository = SQLUserRepository(session=mock_db_session)
    users = await repository.list_users(skip=0, limit=10)

    assert users == []
    mock_db_session.execute.assert_awaited_once()
    mock_db_session.execute.return_value.scalars.assert_called_once()
    mock_db_session.execute.return_value.scalars.return_value.all.assert_called_once()


async def test_create_user(mock_db_session: MagicMock):
    """测试 create_user"""
    user_to_create = User(id=uuid4(), email="create@example.com", hashed_password="new_hash")

    repository = SQLUserRepository(session=mock_db_session)
    returned_user = await repository.create_user(user=user_to_create)

    assert returned_user is user_to_create # 应返回传入的对象
    mock_db_session.add.assert_called_once_with(user_to_create)
    mock_db_session.execute.assert_not_awaited() # 不应调用 execute

async def test_create_user_profile(mock_db_session: MagicMock):
    """测试 create_user_profile"""
    profile_to_create = UserProfile(id=uuid4(), user_id=uuid4(), bio="New Profile")

    repository = SQLUserRepository(session=mock_db_session)
    returned_profile = await repository.create_user_profile(profile=profile_to_create)

    assert returned_profile is profile_to_create
    mock_db_session.add.assert_called_once_with(profile_to_create)
    mock_db_session.execute.assert_not_awaited()

async def test_update_user(mock_db_session: MagicMock):
    """测试 update_user"""
    user_to_update = User(id=uuid4(), email="update@example.com", hashed_password="updated_hash")

    repository = SQLUserRepository(session=mock_db_session)
    returned_user = await repository.update_user(user=user_to_update)

    assert returned_user is user_to_update
    mock_db_session.add.assert_called_once_with(user_to_update)
    mock_db_session.execute.assert_not_awaited()

async def test_update_user_profile(mock_db_session: MagicMock):
    """测试 update_user_profile"""
    profile_to_update = UserProfile(id=uuid4(), user_id=uuid4(), bio="Updated Profile")

    repository = SQLUserRepository(session=mock_db_session)
    returned_profile = await repository.update_user_profile(profile=profile_to_update)

    assert returned_profile is profile_to_update
    mock_db_session.add.assert_called_once_with(profile_to_update)
    mock_db_session.execute.assert_not_awaited() 