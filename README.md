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

## 认证系统

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
