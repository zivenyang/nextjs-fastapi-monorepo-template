from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from app.models.user import User, UserProfile


class IUserRepository(ABC):
    """用户仓库接口 (抽象基类)"""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """通过 ID 获取用户"""
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        raise NotImplementedError

    @abstractmethod
    async def get_profile_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        """通过用户 ID 获取用户资料"""
        raise NotImplementedError

    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表 (分页)"""
        raise NotImplementedError

    @abstractmethod
    async def create_user(self, user: User) -> User:
        """创建新用户 (添加到 session)"""
        raise NotImplementedError

    @abstractmethod
    async def create_user_profile(self, profile: UserProfile) -> UserProfile:
        """创建用户资料 (添加到 session)"""
        raise NotImplementedError

    @abstractmethod
    async def update_user(self, user: User) -> User:
        """更新用户信息 (添加到 session)"""
        raise NotImplementedError
        
    @abstractmethod
    async def update_user_profile(self, profile: UserProfile) -> UserProfile:
        """更新用户资料 (添加到 session)"""
        raise NotImplementedError

    # 注意：接口通常不包含事务管理方法 (commit, rollback, refresh)
    # 这些由更高层（如 Unit of Work 或服务层）处理 