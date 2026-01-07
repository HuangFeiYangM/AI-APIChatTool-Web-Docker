// src/api/chat.ts - 完整修复版
import request from '@/utils/request';
import type { ApiResponse } from '@/types/api';

export const chatApi = {
  // 创建对话
  createConversation: async (data: { title?: string; model_id: number }): Promise<ApiResponse<any>> => {
    return request.post('/conversations', data);
  },
  
  // 获取对话列表
  getConversations: async (params?: {
    skip?: number;
    limit?: number;
    include_archived?: boolean;
    include_deleted?: boolean;
  }): Promise<ApiResponse<any>> => {
    return request.get('/conversations', { params });
  },
  
  // 获取对话详情
  getConversationDetail: async (conversationId: number): Promise<ApiResponse<any>> => {
    return request.get(`/conversations/${conversationId}`);
  },
  
  // 修改 sendMessage 函数，适配后端实际返回的数据结构
  sendMessage: async (data: {
    message: string;
    model: string;
    conversation_id?: number;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  }): Promise<ApiResponse<any>> => {
    try {
      const response = await request.post('/models/chat', data);
      
      console.log('sendMessage 原始响应:', response);
      
      // 后端直接返回聊天数据，而不是包装在 ApiResponse 结构中
      // 我们需要手动包装它
      if (response && typeof response === 'object') {
        // 检查是否已经是 ApiResponse 格式（有 success 字段）
        if ('success' in response) {
          return response as ApiResponse;
        }
        
        // 否则，包装成 ApiResponse 格式
        return {
          success: true,
          message: '发送成功',
          data: response
        };
      }
      
      // 其他情况
      return {
        success: false,
        error: '响应格式不正确'
      };
      
    } catch (error: any) {
      console.error('sendMessage 请求失败:', error);
      throw error;
    }
  },
  
  // 获取对话消息
  getConversationMessages: async (conversationId: number, params?: {
    skip?: number;
    limit?: number;
    include_deleted?: boolean;
  }): Promise<ApiResponse<any>> => {
    return request.get(`/conversations/${conversationId}/messages`, { params });
  },
  
  // 创建消息
  createMessage: async (conversationId: number, data: {
    content: string;
    role?: string;
    model_id?: number;
    tokens_used?: number;
  }): Promise<ApiResponse<any>> => {
    return request.post(`/conversations/${conversationId}/messages`, data);
  },
  
  // 检查模型配置
  checkModelConfig: async (modelId: number): Promise<ApiResponse<any>> => {
    return request.get(`/models/config/${modelId}`);
  },
  
  // 获取可用模型
  getAvailableModels: async (): Promise<ApiResponse<any>> => {
    return request.get('/models/available');
  },
  
  // 删除对话
  deleteConversation: async (conversationId: number): Promise<ApiResponse> => {
    return request.delete(`/conversations/${conversationId}`);
  },
  
  // 新增：更新对话（用于重命名）
  updateConversation: async (conversationId: number, data: { title?: string }): Promise<ApiResponse<any>> => {
    return request.put(`/conversations/${conversationId}`, data);
  },
  
  // 新增：获取对话统计信息
  getConversationStats: async (conversationId: number): Promise<ApiResponse<any>> => {
    return request.get(`/conversations/${conversationId}`);
  },
  
  // 新增：更新消息
  updateMessage: async (
    conversationId: number, 
    messageId: number, 
    data: { content: string }
  ): Promise<ApiResponse<any>> => {
    try {
      const response = await request.put(`/conversations/${conversationId}/messages/${messageId}`, data);
      
      // 包装响应
      if (response && typeof response === 'object') {
        if ('success' in response) {
          return response as ApiResponse;
        }
        
        return {
          success: true,
          message: '消息更新成功',
          data: response
        };
      }
      
      return {
        success: false,
        error: '响应格式不正确'
      };
    } catch (error: any) {
      console.error('更新消息失败:', error);
      throw error;
    }
  },
  
  // 新增：删除消息
  deleteMessage: async (conversationId: number, messageId: number): Promise<ApiResponse> => {
    try {
      const response = await request.delete(`/conversations/${conversationId}/messages/${messageId}`);
      
      // 后端直接返回响应，需要包装成 ApiResponse 格式
      if (response && typeof response === 'object') {
        if ('success' in response) {
          return response as ApiResponse;
        }
        
        // 包装成 ApiResponse 格式
        return {
          success: true,
          message: '消息删除成功',
          data: response
        };
      }
      
      return {
        success: false,
        error: '响应格式不正确'
      };
    } catch (error: any) {
      console.error('删除消息失败:', error);
      throw error;
    }
  },
};

export default chatApi;
