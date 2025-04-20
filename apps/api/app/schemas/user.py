from typing import Optional, Annotated, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from datetime import datetime

from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础数据模型"""
    email: Optional[Annotated[str, EmailStr]] = Field(None, description="用户邮箱")
    username: Optional[str] = Field(None, description="用户名")
    full_name: Optional[str] = Field(None, description="用户全名")
    is_active: Optional[bool] = Field(True, description="用户是否激活")
    role: Optional[UserRole] = Field(None, description="用户角色")
    is_superuser: Optional[bool] = Field(None, description="是否为超级用户")
    is_verified: Optional[bool] = Field(None, description="邮箱是否已验证")
    

class UserCreate(UserBase):
    """用户创建数据模型"""
    email: Annotated[str, EmailStr] = Field(..., description="用户邮箱（必填）")
    password: str = Field(..., min_length=8, description="用户密码（至少8位）")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "strongpassword",
                "username": "username",
                "full_name": "Full Name"
            }
        }
    )

    @model_validator(mode="after")
    def set_username_if_empty(self) -> "UserCreate":
        """如果未提供用户名，则使用邮箱前缀作为用户名"""
        if not self.username and self.email:
            self.username = self.email.split("@")[0]
        return self


class UserProfileBase(BaseModel):
    """用户资料基本信息"""
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    """用户资料更新模式"""
    pass


class UserUpdate(UserBase):
    """用户更新数据模型"""
    password: Optional[str] = Field(None, min_length=8, description="用户密码（如需更新）")
    profile: Optional[UserProfileUpdate] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "updated@example.com",
                "full_name": "Updated Name",
                "is_active": True
            }
        }
    )


class UserProfileResponse(UserProfileBase):
    """用户资料响应模式"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """API响应中的用户数据模型"""
    id: UUID = Field(..., description="用户ID")
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    profile: Optional[UserProfileResponse] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "username",
                "full_name": "Full Name",
                "is_active": True,
                "is_superuser": False,
                "is_verified": True,
                "role": "user"
            }
        }
    )


# 仅在内部使用的带密码的用户模型
class UserInDB(UserResponse):
    """数据库中的用户模型（包含敏感信息）"""
    hashed_password: str = Field(..., description="加密后的密码")
    
    model_config = ConfigDict(from_attributes=True) 