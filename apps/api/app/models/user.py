import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Annotated

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime, String, func, text
from pydantic import EmailStr, field_validator, ConfigDict
import enum

# 定义用户角色
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# 定义 User 模型，它同时是 Pydantic 模型和 SQLAlchemy 表模型
class User(SQLModel, table=True):
    """用户模型，存储用户基本信息"""
    
    __tablename__ = "users"
    
    # 主键和核心字段
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    email: Annotated[str, EmailStr] = Field(
        unique=True, 
        index=True, 
        max_length=255,
        sa_column_kwargs={"comment": "用户邮箱，唯一标识"}
    )
    hashed_password: str = Field(
        nullable=False,
        sa_column_kwargs={"comment": "加密后的密码"}
    )
    
    # 用户信息字段
    username: str = Field(
        index=True, 
        max_length=50, 
        nullable=True,
        sa_column_kwargs={"comment": "用户名，可用于登录"}
    )
    full_name: Optional[str] = Field(
        default=None, 
        max_length=100,
        sa_column_kwargs={"comment": "用户全名"}
    )
    role: UserRole = Field(
        default=UserRole.USER, 
        sa_column=Column(
            String, 
            nullable=False,
            comment="用户角色",
            server_default=text(f"'{UserRole.USER}'")
        )
    )
    
    # 状态标志
    is_active: bool = Field(
        default=True,
        sa_column_kwargs={"comment": "用户是否激活", "server_default": "true"}
    )
    is_superuser: bool = Field(
        default=False,
        sa_column_kwargs={"comment": "是否超级用户", "server_default": "false"}
    )
    is_verified: bool = Field(
        default=False,
        sa_column_kwargs={"comment": "邮箱是否已验证", "server_default": "false"}
    )
    
    # 时间戳字段
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(0))),
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False,
            server_default=func.now(),
            comment="创建时间"
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=True,
            onupdate=func.now(),
            comment="更新时间"
        )
    )
    last_login: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"comment": "最后登录时间"}
    )
    
    # Pydantic配置
    model_config = ConfigDict(
        from_attributes=True,  # 替代 orm_mode=True
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "username",
                "full_name": "Full Name",
                "role": "user"
            }
        }
    )
    
    # 字段验证器
    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if v and "@" not in v:
            raise ValueError("无效的邮箱地址")
        return v.lower() if v else v
    
    def __repr__(self) -> str:
        """用户对象的字符串表示"""
        return f"User(id={self.id}, email={self.email}, username={self.username}, role={self.role})"


# 用户个人资料表
class UserProfile(SQLModel, table=True):
    """用户个人资料，存储用户的详细信息"""
    
    __tablename__ = "user_profiles"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    user_id: uuid.UUID = Field(
        foreign_key="users.id", 
        unique=True,
        sa_column_kwargs={"comment": "关联的用户ID"}
    )
    avatar_url: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "头像URL"}
    )
    bio: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "个人简介"}
    )
    phone_number: Optional[str] = Field(
        default=None, 
        max_length=20,
        sa_column_kwargs={"comment": "电话号码"}
    )
    address: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"comment": "地址"}
    )
    
    # 时间戳字段
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(0))),
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False,
            server_default=func.now(),
            comment="创建时间"
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=True,
            onupdate=func.now(),
            comment="更新时间"
        )
    )
    
    # Pydantic配置
    model_config = ConfigDict(from_attributes=True) 