"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@repo/ui/components/button";
import { useAuth } from "@/contexts/auth.context";
import { useRouter, usePathname } from "next/navigation";
import { checkUserPermission } from "@/actions/user";

export function NavBar() {
  const { isAuthenticated, logout, isPending } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isAdmin, setIsAdmin] = useState(false);
  
  // 检查用户是否有管理员权限
  useEffect(() => {
    if (isAuthenticated) {
      const checkAdmin = async () => {
        try {
          const result = await checkUserPermission("admin");
          setIsAdmin(result);
        } catch (error) {
          console.error("检查权限失败:", error);
          setIsAdmin(false);
        }
      };
      
      checkAdmin();
    }
  }, [isAuthenticated]);

  // 直接跳转处理函数，避免可能的事件冒泡问题
  const handleLoginClick = () => router.push("/login");
  const handleRegisterClick = () => router.push("/register");
  const handleProfileClick = () => router.push("/profile");
  const handleUsersClick = () => router.push("/users");

  return (
    <header className="w-full border-b bg-background">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center space-x-6">
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
          
          {isAuthenticated && (
            <nav className="flex items-center space-x-4">
              <Button 
                variant={pathname === "/profile" ? "default" : "ghost"}
                onClick={handleProfileClick}
              >
                个人资料
              </Button>
              
              {isAdmin && (
                <Button 
                  variant={pathname.startsWith("/users") ? "default" : "ghost"}
                  onClick={handleUsersClick}
                >
                  用户管理
                </Button>
              )}
            </nav>
          )}
        </div>
        
        <div className="flex items-center space-x-4">
          {isAuthenticated ? (
            <Button
              variant="outline"
              onClick={logout}
              disabled={isPending}
            >
              {isPending ? "登出中..." : "登出"}
            </Button>
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
        </div>
      </div>
    </header>
  );
} 