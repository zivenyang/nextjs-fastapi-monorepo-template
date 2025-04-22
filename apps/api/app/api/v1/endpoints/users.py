from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, status
# 不再需要直接从端点导入 AsyncSession
# from sqlmodel.ext.asyncio.session import AsyncSession
# 不再直接使用 HTTPException
# from fastapi import HTTPException

# 导入新的依赖和类型
from app.api.deps import get_current_user, get_user_service, get_settings
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.logging import get_logger
# 导入 UserService 和 Settings 类型
from app.services.user_service import UserService
from app.core.config import Settings
# 导入自定义异常
from app.core.exceptions import UserNotFoundException, ForbiddenException, AppException

# 创建模块日志记录器
logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def read_users(
    # 移除 db: AsyncSession = Depends(get_db)
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    # 注入依赖
    user_service_instance: UserService = Depends(get_user_service),
    app_settings: Settings = Depends(get_settings),
) -> Any:
    """
    获取用户列表。
    (需要管理员权限)
    """
    logger.info(f"用户 {current_user.id} 请求获取用户列表 (skip={skip}, limit={limit})")

    # --- 权限检查 (保留在API层) ---
    if not current_user.is_superuser:
        logger.warning(f"权限不足: 用户 {current_user.id} 尝试访问用户列表，但不是超级用户")
        # 使用自定义异常
        raise ForbiddenException(detail="权限不足，需要管理员权限")

    # --- 调用注入的服务实例 --- (不再传递 db)
    # 移除 try...except，让全局处理器处理
    users = await user_service_instance.get_users(skip=skip, limit=limit)
    logger.info(f"成功获取 {len(users)} 个用户记录")
    # FastAPI 会自动处理 response_model 的转换
    return users


@router.get("/me", response_model=UserResponse)
async def read_user_me(
    # 移除 db: AsyncSession = Depends(get_db)
    current_user: User = Depends(get_current_user),
    # 注入依赖
    user_service_instance: UserService = Depends(get_user_service),
    app_settings: Settings = Depends(get_settings),
) -> Any:
    """
    获取当前用户信息（包含个人资料）。
    """
    logger.info(f"用户 {current_user.id} 请求获取个人信息")

    # --- 调用注入的服务实例，不再传递 db ---
    # 移除 try...except，让全局处理器处理
    user_data = await user_service_instance.get_user_with_profile(user_id=current_user.id)
    if not user_data:
        # 这理论上不应该发生，因为 current_user 存在
        logger.error(f"获取当前用户信息失败: 未找到用户 {current_user.id}")
        # 使用自定义异常
        raise UserNotFoundException(detail="当前用户未在数据库中找到")

    user, profile = user_data

    # --- 构建响应 ---
    # 使用 UserResponse.model_validate 来创建响应模型实例
    # Pydantic v2 使用 model_validate 替代 from_orm
    response_data = UserResponse.model_validate(user)
    # 注意：UserResponse 需要能处理 profile=None 的情况
    if profile:
        # Pydantic 会自动将 UserProfile ORM 对象转换为 UserProfileResponse
        response_data.profile = profile

    return response_data


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: UUID,
    # 移除 db: AsyncSession = Depends(get_db)
    current_user: User = Depends(get_current_user),
    # 注入依赖
    user_service_instance: UserService = Depends(get_user_service),
    app_settings: Settings = Depends(get_settings),
) -> Any:
    """
    根据ID获取用户（包含个人资料）。
    (需要管理员权限或用户本人)
    """
    logger.info(f"用户 {current_user.id} 请求获取用户 {user_id} 的信息")

    # --- 权限检查 (保留在API层) ---
    if not current_user.is_superuser and current_user.id != user_id:
        logger.warning(f"权限不足: 用户 {current_user.id} 尝试访问用户 {user_id} 的信息")
        # 使用自定义异常
        raise ForbiddenException(detail="权限不足，无法访问其他用户信息")

    # --- 调用注入的服务实例，不再传递 db ---
    # 移除 try...except，让全局处理器处理
    user_data = await user_service_instance.get_user_with_profile(user_id=user_id)

    if not user_data:
        logger.warning(f"未找到用户: {user_id}")
        # 使用自定义异常
        raise UserNotFoundException(detail="用户不存在")

    user, profile = user_data
    logger.info(f"成功获取用户 {user_id} 的信息")

    # --- 构建响应 ---
    response_data = UserResponse.model_validate(user)
    if profile:
        response_data.profile = profile

    return response_data


@router.patch("/me", response_model=UserResponse)
async def update_user_me(
    *,
    # 移除 db: AsyncSession = Depends(get_db)
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    # 注入依赖
    user_service_instance: UserService = Depends(get_user_service),
    app_settings: Settings = Depends(get_settings),
) -> Any:
    """
    更新当前用户信息（包含个人资料）。
    """
    logger.info(f"用户 {current_user.id} 请求更新个人信息")

    # --- 调用注入的服务实例，不再传递 db ---
    # 移除 try...except，让全局处理器处理
    # 注意：我们将 current_user (从 token 获取的 User 对象)
    # 和 user_update (请求体中的更新数据) 传递给服务层
    updated_user, updated_profile = await user_service_instance.update_user(
        user_to_update=current_user, user_update_data=user_update
    )

    # --- 构建响应 ---
    response_data = UserResponse.model_validate(updated_user)
    if updated_profile:
        response_data.profile = updated_profile

    return response_data 