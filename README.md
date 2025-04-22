# Next.js FastAPI Monorepo模板

## 项目简介

这是一个基于Next.js和FastAPI的全栈应用模板，使用Turborepo管理monorepo结构。该项目提供了现代化的Web应用开发基础，包括身份验证、数据库集成和UI组件库。

## 项目架构

项目采用monorepo结构，主要包含以下部分：

```
.
├── apps/
│   ├── web/       # Next.js前端应用
│   └── api/       # FastAPI后端应用
└── packages/      # 共享包
    ├── ui/        # UI组件库
    ├── eslint/    # ESLint配置
    └── tsconfig/  # TypeScript配置
```

### 前端架构 (Next.js)

前端采用Next.js框架，具有以下特点：

- 基于React，支持服务器端渲染(SSR)和静态生成(SSG)
- 使用App Router结构进行路由管理
- 通过Server Actions进行服务器端操作
- 使用Context API进行状态管理

### 后端架构 (FastAPI)

后端采用FastAPI框架，具有以下特点：

- 高性能的Python API框架
- 自动生成OpenAPI文档
- SQLModel用于数据库ORM
- JWT认证机制

#### 分层架构与仓储模式

为了更好地组织代码和解耦，后端采用了分层架构，并引入了**仓储模式 (Repository Pattern)**：

1.  **接口层 (API Endpoints - `app/api/v1/endpoints/`)**:
    *   负责处理 HTTP 请求和响应。
    *   依赖于服务层来执行业务操作。
    *   使用 Pydantic/SQLModel schemas (`app/schemas/`) 定义 API 数据结构。

2.  **服务层 (Services - `app/services/`)**:
    *   包含核心业务逻辑（例如，用户注册流程、信息更新规则）。
    *   依赖于**仓储接口** (`app/repositories/interfaces/`) 来进行数据持久化操作。
    *   **负责事务管理**（控制数据库 `commit`, `rollback`, `refresh`）。目前事务控制在服务层，未来可能引入 Unit of Work (UoW) 模式进一步优化。

3.  **仓储层 (Repositories)**:
    *   **接口 (`app/repositories/interfaces/`)**: 定义数据访问操作的契约（例如 `IUserRepository` 定义了获取、创建、更新用户的方法）。服务层依赖这些接口。
    *   **实现 (`app/repositories/sql/`)**: 提供仓库接口的具体实现（例如 `SQLUserRepository` 使用 `AsyncSession` 和 SQLModel 执行数据库操作）。这部分封装了数据访问的细节。

4.  **数据模型层 (Models - `app/models/`)**:
    *   定义应用程序的数据结构和数据库表映射（使用 SQLModel）。

这种架构使得：
*   **业务逻辑**与**数据访问逻辑**分离。
*   **服务层**的单元测试更加简单，只需 Mock 仓库接口。
*   **仓库实现**可以独立测试其数据库交互。
*   未来更换数据库技术或 ORM 对业务逻辑层的影响更小。

依赖注入系统 (`app/api/deps.py`) 负责将具体的仓库实现 (`SQLUserRepository`) 注入到需要仓库接口 (`IUserRepository`) 的服务层 (`UserService`) 中。

### JWT 认证系统

项目实现了完整的JWT认证系统：

### 前端认证流程

1. 用户登录时，前端发送凭据到后端
2. 后端验证凭据并返回JWT令牌
3. 前端将令牌存储在HTTP-only cookie中
4. 使用React Context管理身份验证状态
5. 定期检查认证状态以确保同步

### 后端认证流程

1. 实现JWT令牌创建和验证
2. 维护令牌黑名单用于处理登出操作
3. 使用依赖项注入确保API端点的安全访问

## 优化方案

根据React 19和Next.js 15的新特性，以下是对认证系统的优化建议：

1. 使用React 19的useActionState代替useState和useEffect组合
2. 利用Next.js 15的服务器动作进行认证操作
3. 简化Context API的使用，减少不必要的重渲染
4. 使用React 19的useOptimistic提升UI响应速度
5. 利用React Server Components减少客户端JavaScript体积

## 快速开始

### 安装依赖

```bash
npm install
```

### 运行开发环境

```bash
npm run dev
```

### 构建生产环境

```bash
npm run build
```

## 文件结构说明

### 前端关键文件

- `apps/web/contexts/auth.context.tsx`: 认证上下文管理
- `apps/web/components/auth/login-form.tsx`: 登录表单组件
- `apps/web/actions/auth/index.ts`: 认证相关的服务器动作

### 后端关键文件

- `apps/api/app/api/v1/endpoints/auth.py`: 认证相关API端点
- `apps/api/app/core/security.py`: 安全相关功能
- `apps/api/app/api/deps.py`: API依赖项（包括认证）

## 贡献

欢迎提交问题和拉取请求来改进项目。

## 许可

MIT
