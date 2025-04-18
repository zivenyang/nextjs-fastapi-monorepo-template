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
from app.schemas.token import TokenPayload

# OAuth2 密码流认证令牌URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 数据库会话依赖
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话的FastAPI依赖"""
    async for session in get_session():
        try:
            yield session
        finally:
            await session.close()

# 当前用户依赖
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """验证token并获取当前用户"""
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id: UUID = token_data.sub
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="身份验证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从数据库获取用户
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已禁用"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户时发生错误: {str(e)}"
        )
