from typing import Dict
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.core.logging import get_logger
from app.core.redis_cache import get_redis_client

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", summary="服务健康检查")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict:
    """
    健康检查端点
    
    检查数据库和Redis连接是否正常
    """
    logger.debug("执行健康检查")
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # 检查数据库连接
    try:
        result = await db.execute("SELECT 1")
        database_status = "healthy" if result else "unavailable"
        health_status["database"] = database_status
    except Exception as e:
        logger.error(f"数据库健康检查失败: {str(e)}", exc_info=True)
        health_status["database"] = "unhealthy"
        health_status["database_error"] = str(e)
    
    # 检查Redis连接
    try:
        redis_client = await get_redis_client()
        # 尝试设置和获取一个键值对
        result = await redis_client.set("health_check", "1", ex=10)
        redis_value = await redis_client.get("health_check")
        
        if result and redis_value:
            health_status["redis"] = "healthy"
        else:
            health_status["redis"] = "unavailable"
    except Exception as e:
        logger.error(f"Redis健康检查失败: {str(e)}", exc_info=True)
        health_status["redis"] = "unhealthy"
        health_status["redis_error"] = str(e)
    
    # 如果任何依赖服务不健康，更新整体状态
    if "unhealthy" in [health_status["database"], health_status["redis"]]:
        health_status["status"] = "unhealthy"
    elif "unavailable" in [health_status["database"], health_status["redis"]]:
        health_status["status"] = "degraded"
    
    return health_status 