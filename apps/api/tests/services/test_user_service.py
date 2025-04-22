import pytest
from unittest.mock import AsyncMock, MagicMock, patch # 导入 Mock 工具
from uuid import uuid4

from sqlmodel.ext.asyncio.session import AsyncSession # 导入类型
from fastapi import HTTPException

from app.services.user_service import UserService
from app.models.user import User, UserProfile
from app.schemas.user import UserUpdate, UserCreate, UserProfileUpdate
from app.services.user_service import EmailAlreadyExistsException

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
        with pytest.raises(EmailAlreadyExistsException) as exc_info:
            await user_service.create_user(user_create_data=user_in)

    # 4. 断言异常和调用
    assert f"邮箱 {user_in.email} 已被注册" in str(exc_info.value)
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

# --- Helper for get_users tests ---
async def _get_users_logic_helper(mock_db_session: MagicMock, expected_users: list, skip: int, limit: int):
    """Helper function to test get_users logic"""
    # 配置 execute -> scalars -> all 返回期望列表
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = expected_users
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result # execute await 后返回 mock_result

    user_service = UserService(db=mock_db_session)
    users = await user_service.get_users(skip=skip, limit=limit)

    assert users == expected_users
    mock_db_session.execute.assert_awaited_once()
    # 验证结果链被调用
    mock_db_session.execute.return_value.scalars.assert_called_once()
    mock_db_session.execute.return_value.scalars.return_value.all.assert_called_once()

async def test_get_users_with_skip(mock_db_session: MagicMock):
    """测试 get_users 的 skip 参数"""
    # 注意：这个测试本身无法验证 skip 是否真的生效，只能验证代码执行流程
    # 真正验证 skip 需要集成测试或更复杂的 Mock 来检查传递给 execute 的 query
    await _get_users_logic_helper(
        mock_db_session,
        expected_users=[User(id=uuid4()), User(id=uuid4())],
        skip=5,
        limit=10
    )

@pytest.mark.asyncio
async def test_get_users_with_limit(mock_db_session: MagicMock):
    """Test get_users with limit"""
    users_data = [
        User(id=uuid4(), email="test1@example.com", full_name="Test User 1"),
        User(id=uuid4(), email="test2@example.com", full_name="Test User 2"),
    ]
    await _get_users_logic_helper(mock_db_session, users_data[:1], skip=0, limit=1)

@pytest.mark.asyncio
async def test_get_users_empty(mock_db_session: MagicMock):
    """Test get_users when no users exist"""
    await _get_users_logic_helper(mock_db_session, [], skip=0, limit=10)

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

async def test_update_user_basic_and_password(mock_db_session: MagicMock):
    """测试同时更新基本信息和密码"""
    user_id = uuid4()
    user_to_update = User(
        id=user_id,
        email="combo@example.com",
        hashed_password="old_hash",
        full_name="Old Name"
    )
    user_update_data = UserUpdate(full_name="New Combo Name", password="combo_password123")

    # 模拟 profile 查询返回 None
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    user_service = UserService(db=mock_db_session)

    with patch('app.services.user_service.get_password_hash', return_value="hashed_combo_password") as mock_hash:
        updated_user, _ = await user_service.update_user(
            user_to_update=user_to_update, user_update_data=user_update_data
        )

    assert updated_user.full_name == "New Combo Name"
    assert updated_user.hashed_password == "hashed_combo_password"
    mock_hash.assert_called_once_with("combo_password123")
    # add 应该被调用两次 (一次为 full_name, 一次为 password)
    assert mock_db_session.add.call_count == 2
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)

async def test_update_user_basic_and_new_profile(mock_db_session: MagicMock):
    """测试同时更新基本信息和创建新 Profile"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="combo2@example.com", hashed_password="hash", full_name="Old Combo")
    profile_update_data = UserProfileUpdate(bio="Combo Bio")
    user_update_data = UserUpdate(full_name="New Combo Name", profile=profile_update_data)

    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    user_service = UserService(db=mock_db_session)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user.full_name == "New Combo Name"
    assert updated_profile is not None
    assert updated_profile.bio == "Combo Bio"
    # add 被调用两次 (一次 user, 一次 profile)
    assert mock_db_session.add.call_count == 2
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)

async def test_update_user_basic_and_existing_profile(mock_db_session: MagicMock):
    """测试同时更新基本信息和更新现有 Profile"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="combo3@example.com", hashed_password="hash", full_name="Old Combo 3")
    existing_profile = UserProfile(user_id=user_id, bio="Old Bio 3")
    profile_update_data = UserProfileUpdate(bio="Updated Combo Bio 3")
    user_update_data = UserUpdate(full_name="New Combo Name 3", profile=profile_update_data)

    mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_profile

    user_service = UserService(db=mock_db_session)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user.full_name == "New Combo Name 3"
    assert updated_profile is not None
    assert updated_profile.bio == "Updated Combo Bio 3"
    # add 被调用两次 (一次 user, 一次 profile)
    assert mock_db_session.add.call_count == 2
    mock_db_session.commit.assert_awaited_once()
    assert mock_db_session.refresh.await_count == 2
    mock_db_session.refresh.assert_any_await(user_to_update)
    mock_db_session.refresh.assert_any_await(existing_profile)

async def test_update_user_empty_profile_data(mock_db_session: MagicMock):
    """测试传入空的 Profile 更新数据"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="empty@example.com", hashed_password="hash")
    # 传入空的 profile update
    user_update_data = UserUpdate(profile=UserProfileUpdate())

    # 模拟 profile 查询返回 None 或 Existing, 结果应该一样
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

    user_service = UserService(db=mock_db_session)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user is user_to_update # 用户本身未更新
    assert updated_profile is None # Profile 也未更新
    mock_db_session.add.assert_not_called() # 不应该有 add 调用
    mock_db_session.commit.assert_awaited_once() # 但 commit 仍然会调用
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)

async def test_update_user_profile_clear_fields(mock_db_session: AsyncMock):
    """测试更新用户 Profile 时将字段设置为空"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="clearprofile@example.com", hashed_password="hash")
    existing_profile = UserProfile(user_id=user_id, bio="Has Bio", phone_number="12345")
    # 更新数据中将 phone_number 设为 None
    profile_update_data = UserProfileUpdate(bio="Still Has Bio", phone_number=None)
    user_update_data = UserUpdate(profile=profile_update_data)

    # 模拟 profile 查询返回已存在的 profile
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_profile

    user_service = UserService(db=mock_db_session)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_profile is not None
    assert updated_profile.bio == "Still Has Bio"
    assert updated_profile.phone_number is None # 确认字段被清空
    assert updated_profile is existing_profile
    # 确认 add 被调用一次 (更新 profile)
    mock_db_session.add.assert_called_once_with(existing_profile)
    mock_db_session.commit.assert_awaited_once()
    assert mock_db_session.refresh.await_count == 2 # user 和 profile 都 refresh
    mock_db_session.refresh.assert_any_await(user_to_update)
    mock_db_session.refresh.assert_any_await(existing_profile)

async def test_update_user_only_profile(mock_db_session: AsyncMock):
    """测试只更新用户 Profile，不更新 User 基本信息"""
    user_id = uuid4()
    # 用户信息保持不变
    user_to_update = User(id=user_id, email="onlyprofile@example.com", hashed_password="hash", full_name="Original Name")
    existing_profile = UserProfile(user_id=user_id, bio="Old Bio")
    profile_update_data = UserProfileUpdate(bio="Updated Bio Only")
    # UserUpdate 中只有 profile
    user_update_data = UserUpdate(profile=profile_update_data)

    # 模拟 profile 查询返回已存在的 profile
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_profile

    user_service = UserService(db=mock_db_session)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user is user_to_update # User 对象本身未变
    assert updated_user.full_name == "Original Name" # User 字段未变
    assert updated_profile is not None
    assert updated_profile.bio == "Updated Bio Only"
    assert updated_profile is existing_profile
    # 只调用了一次 add (更新 profile)
    mock_db_session.add.assert_called_once_with(existing_profile)
    mock_db_session.commit.assert_awaited_once()
    assert mock_db_session.refresh.await_count == 2 # user 和 profile 都 refresh
    mock_db_session.refresh.assert_any_await(user_to_update)
    mock_db_session.refresh.assert_any_await(existing_profile)

async def test_create_user_commit_fails(mock_db_session: AsyncMock):
    """测试创建用户时数据库提交失败的回滚"""
    user_in = UserCreate(
        email="failcreate@example.com",
        password="password123",
        username="failuser",
    )

    # 模拟 get_user_by_email 返回 None (因为要走到创建逻辑)
    # 注意：UserService.create_user 内部会调用 get_user_by_email
    # 所以我们需要 patch 它，而不是 mock session.execute
    # 但是这里 mock_db_session 已经模拟了 execute, 如果 get_user_by_email 内部用了它
    # 就会冲突。所以我们直接 mock get_user_by_email

    # 模拟 commit 抛出异常
    mock_db_session.commit.side_effect = RuntimeError("DB commit failed during create")

    user_service = UserService(db=mock_db_session)

    # Mock get_user_by_email 和 get_password_hash
    with patch.object(user_service, 'get_user_by_email', new_callable=AsyncMock, return_value=None) as mock_get_email, \
         patch('app.services.user_service.get_password_hash', return_value="hashed_password_fail") as mock_hash:
        # 调用并断言异常
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(user_create_data=user_in)

    # 断言异常类型和消息
    assert exc_info.value.status_code == 500
    assert "创建用户时发生内部错误" in exc_info.value.detail

    # 确认调用流程
    mock_get_email.assert_awaited_once_with(user_in.email) # 确认邮箱检查被调用
    mock_hash.assert_called_once_with(user_in.password)
    mock_db_session.add.assert_called_once() # add 应该被调用
    mock_db_session.commit.assert_awaited_once() # commit 被尝试调用
    mock_db_session.rollback.assert_awaited_once() # rollback 被调用
    mock_db_session.refresh.assert_not_awaited() # refresh 不应该被调用