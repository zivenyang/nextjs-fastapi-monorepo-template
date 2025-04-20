"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { loginAccessToken, registerUser, logout as apiLogout } from "../api/sdk";

export interface AuthState {
  error: string | null;
  success: boolean;
}

export async function login(
  _prevState: AuthState,
  formData: FormData
): Promise<AuthState> {
  try {
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    if (!email || !password) {
      return {
        error: "请输入邮箱和密码",
        success: false,
      };
    }

    const response = await loginAccessToken({
      body: {
        username: email,
        password: password,
      },
    });

    if (response.data) {
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
        error: "登录失败",
        success: false,
      };
    }
  } catch (error) {
    console.error("登录失败:", error);
    return {
      error: "邮箱或密码错误",
      success: false,
    };
  }
}

export async function register(
  _prevState: AuthState,
  formData: FormData
): Promise<AuthState> {
  try {
    const username = formData.get("username") as string;
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const confirmPassword = formData.get("confirmPassword") as string;

    if (!username || !email || !password) {
      return {
        error: "请填写所有必填字段",
        success: false,
      };
    }

    if (password !== confirmPassword) {
      return {
        error: "两次输入的密码不一致",
        success: false,
      };
    }

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
    return {
      error: "注册失败，请稍后再试",
      success: false,
    };
  }
}

export async function logout() {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;
    if (token) {
      await apiLogout({
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.error("API登出失败:", error);
  }
  
  const cookieStore = await cookies();
  cookieStore.delete("auth-token");
  redirect("/login");
}

export async function checkAuthStatus(): Promise<boolean> {
  const cookieStore = await cookies();
  const token = cookieStore.get("auth-token")?.value;
  return !!token;
} 