from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

# 创建模块日志记录器
logger = get_logger(__name__)

# 创建一个密码哈希上下文，使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger.debug("密码哈希上下文已初始化 (scheme: bcrypt)")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建JWT访问令牌
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    logger.debug(f"创建JWT令牌 (subject: {subject}, expires: {expire.isoformat()})")
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        logger.debug("JWT令牌创建成功")
        return encoded_jwt
    except Exception as e:
        logger.error(f"JWT令牌创建失败: {str(e)}", exc_info=True)
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希密码匹配
    """
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        log_message = "密码验证成功" if result else "密码验证失败"
        logger.debug(log_message)
        return result
    except Exception as e:
        logger.error(f"密码验证过程出错: {str(e)}", exc_info=True)
        return False


def get_password_hash(password: str) -> str:
    """
    获取密码的哈希值
    """
    try:
        hashed = pwd_context.hash(password)
        logger.debug("密码哈希生成成功")
        return hashed
    except Exception as e:
        logger.error(f"密码哈希生成失败: {str(e)}", exc_info=True)
        raise 