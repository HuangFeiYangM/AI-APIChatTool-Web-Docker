// src/types/api.ts
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
  status?: number;
}

// 认证响应数据（根据后端实际返回）
export interface AuthResponseData {
  access_token: string;
  token_type: string;
  user_id: number;
  username: string;
  email?: string;
}

// 聊天响应数据
export interface ChatResponseData {
  response: string;
  conversation_id: number;
  model_used: string;
  tokens_used?: number;
  processing_time_ms?: number;
}

// 对话响应
export interface ConversationResponse {
  conversation_id: number;
  user_id: number;
  title: string;
  model_id: number;
  total_tokens: number;
  message_count: number;
  is_archived: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

// 消息响应
export interface MessageResponse {
  message_id: number;
  conversation_id: number;
  role: string;
  content: string;
  tokens_used: number;
  model_id?: number;
  created_at: string;
}

// 模型信息
export interface ModelInfo {
  model_id: number;
  model_name: string;
  model_provider: string;
  model_type: string;
  api_endpoint: string;
  is_available: boolean;
  is_default: boolean;
  max_tokens: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

// 后端实际的用户格式
export interface BackendUser {
  user_id: number;
  username: string;
  email?: string;
  is_active: boolean;
  is_locked: boolean;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

// 获取当前用户信息的响应
export interface UserInfoResponse {
  user_id: number;
  username: string;
  email?: string;
  is_active: boolean;
  is_locked: boolean;
  last_login_at?: string;
  created_at: string;
}

// 前端使用的用户格式（转换后的）
export interface FrontendUser {
  id: number;
  user_id: number;
  username: string;
  email?: string;
  is_active: boolean;
  is_locked: boolean;
  role: string;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  avatar_url?: string;
  // 添加管理员属性
  is_admin?: boolean;
}
