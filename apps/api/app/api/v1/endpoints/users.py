from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserResponse, UserUpdate
from app.core.logging import get_logger

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
    """
    logger.info(f"用户 {current_user.id} 请求获取用户列表 (skip={skip}, limit={limit})")
    
    # 只有超级用户可以获取用户列表
    if not current_user.is_superuser:
        logger.warning(f"权限不足: 用户 {current_user.id} 尝试访问用户列表，但不是超级用户")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    query = select(User).offset(skip).limit(limit)
    logger.debug(f"执行查询: {query}")
    
    try:
        result = await db.execute(query)
        users = result.scalars().all()
        logger.info(f"成功获取 {len(users)} 个用户记录")
        return users
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
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
    获取当前用户信息。
    """
    logger.info(f"用户 {current_user.id} 请求获取个人信息")
    
    # 加载用户资料
    try:
        query = select(UserProfile).where(UserProfile.user_id == current_user.id)
        logger.debug(f"执行查询用户资料: {query}")
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        
        # 将资料附加到用户对象
        response_data = UserResponse.model_validate(current_user)
        response_data.profile = profile
        
        return response_data
    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}", exc_info=True)
        # 即使获取资料失败，仍返回用户基本信息
        return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    根据ID获取用户。
    """
    logger.info(f"用户 {current_user.id} 请求获取用户 {user_id} 的信息")
    
    # 检查权限：只有超级用户或请求自己的信息才允许
    if not current_user.is_superuser and current_user.id != user_id:
        logger.warning(f"权限不足: 用户 {current_user.id} 尝试访问用户 {user_id} 的信息")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法访问其他用户信息"
        )
    
    try:
        query = select(User).where(User.id == user_id)
        logger.debug(f"执行查询: {query}")
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"未找到用户: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 加载用户资料
        profile_query = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()
        
        # 构建响应
        response_data = UserResponse.model_validate(user)
        response_data.profile = profile
        
        logger.info(f"成功获取用户 {user_id} 的信息")
        return response_data
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取用户 {user_id} 信息失败: {str(e)}", exc_info=True)
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
    更新当前用户信息。
    """
    logger.info(f"用户 {current_user.id} 请求更新个人信息")
    
    try:
        # 更新用户基本信息
        user_data = user_update.model_dump(exclude_unset=True, exclude={"profile"})
        
        if user_data:
            for key, value in user_data.items():
                setattr(current_user, key, value)
            
            db.add(current_user)
        
        # 处理资料更新
        if user_update.profile:
            profile_data = user_update.profile.model_dump(exclude_unset=True)
            if profile_data:
                # 查询现有资料
                query = select(UserProfile).where(UserProfile.user_id == current_user.id)
                result = await db.execute(query)
                profile = result.scalar_one_or_none()
                
                if profile:
                    # 更新现有资料
                    for key, value in profile_data.items():
                        setattr(profile, key, value)
                    db.add(profile)
                else:
                    # 创建新资料
                    new_profile = UserProfile(user_id=current_user.id, **profile_data)
                    db.add(new_profile)
        
        # 提交更改
        await db.commit()
        await db.refresh(current_user)
        
        # 重新加载完整用户信息，包括资料
        return await read_user_me(current_user, db)
    
    except Exception as e:
        await db.rollback()
        logger.error(f"更新用户信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息时发生错误"
        ) 