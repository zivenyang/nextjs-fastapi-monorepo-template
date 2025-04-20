# Next.js 15 Web应用

本项目是一个基于Next.js 15的现代化Web应用，采用了App Router、React Server Components和Server Actions等最新特性，并进行了代码优化以遵循最佳实践。

## 功能特性

- 💻 基于Next.js 15最新特性
- 🔒 完整的用户认证系统（注册、登录、登出）
- 🚀 SSR服务器端渲染和RSC服务器组件
- 🎨 使用Tailwind CSS和shadcn/ui构建的现代UI
- 📱 响应式设计，支持各种设备
- 🔧 表单验证和错误处理
- 🔄 客户端和服务器端状态同步

## 快速开始

首先，运行开发服务器:

```bash
bun run dev
```

在浏览器中打开 [http://localhost:3000](http://localhost:3000) 查看结果。

## 应用架构

该应用采用了Next.js 15的最新架构，主要包括：

### 目录结构

- `app/` - 应用路由和页面组件
- `components/` - 可重用的UI组件
- `actions/` - 服务器Actions，用于处理表单和数据操作
- `api/` - API集成和路由处理器
- `lib/` - 实用工具和类型定义

### 认证系统

该应用实现了一个完整的认证系统，具有以下特点：

#### 用户注册

- 使用Zod进行表单验证
- 密码确认匹配检查
- 服务器端错误处理和用户反馈
- 注册成功自动重定向到登录页面

#### 用户登录

- 基于JWT的认证机制
- 使用`useActionState` hook管理表单提交状态
- 安全的cookie存储（httpOnly, secure, sameSite）
- 错误处理和用户反馈
- 登录成功后重定向到首页

#### 会话管理

- 服务器端会话状态检查（使用`checkAuthStatus`）
- 客户端认证状态管理（通过AuthProvider和Context API）
- 定期同步客户端和服务器端认证状态
- 路由保护，阻止未认证用户访问受保护页面

#### 用户登出

- 安全清除会话数据
- 从cookie中移除认证令牌
- 调用后端API使当前令牌失效
- 重定向到登录页面

## 最佳实践

该应用采用了Next.js 15的最佳实践：

### 服务器组件 (RSC)

- 使用服务器组件减少客户端JavaScript体积
- 在服务器上安全地获取认证状态
- 通过props将数据传递给客户端组件

### 服务器操作 (Server Actions)

- 使用"use server"指令定义服务器操作
- 实现类型安全的表单处理
- 使用useActionState来管理操作状态
- 错误处理和状态管理

### 异步组件

- 使用async/await语法在服务器组件中获取数据
- 服务器端数据获取避免瀑布式请求

### 性能优化

- 使用React Hooks：useCallback和useMemo避免不必要的渲染
- 组件分割和懒加载策略
- 使用useEffect正确处理副作用
- 实现API路由CORS支持

## API集成

该应用通过OpenAPI客户端与后端API集成，包括：

- 用户注册
- 用户登录
- 用户登出
- 认证状态检查
- 其他API调用

## 认证流程

1. 用户首次访问应用时，服务器会检查cookies中是否存在有效的认证令牌
2. 如果用户未认证且尝试访问受保护的路由，会被重定向到登录页面
3. 登录成功后，服务器将JWT令牌存储在安全的httpOnly cookie中
4. 前端应用使用Context API维护认证状态，并定期与服务器同步
5. 退出登录时，客户端和服务器端的会话数据都会被清除

## 代码优化

本项目进行了多项代码优化，包括：

1. **修复路由跳转问题** - 使用useEffect处理登录成功后的路由跳转
2. **增强错误处理** - 添加结构化的错误处理和用户反馈
3. **表单验证** - 使用Zod进行类型安全的表单验证
4. **状态同步** - 实现客户端和服务器端认证状态的定期同步
5. **性能优化** - 使用React.memo, useCallback和useMemo减少不必要的渲染
6. **改进API路由** - 添加更强健的错误处理和CORS支持
7. **类型安全** - 增强TypeScript类型定义，提高代码质量

## 部署

该应用可以轻松部署到Vercel平台。查看[Next.js部署文档](https://nextjs.org/docs/deployment)获取更多详情。

## 学习更多

要了解更多关于Next.js的信息，请查看以下资源：

- [Next.js文档](https://nextjs.org/docs) - 了解Next.js的特性和API
- [学习Next.js](https://nextjs.org/learn) - 一个交互式的Next.js教程

# Next.js 前端应用

这是一个基于Next.js 15构建的现代化前端应用，采用了最新的React Server Components和Server Actions架构。

## 项目结构

```
/app                  # Next.js App Router路由和页面
  /api                # API路由处理程序
  /login              # 登录页面
  /register           # 注册页面
  /profile            # 用户个人资料页面
  layout.tsx          # 根布局组件
  page.tsx            # 首页组件

/actions              # 服务器操作 (Server Actions)
  /auth               # 认证相关的服务器操作
    index.ts          # 主要认证动作 (登录、注册、登出等)
    schemas.ts        # 验证模式导出
    types.ts          # 类型定义导出

/components           # 可复用UI组件
  /auth               # 认证相关组件
    index.ts          # 导出文件
    login-form.tsx    # 登录表单组件
    register-form.tsx # 注册表单组件
  /layout             # 布局相关组件
    index.ts          # 导出文件
    nav-bar.tsx       # 导航栏组件
  index.ts            # 主导出文件

/contexts             # React上下文
  index.ts            # 导出文件
  auth.context.tsx    # 认证上下文
  providers.tsx       # 上下文提供者组件
  theme.context.tsx   # 主题上下文

/lib                  # 工具函数和服务
  validation.ts       # 表单验证工具

/schemas              # 验证模式
  index.ts            # 导出文件
  auth.ts             # 认证相关验证模式

/types                # 类型定义
  index.ts            # 导出文件
  auth.ts             # 认证相关类型
  api.ts              # API相关类型

/hooks                # 自定义React钩子
```

## 架构最佳实践

### 1. Server vs Client 组件分离

- 服务器组件位于`app/`目录下
- 客户端组件使用`"use client"`指令标记，主要放在`components/`目录下
- 清晰的职责分离，服务器组件负责数据获取和页面框架，客户端组件负责交互和状态管理

### 2. 类型管理

- 集中在`types/`目录下定义所有类型
- 使用`index.ts`文件导出类型，简化导入
- 按功能模块分组类型定义

### 3. 验证模式

- 使用Zod进行表单验证
- 验证模式集中在`schemas/`目录下
- 实现了类型安全的表单处理

### 4. 服务器操作 (Server Actions)

- 遵循Next.js 15的规则：`"use server"`文件只导出异步函数
- 服务器操作集中在`actions/`目录下
- 使用工具函数简化错误处理和状态创建

### 5. 状态管理

- 使用React Context API管理全局状态
- 上下文提供者集中在`contexts/`目录下
- 清晰的状态提供层次结构

### 6. 目录和文件命名约定

- 使用kebab-case命名组件文件
- 使用camelCase命名工具和类型文件
- 使用功能模块组织代码而不是技术角色

## Next.js 15 最佳实践

1. **Server Actions**：使用强类型和Server Actions进行表单处理，确保每个标记为"use server"的文件只导出异步函数

2. **类型安全**：使用TypeScript和Zod实现端到端类型安全

3. **模块组织**：按功能而非技术角色组织代码，提高可维护性

4. **路径别名**：使用`@/`前缀的绝对导入路径，提高可读性

5. **按需组件渲染**：根据需要选择服务器组件或客户端组件，优化性能和用户体验

6. **统一的错误处理**：使用集中式错误处理和状态管理

7. **单一职责组件**：组件设计遵循单一职责原则，提高复用性和可测试性

## 开发和构建

```bash
# 开发环境运行
npm run dev

# 构建生产版本
npm run build

# 启动生产版本
npm run start
```
