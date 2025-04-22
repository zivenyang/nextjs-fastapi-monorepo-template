from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
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
         raise HTTPException(status_code=500, detail="数据库连接失败")
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

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_jwt_token(token)
        if payload is None:
            logger.warning("获取当前用户失败: 令牌解码失败或无效")
            raise credentials_exception

        user_id: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")

        if user_id is None:
            logger.warning("获取当前用户失败: 令牌中缺少 'sub' (user_id)")
            raise credentials_exception

        if jti and await is_blacklisted(jti):
            logger.warning(f"获取当前用户失败: 令牌已加入黑名单 (jti: {jti})")
            raise credentials_exception

    except JWTError as e:
        logger.warning(f"获取当前用户失败: JWT错误 - {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"获取当前用户时发生意外错误: {str(e)}", exc_info=True)
        raise credentials_exception

    # --- 用户查找：保持使用 db.get 或改为使用仓库 --- 
    # 方案 A: 保持现状 (直接用 db.get)
    user = await db.get(User, UUID(user_id))
    # 方案 B: 改为使用仓库 (需要注入 user_repo)
    # user = await user_repo.get_by_id(UUID(user_id))
    
    if user is None:
        logger.warning(f"获取当前用户失败: 未找到用户ID {user_id}")
        raise credentials_exception
    
    logger.debug(f"成功获取当前用户: {user.id} ({user.email})")
    return user
