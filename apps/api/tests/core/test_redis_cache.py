import pytest
import json
from datetime import timedelta
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.config import settings

from app.core.redis_cache import (
    RedisCache,
    get_redis_client,
    api_cache,
    add_token_to_blacklist,
    is_token_blacklisted
)


@pytest.fixture
async def mock_redis():
    """Mock Redis客户端"""
    redis_mock = AsyncMock()
    
    # 设置默认的mock响应
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.exists.return_value = 0  # 默认为0，表示不存在
    redis_mock.setex.return_value = True
    
    with patch("app.core.redis_cache.get_redis_client", return_value=redis_mock):
        yield redis_mock


class TestRedisCache:
    """测试Redis缓存服务类"""

    @pytest.mark.asyncio
    async def test_set_get_delete(self, mock_redis):
        """测试基本的设置、获取和删除操作"""
        cache = RedisCache(prefix="test")
        
        # 设置缓存
        result = await cache.set("key1", "value1", expire=60)
        assert result is True
        mock_redis.set.assert_called_with(
            "test:key1", json.dumps("value1"), ex=60
        )
        
        # 获取缓存
        mock_redis.get.return_value = json.dumps("value1").encode()
        value = await cache.get("key1")
        assert value == "value1"
        mock_redis.get.assert_called_with("test:key1")
        
        # 删除缓存
        result = await cache.delete("key1")
        assert result == 1
        mock_redis.delete.assert_called_with("test:key1")

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, mock_redis):
        """测试获取不存在的键"""
        cache = RedisCache(prefix="test")
        mock_redis.get.return_value = None
        value = await cache.get("nonexistent")
        assert value is None
        mock_redis.get.assert_called_with("test:nonexistent")

    @pytest.mark.asyncio
    async def test_set_complex_data(self, mock_redis):
        """测试设置复杂数据结构"""
        cache = RedisCache(prefix="test")
        data = {"name": "test", "value": [1, 2, 3]}
        
        result = await cache.set("complex", data, expire=60)
        assert result is True
        mock_redis.set.assert_called_with(
            "test:complex", json.dumps(data), ex=60
        )
        
        mock_redis.get.return_value = json.dumps(data).encode()
        value = await cache.get("complex")
        assert value == data


class TestAPICacheDecorator:
    """测试API缓存装饰器"""

    @pytest.mark.asyncio
    async def test_api_cache_decorator(self, mock_redis):
        """测试API缓存装饰器功能"""
        # 模拟Redis返回缓存未命中
        mock_redis.get.return_value = None
        
        # 模拟被装饰的API函数
        @api_cache(expire=60)
        async def test_api(param1: str, param2: int):
            return {"result": f"{param1}_{param2}"}
        
        # 首次调用应该执行函数并缓存结果
        result = await test_api("test", 123)
        assert result == {"result": "test_123"}
        
        # 验证缓存设置
        mock_redis.set.assert_called()
        
        # 模拟缓存命中
        mock_redis.get.return_value = json.dumps({"result": "test_123"}).encode()
        
        # 第二次调用应从缓存返回
        result = await test_api("test", 123)
        assert result == {"result": "test_123"}


class TestJWTCache:
    """测试JWT令牌缓存功能"""

    @pytest.mark.asyncio
    async def test_add_token_to_blacklist(self, mock_redis):
        """测试添加令牌到黑名单"""
        token_jti = str(uuid.uuid4())
        expiration = timedelta(minutes=15)
        
        # 设置模拟对象以应对新的实现
        jwt_cache_mock = AsyncMock()
        jwt_cache_mock.setex.return_value = True
        
        with patch("app.core.redis_cache.jwt_cache_instance.setex", jwt_cache_mock.setex):
            result = await add_token_to_blacklist(token_jti, expiration)
            assert result is True
            # 验证setex被调用，并检查参数
            jwt_cache_mock.setex.assert_called_once()
            # 获取调用参数
            args, kwargs = jwt_cache_mock.setex.call_args
            # 验证第一个参数是token_jti
            assert args[0] == token_jti
            # 验证第二个参数是过期时间（秒）
            assert args[1] == int(expiration.total_seconds())
            # 验证第三个参数是值
            assert args[2] == "1"

    @pytest.mark.asyncio
    async def test_is_token_blacklisted(self):
        """测试检查令牌是否在黑名单中"""
        token_jti = "test-token-jti"
        
        # 方法1：直接测试is_token_blacklisted函数
        with patch("app.core.redis_cache.jwt_cache_instance.exists") as mock_exists:
            # 测试不在黑名单的情况
            mock_exists.return_value = False
            result = await is_token_blacklisted(token_jti)
            assert result is False
            
            # 测试在黑名单的情况
            mock_exists.return_value = True
            result = await is_token_blacklisted(token_jti)
            assert result is True
            
        # 测试异常情况
        with patch("app.core.redis_cache.jwt_cache_instance.exists", 
                   side_effect=Exception("测试异常")):
            result = await is_token_blacklisted(token_jti)
            assert result is True  # 出错时应该返回True（安全起见） 