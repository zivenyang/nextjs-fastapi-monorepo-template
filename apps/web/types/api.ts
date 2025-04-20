/**
 * API交互相关的类型定义
 */

// API响应基础接口
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  statusCode?: number;
}

// 登录API响应数据
export interface LoginResponseData {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
}

// 用户API响应数据
export interface UserResponseData {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  role: string;
}

// HTTP方法类型
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'; 