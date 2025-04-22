from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User, UserProfile, UserRole
from app.schemas.user import UserUpdate, UserCreate
from app.core.security import get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)

class UserService:
    """用户相关的业务逻辑服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # 初始化 logger 实例
        self.logger = get_logger(__name__)

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """通过ID获取单个用户"""
        self.logger.debug(f"服务层: 开始查询用户 {user_id}")
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            self.logger.debug(f"服务层: 找到用户 {user_id}")
        else:
            self.logger.debug(f"服务层: 未找到用户 {user_id}")
        return user

    async def get_user_with_profile(self, user_id: UUID) -> Optional[tuple[User, Optional[UserProfile]]]:
        """获取用户及其关联的个人资料"""
        self.logger.debug(f"服务层: 开始查询用户及资料 {user_id}")
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        profile_query = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_result = await self.db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()
        self.logger.debug(f"服务层: 获取用户 {user_id} 的资料完成 (资料存在: {profile is not None})")
        return user, profile

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表 (分页)"""
        self.logger.debug(f"服务层: 开始查询用户列表 (skip={skip}, limit={limit})")
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()
        self.logger.debug(f"服务层: 成功获取 {len(users)} 个用户")
        return users

    async def update_user(self, user_to_update: User, user_update_data: UserUpdate) -> tuple[User, Optional[UserProfile]]:
        """更新用户信息和资料"""
        self.logger.debug(f"服务层: 开始更新用户 {user_to_update.id}")
        user_data = user_update_data.model_dump(exclude_unset=True, exclude={"profile", "password"})

        # 更新用户基本信息
        if user_data:
            for key, value in user_data.items():
                setattr(user_to_update, key, value)
            self.db.add(user_to_update)
            self.logger.debug(f"服务层: 用户 {user_to_update.id} 基本信息已更新")

        # 更新密码
        if user_update_data.password:
            hashed_password = get_password_hash(user_update_data.password)
            user_to_update.hashed_password = hashed_password
            self.db.add(user_to_update)
            self.logger.info(f"服务层: 用户 {user_to_update.id} 密码已更新")

        # 处理资料更新
        updated_profile = None
        if user_update_data.profile:
            profile_data = user_update_data.profile.model_dump(exclude_unset=True)
            if profile_data:
                # 查询现有资料
                query = select(UserProfile).where(UserProfile.user_id == user_to_update.id)
                result = await self.db.execute(query)
                profile = result.scalar_one_or_none()

                if profile:
                    self.logger.debug(f"服务层: 更新用户 {user_to_update.id} 的现有资料")
                    for key, value in profile_data.items():
                        setattr(profile, key, value)
                    self.db.add(profile)
                    updated_profile = profile
                else:
                    self.logger.debug(f"服务层: 为用户 {user_to_update.id} 创建新的资料")
                    new_profile = UserProfile(user_id=user_to_update.id, **profile_data)
                    self.db.add(new_profile)
                    updated_profile = new_profile
        
        try:
            await self.db.commit()
            await self.db.refresh(user_to_update)
            if updated_profile:
                 if profile and profile is updated_profile:
                     await self.db.refresh(updated_profile)

            self.logger.info(f"服务层: 用户 {user_to_update.id} 信息更新成功")
            if not updated_profile:
                profile_query = select(UserProfile).where(UserProfile.user_id == user_to_update.id)
                profile_result = await self.db.execute(profile_query)
                updated_profile = profile_result.scalar_one_or_none()
                
            return user_to_update, updated_profile
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"服务层: 更新用户 {user_to_update.id} 失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户信息时发生内部错误"
            )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        self.logger.debug(f"服务层: 开始查询用户 (邮箱: {email})")
        query = select(User).where(User.email == email.lower())
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            self.logger.debug(f"服务层: 找到用户 (邮箱: {email})")
        else:
            self.logger.debug(f"服务层: 未找到用户 (邮箱: {email})")
        return user

    async def create_user(self, user_create_data: UserCreate) -> User:
        """创建新用户"""
        self.logger.debug(f"服务层: 开始创建用户 (邮箱: {user_create_data.email})")
        
        # 在服务层进行邮箱存在性检查
        existing_user = await self.get_user_by_email(user_create_data.email)
        if existing_user:
            self.logger.warning(f"服务层: 注册失败 - 邮箱 {user_create_data.email} 已存在")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )
            
        try:
            hashed_password = get_password_hash(user_create_data.password)
            self.logger.debug(f"密码哈希生成成功")

            # 明确指定要传递给 User 模型的字段
            # 不再从 user_create_data 获取 is_active 和 is_superuser
            # 依赖 User 模型中的默认值 (is_active=True, is_superuser=False)
            db_user = User(
                email=user_create_data.email.lower(),
                hashed_password=hashed_password,
                username=user_create_data.username,
                full_name=user_create_data.full_name,
                role=user_create_data.role or UserRole.USER,  # 设置默认角色
                is_verified=False, # 新用户默认未验证
                created_at=datetime.now(timezone.utc),
            )

            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
            self.logger.info(f"服务层: 新用户创建成功 (ID: {db_user.id})")
            return db_user
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"服务层: 创建用户失败: {str(e)}", exc_info=True)
            # 重新抛出通用错误，让上层处理
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建用户时发生内部错误"
            )

# 不再需要全局 logger，因为每个服务实例都有自己的 logger
# logger = get_logger(__name__) 