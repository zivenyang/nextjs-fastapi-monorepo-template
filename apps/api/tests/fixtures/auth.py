"""
认证相关的测试fixtures。

提供认证令牌和请求头，用于测试需要认证的API端点。
"""

from typing import Dict

import pytest

from app.core.security import create_access_token
from app.models.user import User

@pytest.fixture(scope="function")
def token_headers(test_user: User) -> Dict[str, str]:
    """
    获取带有测试用户令牌的认证头。
    
    为测试用户创建JWT访问令牌，并返回格式化为Authorization请求头的字典。
    
    Args:
        test_user: 测试用户fixture
        
    Returns:
        Dict[str, str]: 包含认证头的字典，格式为 {"Authorization": "Bearer token..."}
    """
    access_token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def superuser_token_headers(test_superuser: User) -> Dict[str, str]:
    """
    获取带有超级用户令牌的认证头。
    
    为测试超级用户创建JWT访问令牌，并返回格式化为Authorization请求头的字典。
    
    Args:
        test_superuser: 测试超级用户fixture
        
    Returns:
        Dict[str, str]: 包含认证头的字典，格式为 {"Authorization": "Bearer token..."}
    """
    access_token = create_access_token(subject=str(test_superuser.id))
    return {"Authorization": f"Bearer {access_token}"} 