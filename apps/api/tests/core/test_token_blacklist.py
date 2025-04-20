import pytest
from datetime import datetime, timedelta
import time

from app.core.token_blacklist import logout_tokens, cleanup_expired_tokens

# 标记所有测试为单元测试
pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


async def test_logout_tokens_dictionary():
    """测试 logout_tokens 字典是否正确初始化"""
    # 检查 logout_tokens 是否是字典类型
    assert isinstance(logout_tokens, dict)
    # 初始状态下应该是空的
    initial_length = len(logout_tokens)


async def test_add_token_to_blacklist():
    """测试向黑名单中添加令牌"""
    # 清空之前的测试数据
    logout_tokens.clear()
    
    # 创建一个测试令牌
    token_id = "test-token-1"
    # 设置过期时间为当前时间后5分钟
    expiry = datetime.utcnow() + timedelta(minutes=5)
    
    # 添加令牌到黑名单
    logout_tokens[token_id] = expiry
    
    # 验证令牌是否在黑名单中
    assert token_id in logout_tokens
    assert logout_tokens[token_id] == expiry


async def test_cleanup_expired_tokens():
    """测试清理过期令牌的功能"""
    # 清空之前的测试数据
    logout_tokens.clear()
    
    # 添加一个过期的令牌（过期时间为1分钟前）
    expired_token = "expired-token"
    expired_time = datetime.utcnow() - timedelta(minutes=1)
    logout_tokens[expired_token] = expired_time
    
    # 添加一个未过期的令牌（过期时间为5分钟后）
    valid_token = "valid-token"
    valid_time = datetime.utcnow() + timedelta(minutes=5)
    logout_tokens[valid_token] = valid_time
    
    # 执行清理
    cleanup_expired_tokens()
    
    # 验证过期的令牌已被移除，而未过期的仍然存在
    assert expired_token not in logout_tokens
    assert valid_token in logout_tokens
    assert logout_tokens[valid_token] == valid_time


async def test_cleanup_with_multiple_expired_tokens():
    """测试同时清理多个过期令牌"""
    # 清空之前的测试数据
    logout_tokens.clear()
    
    # 添加多个过期的令牌
    now = datetime.utcnow()
    for i in range(5):
        token_id = f"expired-token-{i}"
        # 每个令牌都设置为过期（过期时间为 i+1 分钟前）
        expiry = now - timedelta(minutes=i+1)
        logout_tokens[token_id] = expiry
    
    # 添加一个未过期的令牌
    valid_token = "still-valid"
    valid_expiry = now + timedelta(minutes=10)
    logout_tokens[valid_token] = valid_expiry
    
    # 执行清理
    cleanup_expired_tokens()
    
    # 验证所有过期令牌都被移除
    for i in range(5):
        assert f"expired-token-{i}" not in logout_tokens
    
    # 验证未过期令牌仍然存在
    assert valid_token in logout_tokens


async def test_token_expiration_check():
    """测试令牌过期检查逻辑"""
    # 清空之前的测试数据
    logout_tokens.clear()
    
    # 添加一个即将过期的令牌（过期时间为0.5秒后）
    soon_expire_token = "soon-expire"
    soon_expire_time = datetime.utcnow() + timedelta(seconds=0.5)
    logout_tokens[soon_expire_token] = soon_expire_time
    
    # 初始状态下令牌应该存在
    assert soon_expire_token in logout_tokens
    
    # 等待0.6秒，使令牌过期
    time.sleep(0.6)
    
    # 执行清理
    cleanup_expired_tokens()
    
    # 验证令牌已被清理
    assert soon_expire_token not in logout_tokens 