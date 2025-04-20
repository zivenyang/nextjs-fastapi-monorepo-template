"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";
import { loginAccessToken, registerUser, logout as apiLogout } from "@/openapi/sdk";
import { loginSchema, registerSchema } from "@/schemas/auth";
import type { AuthActionState } from "@/types/auth";
import { validateFormData, createErrorState, createSuccessState } from "@/lib/validation";

/**
 * 登录操作
 * 验证表单数据并调用登录API
 */
export async function login(
  _prevState: AuthActionState,
  formData: FormData
): Promise<AuthActionState> {
  try {
    // 获取表单数据
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    // 验证表单数据
    const validation = validateFormData(loginSchema, { email, password });
    if (!validation.success) {
      return createErrorState(validation.error!);
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

      return createSuccessState();
    } else {
      return createErrorState("登录失败，服务器没有返回Token");
    }
  } catch (error) {
    console.error("登录失败:", error);
    // 区分不同类型的错误
    if (error instanceof Error) {
      return createErrorState(`登录失败: ${error.message}`);
    }
    return createErrorState("登录时发生未知错误");
  }
}

/**
 * 注册操作
 * 验证表单数据并调用注册API
 */
export async function register(
  _prevState: AuthActionState,
  formData: FormData
): Promise<AuthActionState> {
  try {
    // 获取表单数据
    const username = formData.get("username") as string;
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const confirmPassword = formData.get("confirmPassword") as string;

    // 验证表单数据
    const validation = validateFormData(
      registerSchema, 
      { username, email, password, confirmPassword }
    );
    
    if (!validation.success) {
      return createErrorState(validation.error!);
    }

    // 调用API注册
    await registerUser({
      body: {
        email,
        username,
        password,
      },
    });

    return createSuccessState();
  } catch (error) {
    console.error("注册失败:", error);
    // 区分不同类型的错误
    if (error instanceof Error) {
      // 尝试识别常见错误模式
      if (error.message.includes("email") && error.message.includes("already")) {
        return createErrorState("该邮箱已被注册");
      }
      if (error.message.includes("username") && error.message.includes("already")) {
        return createErrorState("该用户名已被使用");
      }
      return createErrorState(`注册失败: ${error.message}`);
    }
    return createErrorState("注册时发生未知错误");
  }
}

/**
 * 登出操作
 * 清除token并重定向到登录页面
 */
export async function logout() {
  try {
    // 获取token
    const token = (await cookies()).get("auth-token")?.value;

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
    (await
          // 无论API调用成功与否，都移除本地token
          cookies()).delete("auth-token");
    
    // 重定向到登录页面
    redirect("/login");
  }
}

/**
 * 检查认证状态（使用cache优化性能）
 * 用于服务器端组件判断用户是否已登录
 */
export const checkAuthStatus = cache(async (): Promise<boolean> => {
  try {
    const token = (await cookies()).get("auth-token")?.value;
    return !!token;
  } catch (error) {
    console.error("检查认证状态失败:", error);
    return false;
  }
});

/**
 * 获取认证Token
 * 用于API请求
 */
export const getAuthToken = cache(async (): Promise<string | null> => {
  try {
    return (await cookies()).get("auth-token")?.value || null;
  } catch (error) {
    console.error("获取认证Token失败:", error);
    return null;
  }
}); 