"use client";

import React, { createContext, useContext, useOptimistic, useTransition, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import { checkAuthStatus } from "@/actions/auth";
import { useSyncExternalStore } from "react";

// 认证上下文类型定义
interface AuthContextType {
  isAuthenticated: boolean;
  isPending: boolean;
  logout: () => Promise<void>;
  setAuth: (value: boolean) => void;
}

// 创建上下文
const AuthContext = createContext<AuthContextType | null>(null);

// 导出自定义钩子供组件使用
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

// 认证状态存储
class AuthStore {
  private listeners: Set<() => void> = new Set();
  private state: boolean;

  constructor(initialState: boolean) {
    this.state = initialState;
  }

  // 订阅方法
  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // 获取状态
  getState() {
    return this.state;
  }

  // 设置状态
  setState(newState: boolean) {
    if (this.state !== newState) {
      this.state = newState;
      this.listeners.forEach(listener => listener());
    }
  }
}

// 认证上下文提供者组件
export function AuthProvider({ initialAuth, children }: AuthProviderProps) {
  // 使用useRef保存AuthStore实例，避免每次渲染创建新实例
  const authStoreRef = useRef<AuthStore>(new AuthStore(initialAuth));
  
  // 使用useSyncExternalStore与外部状态同步
  const isAuthenticated = useSyncExternalStore(
    listener => authStoreRef.current.subscribe(listener),
    () => authStoreRef.current.getState(),
    () => initialAuth // 添加getServerSnapshot参数，返回初始认证状态
  );

  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();
  
  // 使用useOptimistic预先显示乐观的UI状态
  const [optimisticAuth, setOptimisticAuth] = useOptimistic(
    isAuthenticated,
    (state, newValue: boolean) => newValue
  );
  
  // 定期检查认证状态
  React.useEffect(() => {
    // 首次加载时检查状态
    startTransition(async () => {
      try {
        const authenticated = await checkAuthStatus();
        if (authenticated !== isAuthenticated) {
          setAuth(authenticated);
        }
      } catch (error) {
        console.error("检查认证状态失败:", error);
      }
    });
    
    // 定期检查状态（每60秒）
    const interval = setInterval(async () => {
      startTransition(async () => {
        try {
          const authenticated = await checkAuthStatus();
          if (authenticated !== isAuthenticated) {
            setAuth(authenticated);
            
            // 如果变为未认证状态，且当前页面需要认证，则重定向
            if (!authenticated) {
              const publicRoutes = ["/login", "/register", "/"];
              const isPublicRoute = publicRoutes.some(route => 
                pathname === route || pathname.startsWith(`${route}/`)
              );
              
              if (!isPublicRoute) {
                router.push("/login");
              }
            }
          }
        } catch (error) {
          console.error("检查认证状态失败:", error);
        }
      });
    }, 60000); // 每60秒检查一次
    
    return () => clearInterval(interval);
  }, [isAuthenticated, pathname, router]);
  
  // 检查是否在受保护的路由上
  React.useEffect(() => {
    const publicRoutes = ["/login", "/register", "/"];
    const isPublicRoute = publicRoutes.some(route => 
      pathname === route || pathname.startsWith(`${route}/`)
    );
    
    if (!isAuthenticated && !isPublicRoute) {
      router.push("/login");
    }
  }, [isAuthenticated, pathname, router]);

  // 设置认证状态的方法
  const setAuth = React.useCallback((value: boolean) => {
    // 更新状态存储
    authStoreRef.current.setState(value);
  }, []);

  // 优化登出方法
  const logout = React.useCallback(async () => {
    if (isPending) return; // 防止重复点击
    
    startTransition(async () => {
      // 乐观更新先将状态设为false
      setOptimisticAuth(false);
      
      try {
        const response = await fetch("/api/auth/logout", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });
        
        if (response.ok) {
          setAuth(false);
          router.push("/login");
        } else {
          // 错误处理，还原乐观更新
          setAuth(true);
          const data = await response.json();
          console.error("登出失败:", data.error);
        }
      } catch (error) {
        // 错误处理，还原乐观更新
        setAuth(true);
        console.error("登出请求失败:", error);
      }
    });
  }, [isPending, router, optimisticAuth, setOptimisticAuth]);

  // 提供的上下文值
  const contextValue = React.useMemo(() => ({
    isAuthenticated: optimisticAuth,  // 使用乐观更新的状态
    isPending,
    logout,
    setAuth
  }), [optimisticAuth, isPending, logout, setAuth]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
} 