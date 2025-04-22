"""
中间件模块

提供各种中间件，包括请求日志记录、性能监控等功能。
"""

import time
import uuid
from typing import Callable, Dict, Optional

from fastapi import FastAPI, Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from pydantic import BaseModel, Field

from app.core.logging import get_logger, request_id_var
from app.core.config import settings

# 创建模块日志记录器
logger = get_logger(__name__)

# --- 新增：定义标准错误响应模型 ---
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="错误详细信息")
    request_id: Optional[str] = Field(None, description="引起错误的请求ID")
    # 可以根据需要添加 error_code 等字段
    # error_code: Optional[str] = None 


# --- 新增：全局错误处理中间件 ---
class GlobalErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    全局错误处理中间件
    
    捕获所有未处理的异常和HTTPException，返回统一格式的JSON错误响应。
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request_id_var.get() # 获取当前请求ID
        try:
            # 正常处理请求
            response = await call_next(request)
            return response
        except HTTPException as http_exc:
            # 处理 FastAPI/Starlette 抛出的 HTTP 异常
            # 通常这些是预期的错误 (如 404 Not Found, 401 Unauthorized, 422 Validation Error)
            # 我们可以记录这些错误，但可能不需要完整的堆栈跟踪
            logger.warning(
                f"HTTP Exception intercepted [{request_id}]: {http_exc.status_code} - {http_exc.detail}"
            )
            error_content = ErrorResponse(
                detail=http_exc.detail,
                request_id=request_id
            ).model_dump()
            return JSONResponse(
                status_code=http_exc.status_code,
                content=error_content,
                headers=getattr(http_exc, 'headers', None) # 保留原有的 headers
            )
        except Exception as exc:
            # 处理所有其他未预料到的异常
            logger.error(
                f"Unhandled Exception intercepted [{request_id}]: {str(exc)}", 
                exc_info=True # 包含堆栈跟踪
            )
            # 避免在生产环境中泄露内部错误细节
            detail_message = "Internal Server Error"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if settings.DEBUG:
                 detail_message = f"Internal Server Error: {str(exc)}"
            
            error_content = ErrorResponse(
                detail=detail_message,
                request_id=request_id
            ).model_dump()
            return JSONResponse(
                status_code=status_code,
                content=error_content
            )


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有HTTP请求的详细信息，包括请求方法、路径、状态码、处理时间等。
    为每个请求分配唯一ID，方便在日志中追踪整个请求的处理流程。
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 重置 context var (可能不是必须，但更安全)
        token = None
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 设置 context var
        token = request_id_var.set(request_id)
        
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
        # 注意：这里的 try...except 块是为了记录请求完成或异常，
        # 而全局错误处理中间件的 try...except 是为了返回标准错误响应
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
            # 记录此中间件捕获的异常 (可能已被上层错误中间件处理并转换为Response)
            # 但如果上层没有捕获（例如ASGI服务器错误），这里仍然会记录
            process_time = time.time() - start_time
            # 检查是否已经被处理为 Response (例如被 GlobalErrorHandlingMiddleware 捕获)
            # 这里的 'e' 可能是原始异常，也可能是其他问题
            # 为了避免重复记录，可以考虑不再在这里记录 ERROR，因为上层会记录
            # logger.error(
            #     f"请求异常 in RequestLogMiddleware [{request_id}] {method} {path} - "
            #     f"({process_time:.4f}s): {str(e)}",
            #     exc_info=True
            # )
            # 只需要确保 finally 中的 reset 执行即可
            raise # 重新抛出，让 FastAPI 或 ASGI 服务器处理最终响应
        finally:
            # 在请求处理完成后（无论成功或失败）重置 context var
            if token:
                request_id_var.reset(token)


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
    # --- 修改：将全局错误处理放在最前面 ---
    app.add_middleware(GlobalErrorHandlingMiddleware)
    
    # 添加请求日志中间件（在错误处理之后）
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(ResponseSizeLogMiddleware)
    
    logger.info("中间件已设置完成 (包含全局错误处理)") 