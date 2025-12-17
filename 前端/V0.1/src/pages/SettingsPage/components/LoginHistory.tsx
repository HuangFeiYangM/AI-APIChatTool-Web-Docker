import React, { useState, useEffect } from 'react';
import { Table, Tag, message } from 'antd';
import { UserOutlined, GlobalOutlined, ClockCircleOutlined } from '@ant-design/icons';
import authApi from '@/api/auth';
import styles from '../SettingsPage.module.css';

interface LoginAttempt {
  attempt_id: number;
  username: string;
  ip_address: string;
  user_agent: string;
  is_success: boolean;
  attempt_time: string;
  failure_reason?: string;
}

const LoginHistory: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [loginHistory, setLoginHistory] = useState<LoginAttempt[]>([]);

  // 加载登录历史
  const loadLoginHistory = async () => {
    setLoading(true);
    try {
      // 这里应该调用获取登录历史的API
      // 暂时使用模拟数据
      const mockData: LoginAttempt[] = [
        {
          attempt_id: 1,
          username: 'admin',
          ip_address: '192.168.1.100',
          user_agent: 'Chrome/120.0.0.0',
          is_success: true,
          attempt_time: new Date().toISOString(),
        },
        {
          attempt_id: 2,
          username: 'admin',
          ip_address: '192.168.1.101',
          user_agent: 'Firefox/121.0',
          is_success: false,
          attempt_time: new Date(Date.now() - 3600000).toISOString(),
          failure_reason: '密码错误',
        },
        {
          attempt_id: 3,
          username: 'admin',
          ip_address: '192.168.1.102',
          user_agent: 'Safari/17.2',
          is_success: true,
          attempt_time: new Date(Date.now() - 7200000).toISOString(),
        },
      ];
      setLoginHistory(mockData);
    } catch (error) {
      message.error('加载登录历史失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLoginHistory();
  }, []);

  const columns = [
    {
      title: '时间',
      dataIndex: 'attempt_time',
      key: 'attempt_time',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 150,
    },
    {
      title: '状态',
      dataIndex: 'is_success',
      key: 'is_success',
      width: 100,
      render: (success: boolean) => (
        <Tag color={success ? 'success' : 'error'}>
          {success ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '失败原因',
      dataIndex: 'failure_reason',
      key: 'failure_reason',
      render: (text: string) => text || '-',
    },
    {
      title: '客户端',
      dataIndex: 'user_agent',
      key: 'user_agent',
      render: (text: string) => (
        <span title={text} className={styles.userAgent}>
          {text.length > 30 ? text.substring(0, 30) + '...' : text}
        </span>
      ),
    },
  ];

  return (
    <div className={styles.loginHistory}>
      <div className={styles.sectionHeader}>
        <h3>登录历史</h3>
        <p>查看最近的登录尝试记录</p>
      </div>
      
      <Table
        columns={columns}
        dataSource={loginHistory}
        rowKey="attempt_id"
        loading={loading}
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
      />
    </div>
  );
};

export default LoginHistory;
