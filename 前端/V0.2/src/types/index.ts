// 简化版类型定义
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
  status?: number;
}

export interface AuthData {
  token: string;
  user: {
    user_id: number;
    username: string;
    email: string;
    is_admin?: boolean;
    created_at?: string;
    updated_at?: string;
  };
}
