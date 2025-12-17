// src/pages/ChatPage/ChatArea.tsx - 完整修复版
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
  Modal
} from 'antd';
import { 
  SendOutlined, 
  UserOutlined, 
  RobotOutlined, 
  SettingOutlined, 
  ExclamationCircleOutlined,
  CopyOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { useChatStore, type Message } from '@/store/chatStore';
import chatApi from '@/api/chat';
import { modelConfigService } from '@/services/modelConfigService';
import styles from './ChatPage.module.css';

// 移除了 TextArea 的解构，因为我们直接使用 Input.TextArea
// const { TextArea } = Input; // 注释掉这行

interface ModelInfo {
  model_id: number;
  model_name: string;
  model_provider?: string;
  is_enabled: boolean;
}

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
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    currentConversation,
    addMessage,
    setIsGenerating,
    selectedModel,
    setSelectedModel,
  } = useChatStore();

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
    if (selectedModel) return selectedModel;
    
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

  // 修改 handleEditMessage 方法
  const handleEditMessage = useCallback((message: Message) => {
    setSelectedMessage(message);
    setEditModalVisible(true);
    setEditContent(message.content);
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
      
      const response = await chatApi.updateMessage(conversationId, messageId, {
        content: editContent.trim()
      });
      
      if (response.success) {
        // 更新本地状态
        useChatStore.getState().updateMessageContent(
          currentConversation.id,
          selectedMessage.id,
          editContent.trim()
        );
        
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
  }, [selectedMessage, currentConversation, editContent, message]);

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
            useChatStore.getState().deleteMessage(currentConversation.id, messageId);
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
  }, [currentConversation, Modal, message]);

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

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    // 添加用户消息
    if (currentConversation) {
      addMessage(currentConversation.id, userMessage);
    }

    const messageToSend = inputValue;
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
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date(),
          model: modelToUse,
        };

        if (currentConversation) {
          addMessage(currentConversation.id, assistantMessage);
        }
      } else {
        message.error(response.message || '发送消息失败');
      }
    } catch (error: any) {
      console.error('发送消息失败:', error);
      
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

  const handleModelChange = (modelName: string) => {
    // 找到对应的模型ID
    const model = configuredModels.find(m => m.model_name === modelName);
    if (model) {
      setSelectedModel(modelName);
      message.info(`已切换到模型: ${modelName}`);
    }
  };

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

    // 显示当前模型和可切换的模型
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
        {configuredModels
          .filter(model => model.model_name !== currentModelName)
          .map((model) => (
            <Tag
              key={model.model_id}
              color="default"
              style={{ cursor: 'pointer', marginRight: 8 }}
              onClick={() => handleModelChange(model.model_name)}
            >
              {model.model_name}
            </Tag>
          ))}
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

      <div className={styles.messagesContainer}>
        {currentConversation.messages.map((msg) => (
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
                <>
                  <div className={styles.messageText}>{msg.content}</div>
                  
                  {/* 消息操作按钮 */}
                  <div className={styles.messageActions}>
                    <Button
                      className={styles.messageActionButton}
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => handleCopyMessage(msg.content)}
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
                </>
              </div>
            </div>
          </div>
        ))}
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
