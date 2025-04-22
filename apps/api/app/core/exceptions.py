from fastapi import status

class AppException(Exception):
    """基础应用异常类"""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected internal server error occurred."

    def __init__(self, detail: str | None = None, status_code: int | None = None):
        self.detail = detail or self.detail
        self.status_code = status_code or self.status_code
        super().__init__(self.detail)

class NotFoundException(AppException):
    """资源未找到异常 (404)"""
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found."

class BadRequestException(AppException):
    """错误请求异常 (400)"""
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Bad request."

class ForbiddenException(AppException):
    """禁止访问异常 (403)"""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Access forbidden."

class UnauthorizedException(AppException):
    """未授权异常 (401)"""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required."

class ConflictException(AppException):
    """资源冲突异常 (409)"""
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource conflict."

# --- 特定业务异常 ---

class UserNotFoundException(NotFoundException):
    """用户未找到异常"""
    detail = "User not found."

class EmailAlreadyExistsException(ConflictException):
    """邮箱已存在异常"""
    detail = "Email already registered by another user."

class InvalidCredentialsException(UnauthorizedException):
    """无效凭证异常 (用于登录)"""
    detail = "Incorrect email or password."

class InactiveUserException(ForbiddenException):
    """非活动用户异常"""
    detail = "Inactive user."

class NotSuperuserException(ForbiddenException):
    """非超级用户异常"""
    detail = "The user doesn't have enough privileges."

class InvalidTokenException(UnauthorizedException):
    """无效令牌异常"""
    detail = "Invalid authentication token."

class ExpiredTokenException(UnauthorizedException):
    """过期令牌异常"""
    detail = "Authentication token has expired." 