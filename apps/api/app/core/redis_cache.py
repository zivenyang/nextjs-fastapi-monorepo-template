import json
import functools
import hashlib
from datetime import timedelta
from typing import Any, Callable, Dict, Optional, TypeVar, cast, Awaitable, Union

import redis.asyncio as redis_async
from fastapi import Request
from app.core.config import settings
from app.core.logging import get_logger

# 创建模块日志记录器
logger = get_logger(__name__)

# 类型变量定义，用于装饰器类型提示
T = TypeVar("T", bound=Callable[..., Awaitable[Any]])

# Redis客户端单例
_redis_client = None

async def get_redis_client() -> redis_async.Redis:
    """
    获取Redis客户端实例（单例模式）
    """
    global _redis_client
    if _redis_client is None:
        logger.info("初始化Redis客户端连接")
        _redis_client = redis_async.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=False  # 我们自己处理解码
        )
    return _redis_client


class RedisCache:
    """
    Redis缓存服务基类 - 异步实现
    """
    def __init__(self, prefix: str = "cache"):
        """
        初始化Redis缓存服务
        
        Args:
            prefix: 缓存键前缀，用于避免键名冲突
        """
        self.prefix = prefix
        self._redis = None
        logger.debug(f"创建Redis缓存服务 (prefix: {prefix})")
    
    async def _get_redis(self) -> redis_async.Redis:
        """
        获取Redis连接
        """
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis
    
    def _get_key(self, key: str) -> str:
        """
        获取带前缀的完整键名
        """
        return f"{self.prefix}:{key}"
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值（将被JSON序列化）
            expire: 过期时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            full_key = self._get_key(key)
            serialized_value = json.dumps(value)
            redis = await self._get_redis()
            result = await redis.set(full_key, serialized_value, ex=expire)
            logger.debug(f"设置缓存 {full_key}, expire={expire}")
            return result
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {str(e)}", exc_info=True)
            return False
    
    async def setex(self, key: str, expire: int, value: str) -> bool:
        """
        设置缓存并指定过期时间（用于黑名单令牌等无需序列化的值）
        
        Args:
            key: 缓存键
            expire: 过期时间（秒）
            value: 缓存值（将直接存储，不进行序列化）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            full_key = self._get_key(key)
            redis = await self._get_redis()
            result = await redis.setex(full_key, expire, value)
            logger.debug(f"设置带过期时间的缓存 {full_key}, expire={expire}")
            return result
        except Exception as e:
            logger.error(f"设置带过期时间的缓存失败 {key}: {str(e)}", exc_info=True)
            return False
    
    async def get(self, key: str) -> Any:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值，未找到返回None
        """
        try:
            full_key = self._get_key(key)
            redis = await self._get_redis()
            data = await redis.get(full_key)
            if data is None:
                logger.debug(f"缓存未命中 {full_key}")
                return None
            
            value = json.loads(data)
            logger.debug(f"缓存命中 {full_key}")
            return value
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {str(e)}", exc_info=True)
            return None
    
    async def delete(self, key: str) -> int:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            int: 删除的键数量
        """
        try:
            full_key = self._get_key(key)
            redis = await self._get_redis()
            result = await redis.delete(full_key)
            logger.debug(f"删除缓存 {full_key}")
            return result
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {str(e)}", exc_info=True)
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        try:
            full_key = self._get_key(key)
            redis = await self._get_redis()
            # Redis的exists命令返回整数：0表示不存在，非0表示存在
            exists_count = await redis.exists(full_key)
            # 转换为布尔值：0 -> False, 非0 -> True
            result = bool(exists_count)
            logger.debug(f"检查缓存 {full_key} 存在: {result}")
            return result
        except Exception as e:
            logger.error(f"检查缓存失败 {key}: {str(e)}", exc_info=True)
            return False


# API响应缓存实例
api_cache_instance = RedisCache(prefix="api")

# JWT黑名单缓存实例
jwt_cache_instance = RedisCache(prefix="jwt:blacklist")


def api_cache(expire: int = 300):
    """
    API响应缓存装饰器
    
    Args:
        expire: 缓存过期时间（秒），默认5分钟
        
    Returns:
        装饰后的函数
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取缓存键
            # 根据函数名称和参数生成缓存键
            func_name = func.__name__
            kwargs_str = json.dumps(kwargs, sort_keys=True)
            args_str = json.dumps(args, sort_keys=True)
            
            # 处理FastAPI的Request对象，从URL和查询参数生成缓存键
            request_obj = None
            for arg in args:
                if isinstance(arg, Request):
                    request_obj = arg
                    break
            
            if request_obj:
                # 如果存在Request对象，使用请求的完整URL作为键的一部分
                url = str(request_obj.url)
                cache_key = hashlib.md5(f"{func_name}:{url}:{args_str}:{kwargs_str}".encode()).hexdigest()
            else:
                cache_key = hashlib.md5(f"{func_name}:{args_str}:{kwargs_str}".encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_result = await api_cache_instance.get(cache_key)
            if cached_result is not None:
                logger.debug(f"从缓存返回API响应: {cache_key}")
                return cached_result
            
            # 缓存未命中，执行原函数
            logger.debug(f"API缓存未命中，执行函数: {func_name}")
            result = await func(*args, **kwargs)
            
            # 缓存结果
            try:
                await api_cache_instance.set(cache_key, result, expire=expire)
                logger.debug(f"API响应已缓存: {cache_key}, expire={expire}")
            except Exception as e:
                logger.error(f"缓存API响应失败: {str(e)}", exc_info=True)
            
            return result
        
        return cast(T, wrapper)
    
    return decorator


# 简化使用的别名
api_cache = api_cache

# JWT令牌黑名单相关方法
async def add_token_to_blacklist(token_jti: str, expiration: timedelta) -> bool:
    """
    添加JWT令牌到黑名单
    
    Args:
        token_jti: 令牌的JTI（唯一标识符）
        expiration: 令牌的过期时间间隔
        
    Returns:
        bool: 是否成功添加
    """
    try:
        # 在Redis中设置令牌，到期时间与令牌过期时间一致，自动过期
        expiry_seconds = int(expiration.total_seconds())
        logger.info(f"将令牌添加到黑名单: {token_jti}, 过期时间: {expiry_seconds}秒")
        
        # 使用缓存实例的setex方法设置键值对
        result = await jwt_cache_instance.setex(token_jti, expiry_seconds, "1")
        return result
    except Exception as e:
        logger.error(f"将令牌添加到黑名单失败: {str(e)}", exc_info=True)
        return False


async def is_token_blacklisted(token_jti: str) -> bool:
    """
    检查令牌是否在黑名单中
    
    Args:
        token_jti: 令牌的JTI（唯一标识符）
        
    Returns:
        bool: 是否在黑名单中
    """
    try:
        # 使用缓存实例的exists方法检查令牌是否在黑名单中
        result = await jwt_cache_instance.exists(token_jti)
        if result:
            logger.debug(f"令牌在黑名单中: {token_jti}")
        return result
    except Exception as e:
        logger.error(f"检查令牌黑名单失败: {str(e)}", exc_info=True)
        # 出现错误时，为安全起见，视为在黑名单中
        return True


async def cleanup_expired_tokens() -> int:
    """
    清理过期的黑名单令牌
    注意：使用Redis时，过期的键会自动删除，此函数主要用于兼容现有代码
    
    Returns:
        int: 已清理的令牌数量（使用Redis时固定返回0）
    """
    logger.debug("Redis会自动清理过期令牌，无需手动清理")
    return 0 