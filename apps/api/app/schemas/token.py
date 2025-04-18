from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    """API认证令牌模型"""
    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )


class TokenPayload(BaseModel):
    """JWT令牌载荷模型"""
    sub: Optional[UUID] = Field(None, description="主题（用户ID）")
    exp: Optional[int] = Field(None, description="过期时间")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "123e4567-e89b-12d3-a456-426614174000",
                "exp": 1645556823
            }
        }
    ) 