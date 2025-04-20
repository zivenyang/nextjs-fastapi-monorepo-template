# FastAPI API 模板

一个基于FastAPI和SQLModel的API模板，支持异步SQLAlchemy和PostgreSQL。

## 特性

- 基于 **FastAPI** 和 **SQLModel** 构建的API
- **异步SQLAlchemy** - 使用异步数据库操作
- **PostgreSQL** - 作为主要数据库
- **JWT认证** - 使用OAuth2密码流认证
- **依赖注入** - 使用FastAPI的依赖注入系统
- **SQLModel** - 结合了SQLAlchemy的强大和Pydantic的验证
- **自动API文档** - 使用FastAPI的自动文档
- **环境配置** - 支持不同环境的配置
- **Alembic** - 数据库迁移工具
- **Docker支持** - 使用Docker容器化
- **测试** - 使用pytest进行API测试
- **日志系统** - 完整的日志记录功能，支持请求、错误、性能监控日志

## 快速开始

### 前提条件

- Python 3.9+
- PostgreSQL

### 安装

1. 克隆仓库：

```bash
git clone https://github.com/zivenyang/nextjs-fastapi-monorepo-template.git
cd fastapi-template/apps/api
```

2. 创建虚拟环境并安装依赖：

```bash
uv sync
uv venv
```

3. 配置环境变量：

复制`.env.template`为`.env`并按需修改配置。

4. 创建数据库：

使用postgresql创建mydb数据库

5. 运行应用：

```bash
uv run fastapi dev
```

访问：http://localhost:8000/docs 查看API文档。

## 项目结构

```
api/
├── alembic/              # 数据库迁移
├── app/                  # 应用代码
│   ├── api/              # API路由
│   │   ├── deps.py       # 依赖项
│   │   └── v1/           # API v1版本
│   │       ├── endpoints/# API端点
│   │       └── __init__.py # 路由注册
│   ├── core/             # 核心模块
│   │   ├── config.py     # 配置
│   │   ├── db.py         # 数据库设置
│   │   ├── security.py   # 安全/认证
│   │   ├── logging.py    # 日志配置
│   │   └── middleware.py # 中间件
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic模式
│   └── services/         # 业务逻辑
├── logs/                 # 日志文件
├── tests/                # 测试
├── .env                  # 环境变量
├── .env.test             # 测试环境变量
├── alembic.ini           # Alembic配置
├── pyproject.toml        # 项目配置
└── run.py                # 启动脚本
```

## 日志系统

本项目包含完整的日志系统，支持多种日志记录需求：

### 日志特性

1. **多级别日志**：支持DEBUG、INFO、WARNING、ERROR和CRITICAL级别
2. **请求日志**：记录所有HTTP请求的详细信息，包括方法、路径、状态码、执行时间等
3. **错误日志**：分离记录错误信息，便于问题排查
4. **性能监控**：记录大型响应和长时间运行的请求
5. **请求追踪**：为每个请求分配唯一ID，便于跟踪完整请求流程
6. **日志文件轮转**：支持按大小和时间轮转日志文件
7. **可配置性**：通过环境变量控制日志级别和文件设置

### 日志配置

在`.env`文件中配置日志选项：

```
# 日志设置
LOGGING_LEVEL=INFO             # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE_MAX_SIZE=10485760     # 日志文件最大大小 (字节): 10MB
LOG_FILE_BACKUP_COUNT=5        # 保留的日志文件数量
ERROR_LOG_RETENTION_DAYS=30    # 错误日志保留天数
```

### 在代码中使用日志

```python
from app.core.logging import get_logger

# 创建模块日志记录器
logger = get_logger(__name__)

# 使用不同级别记录日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误信息")

# 记录异常
try:
    # 代码操作
except Exception as e:
    logger.error(f"操作失败: {str(e)}", exc_info=True)
```

## 测试

运行测试：

```bash
uv run pytest
```

## 许可证

MIT
