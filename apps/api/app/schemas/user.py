from typing import Optional, Annotated
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础数据模型"""
    email: Optional[Annotated[str, EmailStr]] = Field(None, description="用户邮箱")
    username: Optional[str] = Field(None, description="用户名")
    full_name: Optional[str] = Field(None, description="用户全名")
    is_active: Optional[bool] = Field(True, description="用户是否激活")
    role: Optional[UserRole] = Field(None, description="用户角色")
    

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


class UserUpdate(UserBase):
    """用户更新数据模型"""
    password: Optional[str] = Field(None, min_length=8, description="用户密码（如需更新）")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "updated@example.com",
                "full_name": "Updated Name",
                "is_active": True
            }
        }
    )


class UserResponse(UserBase):
    """API响应中的用户数据模型"""
    id: UUID = Field(..., description="用户ID")
    is_superuser: bool = Field(..., description="是否为超级用户")
    is_verified: bool = Field(..., description="邮箱是否已验证")
    
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