from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.logging import get_logger
from app.services.user_service import user_service

# 创建模块日志记录器
logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取用户列表。
    (需要管理员权限)
    """
    logger.info(f"用户 {current_user.id} 请求获取用户列表 (skip={skip}, limit={limit})")

    # --- 权限检查 (保留在API层) ---
    if not current_user.is_superuser:
        logger.warning(f"权限不足: 用户 {current_user.id} 尝试访问用户列表，但不是超级用户")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )

    # --- 调用服务层 ---
    try:
        users = await user_service.get_users(db=db, skip=skip, limit=limit)
        logger.info(f"成功获取 {len(users)} 个用户记录")
        # FastAPI 会自动处理 response_model 的转换
        return users
    except Exception as e:
        # 服务层通常会处理内部错误，但这里可以加一层以防万一
        logger.error(f"获取用户列表失败 (API层): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表时发生错误"
        )


@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    获取当前用户信息（包含个人资料）。
    """
    logger.info(f"用户 {current_user.id} 请求获取个人信息")

    # --- 调用服务层获取用户和资料 ---
    # 注意: current_user 是通过 get_current_user 获取的，可能不包含 profile
    # 我们需要通过服务层重新获取完整的用户和资料信息
    try:
        user_data = await user_service.get_user_with_profile(db=db, user_id=current_user.id)
        if not user_data:
             # 这理论上不应该发生，因为 current_user 存在
             logger.error(f"获取当前用户信息失败: 未找到用户 {current_user.id}")
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

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
    except Exception as e:
        logger.error(f"获取当前用户信息失败 (API层): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息时发生错误"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    根据ID获取用户（包含个人资料）。
    (需要管理员权限或用户本人)
    """
    logger.info(f"用户 {current_user.id} 请求获取用户 {user_id} 的信息")

    # --- 权限检查 (保留在API层) ---
    if not current_user.is_superuser and current_user.id != user_id:
        logger.warning(f"权限不足: 用户 {current_user.id} 尝试访问用户 {user_id} 的信息")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法访问其他用户信息"
        )

    # --- 调用服务层 ---
    try:
        user_data = await user_service.get_user_with_profile(db=db, user_id=user_id)

        if not user_data:
            logger.warning(f"未找到用户: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        user, profile = user_data
        logger.info(f"成功获取用户 {user_id} 的信息")

        # --- 构建响应 ---
        response_data = UserResponse.model_validate(user)
        if profile:
            response_data.profile = profile

        return response_data
    except HTTPException:
        # 直接重新抛出服务层或权限检查抛出的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取用户 {user_id} 信息失败 (API层): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息时发生错误"
        )


@router.patch("/me", response_model=UserResponse)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    更新当前用户信息（包含个人资料）。
    """
    logger.info(f"用户 {current_user.id} 请求更新个人信息")

    # --- 调用服务层 ---
    try:
        # 注意：我们将 current_user (从 token 获取的 User 对象)
        # 和 user_update (请求体中的更新数据) 传递给服务层
        updated_user, updated_profile = await user_service.update_user(
            db=db, user_to_update=current_user, user_update_data=user_update
        )

        # --- 构建响应 ---
        response_data = UserResponse.model_validate(updated_user)
        if updated_profile:
            response_data.profile = updated_profile

        return response_data

    except HTTPException:
         # 直接重新抛出服务层可能抛出的HTTP异常 (例如更新失败)
        raise
    except Exception as e:
        # 服务层的 update_user 应该已经处理了 rollback，这里只需记录和返回错误
        logger.error(f"更新用户信息失败 (API层): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息时发生错误"
        ) 