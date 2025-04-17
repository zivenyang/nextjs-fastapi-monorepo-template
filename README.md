# Turborepo Tailwind CSS 入门模板

这个 Turborepo 入门模板由 Turborepo 核心团队维护。它提供了一个基础配置，用于构建使用 Next.js、Tailwind CSS 和共享 UI 组件的 Web 应用。

## 如何使用这个模板

要基于此模板创建一个新项目，请运行以下命令：

```sh
git clone https://github.com/zivenyang/nextjs-fastapi-template.git
```

## 安装依赖 (Install Dependencies)

在你克隆（clone）了项目代码之后，进入项目根目录，并运行以下命令来安装所有必需的依赖项：

```sh
bun install
```

这个命令会安装前端（Next.js, React, UI库等）和后端（如果未来添加，如FastAPI）以及开发时需要的所有工具。

## 项目包含什么？

这个 Turborepo 项目包含了以下的包（packages）和应用（applications）：

### 应用和包

- `apps/docs`: 一个 [Next.js](https://nextjs.org/) 应用（例如，用于文档）。
- `apps/web`: 另一个 [Next.js](https://nextjs.org/) 应用（例如，主要的 Web 应用）。
- `packages/ui`: 一个共享的 React 组件库，使用了 [Tailwind CSS](https://tailwindcss.com/) & [shadcn/ui](https://ui.shadcn.com/)。这里的组件可以被多个应用共用。
- `packages/eslint-config`: 共享的 [ESLint](https://eslint.org/) 配置。
- `packages/typescript-config`: 在整个 monorepo 中使用的共享 `tsconfig.json` 配置。

所有的包和应用都是用 [TypeScript](https://www.typescriptlang.org/) 编写的。

### 构建 `packages/ui`

共享 UI 包 (`packages/ui`) 的组件被 Next.js 应用 (`apps/web`, `apps/docs`) 直接使用。这是通过应用各自的 `next.config.js` 文件中的 `transpilePackages` 配置项实现的。这种设置简化了共享 Tailwind 配置，并确保样式被正确应用。

### 工具集

本项目预先配置了一些基础开发工具：

- [shadcn/ui](https://ui.shadcn.com/): 基于tailwindcss的现代化UI组件库。
- [Tailwind CSS](https://tailwindcss.com/)：用于实现原子化 CSS 样式。
- [TypeScript](https://www.typescriptlang.org/)：用于静态类型检查。
- [ESLint](https://eslint.org/)：用于代码检查和强制代码风格。
- [Prettier](https://prettier.io)：用于自动格式化代码。

## 项目路径别名说明

为了方便模块导入和管理，本项目使用了一些路径别名：

- `@repo/ui/...`: 指向 `packages/ui` 目录下的共享 UI 组件和工具函数。（例如：`@repo/ui/button`）
- `@repo/typescript-config/...`: 指向 `packages/typescript-config` 目录下的 TypeScript 配置文件。
- `@repo/eslint-config/...`: 指向 `packages/eslint-config` 目录下的 ESLint 配置文件。
- `@/`: 在 `apps/web` 内部使用时，通常指向各自应用内部的根目录或 `src` 目录（具体配置请查看对应应用的 `tsconfig.json` 文件）。

**重要提示:** 当你在 `apps/web` 中需要导入 `packages/ui` 中的模块时，请务必使用 `@repo/ui/...` 这个别名，而不是 `@/...`。例如，导入按钮组件应写为 `import { Button } from '@repo/ui/button';`。

## 如何运行

你可以在项目根目录下使用 `bun` 命令来运行和管理这个项目。

例如，要启动前端项目 `web`：

```sh
bun run dev:web
```

要启动后端项目 `api`:

```sh
bun run dev:api
```

要同时启动前后端项目：

```sh
bun run dev
```

更多命令请参考 Turborepo 的官方文档。
