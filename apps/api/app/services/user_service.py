from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User, UserProfile, UserRole
from app.schemas.user import UserUpdate, UserCreate
from app.core.security import get_password_hash
from app.core.logging import get_logger
# 导入仓库接口
from app.repositories.interfaces.user_interface import IUserRepository
# 导入自定义异常
from app.core.exceptions import EmailAlreadyExistsException, UserNotFoundException

logger = get_logger(__name__)

# --- 添加异常类定义 ---
# class UserNotFoundException(Exception):
#     \"\"\"当尝试操作的用户不存在时抛出\"\"\"
#     pass

# class EmailAlreadyExistsException(Exception):
#     \"\"\"当尝试创建的用户邮箱已存在时抛出\"\"\"
#     pass
# --- 结束添加 ---

class UserService:
    """用户相关的业务逻辑服务"""

    def __init__(self, db: AsyncSession, user_repo: IUserRepository):
        self.db = db # 仍然需要 db 来管理事务
        self.user_repo = user_repo # 依赖仓库接口
        self.logger = get_logger(__name__)

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """通过ID获取单个用户 (现在通过仓库)"""
        self.logger.debug(f"服务层: 开始查询用户 {user_id}")
        # 调用仓库方法
        user = await self.user_repo.get_by_id(user_id)
        if user:
            self.logger.debug(f"服务层: 找到用户 {user_id}")
        else:
            self.logger.debug(f"服务层: 未找到用户 {user_id}")
        return user

    async def get_user_with_profile(self, user_id: UUID) -> Optional[tuple[User, Optional[UserProfile]]]:
        """获取用户及其关联的个人资料 (现在通过仓库)"""
        self.logger.debug(f"服务层: 开始查询用户及资料 {user_id}")
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # 通过仓库获取 profile
        profile = await self.user_repo.get_profile_by_user_id(user_id)
        self.logger.debug(f"服务层: 获取用户 {user_id} 的资料完成 (资料存在: {profile is not None}) ")
        return user, profile

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表 (分页) (现在通过仓库)"""
        self.logger.debug(f"服务层: 开始查询用户列表 (skip={skip}, limit={limit})")
        # 调用仓库方法
        users = await self.user_repo.list_users(skip=skip, limit=limit)
        self.logger.debug(f"服务层: 成功获取 {len(users)} 个用户")
        return users

    async def update_user(self, user_to_update: User, user_update_data: UserUpdate) -> tuple[User, Optional[UserProfile]]:
        """更新用户信息和资料"""
        self.logger.debug(f"服务层: 开始更新用户 {user_to_update.id}")
        user_data = user_update_data.model_dump(exclude_unset=True, exclude={"profile", "password"})
        profile_updated = False
        user_updated = False

        # 更新用户基本信息
        if user_data:
            for key, value in user_data.items():
                setattr(user_to_update, key, value)
            # 调用仓库更新 user (只是添加到 session)
            await self.user_repo.update_user(user_to_update)
            user_updated = True
            self.logger.debug(f"服务层: 用户 {user_to_update.id} 基本信息变更已加入事务")

        # 更新密码
        if user_update_data.password:
            hashed_password = get_password_hash(user_update_data.password)
            user_to_update.hashed_password = hashed_password
            # 调用仓库更新 user (只是添加到 session)
            if not user_updated: # 避免重复添加
                await self.user_repo.update_user(user_to_update)
                user_updated = True
            self.logger.info(f"服务层: 用户 {user_to_update.id} 密码变更已加入事务")

        # 处理资料更新
        updated_profile = None
        if user_update_data.profile:
            profile_data = user_update_data.profile.model_dump(exclude_unset=True)
            if profile_data:
                # 通过仓库查询现有资料
                profile = await self.user_repo.get_profile_by_user_id(user_to_update.id)

                if profile:
                    self.logger.debug(f"服务层: 更新用户 {user_to_update.id} 的现有资料")
                    for key, value in profile_data.items():
                        setattr(profile, key, value)
                    # 调用仓库更新 profile (只是添加到 session)
                    await self.user_repo.update_user_profile(profile)
                    updated_profile = profile
                    profile_updated = True
                else:
                    self.logger.debug(f"服务层: 为用户 {user_to_update.id} 创建新的资料")
                    new_profile = UserProfile(user_id=user_to_update.id, **profile_data)
                    # 调用仓库创建 profile (只是添加到 session)
                    await self.user_repo.create_user_profile(new_profile)
                    updated_profile = new_profile # 此时还没有 ID
                    profile_updated = True
        
        # --- 事务管理 --- 
        if not user_updated and not profile_updated:
             self.logger.debug(f"服务层: 用户 {user_to_update.id} 无任何更新, 无需提交")
             # 如果没有更新，仍然尝试获取最新的 profile 返回
             if not updated_profile: 
                 updated_profile = await self.user_repo.get_profile_by_user_id(user_to_update.id)
             return user_to_update, updated_profile
             
        try:
            # 提交事务
            await self.db.commit()
            self.logger.debug(f"服务层: 用户 {user_to_update.id} 更新事务已提交")
            
            # 刷新数据 (从数据库加载最新状态，包括生成的 ID)
            # 总是尝试刷新 user 对象，以获取最新状态 (即使只有 profile 更新)
            # if user_updated:
            await self.db.refresh(user_to_update)
            self.logger.debug(f"服务层: 用户 {user_to_update.id} 数据已刷新")
            
            if profile_updated and updated_profile:
                 await self.db.refresh(updated_profile)
                 self.logger.debug(f"服务层: 用户 {user_to_update.id} 资料数据已刷新")

            self.logger.info(f"服务层: 用户 {user_to_update.id} 信息更新成功")
            # 如果 profile 未在本次更新，提交后重新获取一次以确保返回最新
            if not updated_profile:
                 updated_profile = await self.user_repo.get_profile_by_user_id(user_to_update.id)
                
            return user_to_update, updated_profile
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"服务层: 更新用户 {user_to_update.id} 失败: {str(e)}", exc_info=True)
            # 不再抛出 HTTPException，让全局处理器处理
            raise e

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户 (现在通过仓库)"""
        self.logger.debug(f"服务层: 开始查询用户 (邮箱: {email}) ")
        # 调用仓库方法
        user = await self.user_repo.get_by_email(email)
        if user:
            self.logger.debug(f"服务层: 找到用户 (邮箱: {email}) ")
        else:
            self.logger.debug(f"服务层: 未找到用户 (邮箱: {email}) ")
        return user

    async def create_user(self, user_create_data: UserCreate) -> User:
        """创建新用户"""
        self.logger.debug(f"服务层: 开始创建用户 (邮箱: {user_create_data.email}) ")
        
        # 在服务层进行邮箱存在性检查 (调用仓库)
        existing_user = await self.user_repo.get_by_email(user_create_data.email)
        if existing_user:
            self.logger.warning(f"服务层: 注册失败 - 邮箱 {user_create_data.email} 已存在")
            raise EmailAlreadyExistsException(f"邮箱 {user_create_data.email} 已被注册")
            
        try:
            hashed_password = get_password_hash(user_create_data.password)
            self.logger.debug(f"密码哈希生成成功")

            db_user = User(
                email=user_create_data.email.lower(),
                hashed_password=hashed_password,
                username=user_create_data.username,
                full_name=user_create_data.full_name,
                role=user_create_data.role or UserRole.USER,
                is_verified=False,
                created_at=datetime.now(timezone.utc),
                # 依赖 User 模型中的默认值 (is_active=True, is_superuser=False)
            )

            # 调用仓库创建用户 (添加到 session)
            await self.user_repo.create_user(db_user)
            self.logger.debug(f"服务层: 新用户 {db_user.email} 已加入事务")

            # --- 事务管理 ---
            await self.db.commit()
            self.logger.debug(f"服务层: 创建用户事务已提交")
            await self.db.refresh(db_user)
            self.logger.debug(f"服务层: 新用户 {db_user.email} 数据已刷新")
            
            self.logger.info(f"服务层: 新用户创建成功 (ID: {db_user.id}) ")
            return db_user
        except EmailAlreadyExistsException: # 再次捕获以防万一 (理论上前面检查过了)
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"服务层: 创建用户失败: {str(e)}", exc_info=True)
            # 不再抛出 HTTPException，让全局处理器处理
            raise e

# 不再需要全局 logger，因为每个服务实例都有自己的 logger
# logger = get_logger(__name__) 