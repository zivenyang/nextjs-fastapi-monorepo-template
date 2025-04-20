"use client";

import Link from "next/link";
import { Button } from "@repo/ui/components/button";
import { useAuth } from "./auth-provider";

export function NavBar() {
  const { isAuthenticated, logout, loading } = useAuth();

  return (
    <header className="w-full border-b bg-background">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center">
          <Link href="/" className="text-lg font-bold">
            Next.js 15 应用
          </Link>
        </div>
        <nav className="flex items-center space-x-4">
          {isAuthenticated ? (
            <>
              <Link href="/profile">
                <Button variant="ghost">个人资料</Button>
              </Link>
              <Button
                variant="outline"
                onClick={logout}
                disabled={loading}
              >
                {loading ? "登出中..." : "登出"}
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost">登录</Button>
              </Link>
              <Link href="/register">
                <Button variant="default">注册</Button>
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
} 