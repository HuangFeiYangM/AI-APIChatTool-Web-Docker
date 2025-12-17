import React, { useState } from 'react';
import { Tabs, Card, Row, Col, Typography } from 'antd';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import styles from './LoginPage.module.css';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('login');

  const handleTabChange = (key: string) => {
    setActiveTab(key);
  };

  const tabItems = [
    {
      key: 'login',
      label: '登录',
      children: <LoginForm />,
    },
    {
      key: 'register',
      label: '注册',
      children: <RegisterForm />,
    },
  ];

  return (
    <div className={styles.loginPage}>
      <Row justify="center" align="middle" className={styles.loginContainer}>
        <Col xs={24} sm={20} md={16} lg={12} xl={8}>
          <div className={styles.loginHeader}>
            <Title level={2} className={styles.appTitle}>AI助手平台</Title>
            <Text type="secondary" className={styles.appDescription}>
              与最先进的AI模型进行智能对话
            </Text>
          </div>
          
          <Card className={styles.loginCard}>
            <Tabs 
              activeKey={activeTab} 
              onChange={handleTabChange} 
              items={tabItems}
              centered
              className={styles.loginTabs}
            />
          </Card>
          
          <div className={styles.loginFooter}>
            <Text type="secondary">
              支持多模型，智能对话，安全可靠
            </Text>
            <div className={styles.features}>
              <Text type="secondary">• GPT系列 • Claude • 文心一言 • 通义千问</Text>
            </div>
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default LoginPage;
