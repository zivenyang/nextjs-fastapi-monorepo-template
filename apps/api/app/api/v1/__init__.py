from fastapi import APIRouter

from app.api.v1.endpoints import users, auth, cache_demo, health

api_router = APIRouter()

# 添加各模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(cache_demo.router, prefix="/cache-demo", tags=["缓存演示"])
api_router.include_router(health.router, prefix="/system", tags=["系统"])
