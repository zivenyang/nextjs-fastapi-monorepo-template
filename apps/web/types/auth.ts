/**
 * 认证相关的类型定义
 */

// 服务端Action响应状态
export interface AuthActionState {
  error: string | null;
  success: boolean;
}

// 用户信息
export interface User {
  id: string;
  username: string;
  email: string;
  createdAt: string;
  role: 'user' | 'admin';
}

// 登录表单字段
export interface LoginFormFields {
  email: string;
  password: string;
}

// 注册表单字段
export interface RegisterFormFields {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
} 