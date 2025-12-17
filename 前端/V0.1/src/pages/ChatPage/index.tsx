// src/pages/ChatPage/index.tsx
import React, { useState } from 'react';
import { Layout, FloatButton, message } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import ChatArea from './ChatArea';
import Sidebar from './Sidebar';
import styles from './ChatPage.module.css';

const { Header, Content, Sider } = Layout;

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  // 从 localStorage 获取用户信息 - 安全的 JSON 解析
  const userStr = localStorage.getItem('user');
  let user = null;
  
  if (userStr && userStr !== 'undefined') {
    try {
      user = JSON.parse(userStr);
    } catch (error) {
      console.error('解析用户信息失败:', error, '原始字符串:', userStr);
      // 清除无效数据并重定向到登录页
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      message.error('用户信息无效，请重新登录');
      window.location.href = '/login';
      return null;
    }
  }

  if (!user) {
    // 如果用户信息不存在，应该不会进入这个页面（由路由守卫保护）
    // 但为了安全起见，还是重定向到登录页
    console.warn('用户信息不存在，重定向到登录页');
    window.location.href = '/login';
    return null;
  }

  return (
    <Layout className={styles.chatLayout}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={280}
        className={styles.sidebar}
      >
        <Sidebar collapsed={collapsed} />
      </Sider>
      
      <Layout>
        <Header className={styles.header}>
          <div className={styles.headerContent}>
            <h1 className={styles.title}>AI 智能对话</h1>
            <div className={styles.userInfo}>
              <span className={styles.username}>{user.username}</span>
            </div>
          </div>
        </Header>
        
        <Content className={styles.content}>
          <ChatArea />
        </Content>
      </Layout>
      
      <FloatButton.Group shape="circle" style={{ right: 24 }}>
        <FloatButton
          icon={<SettingOutlined />}
          onClick={() => navigate('/settings')}
          tooltip="设置"
        />
        <FloatButton.BackTop visibilityHeight={0} />
      </FloatButton.Group>
    </Layout>
  );
};

export default ChatPage;
