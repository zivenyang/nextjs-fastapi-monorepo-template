# Next.js 15 Web应用

本项目是一个基于Next.js 15的现代化Web应用，采用了App Router、React Server Components和Server Actions等最新特性。

## 功能特性

- 💻 基于Next.js 15最新特性
- 🔒 完整的用户认证系统（注册、登录、登出）
- 🚀 SSR服务器端渲染和RSC服务器组件
- 🎨 使用Tailwind CSS和shadcn/ui构建的现代UI
- 📱 响应式设计，支持各种设备

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

- 表单验证确保数据正确性
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

### 异步组件

- 使用async/await语法在服务器组件中获取数据
- 服务器端数据获取避免瀑布式请求

### API集成

该应用通过OpenAPI客户端与后端API集成，包括：

- 用户注册
- 用户登录
- 用户登出
- 其他API调用

## 认证流程

1. 用户首次访问应用时，服务器会检查cookies中是否存在有效的认证令牌
2. 如果用户未认证且尝试访问受保护的路由，会被重定向到登录页面
3. 登录成功后，服务器将JWT令牌存储在安全的httpOnly cookie中
4. 前端应用使用Context API维护认证状态
5. 退出登录时，客户端和服务器端的会话数据都会被清除

## 部署

该应用可以轻松部署到Vercel平台。查看[Next.js部署文档](https://nextjs.org/docs/deployment)获取更多详情。

## 学习更多

要了解更多关于Next.js的信息，请查看以下资源：

- [Next.js文档](https://nextjs.org/docs) - 了解Next.js的特性和API
- [学习Next.js](https://nextjs.org/learn) - 一个交互式的Next.js教程
