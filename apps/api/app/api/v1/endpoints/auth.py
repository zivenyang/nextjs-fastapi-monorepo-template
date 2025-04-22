from datetime import timedelta, datetime, UTC
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
# 不再需要直接从端点导入 AsyncSession
# from sqlmodel.ext.asyncio.session import AsyncSession

# 导入新的依赖和类型
from app.api.deps import get_current_user, get_user_service, get_settings 
from app.core.config import Settings # 导入类型
from app.core.security import create_access_token, verify_password, decode_jwt_token
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.core.logging import get_logger
from app.core.token_blacklist import add_to_blacklist
# 导入 UserService 类型和异常
from app.services.user_service import UserService, EmailAlreadyExistsException

# 创建模块日志记录器
logger = get_logger(__name__)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    # 移除 db: AsyncSession = Depends(get_db)
    form_data: OAuth2PasswordRequestForm = Depends(),
    # 注入依赖
    user_service_instance: UserService = Depends(get_user_service),
    app_settings: Settings = Depends(get_settings),
) -> Any:
    """
    OAuth2 密码流认证，获取JWT token
    """
    logger.info(f"用户登录尝试: {form_data.username}")
    
    try:
        # 使用注入的服务实例，不再传递 db
        user = await user_service_instance.get_user_by_email(email=form_data.username)
        
        # 验证用户和密码
        if not user:
            logger.warning(f"登录失败: 用户 {form_data.username} 不存在")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        logger.debug(f"开始验证用户 {user.email} 的密码")
        password_match = verify_password(form_data.password, user.hashed_password)
        logger.debug(f"密码验证函数 verify_password 返回值: {password_match}")
        
        if not password_match:
            logger.warning(f"登录失败: 用户 {form_data.username} 密码错误 (验证函数返回 False)")
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
        
        # 使用注入的 settings
        access_token_expires = timedelta(minutes=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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
    # 注入 settings
    app_settings: Settings = Depends(get_settings),
    # 如果 add_to_blacklist 需要 redis client, 需要注入 BlacklistService
    # blacklist_service: BlacklistService = Depends(get_blacklist_service)
) -> Any:
    """
    用户登出，将当前令牌加入黑名单
    """
    try:
        # 从授权头中提取令牌
        try:
            token_type, token = authorization.split()
            if token_type.lower() != "bearer":
                raise ValueError("Invalid token type")
        except ValueError:
             logger.warning("登出失败: 无效的 Authorization Header 格式")
             raise HTTPException(
                 status_code=status.HTTP_401_UNAUTHORIZED,
                 detail="无效的认证头",
                 headers={"WWW-Authenticate": "Bearer"},
             )
            
        # 解码令牌以获取其到期时间和唯一标识符
        token_data = decode_jwt_token(token)
        if not token_data:
            logger.warning("登出失败: 无法解码令牌")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 获取令牌的有效期和标识
        jti = token_data.get("jti")
        exp = token_data.get("exp")
        
        if not jti:
            # 如果令牌没有 JTI，登出可能无法精确工作，记录警告
            # 可以选择拒绝登出或使用 user_id 作为后备 (但不推荐)
            logger.warning(f"用户 {current_user.id} 尝试登出一个没有 JTI 的令牌")
            # raise HTTPException(status_code=400, detail="无法注销此令牌")
            jti = str(current_user.id) # 使用 user_id 作为后备 (风险：会注销该用户所有无 JTI 的令牌)

        if not exp:
            logger.warning(f"令牌 {jti} 没有过期时间，使用默认值计算黑名单有效期")
            # 使用注入的 settings
            expires_delta = timedelta(minutes=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            # 计算剩余有效期，用于设置黑名单过期时间
            exp_time = datetime.fromtimestamp(exp, UTC)
            now = datetime.now(UTC)
            expires_delta = exp_time - now
            # 如果令牌已过期，理论上 get_current_user 就会失败，但这里可以加个检查
            if expires_delta.total_seconds() <= 0:
                 logger.info(f"令牌 {jti} 已过期，无需加入黑名单")
                 return {"detail": "登出成功 (令牌已过期)"}

        # --- 调用黑名单服务 ---
        # 如果注入服务: await blacklist_service.add_to_blacklist(token_jti=jti, expires_delta=expires_delta)
        added = await add_to_blacklist(token_jti=jti, expires_delta=expires_delta)
        if not added:
             logger.error(f"无法将令牌 {jti} 添加到黑名单")
             # 可以选择是否通知用户失败
             # raise HTTPException(status_code=500, detail="登出操作失败")

        # 清理过期的登出令牌 (移除调用 - Redis 会自动处理)
        # await cleanup_expired_tokens_compat()

        logger.info(f"用户 {current_user.id} ({current_user.email}) 登出成功，令牌 {jti} 已加入黑名单")
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
    # 移除 db: AsyncSession = Depends(get_db)
    user_in: UserCreate,
    # 注入依赖
    user_service_instance: UserService = Depends(get_user_service),
    # 注入 settings (虽然此端点当前未使用，但保持一致性是好的)
    app_settings: Settings = Depends(get_settings),
) -> Any:
    """
    注册新用户
    """
    logger.info(f"新用户注册请求: {user_in.email}")
    
    try:
        # 使用注入的服务实例，不再传递 db
        db_user = await user_service_instance.create_user(user_create_data=user_in)
        
        logger.info(f"新用户注册成功: ID={db_user.id}, 邮箱={db_user.email}")
        # FastAPI 会自动将 User ORM 对象转换为 UserResponse
        return db_user
        
    except EmailAlreadyExistsException as e:
        logger.warning(f"注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"注册失败：{str(e)}" # 可以直接使用异常消息
        )
    except HTTPException:
        # 直接重新抛出 HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"创建用户时发生内部错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户时发生内部错误"
        ) 