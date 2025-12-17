import { useCallback } from 'react';
import { message } from 'antd';
import { useChatStore } from '@/store/chatStore';
import chatApi from '@/api/chat';
import type { ApiResponse } from '@/types/api';

export const useChat = () => {
  const {
    conversations,
    currentConversation,
    selectedModel,
    addConversation,
    updateConversation: updateStoreConversation,
    deleteConversation: deleteStoreConversation,
  } = useChatStore();

  // 获取对话列表
  const fetchConversations = useCallback(async () => {
    try {
      const response: ApiResponse = await chatApi.getConversations({
        include_archived: false,
        include_deleted: false,
      });
      
      if (response.success && response.data?.conversations) {
        // 使用新的初始化方法
        useChatStore.getState().initializeConversationsFromApi(response.data.conversations);
        
        return { success: true, data: response.data };
      } else {
        message.error(response.message || '获取对话列表失败');
        return { success: false, error: response.message };
      }
    } catch (error: any) {
      console.error('获取对话列表错误:', error);
      message.error(error.error || '获取对话列表失败');
      return { success: false, error: error.error };
    }
  }, []);

  // 修改 createConversation 方法，移除前端验证
  const createConversation = useCallback(async (title: string, modelId: number) => {
    try {
      console.log(`尝试创建对话: 标题="${title}", 模型ID=${modelId}`);
      
      // 关键：不进行前端验证，直接发送请求到后端
      const response: ApiResponse = await chatApi.createConversation({
        title,
        model_id: modelId,
      });
      
      console.log('创建对话后端响应:', response);
      
      if (response.success && response.data) {
        message.success(response.message || '对话创建成功');
        return { success: true, data: response.data };
      } else {
        // 后端返回错误，显示后端的具体错误信息
        const errorMsg = response.message || '创建对话失败';
        console.error('后端创建对话失败:', response);
        message.error(errorMsg);
        return { success: false, error: errorMsg };
      }
    } catch (error: any) {
      console.error('创建对话网络错误:', error);
      // 根据错误类型显示不同的消息
      let errorMessage = '创建对话失败';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      message.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  }, []);

  // 删除对话
  const deleteConversation = useCallback(async (conversationId: number) => {
    try {
      const response: ApiResponse = await chatApi.deleteConversation(conversationId);
      
      if (response.success) {
        message.success(response.message || '对话删除成功');
        return { success: true };
      } else {
        message.error(response.message || '删除对话失败');
        return { success: false, error: response.message };
      }
    } catch (error: any) {
      console.error('删除对话错误:', error);
      message.error(error.error || '删除对话失败');
      return { success: false, error: error.error };
    }
  }, []);

  return {
    // 状态
    conversations,
    currentConversation,
    selectedModel,
    
    // 操作
    fetchConversations,
    createConversation,
    deleteConversation,
  };
};

export default useChat;
