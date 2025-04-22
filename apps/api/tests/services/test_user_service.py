import pytest
from unittest.mock import AsyncMock, MagicMock, patch # 导入 Mock 工具
from uuid import uuid4
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession # 导入类型
from fastapi import HTTPException

from app.services.user_service import UserService
# 导入仓库接口，用于 Mock
from app.repositories.interfaces.user_interface import IUserRepository
from app.models.user import User, UserProfile, UserRole
from app.schemas.user import UserUpdate, UserCreate, UserProfileUpdate
from app.core.security import get_password_hash, verify_password
from app.services.user_service import UserNotFoundException, EmailAlreadyExistsException

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

# --- Fixture for Mock Session (仍然需要模拟事务) ---
@pytest.fixture
def mock_db_session() -> MagicMock:
    session = MagicMock(spec=AsyncSession)
    # 模拟 commit, refresh, rollback (因为服务层现在负责事务)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    # execute 和 get 可能在 update_user 中仍被间接用于 profile 查询后的 refresh
    # 但主要逻辑已移至 repo, 所以这里 mock 可以简化或移除
    # session.get = AsyncMock()
    # mock_execute = AsyncMock()
    # session.execute = mock_execute
    # mock_result = MagicMock()
    # mock_result.scalar_one_or_none = MagicMock()
    # mock_scalars = MagicMock()
    # mock_scalars.all = MagicMock()
    # mock_result.scalars.return_value = mock_scalars
    # mock_execute.return_value = mock_result
    session.add = MagicMock() # add 现在只在 repo 中调用, 但 session mock 可能仍需此属性
    return session

# --- Fixture for Mock User Repository ---
@pytest.fixture
def mock_user_repo() -> MagicMock:
    repo = MagicMock(spec=IUserRepository)
    # 为接口中的每个方法创建 AsyncMock
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get_profile_by_user_id = AsyncMock()
    repo.list_users = AsyncMock()
    repo.create_user = AsyncMock()
    repo.create_user_profile = AsyncMock()
    repo.update_user = AsyncMock()
    repo.update_user_profile = AsyncMock()
    return repo

# --- Unit Tests for UserService (Refactored) ---

# 修改测试用例，注入 mock_user_repo
async def test_get_user_by_email_found(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    test_email = "test@example.com"
    expected_user = User(id=uuid4(), email=test_email, hashed_password="hashed")
    # 配置 mock repository 的 get_by_email 返回值
    mock_user_repo.get_by_email.return_value = expected_user

    # 实例化服务，传入 mock session 和 mock repo
    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    found_user = await user_service.get_user_by_email(email=test_email)

    assert found_user == expected_user
    # 确认 repository 的方法被调用
    mock_user_repo.get_by_email.assert_awaited_once_with(test_email)
    # 确认 session 的方法没有被直接调用 (除了可能的事务方法)
    mock_db_session.execute.assert_not_awaited() # 假设 execute 不再需要 mock
    mock_db_session.get.assert_not_awaited()     # 假设 get 不再需要 mock

# 修改测试用例，注入 mock_user_repo
async def test_get_user_by_email_not_found(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    test_email = "notfound@example.com"
    # 配置 mock repository 的 get_by_email 返回 None
    mock_user_repo.get_by_email.return_value = None

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    found_user = await user_service.get_user_by_email(email=test_email)

    assert found_user is None
    mock_user_repo.get_by_email.assert_awaited_once_with(test_email)
    mock_db_session.execute.assert_not_awaited()
    mock_db_session.get.assert_not_awaited()

# 示例：修改 test_create_user_success
async def test_create_user_success(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    user_in = UserCreate(
        email="new@example.com",
        password="password123",
        username="newuser",
        full_name="New User"
    )
    # 模拟仓库的 create_user 返回创建的对象 (虽然仓库只 add, 但服务层期望返回)
    # 注意：这里需要模拟 refresh 后的效果，或者让仓库模拟 refresh
    # 简化：假设 create_user 调用后，对象已包含 ID (这依赖于事务处理)
    created_db_user = User(
        id=uuid4(), # 假设 refresh 后会有 ID
        email=user_in.email.lower(), 
        hashed_password="hashed_password123", # 模拟哈希结果
        username=user_in.username,
        full_name=user_in.full_name,
        role=UserRole.USER,
        is_verified=False,
        created_at=datetime.now()
    )
    # Mock get_user_by_email (检查邮箱是否存在)
    mock_user_repo.get_by_email.return_value = None
    # Mock 仓库的 create_user (只 add, 但测试服务逻辑时，我们关心之后的结果)
    # 服务层调用 create_user 后会 commit 和 refresh
    # 我们需要确保 mock_db_session.refresh 被调用
    # Mock get_password_hash
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password123") as mock_hash:
        # 实例化服务
        user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
        # 调用被测方法
        # 注意：create_user 内部调用了 repo.create_user, 然后 commit/refresh
        # 为了让 refresh 生效，我们需要让 mock_db_session.refresh 修改传入的对象
        # 或者，我们假设 refresh 成功了，直接断言结果
        # 为了简化，我们先假设 refresh 会成功
        created_user = await user_service.create_user(user_create_data=user_in)

    # 断言
    assert created_user is not None
    assert created_user.email == user_in.email.lower()
    assert created_user.hashed_password == "hashed_password123"
    assert created_user.id is not None # 确认有 ID (refresh 效果)
    
    # 确认调用
    mock_user_repo.get_by_email.assert_awaited_once_with(user_in.email)
    mock_hash.assert_called_once_with(user_in.password)
    # 确认仓库的 create_user 被调用 (传入了 User 对象)
    mock_user_repo.create_user.assert_awaited_once()
    # 确认事务被提交和刷新
    mock_db_session.commit.assert_awaited_once()
    # refresh 应该传入的是 repo.create_user 创建的 User 对象实例
    # 获取传递给 repo.create_user 的参数
    call_args, call_kwargs = mock_user_repo.create_user.await_args
    created_db_user_instance = call_args[0] # 第一个位置参数是 user 对象
    mock_db_session.refresh.assert_awaited_once_with(created_db_user_instance)
    mock_db_session.rollback.assert_not_awaited()

# 修改测试用例，注入 mock_user_repo
async def test_create_user_email_exists(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    user_in = UserCreate(
        email="exists@example.com",
        password="password123",
        username="existsuser",
    )
    existing_user = User(id=uuid4(), email=user_in.email, hashed_password="old_hash")

    # 1. 配置 mock repo 返回已存在的用户
    mock_user_repo.get_by_email.return_value = existing_user

    # 2. 实例化服务
    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)

    # 3. 调用并断言异常
    with pytest.raises(EmailAlreadyExistsException) as exc_info:
        await user_service.create_user(user_create_data=user_in)

    # 4. 断言异常和调用
    assert f"邮箱 {user_in.email} 已被注册" in str(exc_info.value)
    mock_user_repo.get_by_email.assert_awaited_once_with(user_in.email)
    # 确认仓库的 create 方法未被调用
    mock_user_repo.create_user.assert_not_awaited()
    # 确认事务未提交
    mock_db_session.commit.assert_not_awaited()
    mock_db_session.refresh.assert_not_awaited()
    mock_db_session.rollback.assert_not_awaited() # 因为异常是在服务层检查抛出的，还没到数据库操作失败

# 修改测试用例，注入 mock_user_repo
async def test_update_user_basic_info(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试更新用户的基本信息"""
    user_id = uuid4()
    user_to_update = User(
        id=user_id,
        email="update@example.com",
        hashed_password="old_hash",
        full_name="Old Name"
    )
    user_update_data = UserUpdate(full_name="New Name", username="newusername")

    # 模拟仓库 profile 查询返回 None
    mock_user_repo.get_profile_by_user_id.return_value = None

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user.full_name == "New Name"
    assert updated_user.username == "newusername"
    assert updated_profile is None
    # 确认仓库的 update_user 被调用
    mock_user_repo.update_user.assert_awaited_once_with(user_to_update)
    # 确认仓库的 profile 相关方法未被调用 (除了查询)
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)
    mock_user_repo.create_user_profile.assert_not_awaited()
    mock_user_repo.update_user_profile.assert_not_awaited()
    # 确认事务操作
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)
    mock_db_session.rollback.assert_not_awaited()

# 修改测试用例，注入 mock_user_repo
async def test_update_user_password(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试更新用户密码"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="pw@example.com", hashed_password="old_hash")
    user_update_data = UserUpdate(password="new_password123")

    # 模拟仓库 profile 查询返回 None
    mock_user_repo.get_profile_by_user_id.return_value = None

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)

    with patch('app.services.user_service.get_password_hash', return_value="hashed_new_password") as mock_hash:
        updated_user, _ = await user_service.update_user(
            user_to_update=user_to_update, user_update_data=user_update_data
        )

    assert updated_user.hashed_password == "hashed_new_password"
    mock_hash.assert_called_once_with("new_password123")
    # 确认仓库 update_user 被调用
    mock_user_repo.update_user.assert_awaited_once_with(user_to_update)
    # 确认事务
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)

# 修改测试用例，注入 mock_user_repo
async def test_update_user_new_profile(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试为用户创建新的 Profile"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="newprofile@example.com", hashed_password="hash")
    profile_update_data = UserProfileUpdate(bio="New Bio", phone_number="12345")
    user_update_data = UserUpdate(profile=profile_update_data)

    # 模拟仓库 profile 查询返回 None (因为是新创建)
    mock_user_repo.get_profile_by_user_id.return_value = None
    
    # 模拟仓库 create_user_profile 返回的结果 (需要带 ID, 假设 refresh 后)
    # 注意: 服务层会在 commit 后 refresh profile 对象
    created_profile_instance = None # 用于在 refresh 时捕获对象
    async def mock_refresh(obj):
        nonlocal created_profile_instance
        if isinstance(obj, UserProfile):
             obj.id = uuid4() # 模拟数据库分配 ID
             created_profile_instance = obj
        elif isinstance(obj, User):
             pass # User refresh 正常
    mock_db_session.refresh.side_effect = mock_refresh

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_profile is not None
    assert updated_profile.bio == "New Bio"
    assert updated_profile.phone_number == "12345"
    assert updated_profile.user_id == user_id
    assert updated_profile.id is not None # 确认有 ID (refresh 效果)
    
    # 确认仓库调用
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)
    mock_user_repo.create_user_profile.assert_awaited_once() # 确认创建被调用
    # 确认传入 create_user_profile 的对象
    call_args, _ = mock_user_repo.create_user_profile.await_args
    profile_arg = call_args[0]
    assert isinstance(profile_arg, UserProfile)
    assert profile_arg.bio == "New Bio"
    assert profile_arg.user_id == user_id
    mock_user_repo.update_user.assert_not_awaited() # User 未更新
    
    # 确认事务
    mock_db_session.commit.assert_awaited_once()
    # 确认 refresh 被调用 (user 和 profile)
    assert mock_db_session.refresh.await_count == 2
    mock_db_session.refresh.assert_any_await(user_to_update)
    assert created_profile_instance is not None
    mock_db_session.refresh.assert_any_await(created_profile_instance)

# 修改测试用例，注入 mock_user_repo
async def test_update_user_existing_profile(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试更新用户已有的 Profile"""
    user_id = uuid4()
    profile_id = uuid4()
    user_to_update = User(id=user_id, email="oldprofile@example.com", hashed_password="hash")
    existing_profile = UserProfile(id=profile_id, user_id=user_id, bio="Old Bio")
    profile_update_data = UserProfileUpdate(bio="Updated Bio", phone_number="54321")
    user_update_data = UserUpdate(profile=profile_update_data)

    # 模拟仓库 profile 查询返回已存在的 profile
    mock_user_repo.get_profile_by_user_id.return_value = existing_profile

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_profile is not None
    assert updated_profile.bio == "Updated Bio"
    assert updated_profile.phone_number == "54321"
    assert updated_profile is existing_profile # 应该是同一个对象被更新
    
    # 确认仓库调用
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)
    mock_user_repo.update_user_profile.assert_awaited_once_with(existing_profile)
    mock_user_repo.create_user_profile.assert_not_awaited()
    mock_user_repo.update_user.assert_not_awaited()

    # 确认事务
    mock_db_session.commit.assert_awaited_once()
    # 确认 refresh 被调用 (user 和 profile)
    assert mock_db_session.refresh.await_count == 2
    mock_db_session.refresh.assert_any_await(user_to_update)
    mock_db_session.refresh.assert_any_await(existing_profile)

# 修改测试用例，注入 mock_user_repo
async def test_update_user_commit_fails(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试更新用户时数据库提交失败"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="commitfail@example.com", hashed_password="hash")
    user_update_data = UserUpdate(full_name="Commit Fail Name")

    # 模拟仓库 profile 查询返回 None
    mock_user_repo.get_profile_by_user_id.return_value = None

    # 模拟 commit 失败
    commit_error = RuntimeError("DB commit failed")
    mock_db_session.commit.side_effect = commit_error

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)

    # 使用 pytest.raises 检查是否抛出了预期的 RuntimeError
    with pytest.raises(RuntimeError, match="DB commit failed"):
        await user_service.update_user(
            user_to_update=user_to_update, user_update_data=user_update_data
        )

    # 确认调用了 update_user
    mock_user_repo.update_user.assert_awaited_once_with(user_to_update)
    # 确认尝试了 commit
    mock_db_session.commit.assert_awaited_once()
    # 确认调用了 rollback
    mock_db_session.rollback.assert_awaited_once()
    # 确认 refresh 没有被调用
    mock_db_session.refresh.assert_not_awaited()

# --- Helper for get_users tests ---
async def _get_users_logic_helper(mock_db_session: MagicMock, mock_user_repo: MagicMock, expected_users: list, skip: int, limit: int):
    """Helper function to test get_users logic (Refactored)"""
    # 配置 mock repo 的 list_users 返回值
    mock_user_repo.list_users.return_value = expected_users

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    users = await user_service.get_users(skip=skip, limit=limit)

    assert users == expected_users
    # 验证仓库方法被调用
    mock_user_repo.list_users.assert_awaited_once_with(skip=skip, limit=limit)
    # 验证 session execute 未被调用
    mock_db_session.execute.assert_not_awaited()

# 修改测试用例，注入 mock_user_repo
async def test_get_users_with_skip(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试 get_users 的 skip 参数"""
    await _get_users_logic_helper(
        mock_db_session, mock_user_repo, # 注入 repo
        expected_users=[User(id=uuid4()), User(id=uuid4())],
        skip=5,
        limit=10
    )

# 修改测试用例，注入 mock_user_repo
@pytest.mark.asyncio
async def test_get_users_with_limit(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """Test get_users with limit"""
    users_data = [
        User(id=uuid4(), email="test1@example.com", full_name="Test User 1"),
        User(id=uuid4(), email="test2@example.com", full_name="Test User 2"),
    ]
    await _get_users_logic_helper(mock_db_session, mock_user_repo, users_data[:1], skip=0, limit=1)

# 修改测试用例，注入 mock_user_repo
@pytest.mark.asyncio
async def test_get_users_empty(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """Test get_users when no users exist"""
    await _get_users_logic_helper(mock_db_session, mock_user_repo, [], skip=0, limit=10)

# 修改测试用例，注入 mock_user_repo
async def test_get_user_with_profile_found(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试获取用户及其存在的 Profile"""
    user_id = uuid4()
    test_user = User(id=user_id, email="profile@example.com", hashed_password="hash")
    test_profile = UserProfile(user_id=user_id, bio="Has Profile")

    # 配置 mock repo 返回值
    mock_user_repo.get_by_id.return_value = test_user
    mock_user_repo.get_profile_by_user_id.return_value = test_profile

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    user, profile = await user_service.get_user_with_profile(user_id=user_id)

    assert user == test_user
    assert profile == test_profile
    # 确认仓库方法被调用
    mock_user_repo.get_by_id.assert_awaited_once_with(user_id)
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)

# 修改测试用例，注入 mock_user_repo
async def test_get_user_with_profile_not_found(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试获取不存在的用户及其 Profile"""
    user_id = uuid4()
    
    # 配置 mock repo 返回 None
    mock_user_repo.get_by_id.return_value = None

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    result = await user_service.get_user_with_profile(user_id=user_id)

    assert result is None
    mock_user_repo.get_by_id.assert_awaited_once_with(user_id)
    # 用户不存在，不应查询 profile
    mock_user_repo.get_profile_by_user_id.assert_not_awaited()

# 修改测试用例，注入 mock_user_repo
async def test_get_user_with_profile_no_profile(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试获取用户但用户没有 Profile"""
    user_id = uuid4()
    test_user = User(id=user_id, email="noprofile@example.com", hashed_password="hash")

    # 配置 mock repo 返回值
    mock_user_repo.get_by_id.return_value = test_user
    mock_user_repo.get_profile_by_user_id.return_value = None

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    user, profile = await user_service.get_user_with_profile(user_id=user_id)

    assert user == test_user
    assert profile is None
    mock_user_repo.get_by_id.assert_awaited_once_with(user_id)
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)

# --- 组合更新测试 --- 

# 修改测试用例，注入 mock_user_repo
async def test_update_user_basic_and_password(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试同时更新基本信息和密码"""
    user_id = uuid4()
    user_to_update = User(
        id=user_id,
        email="combo@example.com",
        hashed_password="old_hash",
        full_name="Old Name"
    )
    user_update_data = UserUpdate(full_name="New Combo Name", password="combo_password123")

    # 模拟仓库 profile 查询返回 None
    mock_user_repo.get_profile_by_user_id.return_value = None

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)

    with patch('app.services.user_service.get_password_hash', return_value="hashed_combo_password") as mock_hash:
        updated_user, _ = await user_service.update_user(
            user_to_update=user_to_update, user_update_data=user_update_data
        )

    assert updated_user.full_name == "New Combo Name"
    assert updated_user.hashed_password == "hashed_combo_password"
    mock_hash.assert_called_once_with("combo_password123")
    # 确认仓库 update_user 被调用 (因为 user 信息和密码都变了)
    # 注意：服务层实现会检查 user_updated 标志，所以只会调用一次 update_user
    mock_user_repo.update_user.assert_awaited_once_with(user_to_update)
    # 确认事务
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user_to_update)

# 修改测试用例，注入 mock_user_repo
async def test_update_user_basic_and_new_profile(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试同时更新基本信息和创建新 Profile"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="combo2@example.com", hashed_password="hash", full_name="Old Combo")
    profile_update_data = UserProfileUpdate(bio="Combo Bio")
    user_update_data = UserUpdate(full_name="New Combo Name", profile=profile_update_data)

    mock_user_repo.get_profile_by_user_id.return_value = None
    
    # 模拟 refresh 分配 ID
    created_profile_instance = None
    async def mock_refresh(obj):
        nonlocal created_profile_instance
        if isinstance(obj, UserProfile):
             obj.id = uuid4()
             created_profile_instance = obj
    mock_db_session.refresh.side_effect = mock_refresh

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user.full_name == "New Combo Name"
    assert updated_profile is not None
    assert updated_profile.bio == "Combo Bio"
    assert updated_profile.id is not None
    # 确认仓库调用
    mock_user_repo.update_user.assert_awaited_once_with(user_to_update)
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)
    mock_user_repo.create_user_profile.assert_awaited_once()
    # 确认事务
    mock_db_session.commit.assert_awaited_once()
    # 确认 refresh 被调用 (user 和 profile)
    assert mock_db_session.refresh.await_count == 2
    mock_db_session.refresh.assert_any_await(user_to_update)
    assert created_profile_instance is not None
    mock_db_session.refresh.assert_any_await(created_profile_instance)

# 修改测试用例，注入 mock_user_repo
async def test_update_user_basic_and_existing_profile(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试同时更新基本信息和更新现有 Profile"""
    user_id = uuid4()
    profile_id = uuid4()
    user_to_update = User(id=user_id, email="combo3@example.com", hashed_password="hash", full_name="Old Combo 3")
    existing_profile = UserProfile(id=profile_id, user_id=user_id, bio="Old Bio 3")
    profile_update_data = UserProfileUpdate(bio="Updated Combo Bio 3")
    user_update_data = UserUpdate(full_name="New Combo Name 3", profile=profile_update_data)

    mock_user_repo.get_profile_by_user_id.return_value = existing_profile

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user.full_name == "New Combo Name 3"
    assert updated_profile is not None
    assert updated_profile.bio == "Updated Combo Bio 3"
    # 确认仓库调用
    mock_user_repo.update_user.assert_awaited_once_with(user_to_update)
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)
    mock_user_repo.update_user_profile.assert_awaited_once_with(existing_profile)
    # 确认事务
    mock_db_session.commit.assert_awaited_once()
    # 确认 refresh 被调用 (user 和 profile)
    assert mock_db_session.refresh.await_count == 2
    mock_db_session.refresh.assert_any_await(user_to_update)
    mock_db_session.refresh.assert_any_await(existing_profile)

# 修改测试用例，注入 mock_user_repo
async def test_update_user_empty_profile_data(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试传入空的 Profile 更新数据"""
    user_id = uuid4()
    user_to_update = User(id=user_id, email="empty@example.com", hashed_password="hash")
    user_update_data = UserUpdate(profile=UserProfileUpdate()) # 空的 profile

    # 模拟仓库 profile 查询返回 None 或 Existing, 结果应该一样
    mock_user_repo.get_profile_by_user_id.return_value = None

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user is user_to_update # 用户本身未更新
    assert updated_profile is None # Profile 也未更新
    # 不应该有仓库写入调用
    mock_user_repo.update_user.assert_not_awaited()
    mock_user_repo.create_user_profile.assert_not_awaited()
    mock_user_repo.update_user_profile.assert_not_awaited()
    # 确认事务: commit 不应被调用，因为无更改
    mock_db_session.commit.assert_not_awaited()
    mock_db_session.refresh.assert_not_awaited() # 因为 commit 没发生

# 修改测试用例，注入 mock_user_repo
async def test_update_user_profile_clear_fields(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试更新用户 Profile 时将字段设置为空"""
    user_id = uuid4()
    profile_id = uuid4()
    user_to_update = User(id=user_id, email="clearprofile@example.com", hashed_password="hash")
    existing_profile = UserProfile(id=profile_id, user_id=user_id, bio="Has Bio", phone_number="12345")
    profile_update_data = UserProfileUpdate(bio="Still Has Bio", phone_number=None)
    user_update_data = UserUpdate(profile=profile_update_data)

    mock_user_repo.get_profile_by_user_id.return_value = existing_profile

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_profile is not None
    assert updated_profile.bio == "Still Has Bio"
    assert updated_profile.phone_number is None # 确认字段被清空
    assert updated_profile is existing_profile
    # 确认仓库调用
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)
    mock_user_repo.update_user_profile.assert_awaited_once_with(existing_profile)
    # 确认事务
    mock_db_session.commit.assert_awaited_once()
    # 确认 refresh 被调用 (user 和 profile)
    assert mock_db_session.refresh.await_count == 2
    mock_db_session.refresh.assert_any_await(user_to_update)
    mock_db_session.refresh.assert_any_await(existing_profile)

# 修改测试用例，注入 mock_user_repo
async def test_update_user_only_profile(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试只更新用户 Profile，不更新 User 基本信息"""
    user_id = uuid4()
    profile_id = uuid4()
    user_to_update = User(id=user_id, email="onlyprofile@example.com", hashed_password="hash", full_name="Original Name")
    existing_profile = UserProfile(id=profile_id, user_id=user_id, bio="Old Bio")
    profile_update_data = UserProfileUpdate(bio="Updated Bio Only")
    user_update_data = UserUpdate(profile=profile_update_data)

    mock_user_repo.get_profile_by_user_id.return_value = existing_profile

    user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)
    updated_user, updated_profile = await user_service.update_user(
        user_to_update=user_to_update, user_update_data=user_update_data
    )

    assert updated_user is user_to_update # User 对象本身未变
    assert updated_user.full_name == "Original Name" # User 字段未变
    assert updated_profile is not None
    assert updated_profile.bio == "Updated Bio Only"
    assert updated_profile is existing_profile
    # 确认仓库调用
    mock_user_repo.update_user.assert_not_awaited() # User 未更新
    mock_user_repo.get_profile_by_user_id.assert_awaited_once_with(user_id)
    mock_user_repo.update_user_profile.assert_awaited_once_with(existing_profile)
    # 确认事务
    mock_db_session.commit.assert_awaited_once()
    # 确认 refresh 被调用 (user 和 profile)
    assert mock_db_session.refresh.await_count == 2
    mock_db_session.refresh.assert_any_await(user_to_update)
    mock_db_session.refresh.assert_any_await(existing_profile)

# 修改测试用例，注入 mock_user_repo
async def test_create_user_commit_fails(mock_db_session: MagicMock, mock_user_repo: MagicMock):
    """测试创建用户时数据库提交失败"""
    user_in = UserCreate(
        email="createfail@example.com",
        password="password123",
        username="createfail",
    )
    # 模拟仓库的 get_by_email (检查邮箱是否存在)
    mock_user_repo.get_by_email.return_value = None

    # 模拟 commit 失败
    commit_error = RuntimeError("DB commit failed during create")
    mock_db_session.commit.side_effect = commit_error

    with patch('app.services.user_service.get_password_hash', return_value="hashed"):
        user_service = UserService(db=mock_db_session, user_repo=mock_user_repo)

        # 使用 pytest.raises 检查是否抛出了预期的 RuntimeError
        with pytest.raises(RuntimeError, match="DB commit failed during create"):
            await user_service.create_user(user_create_data=user_in)

    # 确认调用了 get_by_email 和 create_user
    mock_user_repo.get_by_email.assert_awaited_once_with(user_in.email)
    mock_user_repo.create_user.assert_awaited_once()
    # 确认尝试了 commit
    mock_db_session.commit.assert_awaited_once()
    # 确认调用了 rollback
    mock_db_session.rollback.assert_awaited_once()
    # 确认 refresh 没有被调用
    mock_db_session.refresh.assert_not_awaited()