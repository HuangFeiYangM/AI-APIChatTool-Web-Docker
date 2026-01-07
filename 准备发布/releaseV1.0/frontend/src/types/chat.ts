// src/types/chat.ts - 修复版本
// 消息角色
export type MessageRole = 'user' | 'assistant' | 'system';

// 聊天消息
export interface ChatMessage {
  id: string;
  conversation_id: number;
  role: MessageRole;
  content: string;
  model_used?: string;
  tokens_used?: number;
  created_at: string;
  updated_at: string;
}

// 对话（API响应格式）
export interface ApiConversation {
  conversation_id: number;
  user_id: number;
  title: string;
  model_id: number;
  model_name?: string;
  message_count: number;
  is_archived: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  last_message?: string;
  last_message_at?: string;
}

// 聊天请求
export interface ChatRequest {
  message: string;
  model: string;
  conversation_id?: number;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

// 聊天响应
export interface ChatResponse {
  success: boolean;
  message: string;
  data: {
    response: string;
    conversation_id?: number;
    model_used: string;
    tokens_used: number;
    processing_time: number;
    finish_reason?: string;
  };
}

// 模型信息
export interface ModelInfo {
  model_id: number;
  model_name: string;
  provider: string;
  description?: string;
  is_enabled: boolean;
  supports_streaming: boolean;
  max_tokens: number;
  default_temperature?: number;
  created_at: string;
  updated_at: string;
}

// 对话列表响应
export interface ConversationListResponse {
  success: boolean;
  message: string;
  data: {
    conversations: ApiConversation[];
    total: number;
    skip: number;
    limit: number;
  };
}

// 单个对话响应
export interface SingleConversationResponse {
  success: boolean;
  message: string;
  data: ApiConversation;
}

// 上下文设置
export interface ContextSettings {
  enabled: boolean;
  level: number;  // 对话轮数：1, 3, 5, 10
}
