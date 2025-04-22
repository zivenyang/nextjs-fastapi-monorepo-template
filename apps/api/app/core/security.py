from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, Dict
import uuid

# 导入 OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings
from app.core.logging import get_logger

# 创建模块日志记录器
logger = get_logger(__name__)

# 定义 OAuth2 密码 Bearer 方案
# tokenUrl 指向获取令牌的端点 (即登录接口)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
logger.debug(f"OAuth2PasswordBearer scheme initialized (tokenUrl: /api/v1/auth/login)")

# 正确初始化 PasswordHash，传入 Hasher 实例的元组
pwd_hasher = PasswordHash((BcryptHasher(),))
logger.debug("Password hasher (pwdlib.PasswordHash) initialized with BcryptHasher instance.")


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
    
    # 生成一个唯一标识符，用于标识令牌
    token_jti = str(uuid.uuid4())
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "jti": token_jti  # 添加令牌唯一标识符
    }
    logger.debug(f"创建JWT令牌 (subject: {subject}, jti: {token_jti}, expires: {expire.isoformat()})")
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        logger.debug("JWT令牌创建成功")
        return encoded_jwt
    except Exception as e:
        logger.error(f"JWT令牌创建失败: {str(e)}", exc_info=True)
        raise


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT令牌，获取其内容
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        logger.debug(f"JWT令牌解码成功")
        return payload
    except JWTError as e:
        logger.warning(f"JWT令牌解码失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"JWT令牌解码过程中发生错误: {str(e)}", exc_info=True)
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希密码匹配
    """
    try:
        # 捕获并保存 verify 方法的返回值！
        result = pwd_hasher.verify(plain_password, hashed_password)
        # 根据返回值判断密码是否匹配
        if result:
            logger.debug("密码验证成功")
        else:
            logger.debug("密码验证失败：不匹配")
        return result  # 返回实际的验证结果
    except Exception as e:
        # 仍然捕获可能的异常，例如无效哈希等
        logger.debug(f"密码验证过程中发生错误: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """
    获取密码的哈希值
    """
    try:
        # 使用正确初始化的 pwd_hasher 实例的 hash 方法
        hashed = pwd_hasher.hash(password)
        logger.debug("密码哈希生成成功")
        return hashed
    except Exception as e:
        logger.error(f"密码哈希生成失败: {str(e)}", exc_info=True)
        raise 