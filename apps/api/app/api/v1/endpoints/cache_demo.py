import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.core.redis_cache import api_cache

logger = get_logger(__name__)

router = APIRouter()


@router.get("/time", summary="获取当前时间（无缓存）")
async def get_current_time() -> dict:
    """
    获取当前服务器时间（无缓存示例）
    
    每次调用都会返回最新时间
    """
    logger.debug("获取当前时间（无缓存）")
    return {
        "time": datetime.now().isoformat(),
        "timestamp": time.time(),
        "cached": False
    }


@router.get("/time-cached", summary="获取缓存的当前时间")
@api_cache(expire=30)  # 缓存30秒
async def get_cached_time() -> dict:
    """
    获取缓存的服务器时间
    
    结果将被缓存30秒，在缓存期内多次请求将返回相同结果
    """
    logger.debug("获取当前时间（已缓存30秒）")
    return {
        "time": datetime.now().isoformat(),
        "timestamp": time.time(),
        "cached": True,
        "cache_expires_in": "30秒"
    }


@router.get("/time-cached/{seconds}", summary="获取自定义缓存时间的当前时间")
@api_cache(expire=60)  # 默认缓存60秒，但会被路径参数覆盖
async def get_custom_cached_time(seconds: int) -> dict:
    """
    获取缓存的服务器时间，支持自定义缓存时间
    
    Args:
        seconds: 缓存秒数，1-3600
        
    每个不同的秒数参数会有独立的缓存
    """
    if seconds < 1 or seconds > 3600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缓存时间必须在1-3600秒之间"
        )
    
    logger.debug(f"获取当前时间（已缓存{seconds}秒）")
    return {
        "time": datetime.now().isoformat(),
        "timestamp": time.time(),
        "cached": True,
        "cache_expires_in": f"{seconds}秒",
        "note": "虽然返回值显示自定义缓存时间，但实际缓存时间由装饰器控制"
    }


@router.get("/user-data", summary="获取当前用户数据（带认证的缓存）")
@api_cache(expire=60)
async def get_user_data(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    获取当前用户数据（需要认证）
    
    结果将针对每个用户单独缓存60秒
    """
    logger.debug(f"获取用户数据（用户ID: {current_user.id}）")
    # 模拟耗时操作
    time.sleep(0.5)
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "fullname": current_user.full_name,
        "timestamp": time.time(),
        "cached": True,
        "cache_expires_in": "60秒"
    } 