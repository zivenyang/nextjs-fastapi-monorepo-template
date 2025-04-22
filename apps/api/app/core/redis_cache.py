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

async def get_redis_client() -> redis_async.Redis | None:
    """
    获取Redis客户端实例（单例模式）
    如果 Redis 未启用，则返回 None
    """
    global _redis_client
    # 检查 Redis 是否启用
    if not settings.REDIS_ENABLED:
        if _redis_client is not None:
             # 如果之前已创建但现在禁用了，尝试关闭 (可选)
             try:
                 await _redis_client.close()
             except Exception:
                 pass # 忽略关闭错误
             _redis_client = None
        logger.info("Redis 已禁用，跳过客户端初始化。")
        return None
        
    if _redis_client is None:
        logger.info("初始化Redis客户端连接")
        try:
            _redis_client = redis_async.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=False,  # 我们自己处理解码
                socket_timeout=5, # 添加超时
                socket_connect_timeout=5 # 添加连接超时
            )
            # 尝试 ping 一下确保连接成功 (可选但推荐)
            await _redis_client.ping()
            logger.info("Redis 客户端连接成功")
        except Exception as e:
            logger.error(f"初始化 Redis 客户端失败: {str(e)}", exc_info=True)
            _redis_client = None # 连接失败，重置为 None
            return None
            
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
        self._redis: redis_async.Redis | None = None # 明确类型可能为 None
        logger.debug(f"创建Redis缓存服务 (prefix: {prefix})")
    
    async def _get_redis(self) -> redis_async.Redis | None:
        """
        获取Redis连接 (如果 Redis 已启用)
        """
        # 只有在 Redis 启用时才尝试获取客户端
        if not settings.REDIS_ENABLED:
             if self._redis is not None: self._redis = None # 确保内部状态一致
             return None
             
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
        设置缓存 (如果 Redis 已启用)
        """
        redis = await self._get_redis()
        if redis is None:
            logger.debug(f"Redis 未启用或连接失败，跳过设置缓存: {self.prefix}:{key}")
            return False # 操作未执行
            
        try:
            full_key = self._get_key(key)
            serialized_value = json.dumps(value)
            result = await redis.set(full_key, serialized_value, ex=expire)
            logger.debug(f"设置缓存 {full_key}, expire={expire}")
            return result
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {str(e)}", exc_info=True)
            return False
    
    async def setex(self, key: str, expire: int, value: str) -> bool:
        """
        设置缓存并指定过期时间 (如果 Redis 已启用)
        """
        redis = await self._get_redis()
        if redis is None:
            logger.debug(f"Redis 未启用或连接失败，跳过设置带过期时间的缓存: {self.prefix}:{key}")
            return False
            
        try:
            full_key = self._get_key(key)
            result = await redis.setex(full_key, expire, value)
            logger.debug(f"设置带过期时间的缓存 {full_key}, expire={expire}")
            return result
        except Exception as e:
            logger.error(f"设置带过期时间的缓存失败 {key}: {str(e)}", exc_info=True)
            return False
    
    async def get(self, key: str) -> Any:
        """
        获取缓存 (如果 Redis 已启用)
        """
        redis = await self._get_redis()
        if redis is None:
            logger.debug(f"Redis 未启用或连接失败，跳过获取缓存: {self.prefix}:{key}")
            return None
            
        try:
            full_key = self._get_key(key)
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
        删除缓存 (如果 Redis 已启用)
        """
        redis = await self._get_redis()
        if redis is None:
            logger.debug(f"Redis 未启用或连接失败，跳过删除缓存: {self.prefix}:{key}")
            return 0
            
        try:
            full_key = self._get_key(key)
            result = await redis.delete(full_key)
            logger.debug(f"删除缓存 {full_key}")
            return result
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {str(e)}", exc_info=True)
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在 (如果 Redis 已启用)
        """
        redis = await self._get_redis()
        if redis is None:
            logger.debug(f"Redis 未启用或连接失败，跳过检查缓存: {self.prefix}:{key}")
            return False
            
        try:
            full_key = self._get_key(key)
            exists_count = await redis.exists(full_key)
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
            # 检查 API 缓存是否启用
            if not settings.API_CACHE_ENABLED:
                logger.debug(f"API 缓存已禁用，直接执行函数: {func.__name__}")
                return await func(*args, **kwargs)
                
            # 检查 Redis 是否启用 (通过实例方法间接检查)
            # 如果 Redis 未启用，get/set 会直接返回默认值，效果类似跳过
            # 但我们也可以在这里显式检查 Redis 状态，如果 Redis 必须可用的话
            # redis_client = await api_cache_instance._get_redis()
            # if redis_client is None:
            #     logger.warning(f"Redis 未启用或不可用，无法为 {func.__name__} 提供缓存，直接执行函数。")
            #     return await func(*args, **kwargs)

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