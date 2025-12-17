import React, { useState } from 'react';
import { Tabs, Card } from 'antd';  // 移除 message 导入
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import styles from './LoginPage.module.css';

const { TabPane } = Tabs;

const LoginPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('login');

  const handleTabChange = (key: string) => {
    setActiveTab(key);
  };

  return (
    <div className={styles.loginContainer}>
      <Card className={styles.loginCard}>
        <div className={styles.logoSection}>
          <h1 className={styles.title}>AI 聊天系统</h1>
          <p className={styles.subtitle}>多模型智能对话平台</p>
        </div>
        
        <Tabs activeKey={activeTab} onChange={handleTabChange} centered>
          <TabPane tab="登录" key="login">
            <LoginForm onTabChange={handleTabChange} />
          </TabPane>
          <TabPane tab="注册" key="register">
            <RegisterForm onTabChange={handleTabChange} />
          </TabPane>
        </Tabs>
      </Card>
      
      <div className={styles.footer}>
        <p>© 2024 AI聊天系统. 技术支持与反馈请联系管理员</p>
      </div>
    </div>
  );
};

export default LoginPage;
