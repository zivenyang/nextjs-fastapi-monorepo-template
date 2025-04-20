import { z } from "zod";

/**
 * 认证相关的验证模式
 */

// 登录表单验证schema
export const loginSchema = z.object({
  email: z.string()
    .email("请输入有效的邮箱地址")
    .min(1, "邮箱不能为空"),
  password: z.string()
    .min(6, "密码长度至少为6个字符")
    .max(100, "密码长度不能超过100个字符"),
});

// 注册表单验证schema
export const registerSchema = z.object({
  username: z.string()
    .min(3, "用户名长度至少为3个字符")
    .max(50, "用户名长度不能超过50个字符")
    .regex(/^[a-zA-Z0-9_]+$/, "用户名只能包含字母、数字和下划线"),
  email: z.string()
    .email("请输入有效的邮箱地址")
    .min(1, "邮箱不能为空"),
  password: z.string()
    .min(6, "密码长度至少为6个字符")
    .max(100, "密码长度不能超过100个字符"),
  confirmPassword: z.string()
    .min(1, "请确认密码"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "两次输入的密码不一致",
  path: ["confirmPassword"],
}); 