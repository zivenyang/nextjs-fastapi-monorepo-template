import type { ZodError, ZodSchema } from "zod";
import type { AuthActionState } from "@/types";

/**
 * 处理Zod验证错误，返回格式化的错误消息
 */
export function formatZodError(error: ZodError): string {
  return error.errors[0]?.message || "表单验证失败";
}

/**
 * 验证表单数据
 * @param schema Zod验证模式
 * @param data 待验证的数据
 * @returns 验证结果和格式化的错误消息
 */
export function validateFormData<T>(
  schema: ZodSchema<T>,
  data: unknown
): { success: boolean; data?: T; error?: string } {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return { 
    success: false, 
    error: formatZodError(result.error)
  };
}

/**
 * 创建失败的Action状态
 */
export function createErrorState(message: string): AuthActionState {
  return {
    error: message,
    success: false
  };
}

/**
 * 创建成功的Action状态
 */
export function createSuccessState(): AuthActionState {
  return {
    error: null,
    success: true
  };
} 