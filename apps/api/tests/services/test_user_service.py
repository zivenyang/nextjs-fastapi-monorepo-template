import pytest
from unittest.mock import AsyncMock, MagicMock, patch # 导入 Mock 工具
from uuid import uuid4
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession # 导入类型
from fastapi import HTTPException

from app.services.user_service import UserService
from app.models.user import User, UserProfile, UserRole
from app.schemas.user import UserUpdate, UserCreate, UserProfileUpdate

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

# --- Fixture for Mock Session ---
@pytest.fixture
def mock_db_session() -> MagicMock: # 返回类型改为 MagicMock 更准确，因为它混合了 sync/async
    session = MagicMock(spec=AsyncSession)
    # execute 是一个协程
    mock_execute = AsyncMock()
    session.execute = mock_execute
    # execute await 后的结果是一个 *同步* MagicMock
    mock_result = MagicMock()
    # 这个 mock_result 有一个 *同步* 方法 scalar_one_or_none
    # 我们将在测试中设置这个同步方法的 return_value
    mock_result.scalar_one_or_none = MagicMock()
    mock_execute.return_value = mock_result # execute await 后返回 mock_result

    session.add = MagicMock() # 使用 MagicMock 因为 add 是同步调用
    session.commit = AsyncMock() # commit 是 await
    session.refresh = AsyncMock() # refresh 是 await
    session.rollback = AsyncMock() # rollback 是 await
    session.get = AsyncMock() # get 也是 await
    return session

# --- Unit Tests for UserService ---

async def test_get_user_by_email_found(mock_db_session: MagicMock):
    test_email = "test@example.com"
    expected_user = User(id=uuid4(), email=test_email, hashed_password="hashed")
    # 配置 mock_result 的 scalar_one_or_none() *同步方法* 的返回值
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = expected_user

    user_service = UserService(db=mock_db_session)
    found_user = await user_service.get_user_by_email(email=test_email)

    assert found_user == expected_user
    mock_db_session.execute.assert_awaited_once()
    # 确认同步方法被调用
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()

async def test_get_user_by_email_not_found(mock_db_session: MagicMock):
    test_email = "notfound@example.com"
    # 配置 mock_result 的 scalar_one_or_none() *同步方法* 的返回值
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    user_service = UserService(db=mock_db_session)
    found_user = await user_service.get_user_by_email(email=test_email)

    assert found_user is None
    mock_db_session.execute.assert_awaited_once()
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()

async def test_create_user_success(mock_db_session: MagicMock):
    user_in = UserCreate(
        email="new@example.com",
        password="password123",
        username="newuser",
        full_name="New User"
    )

    # 1. 创建 UserService 实例
    user_service = UserService(db=mock_db_session)

    # 2. Mock get_user_by_email 方法，使其返回 None
    #    并 Mock get_password_hash
    with patch.object(user_service, 'get_user_by_email', new_callable=AsyncMock, return_value=None) as mock_get_email, \
         patch('app.services.user_service.get_password_hash', return_value="hashed_password123") as mock_hash:

        # 3. 调用被测方法
        created_user = await user_service.create_user(user_create_data=user_in)

    # 4. 断言
    assert created_user is not None
    assert created_user.email == user_in.email.lower()
    assert created_user.hashed_password == "hashed_password123"
    mock_get_email.assert_awaited_once_with(user_in.email) # 确认 get_user_by_email 被调用
    mock_hash.assert_called_once_with(user_in.password)
    # 确认数据库写操作被调用 (因为 get_user_by_email 被 mock 了，不再需要检查 execute)
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once()
    mock_db_session.rollback.assert_not_awaited()

async def test_create_user_email_exists(mock_db_session: AsyncMock):
    user_in = UserCreate(
        email="exists@example.com",
        password="password123",
        username="existsuser",
    )
    existing_user = User(id=uuid4(), email=user_in.email, hashed_password="old_hash")

    # 1. 创建 UserService 实例
    user_service = UserService(db=mock_db_session)

    # 2. Mock get_user_by_email 方法，使其返回已存在的用户
    with patch.object(user_service, 'get_user_by_email', new_callable=AsyncMock, return_value=existing_user) as mock_get_email:
        # 3. 调用并断言异常
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(user_create_data=user_in)

    # 4. 断言异常和调用
    assert exc_info.value.status_code == 400
    assert "该邮箱已被注册" in exc_info.value.detail
    mock_get_email.assert_awaited_once_with(user_in.email)
    # 确认数据库写操作未执行
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_awaited()
    mock_db_session.refresh.assert_not_awaited()
    mock_db_session.rollback.assert_not_awaited()

async def test_update_user_basic_info(mock_db_session: AsyncMock):
    """测试更新用户的基本信息"""
    user_id = uuid4()
    user_to_update = User(
        id=user_id,
        email="update@example.com",
        hashed_password="old_hash",
        full_name="Old Name"
    )
    user_update_data = UserUpdate(full_name="New Name", username="newusername")

    # 模拟 profile 查询返回 None
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    user_service = UserService(db=mock_db_session)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user.full_name == "New Name"
    assert updated_user.username == "newusername"
    assert updated_profile is None # 确认 profile 未被更新
    assert mock_db_session.add.call_count == 1 # 只添加了 user
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)
    mock_db_session.rollback.assert_not_awaited()
    # 确认 profile 查询被调用过
    mock_db_session.execute.assert_awaited_once()
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()

async def test_update_user_password(mock_db_session: AsyncMock):
    """测试更新用户密码"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="pw@example.com", hashed_password="old_hash")
    user_update_data = UserUpdate(password="new_password123")

    # 模拟 profile 查询返回 None
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    user_service = UserService(db=mock_db_session)

    with patch('app.services.user_service.get_password_hash', return_value="hashed_new_password") as mock_hash:
        updated_user, _ = await user_service.update_user(
            user_to_update=user_to_update, user_update_data=user_update_data
        )

    assert updated_user.hashed_password == "hashed_new_password"
    mock_hash.assert_called_once_with("new_password123")
    assert mock_db_session.add.call_count == 1 # 只添加了 user
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)

async def test_update_user_new_profile(mock_db_session: AsyncMock):
    """测试为用户创建新的 Profile"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="newprofile@example.com", hashed_password="hash")
    profile_update_data = UserProfileUpdate(bio="New Bio", phone_number="12345")
    user_update_data = UserUpdate(profile=profile_update_data)

    # 模拟 profile 查询返回 None (因为是新创建)
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    user_service = UserService(db=mock_db_session)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_profile is not None
    assert updated_profile.bio == "New Bio"
    assert updated_profile.phone_number == "12345"
    assert updated_profile.user_id == user_id
    assert mock_db_session.add.call_count == 1 # 只添加了 profile (因为 user 没有其他更新)
    # 注意：原代码逻辑是 profile 和 user 分开 add, 如果 user 没更新则 add(user) 不执行
    # 断言 add 被调用一次，其参数是 UserProfile 实例
    added_arg = mock_db_session.add.call_args[0][0]
    assert isinstance(added_arg, UserProfile)
    assert added_arg.bio == "New Bio"

    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)
    # 原代码在创建新 profile 时不 refresh profile，所以这里不检查 refresh profile

async def test_update_user_existing_profile(mock_db_session: AsyncMock):
    """测试更新用户已有的 Profile"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="oldprofile@example.com", hashed_password="hash")
    existing_profile = UserProfile(user_id=user_id, bio="Old Bio")
    profile_update_data = UserProfileUpdate(bio="Updated Bio", phone_number="54321")
    user_update_data = UserUpdate(profile=profile_update_data)

    # 模拟 profile 查询返回已存在的 profile
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_profile

    user_service = UserService(db=mock_db_session)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_profile is not None
    assert updated_profile.bio == "Updated Bio"
    assert updated_profile.phone_number == "54321"
    assert updated_profile is existing_profile # 应该是同一个对象被更新
    # 确认 add 被调用一次，参数是更新后的 profile
    mock_db_session.add.assert_called_once_with(existing_profile)
    mock_db_session.commit.assert_awaited_once()
    # 确认 user 和 profile 都被 refresh
    assert mock_db_session.refresh.await_count == 2
    mock_db_session.refresh.assert_any_await(user_to_update)
    mock_db_session.refresh.assert_any_await(existing_profile)

async def test_update_user_commit_fails(mock_db_session: AsyncMock):
    """测试数据库提交失败的回滚"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="fail@example.com", hashed_password="hash")
    user_update_data = UserUpdate(full_name="Trying To Update")

    # 模拟 commit 抛出异常
    mock_db_session.commit.side_effect = RuntimeError("DB commit failed")
    # 模拟 profile 查询返回 None
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    user_service = UserService(db=mock_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await user_service.update_user(
            user_to_update=user_to_update, user_update_data=user_update_data
        )

    assert exc_info.value.status_code == 500
    assert "更新用户信息时发生内部错误" in exc_info.value.detail
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.rollback.assert_awaited_once()
    mock_db_session.refresh.assert_not_awaited()

async def test_get_users(mock_db_session: AsyncMock):
    """测试获取用户列表"""
    expected_users = [
        User(id=uuid4(), email="user1@example.com", hashed_password="h1"),
        User(id=uuid4(), email="user2@example.com", hashed_password="h2")
    ]
    # 需要模拟 scalars().all()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = expected_users
    mock_db_session.execute.return_value.scalars.return_value = mock_scalars

    user_service = UserService(db=mock_db_session)
    users = await user_service.get_users(skip=0, limit=10)

    assert users == expected_users
    assert len(users) == 2
    mock_db_session.execute.assert_awaited_once()
    mock_db_session.execute.return_value.scalars.assert_called_once()
    mock_db_session.execute.return_value.scalars.return_value.all.assert_called_once()

async def test_get_user_with_profile_found(mock_db_session: AsyncMock):
    """测试获取用户及其存在的 Profile"""
    user_id = uuid4()
    test_user = User(id=user_id, email="profile@example.com", hashed_password="hash")
    test_profile = UserProfile(user_id=user_id, bio="Has Profile")

    user_service = UserService(db=mock_db_session)

    # Mock get_user_by_id 内部调用 和 profile 查询
    # 使用 as mock_get_by_id 来获取 mock 对象
    with patch.object(user_service, 'get_user_by_id', new_callable=AsyncMock, return_value=test_user) as mock_get_by_id:
        # 配置 profile 查询返回 test_profile
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = test_profile

        user, profile = await user_service.get_user_with_profile(user_id=user_id)

    assert user == test_user
    assert profile == test_profile
    # 使用 mock_get_by_id 进行断言
    mock_get_by_id.assert_awaited_once_with(user_id)
    mock_db_session.execute.assert_awaited_once() # 确认 profile 查询被调用
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()

async def test_get_user_with_profile_not_found(mock_db_session: AsyncMock):
    """测试获取不存在的用户及其 Profile"""
    user_id = uuid4()
    user_service = UserService(db=mock_db_session)

    # Mock get_user_by_id 返回 None
    # 使用 as mock_get_by_id 来获取 mock 对象
    with patch.object(user_service, 'get_user_by_id', new_callable=AsyncMock, return_value=None) as mock_get_by_id:
        result = await user_service.get_user_with_profile(user_id=user_id)

    assert result is None
    # 使用 mock_get_by_id 进行断言
    mock_get_by_id.assert_awaited_once_with(user_id)
    mock_db_session.execute.assert_not_awaited() # 用户不存在，不查询 profile

async def test_get_user_with_profile_no_profile(mock_db_session: AsyncMock):
    """测试获取用户但用户没有 Profile"""
    user_id = uuid4()
    test_user = User(id=user_id, email="noprofile@example.com", hashed_password="hash")

    user_service = UserService(db=mock_db_session)

    # Mock get_user_by_id 返回用户，Profile 查询返回 None
    # 使用 as mock_get_by_id 来获取 mock 对象
    with patch.object(user_service, 'get_user_by_id', new_callable=AsyncMock, return_value=test_user) as mock_get_by_id:
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        user, profile = await user_service.get_user_with_profile(user_id=user_id)

    assert user == test_user
    assert profile is None
    # 使用 mock_get_by_id 进行断言
    mock_get_by_id.assert_awaited_once_with(user_id)
    mock_db_session.execute.assert_awaited_once() # 确认 profile 查询被调用
    mock_db_session.execute.return_value.scalar_one_or_none.assert_called_once()

# TODO: 添加更多测试用例覆盖 update_user, get_users, get_user_with_profile 等方法
# TODO: 测试密码更新逻辑
# TODO: 测试 profile 创建和更新逻辑
# TODO: 测试权限相关的逻辑（如果服务层包含）
# TODO: 测试数据库操作失败时的回滚逻辑 (配置 commit 或 refresh 抛出异常) 