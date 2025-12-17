import React, { useState } from 'react';
import { Form, Input, Button, Checkbox, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import styles from './LoginPage.module.css';

interface LoginFormProps {
  onTabChange?: (key: string) => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onTabChange }) => {
  const [loading, setLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const { login } = useAuth();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const result = await login(values.username, values.password);
      if (result.success) {
        // 登录成功消息已经在 useAuth 中显示
        // navigate 也在 useAuth 中处理
      } else {
        // 错误消息已经在 useAuth 中显示
      }
    } catch (error) {
      console.error('登录异常:', error);
      message.error('登录失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.loginForm}>
      <h2 className={styles.formTitle}>登录</h2>
      <p className={styles.formSubtitle}>欢迎回来，请登录您的账户</p>
      
      <Form
        name="login"
        initialValues={{ remember: true }}
        onFinish={onFinish}
        autoComplete="off"
        layout="vertical"
        className={styles.form}
      >
        <Form.Item
          name="username"
          rules={[
            { required: true, message: '请输入用户名!' },
            { min: 3, message: '用户名至少3个字符' },
            { max: 20, message: '用户名最多20个字符' },
          ]}
        >
          <Input 
            prefix={<UserOutlined />} 
            placeholder="用户名" 
            size="large"
            autoComplete="username"
          />
        </Form.Item>

        <Form.Item
          name="password"
          rules={[
            { required: true, message: '请输入密码!' },
            { min: 6, message: '密码至少6个字符' },
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="密码"
            size="large"
            autoComplete="current-password"
          />
        </Form.Item>

        <Form.Item>
          <div className={styles.formOptions}>
            <Checkbox 
              checked={rememberMe} 
              onChange={(e) => setRememberMe(e.target.checked)}
            >
              记住我
            </Checkbox>
            <a href="#" className={styles.forgotPassword}>
              忘记密码？
            </a>
          </div>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            size="large"
            block
            className={styles.loginButton}
          >
            登录
          </Button>
        </Form.Item>

        <div className={styles.registerLink}>
          没有账户？ <a href="#" onClick={(e) => {
            e.preventDefault();
            if (onTabChange) {
              onTabChange('register');
            }
          }}>立即注册</a>
        </div>
      </Form>
    </div>
  );
};

export default LoginForm;
