import { create } from 'zustand';
import { chatApi } from '@/api/chat'; // 假设有这个 API 模块

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  model?: string;
}

export interface StoreConversation {
  id: string;
  title: string;
  messages: Message[];
  model: string;
  modelId?: number; // 添加这个字段
  createdAt: Date;
  updatedAt: Date;
  isArchived: boolean;
}

interface ChatState {
  conversations: StoreConversation[];
  currentConversation: StoreConversation | null;
  selectedModel: string;
  isGenerating: boolean;
  loading: boolean;
  
  // 操作
  setCurrentConversation: (conversation: StoreConversation | null) => void;
  addConversation: (conversation: StoreConversation) => void;
  deleteConversation: (conversationId: string) => void;
  setConversations: (conversations: StoreConversation[]) => void;
  updateConversation: (conversationId: string, updates: Partial<StoreConversation>) => void;
  addMessage: (conversationId: string, message: Message) => void;
  setSelectedModel: (model: string) => void;
  setIsGenerating: (generating: boolean) => void;
  setLoading: (loading: boolean) => void;
  
  // 新增：加载对话的完整信息（包括消息）
  loadConversationMessages: (conversationId: string) => Promise<void>;
  // 新增：从API响应初始化对话列表
  initializeConversationsFromApi: (apiConversations: any[]) => void;
  
  // 新增消息操作方法
  deleteMessage: (conversationId: string, messageId: string) => void;
  updateMessageContent: (conversationId: string, messageId: string, newContent: string) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  selectedModel: '',
  isGenerating: false,
  loading: false,
  
  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
  
  addConversation: (conversation) =>
    set((state) => ({
      conversations: [conversation, ...state.conversations],
    })),
  
  deleteConversation: (conversationId) =>
    set((state) => ({
      conversations: state.conversations.filter((conv) => conv.id !== conversationId),
      currentConversation: 
        state.currentConversation?.id === conversationId 
          ? state.conversations[1] || null 
          : state.currentConversation,
    })),
  
  setConversations: (conversations) => set({ conversations }),
  
  updateConversation: (conversationId, updates) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId ? { ...conv, ...updates } : conv
      ),
      currentConversation:
        state.currentConversation?.id === conversationId
          ? { ...state.currentConversation, ...updates }
          : state.currentConversation,
    })),
  
  addMessage: (conversationId, message) =>
    set((state) => {
      const updatedConversations = state.conversations.map((conv) => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            messages: [...conv.messages, message],
            updatedAt: new Date(),
          };
        }
        return conv;
      });
      
      const updatedCurrentConversation = 
        state.currentConversation?.id === conversationId
          ? {
              ...state.currentConversation,
              messages: [...state.currentConversation.messages, message],
              updatedAt: new Date(),
            }
          : state.currentConversation;
      
      return {
        conversations: updatedConversations,
        currentConversation: updatedCurrentConversation,
      };
    }),
  
  setSelectedModel: (model) => set({ selectedModel: model }),
  
  setIsGenerating: (generating) => set({ isGenerating: generating }),
  
  setLoading: (loading) => set({ loading }),
  
  // 新增：加载对话的完整消息
  loadConversationMessages: async (conversationId: string) => {
    try {
      const response = await chatApi.getConversationMessages(parseInt(conversationId));
      
      if (response.success && response.data?.messages) {
        const messages: Message[] = response.data.messages.map((msg: any) => ({
          id: msg.message_id?.toString() || Date.now().toString(),
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: new Date(msg.created_at || Date.now()),
          model: msg.model_id ? `模型 ${msg.model_id}` : undefined
        }));
        
        // 更新对话的消息
        set((state) => ({
          conversations: state.conversations.map(conv =>
            conv.id === conversationId ? { ...conv, messages } : conv
          ),
          currentConversation:
            state.currentConversation?.id === conversationId
              ? { ...state.currentConversation, messages }
              : state.currentConversation,
        }));
      }
    } catch (error) {
      console.error('加载对话消息失败:', error);
    }
  },
  
  // 新增：从API响应初始化对话列表
  initializeConversationsFromApi: (apiConversations: any[]) => {
    const conversations: StoreConversation[] = apiConversations.map(conv => ({
      id: conv.conversation_id.toString(),
      title: conv.title || '未命名对话',
      messages: [], // 初始为空，需要时再加载
      model: conv.model_name || '默认模型',
      modelId: conv.model_id,
      createdAt: new Date(conv.created_at || Date.now()),
      updatedAt: new Date(conv.updated_at || Date.now()),
      isArchived: conv.is_archived || false
    }));
    
    set({ conversations });
  },
  
  // 新增：删除消息
  deleteMessage: (conversationId: string, messageId: string) =>
    set((state) => {
      const updatedConversations = state.conversations.map((conv) => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            messages: conv.messages.filter((msg) => msg.id !== messageId),
            updatedAt: new Date(),
          };
        }
        return conv;
      });
      
      const updatedCurrentConversation = 
        state.currentConversation?.id === conversationId
          ? {
              ...state.currentConversation,
              messages: state.currentConversation.messages.filter((msg) => msg.id !== messageId),
              updatedAt: new Date(),
            }
          : state.currentConversation;
      
      return {
        conversations: updatedConversations,
        currentConversation: updatedCurrentConversation,
      };
    }),
  
  // 新增：更新消息内容
  updateMessageContent: (conversationId: string, messageId: string, newContent: string) =>
    set((state) => {
      const updatedConversations = state.conversations.map((conv) => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            messages: conv.messages.map((msg) =>
              msg.id === messageId ? { ...msg, content: newContent } : msg
            ),
            updatedAt: new Date(),
          };
        }
        return conv;
      });
      
      const updatedCurrentConversation = 
        state.currentConversation?.id === conversationId
          ? {
              ...state.currentConversation,
              messages: state.currentConversation.messages.map((msg) =>
                msg.id === messageId ? { ...msg, content: newContent } : msg
              ),
              updatedAt: new Date(),
            }
          : state.currentConversation;
      
      return {
        conversations: updatedConversations,
        currentConversation: updatedCurrentConversation,
      };
    }),
}));
