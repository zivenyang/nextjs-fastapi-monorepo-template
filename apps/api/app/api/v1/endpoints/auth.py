from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password, decode_jwt_token
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.core.logging import get_logger
from app.core.token_blacklist import logout_tokens, cleanup_expired_tokens  # 从单独的模块导入

# 创建模块日志记录器
logger = get_logger(__name__)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 密码流认证，获取JWT token
    """
    logger.info(f"用户登录尝试: {form_data.username}")
    
    try:
        # 查询用户
        query = select(User).where(User.email == form_data.username.lower())
        logger.debug(f"执行查询: {query}")
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        # 验证用户和密码
        if not user:
            logger.warning(f"登录失败: 用户 {form_data.username} 不存在")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"登录失败: 用户 {form_data.username} 密码错误")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user.is_active:
            logger.warning(f"登录失败: 用户 {form_data.username} 未激活")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="用户未激活"
            )
        
        # 清理过期的登出令牌
        cleanup_expired_tokens()
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        logger.info(f"用户 {user.id} ({user.email}) 登录成功")
        return {"access_token": token, "token_type": "bearer"}
    
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"登录处理过程中发生错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中发生错误"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    authorization: str = Header(...),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    用户登出，将当前令牌加入黑名单
    """
    try:
        # 从授权头中提取令牌
        token_type, token = authorization.split()
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证类型",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 解码令牌以获取其到期时间和唯一标识符
        token_data = decode_jwt_token(token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 获取令牌的有效期和标识
        jti = token_data.get("jti") or str(current_user.id)  # 使用用户ID作为备用标识
        exp = token_data.get("exp")
        
        if not exp:
            # 如果无法获取过期时间，使用当前时间加上默认过期时间
            exp_time = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            exp_time = datetime.fromtimestamp(exp)
            
        # 将令牌添加到黑名单
        logout_tokens[jti] = exp_time
        
        # 清理过期的登出令牌
        cleanup_expired_tokens()
        
        logger.info(f"用户 {current_user.id} ({current_user.email}) 登出成功")
        return {"detail": "登出成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理登出请求时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出过程中发生错误"
        )


@router.post("/register", response_model=UserResponse)
async def register_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    注册新用户
    """
    logger.info(f"新用户注册请求: {user_in.email}")
    
    try:
        # 检查邮箱是否已存在
        query = select(User).where(User.email == user_in.email.lower())
        logger.debug(f"执行查询: {query}")
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            logger.warning(f"注册失败: 邮箱 {user_in.email} 已被注册")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )
        
        # 创建新用户
        logger.debug(f"创建新用户: {user_in.email}")
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email.lower(),
            hashed_password=hashed_password,
            username=user_in.username,
            full_name=user_in.full_name,
            is_active=True,
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        logger.info(f"新用户注册成功: ID={db_user.id}, 邮箱={db_user.email}")
        return db_user
        
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"用户注册过程中发生错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户注册过程中发生错误"
        ) 