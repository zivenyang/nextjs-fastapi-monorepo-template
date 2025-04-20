"use client";

import Link from "next/link";
import { Button } from "@repo/ui/components/button";
import { useAuth } from "./auth-provider";
import { useRouter } from "next/navigation";

export function NavBar() {
  const { isAuthenticated, logout, loading } = useAuth();
  const router = useRouter();

  // 直接跳转处理函数，避免可能的事件冒泡问题
  const handleLoginClick = () => router.push("/login");
  const handleRegisterClick = () => router.push("/register");
  const handleProfileClick = () => router.push("/profile");

  return (
    <header className="w-full border-b bg-background">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center">
          <Link 
            href="/" 
            className="text-lg font-bold"
            // 确保链接能正常工作
            onClick={(e) => {
              e.preventDefault();
              router.push("/");
            }}
          >
            Next.js 15 应用
          </Link>
        </div>
        <nav className="flex items-center space-x-4">
          {isAuthenticated ? (
            <>
              <Button 
                variant="ghost" 
                onClick={handleProfileClick}
              >
                个人资料
              </Button>
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
              <Button 
                variant="ghost" 
                onClick={handleLoginClick}
              >
                登录
              </Button>
              <Button 
                variant="default"
                onClick={handleRegisterClick}
              >
                注册
              </Button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
} 