import { Button } from "@repo/ui/components/button"
import Link from "next/link"
import { NavBar } from "@/components/nav-bar"

export default function Page() {
  return (
    <div className="flex flex-col min-h-svh">
      <NavBar />
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center justify-center gap-4">
          <h1 className="text-2xl font-bold">欢迎来到 Next.js 15 应用</h1>
          <p className="text-center max-w-md text-muted-foreground">
            这是一个基于 Next.js 15 和 React Server Components 的现代化应用，
            采用了Server Actions来处理表单提交和服务器端操作。
          </p>
        </div>
      </div>
    </div>
  )
}