# FastAPI 后端 (apps/api) 开发规范

## 1. 引言

本文档旨在为 `apps/api` 目录下的 FastAPI 后端项目提供一套统一的开发规范和最佳实践。遵循这些规范有助于提高代码的可读性、可维护性、可测试性，并确保项目架构的一致性。

## 2. 项目架构

本项目采用基于 **FastAPI** 的分层架构，旨在实现关注点分离。主要层级包括：

*   **接口层 (API Endpoints)**: `app/api/v1/endpoints/`
    *   负责处理 HTTP 请求路由、请求体验证、响应模型序列化。
    *   依赖服务层执行业务逻辑。
    *   负责**权限校验**（通过依赖项实现）。
*   **服务层 (Services)**: `app/services/`
    *   包含核心业务逻辑和流程编排。
    *   依赖**仓储接口**进行数据持久化操作。
    *   负责**数据库事务管理** (`commit`, `rollback`, `refresh`)。
*   **仓储层 (Repositories)**:
    *   **接口 (Interfaces)**: `app/repositories/interfaces/` - 定义数据访问契约，服务层依赖于此。
    *   **实现 (Implementations)**: `app/repositories/sql/` - 提供接口的具体实现（如 SQL），封装数据查询细节。
*   **模型层 (Models)**: `app/models/`
    *   使用 `SQLModel` 定义数据库表结构和 ORM 模型。
*   **数据传输对象 (Schemas)**: `app/schemas/`
    *   使用 `Pydantic` 或 `SQLModel` 定义 API 请求/响应的数据结构和验证规则。
*   **核心模块 (Core)**: `app/core/`
    *   包含配置 (`config.py`)、数据库设置 (`db.py`)、安全 (`security.py`)、日志 (`logging.py`)、自定义异常 (`exceptions.py`)、全局异常处理 (`exception_handlers.py`) 等共享功能。
*   **依赖注入 (Dependencies)**: `app/api/deps.py`
    *   定义 FastAPI 依赖项函数，用于注入服务、仓库、配置、数据库会话和当前用户等。

## 3. 编码标准

*   **格式化**: 强制使用 **Black** 进行代码格式化。
*   **Linting**: 使用 **Ruff** 或 **Flake8** 进行代码风格和错误检查。遵循 **PEP 8** 规范。
*   **命名**:
    *   变量、函数、方法：`snake_case` (小写下划线)。
    *   类、异常：`PascalCase` (驼峰式)。
    *   常量：`UPPER_SNAKE_CASE` (大写下划线)。
    *   使用清晰、描述性的名称。
*   **类型提示**: 强制使用 Python 类型提示 (`typing` 模块)，包括函数签名和变量声明。

## 4. API 端点 (Endpoints)

*   **位置**: `app/api/v1/endpoints/` 目录下，按资源分组创建文件 (e.g., `users.py`, `auth.py`)。
*   **路由**: 使用 `APIRouter`。URL 路径使用小写字母和连字符 (`-`)（如果需要分隔），优先使用名词表示资源 (e.g., `/users/`, `/users/{user_id}/profile`)。
*   **HTTP 方法**: 使用正确的 HTTP 动词 (GET, POST, PUT, PATCH, DELETE)。
*   **请求/响应模型**:
    *   使用 `app/schemas/` 中定义的 Pydantic/SQLModel 模型进行请求体验证和响应序列化 (`response_model`)。
    *   为不同的操作创建明确的 Schema (e.g., `UserCreate`, `UserUpdate`, `UserResponse`)。
*   **状态码**: 使用 `fastapi.status` 中定义的标准 HTTP 状态码。
    *   成功: 200 OK, 201 Created, 204 No Content。
    *   客户端错误: 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity。
    *   服务端错误: 500 Internal Server Error (通常由全局异常处理器处理)。
*   **安全与权限**:
    *   使用 `Depends(get_current_user)` 获取已认证用户。
    *   复杂的权限检查逻辑封装在 `deps.py` 中的依赖项函数中。
    *   权限检查应在 API 层进行。
*   **依赖注入**: 使用 `Depends` 注入所需的服务实例、仓库实例、配置等。

## 5. 服务层 (Services)

*   **位置**: `app/services/`。
*   **职责**:
    *   实现核心业务逻辑。
    *   编排对一个或多个仓储接口的调用。
    *   **不应**直接调用其他服务，以保持单一职责；如果需要跨领域逻辑，考虑引入事件驱动或更高层次的协调器。
*   **依赖**:
    *   通过构造函数注入所需的**仓储接口** (`IUserRepository`)。
    *   通过构造函数注入 `AsyncSession` **仅用于事务管理** (`commit`, `rollback`, `refresh`)。
*   **错误处理**:
    *   **必须**抛出 `app.core.exceptions` 中定义的具体业务异常 (e.g., `UserNotFoundException`, `EmailAlreadyExistsException`)。
    *   **禁止**在服务层捕获通用 `Exception` 并返回 `None` 或 `False` 来表示业务错误，应明确抛出异常。
    *   **禁止**直接抛出 `HTTPException`，让全局处理器处理自定义异常。
*   **事务管理**:
    *   对于修改数据的操作（创建、更新、删除），服务方法内部需要显式调用 `await self.db.commit()`。
    *   在 `commit()` 失败或发生其他异常时，需要调用 `await self.db.rollback()`。
    *   在 `commit()` 成功后，如果需要获取数据库生成的值（如 ID）或最新状态，需要调用 `await self.db.refresh(instance)`。

## 6. 仓储层 (Repositories)

*   **接口**:
    *   位置: `app/repositories/interfaces/`。
    *   定义清晰的数据访问方法契约。
    *   服务层依赖这些接口。
*   **实现**:
    *   位置: `app/repositories/sql/` (或其他数据源类型目录)。
    *   实现接口中定义的方法。
    *   **封装所有**与 `SQLModel` / `SQLAlchemy` 相关的查询逻辑 (`select`, `get`, `add`, `delete` 等)。
    *   **不应**包含业务逻辑。
    *   **不应**包含事务管理 (`commit`, `rollback`, `refresh` 由服务层负责)。
    *   通过构造函数注入 `AsyncSession`。

## 7. 模型与数据库 (Models & Database)

*   **模型**:
    *   位置: `app/models/`。
    *   使用 `SQLModel` 定义。一个模型类通常同时定义 Pydantic 验证和 SQLAlchemy 表结构。
    *   合理使用关系 (`Relationship`)。
*   **数据库迁移**:
    *   使用 **Alembic** (`alembic/` 目录)。
    *   修改 `app/models/` 中的模型后，需要运行 `alembic revision --autogenerate -m "Description of changes"` 生成迁移脚本。
    *   **必须**仔细审查自动生成的迁移脚本，确保其正确性。
    *   使用 `alembic upgrade head` 应用迁移。

## 8. 依赖注入 (Dependencies)

*   **位置**: `app/api/deps.py`。
*   **目的**: 定义可重用的依赖项获取函数。
*   **实现**: 创建异步或同步函数，使用 `Depends` 注入其他依赖（如 `get_db`, `get_user_repository`），最终返回所需的对象（如 `UserService` 实例, `Settings`, `User`）。
*   **原则**: 保持依赖项函数简洁，专注于提供单一依赖。

## 9. 错误处理与日志

*   **异常**:
    *   业务逻辑错误使用 `app.core.exceptions` 中的自定义异常。
    *   输入验证错误由 FastAPI 自动处理，通过 `validation_exception_handler` 返回 422。
    *   未预料的内部错误由 `generic_exception_handler` 捕获，返回 500。
*   **日志**:
    *   使用 `app.core.logging` 配置的日志记录器 (`get_logger(__name__)`)。
    *   在关键操作（如 API 请求开始/结束、服务调用、数据库交互、错误发生）处记录日志。
    *   使用合适的日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)。
    *   日志消息应包含上下文信息（如请求 ID、用户 ID、相关实体 ID）。
    *   在服务层或仓库层捕获异常并记录 **详细错误信息** (`exc_info=True`) 后再重新抛出。

## 10. 测试

*   **位置**: `apps/api/tests/` 目录下，按层级组织 (e.g., `api/v1/`, `services/`, `repositories/`)。
*   **框架**: 使用 `pytest` 和 `httpx.AsyncClient`。
*   **类型**:
    *   **API 测试 (集成测试)**:
        *   使用 `AsyncClient` 向测试应用发送请求。
        *   验证 HTTP 状态码、响应体内容。
        *   可选地验证数据库状态变化（使用独立的测试数据库）。
        *   覆盖主要成功路径和常见错误路径 (4xx 状态码)。
    *   **服务测试 (单元测试)**:
        *   **模拟 (Mock)** 依赖的仓储接口 (`IUserRepository`) 和数据库会话 (`AsyncSession` 的 `commit`, `rollback`, `refresh`)。
        *   验证服务方法的业务逻辑是否正确。
        *   验证是否调用了正确的仓库方法和事务方法。
        *   验证是否在适当条件下抛出了正确的自定义业务异常。
    *   **仓库测试 (单元测试)**:
        *   **模拟 (Mock)** `AsyncSession` 的方法 (`execute`, `get`, `add` 等)。
        *   验证仓库方法是否构建了正确的查询语句（通过检查 `execute` 的调用参数）。
        *   验证数据映射是否正确。
*   **数据库**: API 测试应使用独立的测试数据库，并在测试之间清理数据（通过 fixture 实现）。
*   **覆盖率**: 目标是保持高测试覆盖率，特别是对于服务层和仓库层的逻辑。

## 11. 配置管理

*   使用 `app/core/config.py` 中的 Pydantic `Settings` 类。
*   通过环境变量或 `.env` 文件加载配置。
*   在代码中通过 `Depends(get_settings)` 依赖注入配置。
*   **禁止**在代码中硬编码配置值（如数据库 URL、密钥等）。

## 12. 文档

*   API 端点函数**必须**包含清晰的 docstring，FastAPI 会自动用于生成 OpenAPI 文档。
*   复杂的服务逻辑或核心模块应添加必要的代码注释。
*   定期更新本文档和项目根目录的 `README.md` 以反映架构变化和新约定。 