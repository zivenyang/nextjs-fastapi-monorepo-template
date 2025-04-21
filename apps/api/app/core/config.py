from typing import Any, Dict, List, Optional
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, PostgresDsn, Field, field_validator
import secrets
from dotenv import load_dotenv

# 获取项目根目录
API_ROOT = Path(__file__).parent.parent.parent.resolve()

# 确定环境和环境文件
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ENV_FILE = os.getenv("ENV_FILE")

# 如果没有明确指定ENV_FILE，根据环境自动选择
if not ENV_FILE:
    if ENVIRONMENT == "test":
        ENV_FILE = ".env.test"
    elif ENVIRONMENT == "production":
        ENV_FILE = ".env.production"
    else:
        ENV_FILE = ".env"

# 构建环境文件路径
env_path = API_ROOT / ENV_FILE

# 加载环境变量文件
load_dotenv(dotenv_path=env_path)

# 记录使用的环境文件（调试用）
print(f"加载环境配置: {env_path} (环境: {ENVIRONMENT})")


class Settings(BaseSettings):
    """应用程序设置
    
    包含API和数据库配置项，使用环境变量和.env文件进行配置
    """
    ENVIRONMENT: str = Field(..., description="环境类型")
    # API 设置
    API_V1_STR: str = Field("/api/v1", description="API版本前缀")
    PROJECT_NAME: str = Field("FastAPI Template", description="项目名称")
    PROJECT_DESCRIPTION: str = Field("一个基于FastAPI的Web API模板", description="项目描述")
    OPENAPI_OUTPUT_FILE: str = Field("../../packages/openapi-client/openapi.json", description="openapi文件生成路径")
    OPENAPI_URL: str = Field("/openapi.json", description="openapi文件URL路径")
    
    # API 路径设置
    AUTH_TOKEN_URL: str = Field("auth/login", description="认证令牌URL路径(不含API前缀)")
    
    # CORS 设置
    BACKEND_CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000", "http://localhost"], 
        description="允许的CORS来源列表"
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """解析CORS配置，支持逗号分隔的字符串或列表"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 安全设置
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="JWT加密密钥 - 生产环境必须设置为安全值"
    )
    ALGORITHM: str = Field("HS256", description="JWT加密算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="令牌有效期（分钟）", gt=0)
    
    # 数据库设置
    DATABASE_URL: PostgresDsn = Field(
        ..., 
        description="数据库连接字符串 - SQLAlchemy格式"
    )
    
    # Redis设置
    REDIS_HOST: str = Field("localhost", description="Redis主机地址")
    REDIS_PORT: int = Field(6379, description="Redis端口")
    REDIS_DB: int = Field(0, description="Redis数据库索引")
    REDIS_PASSWORD: Optional[str] = Field(None, description="Redis密码")
    REDIS_ENABLED: bool = Field(True, description="是否启用Redis缓存")
    # API缓存设置
    API_CACHE_ENABLED: bool = Field(True, description="是否启用API响应缓存")
    API_CACHE_EXPIRE_SECONDS: int = Field(300, description="API缓存默认过期时间（秒）")
    
    # 其他设置
    DEBUG: bool = Field(False, description="是否开启调试模式")
    TESTING: bool = Field(False, description="是否为测试环境")
    LOGGING_LEVEL: str = Field("INFO", description="日志级别")
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Any:
        """验证数据库URL格式"""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username="postgres",
            password="password",
            host="localhost",
            port="5432",
            path="/mydb",
        )
    
    # Pydantic设置 - 使用已加载的环境变量，而不需要指定文件
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore"
    )
    
    # 获取完整的TOKEN URL (包含API前缀)
    @property
    def FULL_AUTH_TOKEN_URL(self) -> str:
        """返回包含API前缀的完整认证URL路径"""
        return f"{self.API_V1_STR}/{self.AUTH_TOKEN_URL}"


# 创建一个全局可用的 Settings 实例
settings = Settings()


# 派生设置，依赖于基本设置
PROJECT_NAME = settings.PROJECT_NAME
API_V1_STR = settings.API_V1_STR
DEBUG = settings.DEBUG

# 打印当前配置信息（调试用）
if DEBUG:
    print(f"项目名称: {PROJECT_NAME}")
    print(f"API版本路径: {API_V1_STR}")
    print(f"认证路径: {settings.FULL_AUTH_TOKEN_URL}")
    print(f"数据库URL: {settings.DATABASE_URL}")
    print(f"Redis: {'启用' if settings.REDIS_ENABLED else '禁用'} ({settings.REDIS_HOST}:{settings.REDIS_PORT})")
    print(f"API缓存: {'启用' if settings.API_CACHE_ENABLED else '禁用'}")
    print(f"调试模式: {'开启' if DEBUG else '关闭'}")
    print(f"测试模式: {'开启' if settings.TESTING else '关闭'}")
    print(f"日志级别: {settings.LOGGING_LEVEL}")
