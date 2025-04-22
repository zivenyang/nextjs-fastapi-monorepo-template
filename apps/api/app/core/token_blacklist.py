from datetime import datetime, timedelta, UTC
from app.core.logging import get_logger
from app.core.redis_cache import jwt_cache_instance

# 创建模块日志记录器
logger = get_logger(__name__)

async def add_to_blacklist(token_jti: str, expires_delta: timedelta) -> bool:
    """
    将JWT令牌添加到黑名单 (完全依赖Redis)
    
    Args:
        token_jti: JWT令牌的唯一标识符
        expires_delta: 令牌的过期时间间隔
        
    Returns:
        bool: 操作是否成功
    """
    try:
        expiry_seconds = int(expires_delta.total_seconds())
        # 确保过期时间至少为1秒，因为Redis SETEX 不接受0或负数
        if expiry_seconds <= 0:
             logger.warning(f"尝试将已过期或即将过期的令牌 {token_jti} 添加到黑名单，跳过。")
             return True # 视为成功，因为它已经无效了
             
        # 直接使用 jwt_cache_instance (这是 RedisCache 的实例)
        result = await jwt_cache_instance.setex(token_jti, expiry_seconds, "1")
        if result:
             logger.info(f"令牌已添加到Redis黑名单: {token_jti}, 过期: {expiry_seconds}秒")
        else:
             logger.error(f"使用Redis将令牌添加到黑名单失败: {token_jti}")
        return result
    except Exception as e:
        logger.error(f"将令牌添加到Redis黑名单时发生错误: {token_jti}, {str(e)}", exc_info=True)
        return False

async def is_blacklisted(token_jti: str) -> bool:
    """
    检查令牌是否在黑名单中 (完全依赖Redis)
    
    Args:
        token_jti: JWT令牌的唯一标识符
        
    Returns:
        bool: 是否在黑名单中
    """
    try:
         # 直接使用 jwt_cache_instance
        result = await jwt_cache_instance.exists(token_jti)
        if result:
            logger.debug(f"令牌在Redis黑名单中: {token_jti}")
        return result
    except Exception as e:
        logger.error(f"检查Redis令牌黑名单时发生错误: {token_jti}, {str(e)}", exc_info=True)
        # 出现错误时，为安全起见，视为在黑名单中 (保持原策略)
        return True 