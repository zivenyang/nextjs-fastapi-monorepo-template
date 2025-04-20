import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { logout as apiLogout } from "@/api/sdk";

export async function POST() {
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

    // 无论API调用成功与否，都移除本地token
    cookieStore.delete("auth-token");

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("登出失败:", error);
    return NextResponse.json(
      { success: false, error: "登出失败" },
      { status: 500 }
    );
  }
} 