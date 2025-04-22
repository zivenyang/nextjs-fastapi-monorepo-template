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

# 创建模块日志记录器
logger = get_logger(__name__)

# OAuth2 密码流认证令牌URL - 使用配置中的值
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.FULL_AUTH_TOKEN_URL)

# 数据库会话依赖
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话的FastAPI依赖"""
    logger.debug("获取数据库会话依赖")
    # get_session 使用了 asynccontextmanager 和 yield，会自动处理会话关闭和回滚
    async with AsyncSession(engine) as session: # 假设 engine 已定义
        try:
            logger.debug("数据库会话已生成并提供")
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            logger.debug("数据库会话生命周期结束 (由 get_session 管理)")

# 配置依赖
def get_settings() -> Settings:
    """返回应用配置实例"""
    return settings

# 用户服务依赖
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """依赖注入 UserService 实例"""
    return UserService(db=db)

# 当前用户依赖
async def get_current_user(
    db: AsyncSession = Depends(get_db),
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
        jti: str | None = payload.get("jti") # 获取 JTI

        if user_id is None:
            logger.warning("获取当前用户失败: 令牌中缺少 'sub' (user_id)")
            raise credentials_exception

        # --- 黑名单检查 --- 
        if jti and await is_blacklisted(jti):
            logger.warning(f"获取当前用户失败: 令牌已加入黑名单 (jti: {jti})")
            raise credentials_exception
        # --- 结束黑名单检查 ---

    except JWTError as e:
        logger.warning(f"获取当前用户失败: JWT错误 - {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"获取当前用户时发生意外错误: {str(e)}", exc_info=True)
        raise credentials_exception

    # 使用注入的 db 获取用户
    user = await db.get(User, UUID(user_id))
    if user is None:
        logger.warning(f"获取当前用户失败: 未找到用户ID {user_id}")
        raise credentials_exception
    
    logger.debug(f"成功获取当前用户: {user.id} ({user.email})")
    return user
