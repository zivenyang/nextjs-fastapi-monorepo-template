from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings, Settings
from app.core.db import get_session
from app.models.user import User
from app.schemas.auth import TokenPayload
from app.core.logging import get_logger
from app.core.token_blacklist import is_blacklisted
from app.core import security
from app.services.user_service import UserService
from app.repositories.interfaces.user_interface import IUserRepository
from app.repositories.sql.user_repository import SQLUserRepository
from app.core.exceptions import (
    InvalidTokenException,
    UserNotFoundException,
    AppException # 基础异常可能也需要
)

# 创建模块日志记录器
logger = get_logger(__name__)

# OAuth2 密码流认证令牌URL - 使用配置中的值
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.FULL_AUTH_TOKEN_URL)

# 数据库会话依赖
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话的FastAPI依赖"""
    logger.debug("获取数据库会话依赖")
    # 假设 engine 在 app.core.db 中正确配置
    # 这里的 get_session 可能需要调整以适应SQLModel
    # 暂时保持现有结构，但需要确认其与 SQLModel 兼容
    try:
        async with get_session() as session: # 使用 app.core.db.get_session
             logger.debug("数据库会话已生成并提供")
             yield session
    except Exception as e:
         logger.error(f"获取数据库会话失败: {e}", exc_info=True)
         # 让全局处理器处理
         raise # 或者 raise DatabaseConnectionError() 如果定义了
    finally:
        logger.debug("数据库会话依赖结束") # 关闭由 context manager 处理

# 配置依赖
def get_settings() -> Settings:
    """返回应用配置实例"""
    return settings

# --- 新增：仓库依赖 ---
def get_user_repository(db: AsyncSession = Depends(get_db)) -> IUserRepository:
    """依赖注入 SQLUserRepository 实例 (返回接口类型)"""
    logger.debug("创建 SQLUserRepository 实例")
    return SQLUserRepository(session=db)

# --- 修改：用户服务依赖 ---
def get_user_service(
    db: AsyncSession = Depends(get_db),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> UserService:
    """依赖注入 UserService 实例 (现在需要仓库)"""
    logger.debug("创建 UserService 实例 (依赖于仓库)")
    return UserService(db=db, user_repo=user_repo)

# 当前用户依赖 (需要确保 get_user_by_id 在仓库中或直接用 db.get)
# 注意: get_current_user 当前直接使用 db.get(User, UUID(user_id))
# 这绕过了仓库层。理想情况下，它应该依赖 UserService 或 UserRepository。
# 为了减少本次修改范围，暂时保持不变，但这是一个后续改进点。
async def get_current_user(
    db: AsyncSession = Depends(get_db), # 保持 db 依赖用于直接查找
    # 或者: user_repo: IUserRepository = Depends(get_user_repository),
    token: str = Depends(security.oauth2_scheme),
    app_settings: Settings = Depends(get_settings)
) -> User:
    """验证token并获取当前用户 (包含黑名单检查)"""
    logger.debug("验证用户令牌")

    try:
        payload = security.decode_jwt_token(token)
        if payload is None:
            logger.warning("获取当前用户失败: 令牌解码失败或无效")
            raise InvalidTokenException(detail="无效或格式错误的认证令牌")

        user_id: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")

        if user_id is None:
            logger.warning("获取当前用户失败: 令牌中缺少 'sub' (user_id)")
            raise InvalidTokenException(detail="无效或格式错误的认证令牌")

        if jti and await is_blacklisted(jti):
            logger.warning(f"获取当前用户失败: 令牌已加入黑名单 (jti: {jti})")
            raise InvalidTokenException(detail="认证令牌已失效 (已登出)")

        # --- 用户查找：保持使用 db.get 或改为使用仓库 --- 
        try:
            user = await db.get(User, UUID(user_id))
        except Exception as e:
            logger.error(f"根据令牌中的 user_id ({user_id}) 查找用户时出错: {e}", exc_info=True)
            raise InvalidTokenException(detail="无法根据令牌查找用户")
            
        if user is None:
            logger.warning(f"获取当前用户失败: 未找到用户ID {user_id}")
            raise UserNotFoundException(detail="令牌对应的用户不存在")

    except (JWTError, ValidationError) as e: # 捕获已知的解码/验证错误
        logger.warning(f"获取当前用户失败: 令牌验证/解码错误 - {str(e)}")
        raise InvalidTokenException(detail="无法验证认证令牌")
    except (InvalidTokenException, UserNotFoundException): # 重新抛出我们自己定义的特定异常
        raise
    except Exception as e: # 捕获真正未预料到的其他错误
        logger.error(f"获取当前用户时发生未预料的服务器内部错误: {str(e)}", exc_info=True)
        # 对于真正意外的错误，应该返回 500
        raise AppException(detail="处理认证时发生内部错误", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    logger.debug(f"成功获取当前用户: {user.id} ({user.email})")
    return user
