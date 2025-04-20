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
- `lib/` - 实用工具和类型定义

### 认证系统

该应用实现了一个完整的认证系统，具有以下特点：

#### 用户注册

- 表单验证使用Zod进行类型安全的验证
- 密码强度检查（长度、大小写、特殊字符）
- 用户名和邮箱唯一性验证
- 注册成功自动重定向到登录页面

#### 用户登录

- 基于JWT的认证机制
- 安全的cookie存储（httpOnly, secure, sameSite）
- 错误处理和用户反馈
- 登录后重定向到最初请求的页面

#### 会话管理

- 服务器端会话状态检查
- 客户端认证状态管理
- 路由保护中间件

#### 用户登出

- 安全清除会话数据
- 缓存失效处理
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

### 路由中间件

- 保护需要认证的路由
- 根据用户认证状态动态重定向
- 优化路由匹配规则

## API集成

该应用通过OpenAPI客户端与后端API集成，包括：

- 用户注册
- 用户登录
- 用户登出
- 其他API调用

## 部署

该应用可以轻松部署到Vercel平台。查看[Next.js部署文档](https://nextjs.org/docs/deployment)获取更多详情。

## 学习更多

要了解更多关于Next.js的信息，请查看以下资源：

- [Next.js文档](https://nextjs.org/docs) - 了解Next.js的特性和API
- [学习Next.js](https://nextjs.org/learn) - 一个交互式的Next.js教程
