// src/pages/ChatPage/Sidebar.tsx - 完整修复版（添加消息加载功能）
import React, { useState, useEffect, useCallback } from 'react';
import { Menu, Button, Modal, Input, message, Select, Tag } from 'antd';
import {
  PlusOutlined,
  MessageOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useChatStore, type StoreConversation } from '@/store/chatStore';
import chatApi from '@/api/chat';
import settingsApi from '@/api/settings';
import ConversationMenu from './components/ConversationMenu';
import styles from './ChatPage.module.css';

const { Option } = Select;

interface SidebarProps {
  collapsed: boolean;
}

interface AvailableModel {
  model_id: number;
  model_name: string;
  model_provider?: string;
  description?: string;
  is_configured: boolean;
  is_enabled: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [newChatTitle, setNewChatTitle] = useState('');
  const [creatingConversation, setCreatingConversation] = useState(false);
  
  const {
    conversations,
    currentConversation,
    setCurrentConversation,
    addConversation,
    deleteConversation,
    setConversations,
  } = useChatStore();

  const [availableModels, setAvailableModels] = useState<AvailableModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<number | null>(null);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [conversationsLoading, setConversationsLoading] = useState(false);

  // 修复乱码的函数
  const fixChineseEncoding = (text: string): string => {
    if (!text) return '';
    
    const encodingMap: Record<string, string> = {
      'æ¨¡åž‹': '模型',
      'æœ¬': '本',
      'ç‰ˆ': '版',
      'ä¸­æ–‡': '中文',
      'æ•°æ®': '数据',
      'é«˜æ€': '高态',
      'è¯­è¨€': '语言',
      'ç™¾åº¦': '百度',
      'æ–‡å¿ƒ': '文心',
      'ä¸€è¨€': '一言',
      'ernie-bot': '文心一言',
    };
    
    let result = text;
    for (const [encoded, decoded] of Object.entries(encodingMap)) {
      result = result.replace(new RegExp(encoded, 'g'), decoded);
    }
    
    return result;
  };

  // 获取可用模型
  const fetchAvailableModels = useCallback(async () => {
    if (modelsLoading) return;
    
    try {
      setModelsLoading(true);
      console.log('=== 聊天侧边栏：获取用户已配置的模型 ===');
      
      const response = await settingsApi.getUserModelConfigs();
      console.log('用户配置响应:', response);
      
      if (!response.success || !response.data) {
        console.error('获取用户配置失败');
        setAvailableModels([]);
        return;
      }
      
      const userConfigs = Array.isArray(response.data) ? response.data : [];
      console.log('用户配置数据:', userConfigs);
      
      const enabledConfigs = userConfigs.filter((config: any) => {
        const isEnabled = config.is_enabled !== undefined ? config.is_enabled : true;
        const hasApiKey = config.has_api_key !== undefined ? config.has_api_key : 
                         (config.api_key !== undefined && config.api_key !== null);
        
        console.log(`模型 ${config.model_id} (${config.model_name}): isEnabled=${isEnabled}, hasApiKey=${hasApiKey}`);
        
        return isEnabled && hasApiKey;
      });
      
      console.log('已启用且有API密钥的配置:', enabledConfigs);
      
      if (enabledConfigs.length === 0) {
        console.log('没有已启用且有API密钥的模型配置');
        setAvailableModels([]);
        return;
      }
      
      const models: AvailableModel[] = enabledConfigs.map((config: any) => ({
        model_id: config.model_id,
        model_name: fixChineseEncoding(config.model_name || `模型 ${config.model_id}`),
        model_provider: fixChineseEncoding(config.model_provider || '未知'),
        description: config.description ? fixChineseEncoding(config.description) : undefined,
        is_configured: true,
        is_enabled: true
      }));
      
      console.log('最终可用模型列表:', models);
      setAvailableModels(models);
      
      if (models.length > 0 && selectedModel === null) {
        setSelectedModel(models[0].model_id);
        console.log('默认选择模型:', models[0]);
      }
      
    } catch (error: any) {
      console.error('获取用户配置失败:', error);
      message.error('获取模型配置失败');
      setAvailableModels([]);
    } finally {
      setModelsLoading(false);
    }
  }, [selectedModel, modelsLoading]);

  // 获取对话列表
  const fetchConversations = useCallback(async () => {
    if (conversationsLoading) return;
    
    try {
      setConversationsLoading(true);
      console.log('正在获取对话列表...');
      const response = await chatApi.getConversations();
      
      if (response.success && response.data) {
        console.log('获取对话列表成功:', response.data.conversations);
        
        const storeConversations: StoreConversation[] = response.data.conversations.map((conv: any) => {
          const model = availableModels.find(m => m.model_id === conv.model_id);
          const modelName = model ? model.model_name : `模型 ${conv.model_id}`;
          
          return {
            id: conv.conversation_id.toString(),
            title: conv.title,
            messages: [], // 初始为空，稍后按需加载
            model: modelName,
            modelId: conv.model_id,
            createdAt: new Date(conv.created_at),
            updatedAt: new Date(conv.updated_at),
            isArchived: conv.is_archived || false,
          };
        });
        
        setConversations(storeConversations);
        
        if (storeConversations.length > 0 && !currentConversation) {
          setCurrentConversation(storeConversations[0]);
          // 自动加载第一个对话的历史消息
          await useChatStore.getState().loadConversationMessages(storeConversations[0].id);
        }
      } else {
        console.error('获取对话列表失败:', response.message);
      }
    } catch (error: any) {
      console.error('获取对话列表失败:', error);
    } finally {
      setConversationsLoading(false);
    }
  }, [currentConversation, setConversations, setCurrentConversation, availableModels, conversationsLoading]);

  // 切换对话时加载历史消息
  const handleSelectConversation = useCallback(async (conversation: StoreConversation) => {
    console.log('切换到对话:', conversation.id, conversation.title);
    
    // 设置当前对话
    setCurrentConversation(conversation);
    
    try {
      // 如果这个对话还没有消息，或者想要确保是最新的，从后端加载历史消息
      if (conversation.messages.length === 0) {
        console.log('对话消息为空，从后端加载历史消息...');
        await useChatStore.getState().loadConversationMessages(conversation.id);
      } else {
        console.log('对话已有消息，直接使用内存中的消息');
      }
    } catch (error) {
      console.error('加载对话消息失败:', error);
      message.error('加载历史消息失败');
    }
  }, [setCurrentConversation]);

  // 初始加载数据
  useEffect(() => {
    const loadInitialData = async () => {
      await fetchAvailableModels();
      await fetchConversations();
    };
    
    loadInitialData();
  }, []);

  // 检查模型配置
  const checkModelConfiguration = async (modelId: number): Promise<boolean> => {
    try {
      console.log(`检查模型 ${modelId} 配置状态`);
      
      const localModel = availableModels.find(m => m.model_id === modelId);
      if (localModel) {
        console.log(`从本地列表找到模型 ${modelId}，状态: 已配置`);
        return true;
      }
      
      const response = await settingsApi.getModelConfig(modelId);
      console.log(`API检查模型 ${modelId} 响应:`, response);
      
      if (response.success && response.data) {
        console.log(`模型 ${modelId} 已配置`);
        return true;
      }
      
      console.log(`模型 ${modelId} 未配置`);
      return false;
      
    } catch (error: any) {
      console.error(`检查模型 ${modelId} 配置失败:`, error);
      
      if (error.status === 404 || error.isModelNotConfigured) {
        console.log(`模型 ${modelId} 未配置（404错误）`);
        return false;
      }
      
      return false;
    }
  };

  // 创建新对话
  const handleCreateConversation = async () => {
    if (!newChatTitle.trim()) {
      message.warning('请输入对话标题');
      return;
    }

    if (!selectedModel) {
      message.warning('请选择模型');
      return;
    }

    setCreatingConversation(true);
    try {
      const isConfigured = await checkModelConfiguration(selectedModel);
      if (!isConfigured) {
        message.error('该模型未配置或未启用，请先在设置页面配置API密钥');
        return;
      }

      const response = await chatApi.createConversation({
        title: newChatTitle,
        model_id: selectedModel,
      });

      console.log('创建对话响应:', response);

      if (response.success && response.data) {
        const selectedModelInfo = availableModels.find(m => m.model_id === selectedModel);
        
        const newConv: StoreConversation = {
          id: response.data.conversation_id.toString(),
          title: response.data.title,
          messages: [], // 新对话开始为空
          model: selectedModelInfo?.model_name || `模型 ${selectedModel}`,
          modelId: selectedModel,
          createdAt: new Date(response.data.created_at),
          updatedAt: new Date(response.data.updated_at),
          isArchived: response.data.is_archived || false,
        };

        addConversation(newConv);
        setCurrentConversation(newConv);
        setModalVisible(false);
        setNewChatTitle('');
        message.success('对话创建成功');
        
        await fetchConversations();
      } else {
        message.error(response.message || '创建对话失败');
      }
    } catch (error: any) {
      console.error('创建对话失败:', error);
      const errorMsg = error.response?.data?.detail || error.message || '创建对话失败';
      message.error(errorMsg);
    } finally {
      setCreatingConversation(false);
    }
  };

  // 删除对话
  const handleDeleteConversation = async (conversationId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个对话吗？此操作不可恢复。',
      okText: '删除',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await chatApi.deleteConversation?.(parseInt(conversationId));
          if (response?.success) {
            deleteConversation(conversationId);
            message.success('对话删除成功');
            await fetchConversations();
          } else {
            message.error(response?.message || '删除对话失败');
          }
        } catch (error: any) {
          console.error('删除对话失败:', error);
          const errorMsg = error.response?.data?.detail || error.message || '删除对话失败';
          message.error(errorMsg);
        }
      },
    });
  };

  // 如果没有已配置的模型，显示提示
  if (availableModels.length === 0 && !modelsLoading) {
    return (
      <div className={styles.sidebarContainer}>
        <div className={styles.sidebarHeader}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={() => setModalVisible(true)}
            className={styles.newChatButton}
            disabled
          >
            {collapsed ? '' : '新建对话'}
          </Button>
        </div>
        <div style={{ 
          padding: '20px', 
          textAlign: 'center', 
          color: '#d46b08',
          background: '#fff7e6',
          margin: '16px',
          borderRadius: '8px',
          border: '1px solid #ffd591'
        }}>
          <ExclamationCircleOutlined style={{ fontSize: '24px', marginBottom: '12px' }} />
          <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>没有可用的模型</div>
          <div style={{ fontSize: '13px', marginBottom: '12px' }}>
            请先在设置页面配置AI模型的API密钥
          </div>
          <Button
            type="primary"
            size="small"
            onClick={() => window.location.href = '/settings?tab=api'}
          >
            去配置
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.sidebarContainer}>
      <div className={styles.sidebarHeader}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={() => setModalVisible(true)}
          className={styles.newChatButton}
          disabled={availableModels.length === 0}
        >
          {collapsed ? '' : '新建对话'}
        </Button>
      </div>

      {modelsLoading ? (
        <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
          加载模型中...
        </div>
      ) : (
        <Menu
          mode="inline"
          selectedKeys={currentConversation ? [currentConversation.id] : []}
          className={styles.conversationMenu}
          style={{ overflow: 'visible' }}
          overflowedIndicator={null}
          items={conversations.map((conv) => {
            const model = availableModels.find(m => m.model_id === conv.modelId);
            const modelName = model ? model.model_name : `模型 ${conv.modelId}`;
            
            return {
              key: conv.id,
              icon: <MessageOutlined />,
              label: (
                <div 
                  className={styles.conversationItem} 
                  onClick={() => handleSelectConversation(conv)}
                >
                  <div className={styles.conversationTitle}>
                    <span className={styles.titleText}>{conv.title}</span>
                    {conv.modelId && (
                      <Tag 
                        color="blue" 
                        style={{ marginLeft: '8px', fontSize: '10px' }}
                      >
                        {modelName}
                      </Tag>
                    )}
                  </div>
                  <div className={styles.conversationActions}>
                    <ConversationMenu
                      conversation={conv}
                      onUpdate={(updatedConv) => {
                        useChatStore.getState().updateConversation(updatedConv.id, updatedConv);
                      }}
                      onDelete={handleDeleteConversation}
                    />
                  </div>
                </div>
              ),
            };
          })}
        />
      )}

      <Modal
        title="新建对话"
        open={modalVisible}
        onOk={handleCreateConversation}
        onCancel={() => {
          setModalVisible(false);
          setNewChatTitle('');
        }}
        confirmLoading={creatingConversation}
        okText="创建"
        cancelText="取消"
        okButtonProps={{ disabled: availableModels.length === 0 }}
      >
        <div style={{ marginBottom: 16 }}>
          <Input
            placeholder="输入对话标题（如：AI写作助手）"
            value={newChatTitle}
            onChange={(e) => setNewChatTitle(e.target.value)}
            onPressEnter={handleCreateConversation}
            className={styles.modalInput}
            maxLength={50}
          />
        </div>
        <div className={styles.modelSelect}>
          <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
            选择模型：
          </label>
          <Select
            value={selectedModel}
            onChange={(value) => setSelectedModel(value)}
            style={{ width: '100%' }}
            placeholder="选择模型"
            disabled={availableModels.length === 0}
          >
            {availableModels.map((model) => (
              <Option key={model.model_id} value={model.model_id}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <strong>{model.model_name}</strong>
                    <span style={{ marginLeft: '8px', color: '#666', fontSize: '12px' }}>
                      ({model.model_provider || '未知供应商'})
                    </span>
                  </div>
                  {model.is_enabled ? (
                    <Tag color="green">已启用</Tag>
                  ) : (
                    <Tag color="orange">未启用</Tag>
                  )}
                  <Tag color={model.is_configured ? "blue" : "red"}>
                    {model.is_configured ? "已配置" : "未配置"}
                  </Tag>
                </div>
              </Option>
            ))}
          </Select>
          {selectedModel && availableModels.find(m => m.model_id === selectedModel)?.description && (
            <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
              {availableModels.find(m => m.model_id === selectedModel)?.description}
            </div>
          )}
        </div>
        {availableModels.length === 0 && (
          <div style={{ 
            marginTop: '12px', 
            padding: '8px', 
            background: '#fff7e6', 
            border: '1px solid #ffd591',
            borderRadius: '4px',
            fontSize: '12px',
            color: '#d46b08'
          }}>
            <ExclamationCircleOutlined /> 没有可用的模型，请先在设置页面配置API密钥
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Sidebar;
