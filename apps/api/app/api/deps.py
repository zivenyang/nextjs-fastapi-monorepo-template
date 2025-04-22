from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.db import get_session
from app.models.user import User
from app.schemas.auth import TokenPayload
from app.core.logging import get_logger
from app.core.token_blacklist import is_blacklisted  # 使用新的函数名

# 创建模块日志记录器
logger = get_logger(__name__)

# OAuth2 密码流认证令牌URL - 使用配置中的值
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.FULL_AUTH_TOKEN_URL)

# 数据库会话依赖
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话的FastAPI依赖"""
    logger.debug("获取数据库会话依赖")
    # get_session 使用了 asynccontextmanager 和 yield，会自动处理会话关闭和回滚
    async for session in get_session():
        try:
            logger.debug("数据库会话已生成并提供")
            yield session
        finally:
            # 不再需要显式关闭，async with async_session() as session 会处理
            # await session.close()
            logger.debug("数据库会话生命周期结束 (由 get_session 管理)")

# 当前用户依赖
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """验证token并获取当前用户"""
    logger.debug("验证用户令牌")
    
    try:
        # 解码JWT令牌
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        # 确保令牌中包含用户ID
        if token_data.sub is None:
            logger.warning(f"令牌验证失败: 令牌不包含用户ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 检查令牌是否在黑名单中
        jti = token_data.jti or str(token_data.sub)
        if await is_blacklisted(jti):  # 使用异步方法
            logger.warning(f"令牌在黑名单中: {jti}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已失效，请重新登录",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: UUID = token_data.sub
        logger.debug(f"令牌验证成功，用户ID: {user_id}")
    except JWTError as e:
        logger.warning(f"令牌解码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="身份验证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError as e:
        logger.warning(f"令牌负载验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="身份验证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从数据库获取用户
    try:
        logger.debug(f"从数据库获取用户 ID: {user_id}")
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        if not user.is_active:
            logger.warning(f"用户已禁用: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已禁用"
            )
        
        logger.debug(f"用户验证成功: {user_id}")
        return user
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取用户时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户时发生错误: {str(e)}"
        )
