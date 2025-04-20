"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";

interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  logout: () => Promise<void>;
  setAuth: (value: boolean) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth必须在AuthProvider内部使用");
  }
  return context;
}

interface AuthProviderProps {
  initialAuth: boolean;
  children: React.ReactNode;
}

export function AuthProvider({ initialAuth, children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(initialAuth);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  
  // 定期检查认证状态，确保客户端和服务器端的认证状态一致
  useEffect(() => {
    // 首次加载时检查状态
    const checkInitialStatus = async () => {
      try {
        const res = await fetch("/api/auth/status");
        if (res.ok) {
          const data = await res.json();
          if (data.authenticated !== isAuthenticated) {
            setIsAuthenticated(data.authenticated);
          }
        }
      } catch (error) {
        console.error("检查认证状态失败:", error);
      }
    };
    
    checkInitialStatus();
    
    // 定期检查状态（每30秒）
    // 这可以帮助在多个标签页中保持状态同步
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/api/auth/status");
        if (res.ok) {
          const data = await res.json();
          if (data.authenticated !== isAuthenticated) {
            setIsAuthenticated(data.authenticated);
            
            // 如果变为未认证状态，且当前页面需要认证，则重定向
            if (!data.authenticated) {
              const publicRoutes = ["/login", "/register", "/"];
              const isPublicRoute = publicRoutes.some(route => 
                pathname === route || pathname.startsWith(`${route}/`)
              );
              
              if (!isPublicRoute) {
                router.push("/login");
              }
            }
          }
        }
      } catch (error) {
        console.error("检查认证状态失败:", error);
      }
    }, 30000); // 每30秒检查一次
    
    return () => clearInterval(interval);
  }, [isAuthenticated, pathname, router]);
  
  // 检查是否在受保护的路由上
  useEffect(() => {
    const publicRoutes = ["/login", "/register", "/"];
    const isPublicRoute = publicRoutes.some(route => 
      pathname === route || pathname.startsWith(`${route}/`)
    );
    
    if (!isAuthenticated && !isPublicRoute) {
      router.push("/login");
    }
  }, [isAuthenticated, pathname, router]);

  // 设置认证状态的方法（使用useCallback优化性能）
  const setAuth = useCallback((value: boolean) => {
    setIsAuthenticated(value);
  }, []);

  // 优化登出方法
  const logout = useCallback(async () => {
    if (loading) return; // 防止重复点击
    
    setLoading(true);
    try {
      const response = await fetch("/api/auth/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        setIsAuthenticated(false);
        router.push("/login");
      } else {
        // 错误处理
        const data = await response.json();
        console.error("登出失败:", data.error);
      }
    } catch (error) {
      console.error("登出请求失败:", error);
    } finally {
      setLoading(false);
    }
  }, [loading, router]);

  // 提供的上下文值使用useMemo优化
  const contextValue = React.useMemo(() => ({
    isAuthenticated,
    loading,
    logout,
    setAuth
  }), [isAuthenticated, loading, logout, setAuth]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
} 