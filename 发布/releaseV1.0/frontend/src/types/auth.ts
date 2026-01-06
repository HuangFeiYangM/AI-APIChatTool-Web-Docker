// src/types/auth.ts
// 主用户类型定义
export interface User {
  user_id: number;
  username: string;
  email: string;
  avatar?: string;
  is_admin?: boolean;
  is_active?: boolean;
  is_locked?: boolean;
  created_at?: string;
  updated_at?: string;
  last_login_at?: string;
  login_count?: number;
}

// 登录请求
export interface LoginRequest {
  username: string;
  password: string;
}

// 注册请求
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirm_password?: string;
}

// 登录响应
export interface LoginResponse {
  success: boolean;
  message: string;
  data: {
    token: string;
    user: User;
  };
}

// 修改密码请求
export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  errors?: Record<string, string[]>;
}

// 分页响应
export interface PaginatedResponse<T> {
  success: boolean;
  message?: string;
  data: T[];
  total: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
}
