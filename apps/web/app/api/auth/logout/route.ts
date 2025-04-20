import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { logout as apiLogout } from "@/api/sdk";

/**
 * 登出API端点
 * 处理用户登出请求，清除cookie和令牌
 */
export async function POST() {
  try {
    // 获取token
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;

    // 如果有token，则调用API进行登出
    if (token) {
      try {
        await apiLogout({
          headers: {
            authorization: `Bearer ${token}`,
          },
        });
      } catch (apiError) {
        console.error("API登出请求失败:", apiError);
        // 继续执行，确保即使API调用失败，我们仍然清除本地cookie
      }
    }

    // 无论API调用成功与否，都移除本地token
    cookieStore.delete("auth-token");

    // 返回成功响应
    return NextResponse.json({ 
      success: true,
      message: "登出成功" 
    });
  } catch (error) {
    console.error("登出处理失败:", error);
    // 返回错误响应
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : "登出失败" 
      },
      { status: 500 }
    );
  }
}

// 添加OPTIONS处理，以支持CORS
export async function OPTIONS() {
  return NextResponse.json(
    {},
    {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
      },
    }
  );
} 