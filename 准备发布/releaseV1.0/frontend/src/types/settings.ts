// 模型配置
export interface ModelConfig {
  config_id: number;
  user_id: number;
  model_id: number;
  model_name?: string;
  is_enabled: boolean;
  api_key?: string;
  custom_endpoint?: string;
  max_tokens?: number;
  temperature?: number;
  priority: number;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
}

// 系统模型
export interface SystemModel {
  model_id: number;
  model_name: string;
  provider: string;
  endpoint_url: string;
  is_enabled: boolean;
  max_tokens: number;
  supports_streaming: boolean;
  description?: string;
  created_at: string;
  updated_at: string;
}

// API使用统计
export interface ApiUsageStats {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  total_tokens: number;
  avg_response_time: number;
  by_model: Array<{
    model_id: number;
    model_name: string;
    call_count: number;
    success_count: number;
    token_usage: number;
  }>;
  by_day: Array<{
    date: string;
    call_count: number;
    token_usage: number;
  }>;
}

// 用户管理
export interface AdminUser {
  user_id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_locked: boolean;
  locked_reason?: string;
  locked_until?: string;
  failed_login_attempts: number;
  last_login_at?: string;
  conversation_count: number;
  created_at: string;
  updated_at: string;
}

// 系统统计
export interface SystemStats {
  total_users: number;
  active_users: number;
  locked_users: number;
  total_conversations: number;
  total_messages: number;
  total_api_calls: number;
  total_tokens_used: number;
  system_uptime: number;
  avg_response_time: number;
  api_success_rate: number;
}

// 健康状态
export interface HealthStatus {
  status: 'healthy' | 'warning' | 'critical';
  database: boolean;
  disk_usage: number;
  memory_usage: number;
  cpu_usage: number;
  last_check: string;
}

// API调用日志
export interface ApiCallLog {
  log_id: number;
  user_id: number;
  username: string;
  model_id: number;
  model_name: string;
  endpoint: string;
  method: string;
  status_code: number;
  is_success: boolean;
  response_time: number;
  tokens_used: number;
  client_ip: string;
  user_agent: string;
  created_at: string;
}
