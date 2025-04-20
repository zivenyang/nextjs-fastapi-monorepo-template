import { z } from "zod";

/**
 * 用户更新验证模式
 */
export const userUpdateSchema = z.object({
  username: z.string().min(3, "用户名至少需要3个字符").optional().or(z.literal("")),
  full_name: z.string().optional().or(z.literal("")),
  email: z.string().email("请输入有效的电子邮件地址"),
  password: z
    .string()
    .min(8, "密码至少需要8个字符")
    .optional()
    .or(z.literal("")),
});

/**
 * 用户资料更新验证模式
 */
export const userProfileUpdateSchema = z.object({
  bio: z.string().optional().or(z.literal("")),
  phone_number: z.string().optional().or(z.literal("")),
  address: z.string().optional().or(z.literal("")),
  avatar_url: z.string().optional().or(z.literal("")),
}); 