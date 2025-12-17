// src/pages/SettingsPage/components/ApiConfigPanel.tsx - 最终版
import React, { useState, useEffect } from 'react';
import { 
  Card, Button, Tag, Alert, Spin, message, Modal, Form, Input, Switch, Row, Col
} from 'antd';
import { 
  ReloadOutlined, EditOutlined, KeyOutlined
} from '@ant-design/icons';
import settingsApi from '@/api/settings';

interface SystemModel {
  model_id: number;
  model_name: string;
  model_provider?: string;
  description?: string;
  is_available: boolean;
  max_tokens?: number;
  user_has_config: boolean;
  user_config_enabled: boolean;
  user_has_api_key: boolean;
  user_config_priority?: number;
}

const ApiConfigPanel: React.FC = () => {
  const [models, setModels] = useState<SystemModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingModel, setEditingModel] = useState<SystemModel | null>(null);
  const [editForm] = Form.useForm();

  // 加载数据
  // 修改 loadData 函数，避免调用 getModelConfig
const loadData = async () => {
  try {
    setLoading(true);
    
    // 1. 获取系统模型（包含用户配置状态）
    const systemResponse = await settingsApi.getSystemModelsWithConfig();
    
    if (systemResponse.success && systemResponse.data) {
      let systemModelsData: any[] = [];
      
      // 处理不同的数据结构
      const data = systemResponse.data;
      if (Array.isArray(data)) {
        systemModelsData = data;
      } else if (data && typeof data === 'object' && data.models && Array.isArray(data.models)) {
        systemModelsData = data.models;
      } else if (data && typeof data === 'object') {
        systemModelsData = Object.values(data);
      }
      
      console.log('系统模型数据:', systemModelsData);
      
      // 2. 获取用户所有配置
      const configsResponse = await settingsApi.getUserModelConfigs();
      let userConfigs: any[] = [];
      
      if (configsResponse.success && configsResponse.data) {
        userConfigs = Array.isArray(configsResponse.data) ? configsResponse.data : [];
      }
      
      console.log('用户配置数据:', userConfigs);
      
      // 3. 合并数据（不要调用 getModelConfig）
      const mergedModels = systemModelsData.map((model: any) => {
        // 在用户配置中查找该模型的配置
        const userConfig = userConfigs.find(c => c.model_id === model.model_id);
        const hasConfig = !!userConfig;
        
        return {
          ...model,
          model_name: fixChineseEncoding(model.model_name),
          model_provider: fixChineseEncoding(model.model_provider),
          description: model.description ? fixChineseEncoding(model.description) : undefined,
          user_has_config: hasConfig,
          user_config_enabled: hasConfig ? userConfig.is_enabled : false,
          user_has_api_key: hasConfig,
          user_config_priority: hasConfig ? userConfig.priority : 1,
        };
      });
      
      setModels(mergedModels);
    } else {
      message.error('加载模型失败');
    }
  } catch (error) {
    console.error('加载数据失败:', error);
    message.error('加载数据失败');
  } finally {
    setLoading(false);
  }
};


  useEffect(() => {
    loadData();
  }, []);

  const handleOpenEditModal = (model: SystemModel) => {
    setEditingModel(model);
    editForm.setFieldsValue({
      model_id: model.model_id,
      api_key: model.user_has_api_key ? '********' : '',
      is_enabled: model.user_config_enabled,
      priority: model.user_config_priority || 1,
    });
    setEditModalVisible(true);
  };

  // 在 handleSaveConfig 方法中添加缓存清理逻辑
  const handleSaveConfig = async (values: any) => {
    if (!editingModel) return;
    
    try {
      let response;
      const isNewConfig = !editingModel.user_has_config;
      
      if (isNewConfig) {
        // 创建新配置
        if (!values.api_key || values.api_key.trim() === '' || values.api_key === '********') {
          message.error('首次配置必须提供API密钥');
          return;
        }
        
        response = await settingsApi.createModelConfig({
          model_id: editingModel.model_id,
          api_key: values.api_key,
          is_enabled: values.is_enabled,
          priority: values.priority || 1,
        });
      } else {
        // 更新现有配置
        const updateData: any = {
          model_id: editingModel.model_id,
          is_enabled: values.is_enabled,
          priority: values.priority || 1,
        };
        
        // 只有当用户输入了新密钥且不是占位符时才更新密钥
        if (values.api_key && values.api_key !== '********') {
          updateData.api_key = values.api_key;
        }
        
        response = await settingsApi.updateModelConfig(updateData);
      }
      
      if (response.success) {
        message.success('配置保存成功');
        
        // 关键：清除模型配置服务的缓存
        try {
          // 导入 modelConfigService
          import('@/services/modelConfigService').then(module => {
            const modelConfigService = module.modelConfigService;
            // 清除所有缓存
            modelConfigService.clearCache?.();
            console.log(`已清除模型配置缓存`);
          });
        } catch (cacheError) {
          console.error('清除缓存失败:', cacheError);
        }
        
        setEditModalVisible(false);
        editForm.resetFields();
        await loadData(); // 重新加载数据
      } else {
        message.error(response.message || '保存失败');
      }
    } catch (error: any) {
      console.error('保存配置失败:', error);
      message.error(error.response?.data?.detail || '保存失败');
    }
  };

  const handleEnableModel = async (modelId: number, enabled: boolean) => {
    try {
      const response = enabled 
        ? await settingsApi.enableModelConfig(modelId)
        : await settingsApi.disableModelConfig(modelId);
      
      if (response.success) {
        message.success(`模型已${enabled ? '启用' : '禁用'}`);
        await loadData();
      } else {
        message.error(response.message || '操作失败');
      }
    } catch (error) {
      console.error('更新模型状态失败:', error);
      message.error('操作失败');
    }
  };

  const getProviderColor = (provider?: string) => {
    if (!provider) return '#666';
    const providerLower = provider.toLowerCase();
    const colors: Record<string, string> = {
      'openai': '#10a37f',
      'deepseek': '#1e6bff',
      'baidu': '#2932e1',
      '其他': '#666',
    };
    return colors[providerLower] || colors['其他'];
  };

  const fixChineseEncoding = (text?: string): string => {
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
      result = result.replace(new RegExp(encoded, 'gi'), decoded);
    }
    return result;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>正在加载模型配置...</div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 8, fontSize: 20, fontWeight: 600 }}>API配置管理</h2>
        <p style={{ color: '#666' }}>配置各个AI模型的API密钥和参数</p>
      </div>

      <Alert
        message="配置说明"
        description={
          <div>
            <p>1. <strong>API密钥</strong>：从对应AI平台获取（如DeepSeek平台）</p>
            <p>2. 配置成功后，模型将出现在"已配置模型表"中</p>
            <p>3. 只有已配置并启用的模型才能在聊天中使用</p>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Card
        title="所有模型"
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={loadData}
            loading={loading}
          >
            刷新
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        {models.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            暂无模型数据
          </div>
        ) : (
          <div>
            {models.map((model) => (
              <Card
                key={model.model_id}
                style={{ 
                  marginBottom: 12, 
                  borderLeft: `4px solid ${getProviderColor(model.model_provider)}`,
                  background: model.user_config_enabled ? '#f6ffed' : '#fff'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <strong>{model.model_name}</strong>
                      <Tag color={getProviderColor(model.model_provider)}>
                        {model.model_provider || '其他'}
                      </Tag>
                      {model.user_has_config && (
                        <Tag color={model.user_config_enabled ? 'green' : 'orange'}>
                          {model.user_config_enabled ? '已启用' : '已禁用'}
                        </Tag>
                      )}
                      {/* 关键：显示密钥状态 */}
                      <Tag color={model.user_has_api_key ? 'green' : 'orange'}>
                        {model.user_has_api_key ? '已配置' : '未配置'}
                      </Tag>
                    </div>
                    {model.description && (
                      <div style={{ color: '#666', fontSize: 13 }}>{model.description}</div>
                    )}
                  </div>
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {model.user_has_config && (
                      <Switch
                        checked={model.user_config_enabled}
                        onChange={(checked) => handleEnableModel(model.model_id, checked)}
                        size="small"
                      />
                    )}
                    <Button
                      type={model.user_has_config ? "default" : "primary"}
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => handleOpenEditModal(model)}
                    >
                      {model.user_has_config ? "编辑" : "配置"}
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Card>

      {/* 已配置模型表 */}
      <Card title="已配置模型表">
        <Alert
          message="已配置模型"
          description="以下为您已配置的模型。在聊天页面创建对话时，只能选择已配置并启用的模型。"
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        {models.filter(m => m.user_has_config).length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            暂无已配置的模型，请先配置模型
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>模型</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>供应商</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>配置状态</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>密钥状态</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {models
                  .filter(m => m.user_has_config)
                  .map((model) => (
                    <tr key={model.model_id} style={{ 
                      borderBottom: '1px solid #f0f0f0', 
                      backgroundColor: model.user_config_enabled ? '#f6ffed' : '#fffaf0'
                    }}>
                      <td style={{ padding: '12px 16px' }}>
                        <strong>{model.model_name}</strong>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <Tag color={getProviderColor(model.model_provider)}>
                          {model.model_provider || '其他'}
                        </Tag>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <Tag color={model.user_config_enabled ? 'green' : 'orange'}>
                          {model.user_config_enabled ? '已启用' : '未启用'}
                        </Tag>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        {/* 关键：这里也会正确显示已配置 */}
                        <Tag color={model.user_has_api_key ? 'green' : 'orange'}>
                          {model.user_has_api_key ? '已配置' : '未配置'}
                        </Tag>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <Button
                          type="link"
                          size="small"
                          icon={<EditOutlined />}
                          onClick={() => handleOpenEditModal(model)}
                          style={{ padding: '4px 8px' }}
                        >
                          编辑
                        </Button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* 编辑配置模态框 */}
      <Modal
        title={`配置模型: ${editingModel?.model_name || ''}`}
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingModel(null);
          editForm.resetFields();
        }}
        footer={null}
        width={400}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleSaveConfig}
        >
          <Form.Item name="model_id" hidden>
            <Input />
          </Form.Item>
          
          <Form.Item
            label="API密钥"
            name="api_key"
            rules={[
              {
                validator(_, value) {
                  const isNewConfig = !editingModel?.user_has_config;
                  // 如果是首次配置，API密钥必填
                  if (isNewConfig && (!value || value.trim() === '' || value === '********')) {
                    return Promise.reject(new Error('首次配置必须提供API密钥'));
                  }
                  return Promise.resolve();
                },
              },
            ]}
          >
            <Input.Password
              placeholder={editingModel?.user_has_api_key ? '已配置密钥，留空保持原密钥' : '输入API密钥'}
              prefix={<KeyOutlined />}
            />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="优先级" name="priority">
                <Input
                  type="number"
                  min={1}
                  max={10}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_enabled" valuePropName="checked">
                <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                  <span style={{ marginLeft: 8 }}>启用模型</span>
                </div>
              </Form.Item>
            </Col>
          </Row>
          
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 24 }}>
            <Button
              onClick={() => {
                setEditModalVisible(false);
                setEditingModel(null);
                editForm.resetFields();
              }}
            >
              取消
            </Button>
            <Button
              type="primary"
              htmlType="submit"
            >
              保存配置
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default ApiConfigPanel;
