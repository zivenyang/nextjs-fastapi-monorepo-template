# Next.js + FastAPI 全栈应用模板

这是一个基于 Turborepo 构建的现代全栈应用模板，提供了完整的前后端开发环境和基础功能。

## 项目技术栈

### 前端
- **Next.js 14**: 使用 App Router 构建的 React 框架
- **TailwindCSS**: 用于样式设计
- **Shadcn/UI**: 基于 Tailwind 的高质量UI组件库
- **TypeScript**: 提供类型安全
- **Server Actions**: 用于处理表单提交和认证

### 后端
- **FastAPI**: 高性能Python API框架
- **SQLModel**: 结合了SQLAlchemy和Pydantic的ORM
- **PostgreSQL**: 关系型数据库
- **Alembic**: 数据库迁移工具
- **JWT**: 用于认证

## 项目结构

```
/
├── apps
│   ├── api/                  # FastAPI 后端应用
│   │   ├── app/              # API应用代码
│   │   │   ├── api/          # API路由
│   │   │   ├── core/         # 核心配置、中间件等
│   │   │   ├── models/       # 数据库模型
│   │   │   ├── schemas/      # Pydantic模式
│   │   │   └── services/     # 业务逻辑服务
│   │   └── ...
│   └── web/                  # Next.js 前端应用
│       ├── app/              # Next.js App Router
│       ├── components/       # UI组件
│       ├── lib/              # 工具函数和类型
│       └── ...
├── packages
│   ├── ui/                   # 共享UI组件库
│   ├── openapi-client/       # 自动生成的API客户端
│   └── ...
└── ...
```

## 主要功能

### 1. 用户认证系统
- 完整的用户注册和登录流程
- 基于JWT的认证
- 令牌管理（包括登出黑名单）
- 用户角色和权限管理

### 2. 数据库集成
- 使用SQLModel的模型定义
- 异步数据库操作
- 数据库迁移支持

### 3. API开发
- 结构化的API路由组织
- 请求验证
- 错误处理和日志记录
- CORS支持
- OpenAPI文档生成

### 4. 前端特性
- 现代化React组件设计
- 服务端组件和Server Actions
- 响应式布局
- 表单验证
- 主题支持

## 快速开始

### 安装依赖
```bash
# 安装所有工作区依赖
npm install
```

### 环境设置
1. 复制`.env.example`到`.env`（在api和web目录中）
2. 按需修改配置

### 数据库设置
```bash
# 创建数据库
npm run db:create

# 运行迁移
npm run db:migrate
```

### 启动开发服务器
```bash
# 启动所有应用（前端+后端）
npm run dev
```

## API端点

### 认证API
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出

### 用户API
- `GET /api/v1/users/me` - 获取当前用户信息
- `GET /api/v1/users/{user_id}` - 获取特定用户
- `GET /api/v1/users/` - 获取用户列表（管理员）

## 项目规范

- 使用TypeScript类型安全
- 遵循RESTful API设计原则
- 使用Pydantic进行数据验证
- 完整的错误处理和日志记录
- 统一的代码风格和格式

## 扩展方向

- 添加更多身份验证方法（OAuth、社交登录等）
- 实现更多业务模块（如内容管理、支付集成等）
- 添加测试覆盖率
- 部署到云服务（提供Docker支持）

## 贡献

欢迎提交Pull Request和报告问题。

## 许可

MIT
