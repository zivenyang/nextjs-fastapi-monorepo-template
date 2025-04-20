"use server";

import { cookies } from "next/headers";
import { readUser, readUserMe, updateUserMe } from "@/openapi/sdk";
import type { UserUpdateActionState } from "@/types/user";
import { userUpdateSchema } from "@/schemas/user";
import { validateFormData } from "@/lib/validation";

// 创建用户更新操作的错误状态
function createUserErrorState(message: string): UserUpdateActionState {
  return {
    status: "error",
    message
  };
}

// 创建用户更新操作的成功状态
function createUserSuccessState(): UserUpdateActionState {
  return {
    status: "success",
  };
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser() {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;

    if (!token) {
      return null;
    }

    const response = await readUserMe({
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  } catch (error) {
    console.error("获取当前用户信息失败:", error);
    return null;
  }
}

/**
 * 根据ID获取用户信息
 */
export async function getUserById(userId: string) {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;

    if (!token) {
      return null;
    }

    const response = await readUser({
      headers: {
        Authorization: `Bearer ${token}`,
      },
      path: {
        user_id: userId,
      },
    });

    return response.data;
  } catch (error) {
    console.error(`获取用户ID(${userId})信息失败:`, error);
    return null;
  }
}

/**
 * 更新当前用户信息
 */
export async function updateCurrentUser(
  _prevState: UserUpdateActionState,
  formData: FormData
): Promise<UserUpdateActionState> {
  try {
    // 获取表单数据
    const username = formData.get("username") as string;
    const fullName = formData.get("full_name") as string;
    const email = formData.get("email") as string;
    const password = formData.get("password") as string || null;
    const bio = formData.get("bio") as string || null;
    const phoneNumber = formData.get("phone_number") as string || null;
    const address = formData.get("address") as string || null;
    const avatarUrl = formData.get("avatar_url") as string || null;

    // 验证表单数据
    const validation = validateFormData(userUpdateSchema, { 
      username, 
      full_name: fullName, 
      email,
      password
    });
    
    if (!validation.success) {
      return createUserErrorState(validation.error!);
    }

    // 获取token
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;

    if (!token) {
      return createUserErrorState("未授权，请重新登录");
    }

    // 调用API更新用户信息
    const response = await updateUserMe({
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: {
        username,
        full_name: fullName,
        email,
        password: password ? password : undefined,
        profile: {
          bio,
          phone_number: phoneNumber,
          address,
          avatar_url: avatarUrl
        }
      },
    });

    if (response.data) {
      return createUserSuccessState();
    } else {
      return createUserErrorState("更新失败，服务器没有返回数据");
    }
  } catch (error) {
    console.error("更新用户信息失败:", error);
    if (error instanceof Error) {
      return createUserErrorState(`更新失败: ${error.message}`);
    }
    return createUserErrorState("更新时发生未知错误");
  }
}

/**
 * 检查用户是否有特定权限
 * 这里简单实现，实际项目中可能需要更复杂的权限检查逻辑
 */
export async function checkUserPermission(
  requiredRole: "admin" | "user" | "guest" = "user"
): Promise<boolean> {
  try {
    const user = await getCurrentUser();
    if (!user) return false;
    
    // 如果是超级用户，默认有所有权限
    if (user.is_superuser) return true;
    
    // 根据角色权限判断
    switch (requiredRole) {
      case "admin":
        return user.role === "admin";
      case "user":
        return user.role === "admin" || user.role === "user";
      case "guest":
        return true; // 任何角色都有guest权限
      default:
        return false;
    }
  } catch (error) {
    console.error("检查用户权限失败:", error);
    return false;
  }
} 