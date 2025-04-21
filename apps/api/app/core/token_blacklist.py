from datetime import datetime, timedelta, UTC
from app.core.logging import get_logger
from app.core.redis_cache import add_token_to_blacklist, is_token_blacklisted, cleanup_expired_tokens

# 创建模块日志记录器
logger = get_logger(__name__)

# 兼容旧版代码的内存存储，在新版本中不会被使用
# 格式: {token_jti: expiration_time}
logout_tokens = {}

async def add_to_blacklist(token_jti: str, expires_delta: timedelta) -> bool:
    """
    将JWT令牌添加到黑名单
    
    Args:
        token_jti: JWT令牌的唯一标识符
        expires_delta: 令牌的过期时间
        
    Returns:
        bool: 操作是否成功
    """
    # 使用Redis存储黑名单
    result = await add_token_to_blacklist(token_jti, expires_delta)
    
    # 为了向后兼容，也存储在内存中
    logout_tokens[token_jti] = datetime.now(UTC) + expires_delta
    
    logger.info(f"令牌已添加到黑名单: {token_jti}")
    return result

async def is_blacklisted(token_jti: str) -> bool:
    """
    检查令牌是否在黑名单中
    
    Args:
        token_jti: JWT令牌的唯一标识符
        
    Returns:
        bool: 是否在黑名单中
    """
    # 优先使用Redis检查
    result = await is_token_blacklisted(token_jti)
    
    # 如果Redis中没有找到，检查内存存储（向后兼容）
    if not result and token_jti in logout_tokens:
        # 确保使用时区感知的日期时间进行比较
        expiry_time = logout_tokens[token_jti]
        current_time = datetime.now(UTC)
        
        # 如果存储的时间是无时区的，添加UTC时区
        if expiry_time.tzinfo is None:
            expiry_time = expiry_time.replace(tzinfo=UTC)
            
        if expiry_time > current_time:
            result = True
    
    return result

# 清理过期的黑名单令牌
async def cleanup_expired_tokens_compat() -> int:
    """
    清理已过期的黑名单令牌（向后兼容方法）
    
    Returns:
        int: 清理的令牌数量
    """
    # 调用Redis清理函数
    await cleanup_expired_tokens()
    
    # 同时清理内存中的令牌（向后兼容）
    current_time = datetime.now(UTC)
    # 使用列表而不是字典视图，以避免在迭代过程中修改字典
    expired_tokens = []
    
    # 处理时区不兼容问题
    for jti, expires in logout_tokens.items():
        # 如果存储的时间是无时区的，添加UTC时区
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        
        # 检查是否过期
        if expires < current_time:
            expired_tokens.append(jti)
    
    # 确保真正删除过期的令牌
    for jti in expired_tokens:
        if jti in logout_tokens:
            del logout_tokens[jti]
    
    if expired_tokens:
        logger.info(f"清理了 {len(expired_tokens)} 个过期的登出令牌（内存存储）")
        
    return len(expired_tokens) 