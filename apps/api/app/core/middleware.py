"""
中间件模块

提供各种中间件，包括请求日志记录、性能监控等功能。
"""

import time
import uuid
from typing import Callable, Dict

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.logging import get_logger

# 创建模块日志记录器
logger = get_logger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有HTTP请求的详细信息，包括请求方法、路径、状态码、处理时间等。
    为每个请求分配唯一ID，方便在日志中追踪整个请求的处理流程。
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始
        start_time = time.time()
        path = request.url.path
        query_params = request.url.query
        method = request.method
        client_host = request.client.host if request.client else "unknown"
        
        logger.info(
            f"请求开始 [{request_id}] {method} {path}"
            f"{f'?{query_params}' if query_params else ''} "
            f"({client_host})"
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            status_code = response.status_code
            log_level = "warning" if status_code >= 400 else "info"
            getattr(logger, log_level)(
                f"请求完成 [{request_id}] {method} {path} - {status_code} "
                f"({process_time:.4f}s)"
            )
            
            # 添加请求处理时间和请求ID到响应头
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception as e:
            # 记录异常信息
            process_time = time.time() - start_time
            logger.error(
                f"请求异常 [{request_id}] {method} {path} - "
                f"({process_time:.4f}s): {str(e)}",
                exc_info=True
            )
            raise


class ResponseSizeLogMiddleware(BaseHTTPMiddleware):
    """
    响应大小日志中间件
    
    记录响应的大小，监控大型响应，有助于识别性能问题。
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        
        # 获取响应大小
        response_size = int(response.headers.get("content-length", 0))
        if response_size > 1024 * 1024:  # 大于1MB的响应
            request_id = getattr(request.state, "request_id", "-")
            logger.warning(
                f"大型响应 [{request_id}] {request.method} {request.url.path} - "
                f"大小: {response_size/1024/1024:.2f}MB"
            )
            
        return response


def setup_middlewares(app: FastAPI) -> None:
    """
    设置所有中间件
    
    Args:
        app: FastAPI应用实例
    """
    # 添加请求日志中间件（需要最后添加，以便首先执行）
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(ResponseSizeLogMiddleware)
    
    logger.info("中间件已设置完成") 