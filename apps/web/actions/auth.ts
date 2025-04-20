"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { loginAccessToken, registerUser, logout as apiLogout } from "../api/sdk";
import { z } from "zod";

export interface AuthState {
  error: string | null;
  success: boolean;
}

// 登录表单验证schema
const loginSchema = z.object({
  email: z.string().email("请输入有效的邮箱地址"),
  password: z.string().min(6, "密码长度至少为6个字符"),
});

// 注册表单验证schema
const registerSchema = z.object({
  username: z.string().min(3, "用户名长度至少为3个字符"),
  email: z.string().email("请输入有效的邮箱地址"),
  password: z.string().min(6, "密码长度至少为6个字符"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "两次输入的密码不一致",
  path: ["confirmPassword"],
});

export async function login(
  _prevState: AuthState,
  formData: FormData
): Promise<AuthState> {
  try {
    // 获取表单数据
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    // 验证表单数据
    const validationResult = loginSchema.safeParse({ email, password });
    if (!validationResult.success) {
      const errorMessage = validationResult.error.issues[0]?.message || "表单验证失败";
      return {
        error: errorMessage,
        success: false,
      };
    }

    // 调用API登录
    const response = await loginAccessToken({
      body: {
        username: email,
        password: password,
      },
    });

    if (response.data) {
      // 成功登录，保存token到cookie
      const token = response.data.access_token;
      const cookieStore = await cookies();
      cookieStore.set("auth-token", token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7, // 一周
        path: "/",
      });

      return {
        error: null,
        success: true,
      };
    } else {
      return {
        error: "登录失败，服务器没有返回Token",
        success: false,
      };
    }
  } catch (error) {
    console.error("登录失败:", error);
    // 区分不同类型的错误
    if (error instanceof Error) {
      return {
        error: `登录失败: ${error.message}`,
        success: false,
      };
    }
    return {
      error: "登录时发生未知错误",
      success: false,
    };
  }
}

export async function register(
  _prevState: AuthState,
  formData: FormData
): Promise<AuthState> {
  try {
    // 获取表单数据
    const username = formData.get("username") as string;
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const confirmPassword = formData.get("confirmPassword") as string;

    // 验证表单数据
    const validationResult = registerSchema.safeParse({ 
      username, 
      email, 
      password, 
      confirmPassword 
    });
    
    if (!validationResult.success) {
      const errorMessage = validationResult.error.issues[0]?.message || "表单验证失败";
      return {
        error: errorMessage,
        success: false,
      };
    }

    // 调用API注册
    await registerUser({
      body: {
        email,
        username,
        password,
      },
    });

    return {
      error: null,
      success: true,
    };
  } catch (error) {
    console.error("注册失败:", error);
    // 区分不同类型的错误
    if (error instanceof Error) {
      // 尝试识别常见错误模式
      if (error.message.includes("email") && error.message.includes("already")) {
        return {
          error: "该邮箱已被注册",
          success: false,
        };
      }
      if (error.message.includes("username") && error.message.includes("already")) {
        return {
          error: "该用户名已被使用",
          success: false,
        };
      }
      return {
        error: `注册失败: ${error.message}`,
        success: false,
      };
    }
    return {
      error: "注册时发生未知错误",
      success: false,
    };
  }
}

export async function logout() {
  try {
    // 获取token
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;

    if (token) {
      // 调用API登出
      await apiLogout({
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.error("API登出失败:", error);
    // 即使API调用失败，我们仍然需要清除cookie
  } finally {
    // 无论API调用成功与否，都移除本地token
    const cookieStore = await cookies();
    cookieStore.delete("auth-token");
    
    // 重定向到登录页面
    redirect("/login");
  }
}

export async function checkAuthStatus(): Promise<boolean> {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;
    return !!token;
  } catch (error) {
    console.error("检查认证状态失败:", error);
    return false;
  }
} 