from datetime import datetime
from app.core.logging import get_logger

# 创建模块日志记录器
logger = get_logger(__name__)

# 使用内存存储已登出令牌，在生产环境中应该使用Redis等持久化存储
# 格式: {token_jti: expiration_time}
logout_tokens = {}

# 清理过期的黑名单令牌
def cleanup_expired_tokens():
    """
    清理已过期的黑名单令牌
    """
    current_time = datetime.utcnow()
    expired_tokens = [jti for jti, expires in logout_tokens.items() if expires < current_time]
    for jti in expired_tokens:
        logout_tokens.pop(jti, None)
    
    if expired_tokens:
        logger.info(f"清理了 {len(expired_tokens)} 个过期的登出令牌")
        
    return len(expired_tokens) 