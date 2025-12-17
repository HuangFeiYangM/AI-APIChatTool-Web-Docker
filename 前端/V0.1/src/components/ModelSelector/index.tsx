import React, { useState, useEffect } from 'react';
import { Select, Alert, Tag, Button, Space, Spin } from 'antd';
import { SettingOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import settingsApi from '@/api/settings';

const { Option } = Select;

interface ModelSelectorProps {
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
}

interface ConfiguredModel {
  model_id: number;
  model_name: string;
  model_provider?: string;
  is_enabled: boolean;
  priority: number;
  has_api_key?: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ value, onChange, disabled }) => {
  const navigate = useNavigate();
  const [configuredModels, setConfiguredModels] = useState<ConfiguredModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasEnabledModels, setHasEnabledModels] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载已配置并启用的模型
  const loadConfiguredModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await settingsApi.getUserModelConfigs();
      if (response.success && response.data) {
        // 过滤出已启用且已配置API密钥的模型
        const enabledModels = response.data
          .filter((config: any) => {
            const isEnabled = config.is_enabled === true;
            const hasApiKey = config.has_api_key === true || (config.api_key && config.api_key.length > 0);
            return isEnabled && hasApiKey;
          })
          .map((config: any) => ({
            model_id: config.model_id,
            model_name: config.model_name,
            model_provider: config.model_provider,
            is_enabled: config.is_enabled,
            has_api_key: config.has_api_key || (config.api_key && config.api_key.length > 0),
            priority: config.priority,
          }));
        
        setConfiguredModels(enabledModels);
        setHasEnabledModels(enabledModels.length > 0);
        
        if (enabledModels.length === 0) {
          setError('您还没有配置任何可用的AI模型');
        }
      } else {
        setError('加载模型配置失败');
      }
    } catch (error) {
      console.error('加载模型配置失败:', error);
      setError('加载模型配置失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfiguredModels();
  }, []);

  const fixChineseEncoding = (text?: string): string => {
    if (!text) return '';
    const encodingMap: Record<string, string> = {
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

  const getProviderColor = (provider?: string) => {
    if (!provider) return '#666';
    const providerLower = provider.toLowerCase();
    const colors: Record<string, string> = {
      'openai': '#10a37f',
      'deepseek': '#1e6bff',
      'anthropic': '#d4a106',
      'google': '#4285f4',
      'baidu': '#2932e1',
      '其他': '#666',
    };
    return colors[providerLower] || colors['其他'];
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <Spin />
        <div style={{ marginTop: 8, color: '#666' }}>正在加载可用模型...</div>
      </div>
    );
  }

  if (error || !hasEnabledModels) {
    return (
      <div>
        <Alert
          message="无可用模型"
          description={
            <div>
              <p>您还没有配置任何可用的AI模型。</p>
              <p>请在设置页面配置并启用至少一个模型后才能创建对话。</p>
              <div style={{ marginTop: 16 }}>
                <Button
                  type="primary"
                  icon={<SettingOutlined />}
                  onClick={() => navigate('/settings?tab=api')}
                  size="middle"
                >
                  前往配置模型
                </Button>
                <Button
                  style={{ marginLeft: 8 }}
                  icon={<ReloadOutlined />}
                  onClick={loadConfiguredModels}
                  loading={loading}
                >
                  重新加载
                </Button>
              </div>
            </div>
          }
          type="warning"
          showIcon
        />
      </div>
    );
  }

  return (
    <div>
      <Alert
        message="模型选择"
        description="请选择已配置并启用的模型开始对话"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Space direction="vertical" style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontWeight: 500 }}>选择模型：</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={loadConfiguredModels}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              size="small"
              icon={<SettingOutlined />}
              onClick={() => navigate('/settings?tab=api')}
            >
              管理模型
            </Button>
          </div>
        </div>
        
        <Select
          placeholder="请选择AI模型"
          value={value}
          onChange={onChange}
          style={{ width: '100%' }}
          disabled={disabled || loading}
          loading={loading}
          dropdownRender={(menu) => (
            <>
              {menu}
              <div style={{ 
                padding: '8px 12px', 
                borderTop: '1px solid #f0f0f0',
                fontSize: 12,
                color: '#666',
                backgroundColor: '#fafafa'
              }}>
                <div style={{ marginBottom: 4, display: 'flex', justifyContent: 'space-between' }}>
                  <span>已配置 {configuredModels.length} 个模型（已启用）</span>
                  <Tag color="green">可用</Tag>
                </div>
                <Button
                  type="link"
                  size="small"
                  icon={<SettingOutlined />}
                  onClick={() => navigate('/settings?tab=api')}
                  style={{ padding: 0, fontSize: 12 }}
                >
                  前往设置配置更多模型
                </Button>
              </div>
            </>
          )}
        >
          {configuredModels
            .sort((a, b) => a.priority - b.priority)
            .map((model) => (
              <Option key={model.model_id} value={model.model_name}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                    <div style={{ 
                      width: 8, 
                      height: 8, 
                      borderRadius: '50%', 
                      backgroundColor: getProviderColor(model.model_provider),
                    }} />
                    <span style={{ fontWeight: 500 }}>{fixChineseEncoding(model.model_name)}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Tag color={getProviderColor(model.model_provider)} style={{ fontSize: 10, margin: 0 }}>
                      {model.model_provider?.toUpperCase() || '其他'}
                    </Tag>
                    <Tag color="green" style={{ fontSize: 10, margin: 0 }}>已启用</Tag>
                  </div>
                </div>
              </Option>
            ))}
        </Select>
        
        <div style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
          <div>💡 提示：只有已在设置页面配置并启用的模型才会显示在此处</div>
        </div>
      </Space>
    </div>
  );
};

export default ModelSelector;
