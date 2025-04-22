# apps/api/app/core/exception_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import AppException # 导入我们的基础应用异常
from .logging import get_logger

logger = get_logger(__name__)

async def app_exception_handler(request: Request, exc: AppException):
    """处理所有继承自 AppException 的自定义异常"""
    logger.warning(f"应用异常被捕获: {exc.__class__.__name__}, 状态码: {exc.status_code}, 详情: {exc.detail}", exc_info=False) # 通常不需要完整堆栈
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理 Pydantic/FastAPI 的请求体验证错误"""
    error_details = exc.errors()
    logger.warning(f"请求体验证错误: {error_details}", exc_info=False)
    # 统一返回格式
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details},
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 Starlette/FastAPI 的 HTTPException"""
    logger.warning(f"HTTP 异常被捕获: 状态码 {exc.status_code}, 详情: {exc.detail}", exc_info=False)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """处理所有未被捕获的通用异常"""
    logger.error(f"未处理的服务器内部错误: {exc.__class__.__name__}", exc_info=True) # 记录完整堆栈
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "服务器内部发生了一个意外错误。"},
    )

# 可以根据需要添加更多特定的处理器 