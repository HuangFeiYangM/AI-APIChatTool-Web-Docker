// src/pages/ChatPage/ChatArea.tsx - 完整修复版，添加上下文功能（优化版）
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Input, 
  Button, 
  Spin, 
  Empty, 
  Avatar, 
  message, 
  Tag, 
  Alert, 
  Modal,
  Switch,
  Popover
} from 'antd';
import { 
  SendOutlined, 
  UserOutlined, 
  RobotOutlined, 
  SettingOutlined,
  ExclamationCircleOutlined,
  CopyOutlined,
  EditOutlined,
  DeleteOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { useChatStore, type Message } from '@/store/chatStore';
import chatApi from '@/api/chat';
import { modelConfigService } from '@/services/modelConfigService';
import { ContextSettings } from '@/types/chat';
import styles from './ChatPage.module.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// 移除了 TextArea 的解构，因为我们直接使用 Input.TextArea
// const { TextArea } = Input; // 注释掉这行

// 分隔符常量定义
const CONTEXT_START_MARKER = '=== CTX START ===';
const CONTEXT_END_MARKER = '=== CTX END ===';
const USER_PREFIX = '用户: ';

interface ModelInfo {
  model_id: number;
  model_name: string;
  model_provider?: string;
  is_enabled: boolean;
}

/**
 * 清理嵌套的上下文标记（用于修复已有数据）
 */
const cleanupNestedContext = (content: string): string => {
  // 如果内容不包含上下文标记，直接返回
  if (!content.includes(CONTEXT_START_MARKER)) {
    return content;
  }
  
  // 找到最后一个有效的上下文块
  const startIndex = content.lastIndexOf(CONTEXT_START_MARKER);
  const endIndex = content.lastIndexOf(CONTEXT_END_MARKER);
  
  if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
    // 提取最后一个上下文块之后的内容
    const afterContext = content.substring(endIndex + CONTEXT_END_MARKER.length);
    
    // 查找用户输入
    const userPrefixIndex = afterContext.indexOf(USER_PREFIX);
    if (userPrefixIndex !== -1) {
      return afterContext.substring(userPrefixIndex);
    }
  }
  
  return content;
};

/**
 * 从存储的内容中提取原始用户输入（增强版）
 */
const extractOriginalContent = (
  storedContent: string,
  messageId?: string
): string => {
  // 先清理嵌套的上下文
  const cleanedContent = cleanupNestedContext(storedContent);
  
  // 1. 优先从本地映射中查找原始内容
  if (messageId) {
    const store = useChatStore.getState();
    const original = store.originalContentMap[messageId];
    if (original !== undefined) {
      return original;
    }
  }
  
  // 2. 尝试解析分隔符格式（处理嵌套情况）
  // 找到最后一个 CONTEXT_END_MARKER
  const lastEndMarkerIndex = cleanedContent.lastIndexOf(CONTEXT_END_MARKER);
  
  if (lastEndMarkerIndex !== -1) {
    // 从最后一个上下文标记后开始查找用户输入
    const afterLastContext = cleanedContent.substring(lastEndMarkerIndex + CONTEXT_END_MARKER.length);
    
    // 查找 USER_PREFIX
    const userPrefixIndex = afterLastContext.indexOf(USER_PREFIX);
    if (userPrefixIndex !== -1) {
      const userInputStart = userPrefixIndex + USER_PREFIX.length;
      return afterLastContext.substring(userInputStart).trim();
    }
    
    // 如果没有 USER_PREFIX，返回剩余内容
    return afterLastContext.trim();
  }
  
  // 3. 如果没有上下文标记，检查是否有用户前缀
  if (cleanedContent.includes(USER_PREFIX)) {
    // 找到最后一个 USER_PREFIX
    const lastUserPrefixIndex = cleanedContent.lastIndexOf(USER_PREFIX);
    if (lastUserPrefixIndex !== -1) {
      return cleanedContent.substring(lastUserPrefixIndex + USER_PREFIX.length).trim();
    }
  }
  
  // 4. 直接返回原内容（可能是AI回复或旧格式消息）
  return cleanedContent.trim();
};

/**
 * 构建带上下文的消息（使用干净的历史内容）
 */
const buildContextMessage = (
  currentInput: string,
  historyMessages: Message[],
  contextSettings: ContextSettings
): { fullContent: string; originalContent: string } => {
  if (!contextSettings.enabled || !historyMessages.length) {
    return { fullContent: currentInput, originalContent: currentInput };
  }
  
  // 计算需要的历史消息条数（每轮对话包含用户和AI两条消息）
  const messagesToInclude = contextSettings.level * 2;
  
  // 获取最近的历史消息
  const recentMessages = historyMessages.slice(-messagesToInclude);
  
  // 构建上下文字符串，使用提取后的干净内容
  const contextLines = recentMessages.map(msg => {
    const role = msg.role === 'user' ? '用户' : '助手';
    // 关键修改：使用 extractOriginalContent 获取干净的内容
    const cleanContent = extractOriginalContent(msg.content, msg.id);
    return `${role}: ${cleanContent}`;
  });
  
  const context = contextLines.join('\n');
  
  // 使用分隔符标记上下文和用户输入
  const fullContent = `${CONTEXT_START_MARKER}\n${context}\n${CONTEXT_END_MARKER}\n${USER_PREFIX}${currentInput}`;
  
  return { fullContent, originalContent: currentInput };
};

const ChatArea: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [configuredModels, setConfiguredModels] = useState<ModelInfo[]>([]);
  const [currentModelConfigured, setCurrentModelConfigured] = useState<boolean | null>(null);
  
  // 消息操作相关状态 - 修改为模态框方式
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [editContent, setEditContent] = useState('');
  const [editLoading, setEditLoading] = useState(false);

  // 上下文设置相关状态
  const [showContextSettings, setShowContextSettings] = useState(false);
  const contextSettings = useChatStore((state) => state.contextSettings);
  const setContextSettings = useChatStore((state) => state.setContextSettings);
  const setOriginalContent = useChatStore((state) => state.setOriginalContent);
  const clearOriginalContent = useChatStore((state) => state.clearOriginalContent);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  // 添加刷新状态
  const [isRefreshingMessages, setIsRefreshingMessages] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null); // 添加输入框的 ref 引用

  const {
    currentConversation,
    addMessage,
    setIsGenerating,
    selectedModel,
    setSelectedModel,
    updateMessageContent,
    deleteMessage,
  } = useChatStore();

  // 清理过期的原始内容映射
  useEffect(() => {
    const cleanupOriginalContentMap = () => {
      const store = useChatStore.getState();
      const { originalContentMap, conversations } = store;
      
      // 收集所有当前对话中的消息ID
      const allMessageIds = new Set<string>();
      conversations.forEach(conv => {
        conv.messages.forEach(msg => {
          allMessageIds.add(msg.id);
        });
      });
      
      // 过滤掉不存在的消息ID
      const newMap: Record<string, string> = {};
      Object.entries(originalContentMap).forEach(([messageId, content]) => {
        if (allMessageIds.has(messageId)) {
          newMap[messageId] = content;
        }
      });
      
      // 限制映射数量（最多保留最近100条）
      const entries = Object.entries(newMap);
      if (entries.length > 100) {
        const recentEntries = entries.slice(-100);
        useChatStore.setState({
          originalContentMap: Object.fromEntries(recentEntries),
        });
      }
    };
    
    // 初始清理
    cleanupOriginalContentMap();
    
    // 每5分钟清理一次
    const interval = setInterval(cleanupOriginalContentMap, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // 当 currentConversation 变化时，加载历史消息
  useEffect(() => {
    if (currentConversation?.id) {
      const loadMessages = async () => {
        try {
          setLoading(true);
          await useChatStore.getState().loadConversationMessages(currentConversation.id);
        } catch (error) {
          console.error('加载消息失败:', error);
        } finally {
          setLoading(false);
        }
      };
      
      // 如果当前对话没有消息或需要重新加载，则从后端获取
      if (currentConversation.messages.length === 0) {
        loadMessages();
      }
    }
  }, [currentConversation?.id]); // 仅当对话ID变化时触发

  // 获取已配置的模型
  useEffect(() => {
    const fetchConfiguredModels = async () => {
      try {
        const models = await modelConfigService.getConfiguredModels();
        
        const modelInfos: ModelInfo[] = models.map(model => ({
          model_id: model.model_id,
          model_name: model.model_name,
          model_provider: model.model_provider,
          is_enabled: true // 因为getConfiguredModels只返回已启用的
        }));
        
        setConfiguredModels(modelInfos);
        
        // 如果没有选中的模型且当前对话有模型ID，则设置
        if (!selectedModel && currentConversation?.modelId) {
          const modelName = modelInfos.find(m => m.model_id === currentConversation.modelId)?.model_name;
          if (modelName) {
            setSelectedModel(modelName);
          }
        }
      } catch (error) {
        console.error('获取已配置模型失败:', error);
      }
    };

    fetchConfiguredModels();
  }, [currentConversation, selectedModel, setSelectedModel]);

  // 检查当前对话的模型配置状态
  useEffect(() => {
    const checkCurrentModelConfig = async () => {
      if (!currentConversation?.modelId) {
        console.log('当前对话没有模型ID');
        setCurrentModelConfigured(null);
        return false;
      }
      
      try {
        const { configured } = await modelConfigService.checkModelForChat(currentConversation.modelId);
        setCurrentModelConfigured(configured);
        
        if (!configured) {
          console.log(`模型 ${currentConversation.modelId} 未配置，无法发送消息`);
        }
        
        return configured;
      } catch (error: any) {
        console.error('检查模型配置失败:', error);
        // 对于404错误，认为是未配置
        if (error.status === 404 || error.isModelNotConfigured) {
          setCurrentModelConfigured(false);
        } else {
          setCurrentModelConfigured(null);
        }
        return false;
      }
    };

    checkCurrentModelConfig();
  }, [currentConversation]);

  // 从模型ID获取模型名称
  const getModelNameById = (modelId: number): string => {
    const model = configuredModels.find(m => m.model_id === modelId);
    return model?.model_name || `模型 ${modelId}`;
  };

  // 获取当前对话使用的模型名称
  const getCurrentModelName = (): string => {
    // 总是返回对话绑定的模型，忽略 selectedModel
    if (currentConversation?.modelId) {
      return getModelNameById(currentConversation.modelId);
    }
    
    return '未知模型';
  };

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  // 初始加载时和发送消息后自动聚焦输入框
  useEffect(() => {
    // 等待一小段时间确保组件完全渲染
    const timer = setTimeout(() => {
      if (inputRef.current && !loading) {
        inputRef.current.focus();
      }
    }, 100);
    
    return () => clearTimeout(timer);
  }, [loading]);

  // 消息操作方法
  const handleCopyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content)
      .then(() => {
        message.success('已复制到剪贴板');
      })
      .catch(() => {
        message.error('复制失败');
      });
  }, [message]);

  // 修改 handleEditMessage 方法以提取原始内容
  const handleEditMessage = useCallback((message: Message) => {
    const originalContent = extractOriginalContent(message.content, message.id);
    setSelectedMessage(message);
    setEditModalVisible(true);
    setEditContent(originalContent);
  }, []);

  const handleCancelEdit = useCallback(() => {
    setEditModalVisible(false);
    setSelectedMessage(null);
    setEditContent('');
  }, []);

  const handleSaveEdit = useCallback(async () => {
    if (!selectedMessage || !currentConversation) return;
    
    if (!editContent.trim()) {
      message.error('消息内容不能为空');
      return;
    }
    
    setEditLoading(true);
    try {
      const conversationId = parseInt(currentConversation.id);
      const messageId = parseInt(selectedMessage.id);
      
      if (isNaN(conversationId) || isNaN(messageId)) {
        throw new Error('对话ID或消息ID无效');
      }
      
      // 构建要发送的完整内容（可能需要包含上下文）
      const store = useChatStore.getState();
      const historyMessages = currentConversation.messages.filter(msg => msg.id !== selectedMessage.id);
      const { fullContent } = buildContextMessage(
        editContent.trim(),
        historyMessages,
        contextSettings
      );
      
      const response = await chatApi.updateMessage(conversationId, messageId, {
        content: fullContent
      });
      
      if (response.success) {
        // 更新本地状态（显示原始内容）
        updateMessageContent(
          currentConversation.id,
          selectedMessage.id,
          editContent.trim()
        );
        
        // 更新本地映射
        setOriginalContent(selectedMessage.id, editContent.trim());
        
        message.success('消息修改成功');
        setEditModalVisible(false);
        setSelectedMessage(null);
        setEditContent('');
      } else {
        message.error(response.message || '修改消息失败');
      }
    } catch (error: any) {
      console.error('修改消息失败:', error);
      message.error(error.response?.data?.detail || '修改消息失败');
    } finally {
      setEditLoading(false);
    }
  }, [selectedMessage, currentConversation, editContent, contextSettings, updateMessageContent, setOriginalContent, message]);

  const handleDeleteMessage = useCallback(async (messageId: string) => {
    if (!currentConversation) return;
    
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条消息吗？此操作不可恢复。',
      okText: '删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          const conversationId = parseInt(currentConversation.id);
          const msgId = parseInt(messageId);
          
          if (isNaN(conversationId) || isNaN(msgId)) {
            throw new Error('对话ID或消息ID无效');
          }
          
          const response = await chatApi.deleteMessage(conversationId, msgId);
          
          if (response.success) {
            // 更新本地状态
            deleteMessage(currentConversation.id, messageId);
            
            // 从原始内容映射中移除
            const store = useChatStore.getState();
            const newMap = { ...store.originalContentMap };
            delete newMap[messageId];
            useChatStore.setState({ originalContentMap: newMap });
            
            message.success('消息删除成功');
          } else {
            message.error(response.message || '删除消息失败');
          }
        } catch (error: any) {
          console.error('删除消息失败:', error);
          message.error(error.response?.data?.detail || '删除消息失败');
        }
      },
    });
  }, [currentConversation, Modal, message, deleteMessage]);

  // 无感刷新函数 - 在 handleSendMessage 前添加
  const silentRefreshMessages = async (conversationId: string) => {
    if (!conversationId) return;
    
    // 保存当前滚动位置
    const container = messagesContainerRef.current;
    const scrollTop = container?.scrollTop || 0;
    const scrollHeight = container?.scrollHeight || 0;
    
    // 标记刷新状态
    setIsRefreshingMessages(true);
    
    try {
      // 立即刷新消息列表
      await useChatStore.getState().loadConversationMessages(conversationId);
    } catch (error) {
      console.error('刷新消息失败:', error);
    } finally {
      // 微延迟后清除刷新状态，确保渲染完成
      setTimeout(() => {
        setIsRefreshingMessages(false);
        
        // 恢复滚动位置（考虑新消息增加的高度）
        if (container) {
          const newScrollHeight = container.scrollHeight;
          const heightDiff = newScrollHeight - scrollHeight;
          container.scrollTop = scrollTop + heightDiff;
        }
      }, 100);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    // 如果没有当前对话
    if (!currentConversation) {
      message.error('请先创建一个对话');
      return;
    }

    // 如果没有模型ID
    if (!currentConversation.modelId) {
      message.error('对话没有关联的模型，请重新创建对话');
      return;
    }

    // 检查模型配置
    if (currentModelConfigured === false) {
      message.error('该模型未配置或未启用，请先在设置页面配置API密钥');
      return;
    }

    // 如果还在检查配置
    if (currentModelConfigured === null) {
      message.error('正在检查模型配置，请稍后...');
      return;
    }

    const store = useChatStore.getState();
    const { contextSettings } = store;
    
    // 构建带上下文的消息
    const historyMessages = currentConversation.messages || [];
    const { fullContent, originalContent } = buildContextMessage(
      inputValue,
      historyMessages,
      contextSettings
    );

    const tempMessageId = `temp_${Date.now()}`;
    const userMessage: Message = {
      id: tempMessageId,
      role: 'user',
      content: originalContent, // 显示原始内容
      timestamp: new Date(),
    };

    // 保存原始内容到本地映射
    setOriginalContent(tempMessageId, originalContent);

    // 添加用户消息（显示原始内容）
    if (currentConversation) {
      addMessage(currentConversation.id, userMessage);
    }

    const messageToSend = fullContent;
    setInputValue('');
    setLoading(true);
    setIsGenerating(true);

    try {
      // 转换 conversation_id: string -> number
      const conversationId = currentConversation?.id 
        ? parseInt(currentConversation.id, 10) 
        : undefined;
      
      // 确保是有效的数字
      const validConversationId = conversationId && !isNaN(conversationId) 
        ? conversationId 
        : undefined;

      const modelToUse = getCurrentModelName();
      console.log('发送消息到模型:', modelToUse, '对话ID:', validConversationId);

      const response = await chatApi.sendMessage({
        message: messageToSend,
        model: modelToUse,
        conversation_id: validConversationId,
      });

      console.log('发送消息响应:', response);

      if (response.success && response.data) {
        // 更新本地用户消息的ID（如果后端返回了新的消息ID）
        if (response.data.message_id && response.data.message_id !== tempMessageId) {
          // 更新映射中的消息ID
          const newMap = { ...store.originalContentMap };
          delete newMap[tempMessageId];
          newMap[response.data.message_id] = originalContent;
          useChatStore.setState({ originalContentMap: newMap });
          
          // 更新本地消息ID
          // 注意：这里简化处理，实际应该更新消息对象
        }

        const assistantMessage: Message = {
          id: response.data.message_id || (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date(),
          model: modelToUse,
        };

        if (currentConversation) {
          addMessage(currentConversation.id, assistantMessage);
          
          // 🔧 关键修复：利用API成功响应立即无感刷新
          silentRefreshMessages(currentConversation.id);
        }
      } else {
        message.error(response.message || '发送消息失败');
        
        // 移除本地映射
        const newMap = { ...useChatStore.getState().originalContentMap };
        delete newMap[tempMessageId];
        useChatStore.setState({ originalContentMap: newMap });
      }
    } catch (error: any) {
      console.error('发送消息失败:', error);
      
      // 移除本地映射
      const newMap = { ...useChatStore.getState().originalContentMap };
      delete newMap[tempMessageId];
      useChatStore.setState({ originalContentMap: newMap });
      
      // 更详细的错误处理
      if (error.response?.status === 400) {
        if (error.response.data?.detail?.includes('API密钥') || error.response.data?.detail?.includes('未配置')) {
          message.error('模型未配置或API密钥无效，请检查设置中的API配置');
          // 重新检查配置状态
          setCurrentModelConfigured(false);
        } else if (error.response.data?.detail?.includes('模型不可用')) {
          message.error('模型不可用，请选择其他模型或重新配置');
        } else {
          message.error(error.response.data?.detail || '请求参数错误');
        }
      } else if (error.response?.status === 401) {
        message.error('认证失败，请重新登录');
      } else if (error.response?.status === 503) {
        message.error('服务暂时不可用，请稍后重试');
      } else {
        message.error(error.response?.data?.detail || '网络错误，请稍后重试');
      }
    } finally {
      setLoading(false);
      setIsGenerating(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 上下文设置面板内容
  const contextSettingsContent = (
    <div className={styles.contextSettingsPanel}>
      <div className={styles.contextSettingsHeader}>
        <h4>上下文设置</h4>
      </div>
      
      <div className={styles.contextSettingsContent}>
        <div className={styles.contextSwitch}>
          <label style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
            <Switch
              checked={contextSettings.enabled}
              onChange={(checked) => {
                setContextSettings({
                  ...contextSettings,
                  enabled: checked,
                });
              }}
              style={{ marginRight: 8 }}
            />
            <span>启用上下文</span>
          </label>
          <p className={styles.contextDescription} style={{ fontSize: '12px', color: '#666', margin: 0 }}>
            启用后，AI将读取历史对话作为上下文
          </p>
        </div>
        
        <div className={`${styles.contextLevels} ${!contextSettings.enabled ? styles.disabled : ''}`}>
          <label style={{ display: 'block', marginBottom: 8 }}>对话轮数：</label>
          <div className={styles.levelButtons} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            {[1, 3, 5, 10].map((level) => (
              <Button
                key={level}
                size="small"
                type={contextSettings.level === level ? 'primary' : 'default'}
                onClick={() => {
                  if (contextSettings.enabled) {
                    setContextSettings({
                      ...contextSettings,
                      level,
                    });
                  }
                }}
                disabled={!contextSettings.enabled}
              >
                {level}
              </Button>
            ))}
          </div>
          <p className={styles.levelDescription} style={{ fontSize: '12px', color: '#666', margin: 0 }}>
            选择AI读取的历史对话轮数（每轮包含用户和AI消息）
          </p>
        </div>
      </div>
    </div>
  );

  const renderModelStatus = () => {
    // 如果当前模型未配置
    if (currentModelConfigured === false) {
      return (
        <div className={styles.modelSelector}>
          <Tag color="orange" icon={<ExclamationCircleOutlined />}>
            模型未配置
          </Tag>
          <Button
            type="link"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => window.location.href = '/settings?tab=api'}
          >
            去配置
          </Button>
        </div>
      );
    }

    // 如果没有已配置的模型
    if (configuredModels.length === 0) {
      return (
        <div className={styles.modelSelector}>
          <Tag color="orange">未配置模型</Tag>
          <Button
            type="link"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => window.location.href = '/settings?tab=api'}
          >
            去配置
          </Button>
        </div>
      );
    }

    // 显示当前模型（不可点击）
    const currentModelName = getCurrentModelName();
    
    return (
      <div className={styles.modelSelector}>
        <span style={{ marginRight: 8 }}>模型:</span>
        <Tag
          color="blue"
          style={{ marginRight: 8 }}
        >
          {currentModelName}
        </Tag>
      </div>
    );
  };

  if (!currentConversation) {
    return (
      <div className={styles.emptyChat}>
        <Empty
          description="选择一个对话开始聊天"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    );
  }

  // 显示配置警告
  const showConfigWarning = currentModelConfigured === false || configuredModels.length === 0;

  return (
    <div className={styles.chatArea}>
      <div className={styles.chatHeader}>
        <div className={styles.conversationTitle}>
          <h3>{currentConversation.title}</h3>
          {renderModelStatus()}
        </div>
        
        <div className={styles.headerRight}>
          <Popover
            content={contextSettingsContent}
            trigger="click"
            open={showContextSettings}
            onOpenChange={setShowContextSettings}
            placement="bottomRight"
          >
            <Button
              icon={<HistoryOutlined />}
              type={contextSettings.enabled ? "primary" : "default"}
              size="small"
              title="上下文设置"
            >
              读取上下文
            </Button>
          </Popover>
        </div>
      </div>

      {showConfigWarning && (
        <Alert
          message="模型配置提示"
          description={
            currentModelConfigured === false 
              ? `当前对话使用的模型 "${getCurrentModelName()}" 未配置或未启用，请先在设置页面配置API密钥`
              : "没有已配置的模型，请先在设置页面配置API密钥"
          }
          type="warning"
          showIcon
          action={
            <Button 
              size="small" 
              type="primary"
              onClick={() => window.location.href = '/settings?tab=api'}
            >
              去配置
            </Button>
          }
          style={{ margin: '0 16px 16px 16px' }}
        />
      )}

      <div 
        ref={messagesContainerRef}
        className={`${styles.messagesContainer} ${isRefreshingMessages ? styles.refreshing : ''}`}
      >
        {currentConversation.messages.map((msg) => {
          // 提取原始内容显示
          const displayContent = extractOriginalContent(msg.content, msg.id);
          
          return (
            <div
              key={msg.id}
              className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.assistantMessage}`}
            >
              <div className={styles.messageContent}>
                <div className={styles.avatar}>
                  {msg.role === 'user' ? (
                    <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
                  ) : (
                    <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
                  )}
                </div>
                <div className={styles.messageBody}>
                  <div className={styles.messageHeader}>
                    <span className={styles.messageRole}>
                      {msg.role === 'user' ? '你' : 'AI助手'}
                    </span>
                    {msg.model && (
                      <Tag color="blue" style={{ marginLeft: 8 }}>
                        {msg.model}
                      </Tag>
                    )}
                    <span className={styles.messageTime}>
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  
                  {/* 正常显示模式 */}
                  <div className={styles.messageText}>
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // 标题 - 紧凑型
                        h1({node, children, ...props}) {
                          return <h1 className={styles.markdownH1} {...props}>{children}</h1>;
                        },
                        h2({node, children, ...props}) {
                          return <h2 className={styles.markdownH2} {...props}>{children}</h2>;
                        },
                        h3({node, children, ...props}) {
                          return <h3 className={styles.markdownH3} {...props}>{children}</h3>;
                        },
                        h4({node, children, ...props}) {
                          return <h4 className={styles.markdownH4} {...props}>{children}</h4>;
                        },
                        // 段落 - 紧凑型
                        p({node, children, ...props}) {
                          return <p className={styles.markdownParagraph} {...props}>{children}</p>;
                        },
                        // 列表 - 紧凑型
                        ul({node, children, ...props}) {
                          return <ul className={styles.markdownList} {...props}>{children}</ul>;
                        },
                        ol({node, children, ...props}) {
                          return <ol className={styles.markdownList} {...props}>{children}</ol>;
                        },
                        li({node, children, ...props}) {
                          return <li className={styles.markdownListItem} {...props}>{children}</li>;
                        },
                        // 代码块
                        code({node, className, children, ...props}) {
                          const match = /language-(\w+)/.exec(className || '');
                          const isInline = !match;
                          return isInline ? (
                            <code className={styles.inlineCode} {...props}>
                              {children}
                            </code>
                          ) : (
                            <pre className={styles.codeBlock}>
                              <code className={className} {...props}>
                                {children}
                              </code>
                            </pre>
                          );
                        },
                        // 表格 - 带滚动容器
                        table({node, children, ...props}) {
                          return (
                            <div className={styles.tableWrapper}>
                              <table className={styles.table} {...props}>
                                {children}
                              </table>
                            </div>
                          );
                        },
                        // 引用块
                        blockquote({node, children, ...props}) {
                          return (
                            <blockquote className={styles.blockquote} {...props}>
                              {children}
                            </blockquote>
                          );
                        },
                        // 链接
                        a({node, children, ...props}) {
                          return <a className={styles.markdownLink} {...props}>{children}</a>;
                        },
                        // 水平线
                        hr({node, children, ...props}) {
                          return <hr className={styles.markdownHr} {...props} />;
                        }
                      }}
                    >
                      {displayContent}
                    </ReactMarkdown>
                  </div>
                  
                  {/* 消息操作按钮 - 移除条件判断，所有消息都显示修改和删除按钮 */}
                  <div className={styles.messageActions}>
                    <Button
                      className={styles.messageActionButton}
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => handleCopyMessage(displayContent)}
                    >
                      复制
                    </Button>
                    <Button
                      className={styles.messageActionButton}
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => handleEditMessage(msg)}
                    >
                      修改
                    </Button>
                    <Button
                      className={`${styles.messageActionButton} ${styles.danger}`}
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => handleDeleteMessage(msg.id)}
                    >
                      删除
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        {loading && (
          <div className={styles.loadingMessage}>
            <div className={styles.messageContent}>
              <div className={styles.avatar}>
                <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
              </div>
              <div className={styles.messageBody}>
                <Spin size="small" />
                <span className={styles.thinkingText}>正在思考...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputArea}>
        <Input.TextArea  // 改为 Input.TextArea
          ref={inputRef}  // 添加这一行
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={currentModelConfigured === false ? "模型未配置，请先配置API密钥" : "输入消息... (Shift+Enter换行，Enter发送)"}
          autoSize={{ minRows: 1, maxRows: 4 }}
          disabled={loading || currentModelConfigured === false || configuredModels.length === 0}
          className={styles.textArea}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSendMessage}
          loading={loading}
          disabled={!inputValue.trim() || currentModelConfigured === false || configuredModels.length === 0}
          className={styles.sendButton}
        >
          发送
        </Button>
      </div>

      {/* 编辑消息模态框 */}
      <Modal
        title="编辑消息"
        open={editModalVisible}
        onCancel={handleCancelEdit}
        footer={[
          <Button key="cancel" onClick={handleCancelEdit}>
            取消
          </Button>,
          <Button 
            key="save" 
            type="primary" 
            loading={editLoading}
            onClick={handleSaveEdit}
          >
            保存
          </Button>,
        ]}
        className={styles.editMessageModal}
      >
        <Input.TextArea  // 改为 Input.TextArea
          value={editContent}
          onChange={(e) => setEditContent(e.target.value)}
          autoSize={{ minRows: 4, maxRows: 10 }}
          className={styles.editMessageTextArea}
          placeholder="修改消息内容..."
        />
      </Modal>
    </div>
  );
};

export default ChatArea;
