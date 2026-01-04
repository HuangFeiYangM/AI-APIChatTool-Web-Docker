import React, { useState, useEffect } from 'react';
import { Layout, Card, Button, Typography, Space, Modal } from 'antd';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftOutlined, LogoutOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';
import { useAuth } from '@/hooks/useAuth'; // 添加导入
import SettingsSidebar from './components/SettingsSidebar';
import ApiConfigPanel from './components/ApiConfigPanel';
import GeneralSettingsPanel from './components/GeneralSettingsPanel';
import UserManagementPanel from './components/UserManagementPanel';
import SystemStatsPanel from './components/SystemStatsPanel';
import styles from './SettingsPage.module.css';

const { Content, Sider } = Layout;
const { Title, Text } = Typography;
const { confirm } = Modal;

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, updateUser } = useAuthStore();
  const { logout } = useAuth(); // 添加 useAuth hook
  const [activeTab, setActiveTab] = useState('general');
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    // 检查用户角色是否为管理员
    setIsAdmin(user.username === 'admin');
  }, [user, navigate]);

  // 添加退出登录确认函数
  const handleLogout = () => {
    confirm({
      title: '确认退出登录',
      icon: <ExclamationCircleOutlined />,
      content: '确定要退出当前账号吗？',
      okText: '退出登录',
      cancelText: '取消',
      okType: 'danger',
      onOk() {
        logout(); // 调用 useAuth 的 logout 方法
      },
    });
  };

  const handleUpdateUser = async (updates: Partial<any>): Promise<void> => {
    try {
      if (updateUser) {
        updateUser(updates);
      }
      console.log('用户信息已更新（前端）:', updates);
    } catch (error) {
      console.error('更新用户信息失败:', error);
      throw error;
    }
  };

  const handleTabChange = (key: string) => {
    setActiveTab(key);
  };

  const renderContent = () => {
    if (!user) {
      return (
        <Card>
          <p>用户信息加载中...</p>
        </Card>
      );
    }

    switch (activeTab) {
      case 'general':
        return <GeneralSettingsPanel user={user} onUpdateUser={handleUpdateUser} />;
      case 'api':
        return <ApiConfigPanel />;
      case 'users':
        return isAdmin ? <UserManagementPanel /> : (
          <Card>
            <p>需要管理员权限访问用户管理功能</p>
          </Card>
        );
      case 'stats':
        return isAdmin ? <SystemStatsPanel /> : (
          <Card>
            <p>需要管理员权限访问系统统计功能</p>
          </Card>
        );
      default:
        return <GeneralSettingsPanel user={user} onUpdateUser={handleUpdateUser} />;
    }
  };

  const getPageTitle = () => {
    switch (activeTab) {
      case 'general': return '通用设置';
      case 'api': return 'API配置';
      case 'users': return '用户管理';
      case 'stats': return '系统统计';
      default: return '设置';
    }
  };

  if (!user) {
    return null;
  }

  return (
    <Layout className={styles.settingsLayout} style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Sider 
        width={250} 
        className={styles.sider}
        style={{ 
          background: '#fff',
          borderRight: '1px solid #e8e8e8',
          boxShadow: '2px 0 8px rgba(0,0,0,0.05)'
        }}
      >
        <div style={{ padding: '24px 0' }}>
          <div style={{ padding: '0 24px', marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>设置中心</h3>
            <p style={{ margin: '8px 0 0', color: '#666', fontSize: 12 }}>
              用户: {user.username}
            </p>
          </div>
          <SettingsSidebar activeKey={activeTab} onSelect={handleTabChange} isAdmin={isAdmin} />
        </div>
      </Sider>
      
      <Layout>
        <Content className={styles.content} style={{ padding: 0 }}>
          <div style={{ 
            background: '#fff', 
            margin: 24, 
            borderRadius: 8,
            minHeight: 'calc(100vh - 48px)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <div style={{ 
              padding: '16px 24px',
              borderBottom: '1px solid #f0f0f0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <Space>
                <Button 
                  icon={<ArrowLeftOutlined />} 
                  onClick={() => navigate('/chat')}
                  style={{ marginRight: 16 }}
                />
                <Title level={4} style={{ margin: 0 }}>{getPageTitle()}</Title>
              </Space>
              
              <Space>
                {/* 返回聊天按钮 */}
                <Button 
                  icon={<ArrowLeftOutlined />} 
                  onClick={() => navigate('/chat')}
                >
                  返回聊天
                </Button>
                {/* 添加退出登录按钮 */}
                <Button 
                  danger
                  icon={<LogoutOutlined />}
                  onClick={handleLogout}
                >
                  退出登录
                </Button>
              </Space>
            </div>
            
            <div style={{ padding: 24 }}>
              {renderContent()}
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default SettingsPage;
