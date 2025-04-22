from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User, UserProfile
from app.repositories.interfaces.user_interface import IUserRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

class SQLUserRepository(IUserRepository):
    """SQL 实现的用户仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        self.logger.debug(f"仓库层: 查询用户 ID: {user_id}")
        user = await self.session.get(User, user_id)
        if user:
             self.logger.debug(f"仓库层: 找到用户 {user_id}")
        else:
             self.logger.debug(f"仓库层: 未找到用户 {user_id}")
        return user


    async def get_by_email(self, email: str) -> Optional[User]:
        self.logger.debug(f"仓库层: 查询用户邮箱: {email}")
        query = select(User).where(User.email == email.lower())
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if user:
             self.logger.debug(f"仓库层: 找到用户 (邮箱: {email})")
        else:
             self.logger.debug(f"仓库层: 未找到用户 (邮箱: {email})")
        return user

    async def get_profile_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        self.logger.debug(f"仓库层: 查询用户 {user_id} 的资料")
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(query)
        profile = result.scalar_one_or_none()
        self.logger.debug(f"仓库层: 用户 {user_id} 资料查询完成 (存在: {profile is not None})")
        return profile

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        self.logger.debug(f"仓库层: 查询用户列表 (skip={skip}, limit={limit})")
        query = select(User).offset(skip).limit(limit)
        result = await self.session.execute(query)
        users = list(result.scalars().all()) # 转为 list
        self.logger.debug(f"仓库层: 获取 {len(users)} 个用户")
        return users

    async def create_user(self, user: User) -> User:
        self.logger.debug(f"仓库层: 添加新用户到 session (邮箱: {user.email})")
        self.session.add(user)
        # 注意：commit 和 refresh 不在这里做，由调用方（服务层或UoW）管理事务
        self.logger.debug(f"仓库层: 用户 {user.email} 已添加到 session")
        return user # 返回传入的对象，等待 refresh
        
    async def create_user_profile(self, profile: UserProfile) -> UserProfile:
        self.logger.debug(f"仓库层: 添加新用户资料到 session (用户 ID: {profile.user_id})")
        self.session.add(profile)
        self.logger.debug(f"仓库层: 用户资料 {profile.user_id} 已添加到 session")
        return profile

    async def update_user(self, user: User) -> User:
        self.logger.debug(f"仓库层: 添加待更新的用户到 session (ID: {user.id})")
        self.session.add(user) # SQLModel 通过主键识别是更新还是插入
        self.logger.debug(f"仓库层: 用户 {user.id} 更新已添加到 session")
        return user # 返回传入的对象，等待 refresh
        
    async def update_user_profile(self, profile: UserProfile) -> UserProfile:
        self.logger.debug(f"仓库层: 添加待更新的用户资料到 session (ID: {profile.id})")
        self.session.add(profile)
        self.logger.debug(f"仓库层: 用户资料 {profile.id} 更新已添加到 session")
        return profile
        
    # 事务管理 (commit, rollback, refresh) 应该在更高层次处理
    # 例如：服务层方法结束时统一 commit/rollback
    # 或者引入 Unit of Work (UoW) 模式来管理事务边界 