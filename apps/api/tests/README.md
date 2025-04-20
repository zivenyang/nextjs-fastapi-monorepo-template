# FastAPI 测试说明

本项目使用 pytest 进行测试，主要测试内容包括API接口测试和数据库功能测试。

## 测试结构

```
tests/
├── conftest.py                   # 测试配置和全局 fixtures
├── fixtures/                     # 测试数据和辅助功能
│   ├── __init__.py              # fixtures导出
│   ├── auth.py                  # 认证相关的fixtures
│   ├── database.py              # 数据库相关的fixtures
│   ├── http_client.py           # HTTP客户端fixtures
│   └── users.py                 # 用户测试数据fixtures
├── test_db.py                   # 数据库功能测试
├── api/
│   └── v1/
│       ├── test_auth.py         # 认证API测试
│       ├── test_auth_logout.py  # 登出API测试
│       └── test_users.py        # 用户API测试
└── core/
    └── test_token_blacklist.py  # 令牌黑名单单元测试
```

## 环境配置系统

项目使用 **python-dotenv** 库动态加载环境配置文件：

- **开发环境**: `.env` (默认)
- **测试环境**: `.env.test` 
- **生产环境**: `.env.production`

环境选择通过 `ENVIRONMENT` 环境变量控制:
```bash
# 使用测试环境
export ENVIRONMENT=test
# 使用生产环境
export ENVIRONMENT=production
```

在测试中，`pytest.ini` 已配置 `ENVIRONMENT=test` 环境变量，确保自动使用测试环境。

### 测试环境配置

测试环境使用专用的 `.env.test` 文件，主要配置：

- 使用专门的测试数据库 (`postgresql+asyncpg://postgres:password@localhost:5432/test_mydb`)
- 开启调试模式 (`DEBUG=true`)
- 测试专用的密钥和安全设置
- 特定的 CORS 设置格式
- 较长的令牌有效期，方便测试

这种环境隔离确保测试不会影响开发或生产数据，同时又使用相同类型的数据库系统，保证测试的真实性。

## 测试数据库设置

在运行测试前，需要先设置测试数据库：

```bash
# 设置测试数据库
python setup_test_db.py
```

这个脚本会：
1. 检查并创建 `test_mydb` 数据库（如果不存在）
2. 初始化数据库架构（创建所有必要的表）
3. 清理所有现有数据，确保测试从干净的状态开始

## 运行测试

### 运行所有测试

```bash
cd apps/api
pytest
```

### 运行特定测试文件

```bash
# 运行认证测试
pytest tests/api/v1/test_auth.py

# 运行登出功能测试
pytest tests/api/v1/test_auth_logout.py

# 运行令牌黑名单单元测试
pytest tests/core/test_token_blacklist.py

# 运行用户API测试
pytest tests/api/v1/test_users.py

# 运行数据库功能测试
pytest tests/test_db.py
```

### 运行带有特定标记的测试

```bash
# 运行单元测试
pytest -m unit

# 运行所有API测试
pytest -m api

# 运行认证相关测试
pytest -m auth

# 运行所有非慢速测试
pytest -m "not slow"
```

## 测试类型

1. **API 测试**：测试 FastAPI 接口功能，包括：
   - 认证 (登录/注册)
   - 登出功能（令牌黑名单）
   - 用户管理 (获取用户信息、列表)
   - 权限控制

2. **数据库测试**：测试数据库功能，包括：
   - 创建和查询用户
   - 用户角色枚举
   - 自动时间戳字段

3. **核心功能测试**：测试系统核心组件，包括：
   - 令牌黑名单功能（添加令牌、清理过期令牌）
   - 安全组件（密码验证、令牌生成与解码）

## 特定功能测试说明

### 令牌黑名单测试

`token_blacklist.py` 模块是实现登出功能的核心，通过将已登出的令牌存储在内存字典中实现。测试内容包括：

- 测试黑名单字典初始化
- 向黑名单添加令牌
- 清理过期令牌功能
- 处理多个过期令牌
- 令牌过期检查逻辑

### 登出API测试

登出API端点测试验证用户成功登出的功能，包括：

- 测试成功登出
- 测试使用无效令牌登出
- 测试没有提供令牌的情况
- 测试使用错误令牌类型
- 测试多次登出同一令牌

## 测试设计说明

- 使用独立的 SQLite 内存数据库进行测试，不影响开发/生产数据库
- 每个测试函数结束后会回滚数据库更改，确保测试隔离
- 使用预创建的测试用户和超级用户来测试不同权限场景
- 利用令牌头部测试需要认证的 API 端点
- 通过环境变量和 dotenv 配置测试环境，确保测试一致性

## 最佳实践

1. **测试隔离**：每个测试应该独立，不依赖其他测试的执行结果
2. **测试覆盖**：应涵盖正常流程和边缘情况
3. **测试命名**：函数名应清晰描述测试目的
4. **断言明确**：使用具体的断言检查响应状态和内容
5. **环境分离**：使用专用的测试环境和配置 