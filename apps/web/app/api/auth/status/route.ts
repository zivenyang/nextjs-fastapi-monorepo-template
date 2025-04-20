import { cookies } from "next/headers";
import { NextResponse } from "next/server";

/**
 * 认证状态检查API端点
 * 检查用户是否已认证
 */
export async function GET() {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;
    
    return NextResponse.json({ 
      authenticated: !!token,
    });
  } catch (error) {
    console.error("认证状态检查失败:", error);
    return NextResponse.json(
      { 
        authenticated: false, 
        error: error instanceof Error ? error.message : "认证状态检查失败" 
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
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
      },
    }
  );
} 