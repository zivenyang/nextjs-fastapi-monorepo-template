from fastapi import FastAPI
from fastapi.routing import APIRoute
import uvicorn
from app.core.db import init_db
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import setup_middlewares
# 导入自定义异常和处理器
from app.core.exceptions import AppException
from app.core.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)

# 初始化日志系统
configure_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("应用启动中，初始化数据库连接...")
    await init_db()
    logger.info("数据库初始化完成")
    yield
    # 关闭时执行
    logger.info("应用关闭中...")
    # 这里可以添加清理代码
    logger.info("应用已正常关闭")

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

app = FastAPI(
    title=settings.PROJECT_NAME, 
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
    generate_unique_id_function=custom_generate_unique_id,
    openapi_url=settings.OPENAPI_URL,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置中间件
setup_middlewares(app)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)
logger.info(f"API路由已注册，前缀: {settings.API_V1_STR}")

# 注册异常处理器
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
# 通用异常处理器应该最后注册
app.add_exception_handler(Exception, generic_exception_handler)
logger.info("全局异常处理器已注册")

# @app.get("/")
# def read_root():
#     logger.debug("访问根路径")
#     return {"message": "Hello World", "docs_url": "/docs"}


if __name__ == "__main__":
    logger.info(f"独立运行模式，启动服务器 host=0.0.0.0, port=8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
