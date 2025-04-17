# FastAPI Backend (`apps/api`)

本项目使用 FastAPI 构建后端 API 服务。

## 项目结构

```
apps/api/
├── app/                     # 核心应用程序代码
│   ├── __init__.py
│   ├── core/                # 核心配置、通用函数
│   │   ├── __init__.py
│   │   └── config.py        # 应用配置 (例如: Pydantic Settings)
│   ├── db/                  # 数据库交互层
│   │   ├── __init__.py
│   │   ├── base.py          # 数据库连接、基础模型 (例如: SQLAlchemy Base)
│   │   └── models/          # SQLAlchemy 模型
│   │       └── __init__.py
│   ├── api/                 # API 路由/接口层
│   │   ├── __init__.py
│   │   ├── deps.py          # API 依赖项 (例如: 获取 DB session)
│   │   └── v1/              # API 版本 1
│   │       ├── __init__.py
│   │       └── endpoints/     # 具体 API 路由 (例如: users.py, items.py)
│   │           └── __init__.py
│   ├── schemas/             # Pydantic 数据模型 (用于数据校验和序列化)
│   │   └── __init__.py
│   ├── services/            # 业务逻辑层
│   │   └── __init__.py
│   └── main.py              # FastAPI 应用实例创建和全局中间件配置
├── tests/                   # 测试代码
│   └── __init__.py
├── .env                     # 环境变量 (不提交到 Git)
├── .gitignore
├── .python-version          # Python 版本 (pyenv)
├── pyproject.toml           # 项目依赖 (Poetry / PDM)
├── README.md                # 本文档
└── uv.lock                  # 依赖锁定文件 (uv)
```

## 运行项目

(后续添加运行说明)

## 主要模块说明

*   **`app/main.py`**: 创建 FastAPI app 实例，包含全局中间件、异常处理等。
*   **`app/core/config.py`**: 使用 Pydantic Settings 管理配置，从环境变量或 `.env` 文件加载。
*   **`app/db/base.py`**: 初始化数据库连接 (例如 SQLAlchemy engine, sessionmaker)。
*   **`app/db/models/`**: 定义 SQLAlchemy 数据表模型。
*   **`app/schemas/`**: 定义 Pydantic 模型，用于 API 请求体验证和响应数据格式化。
*   **`app/services/`**: 包含核心业务逻辑，处理数据和执行操作。Service 层通常被 API 层调用。
*   **`app/api/deps.py`**: 定义 FastAPI 依赖项，例如用于获取数据库会话、验证用户身份等。
*   **`app/api/v1/endpoints/`**: 存放具体的 API 路由实现，每个文件对应一个资源或功能模块 (例如 `users.py`)。路由函数应保持简洁，主要负责调用 Service 层处理业务逻辑。
*   **`tests/`**: 存放单元测试、集成测试等。

## 添加新功能步骤 (示例)

1.  **定义数据模型**: 在 `app/db/models/` 下创建新的 SQLAlchemy 模型文件 (如果需要数据库表)。
2.  **定义数据 Schema**: 在 `app/schemas/` 下创建 Pydantic 模型文件，定义 API 的输入输出数据结构。
3.  **编写业务逻辑**: 在 `app/services/` 下创建 Service 文件，实现具体的功能逻辑。
4.  **创建 API 路由**: 在 `app/api/v1/endpoints/` 下创建新的路由文件，定义 API 路径、HTTP 方法，并调用相应的 Service 函数。
5.  **注册路由**: 在 `app/api/v1/__init__.py` 或 `app/main.py` 中注册新的路由。
6.  **(可选) 添加依赖**: 如果需要数据库连接或其他依赖，在 `app/api/deps.py` 中定义。
7.  **编写测试**: 在 `tests/` 目录下为新功能添加测试。
