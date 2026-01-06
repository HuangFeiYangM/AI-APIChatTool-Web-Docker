// src/api/auth.ts
import request from '@/utils/request';
import { ApiResponse, AuthResponseData, UserInfoResponse } from '@/types/api';

export const authApi = {
  // 登录 - 精确匹配后端响应
  login: async (data: { username: string; password: string }): Promise<ApiResponse<AuthResponseData>> => {
    try {
      const response = await request.post('/auth/login', data) as ApiResponse<AuthResponseData>;
      console.log('登录API响应:', response);
      return response;
    } catch (error) {
      console.error('登录API错误:', error);
      throw error;
    }
  },
  
  // 注册 - 精确匹配后端响应
  register: async (data: { 
    username: string; 
    email: string; 
    password: string;
    confirm_password?: string;
  }): Promise<ApiResponse<AuthResponseData>> => {
    try {
      const response = await request.post('/auth/register', {
        ...data,
        confirm_password: data.confirm_password || data.password
      }) as ApiResponse<AuthResponseData>;
      
      console.log('注册API响应:', response);
      return response;
    } catch (error) {
      console.error('注册API错误:', error);
      throw error;
    }
  },
  
  // 获取当前用户信息 - 返回 UserInfoResponse
  getCurrentUser: async (): Promise<ApiResponse<UserInfoResponse>> => {
    const response = await request.get('/auth/me') as ApiResponse<UserInfoResponse>;
    console.log('获取当前用户响应:', response);
    return response;
  },
  
  // 登出
  logout: async (): Promise<ApiResponse> => {
    return request.post('/auth/logout');
  },
  
  // 修改密码
  changePassword: async (data: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }): Promise<ApiResponse> => {
    return request.post('/auth/change-password', data);
  },
  
  // 验证token
  validateToken: async (): Promise<ApiResponse> => {
    return request.get('/auth/validate-token');
  },
  
  // 刷新token
  refreshToken: async (): Promise<ApiResponse<{ token: string }>> => {
    return request.post('/auth/refresh-token') as Promise<ApiResponse<{ token: string }>>;
  },
  
  // 忘记密码
  forgotPassword: async (email: string): Promise<ApiResponse> => {
    return request.post('/auth/forgot-password', { email });
  },
  
  // 重置密码
  resetPassword: async (token: string, newPassword: string): Promise<ApiResponse> => {
    return request.post('/auth/reset-password', { token, new_password: newPassword });
  },
  
  // 获取登录尝试记录
  getLoginAttempts: async (username: string): Promise<ApiResponse> => {
    return request.get(`/auth/login-attempts/${username}`);
  },
};

export default authApi;
