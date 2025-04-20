"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";

interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  logout: () => Promise<void>;
  setAuth: (value: boolean) => void; // 添加更新认证状态的方法
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
  
  // 检查是否在受保护的路由上
  useEffect(() => {
    const publicRoutes = ["/login", "/register"];
    const isPublicRoute = publicRoutes.includes(pathname);
    
    if (!isAuthenticated && !isPublicRoute) {
      router.push("/login");
    }
  }, [isAuthenticated, pathname, router]);

  // 登出方法
  const logout = async () => {
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
      }
    } catch (error) {
      console.error("登出失败:", error);
    } finally {
      setLoading(false);
    }
  };
  
    // 添加设置认证状态的方法
    const setAuth = (value: boolean) => {
        setIsAuthenticated(value);
      };
    

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading, logout, setAuth }}>
      {children}
    </AuthContext.Provider>
  );
} 