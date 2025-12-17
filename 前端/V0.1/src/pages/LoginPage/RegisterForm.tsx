import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import styles from './LoginPage.module.css';

interface RegisterFormProps {
  onTabChange?: (key: string) => void;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onTabChange }) => {
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const onFinish = async (values: { 
    username: string; 
    email: string; 
    password: string;
    confirm_password: string;
  }) => {
    if (values.password !== values.confirm_password) {
      message.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      const result = await register(values.username, values.email, values.password, values.confirm_password);
      if (result.success) {
        // 注册成功消息已经在 useAuth 中显示
        // navigate 也在 useAuth 中处理
      } else {
        // 错误消息已经在 useAuth 中显示
      }
    } catch (error) {
      console.error('注册异常:', error);
      message.error('注册失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.registerForm}>
      <h2 className={styles.formTitle}>注册新账户</h2>
      <p className={styles.formSubtitle}>创建您的账户，开始使用AI助手</p>
      
      <Form
        name="register"
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
            { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字和下划线' }
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
          name="email"
          rules={[
            { required: true, message: '请输入邮箱!' },
            { type: 'email', message: '请输入有效的邮箱地址' }
          ]}
        >
          <Input 
            prefix={<MailOutlined />} 
            placeholder="邮箱" 
            size="large"
            autoComplete="email"
          />
        </Form.Item>

        <Form.Item
          name="password"
          rules={[
            { required: true, message: '请输入密码!' },
            { min: 6, message: '密码至少6个字符' },
            { pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{6,}$/, message: '密码必须包含字母和数字' }
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="密码"
            size="large"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item
          name="confirm_password"
          rules={[
            { required: true, message: '请确认密码!' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="确认密码"
            size="large"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item>
          <div className={styles.formTerms}>
            点击"注册"即表示您同意我们的
            <a href="#">服务条款</a>和<a href="#">隐私政策</a>
          </div>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            size="large"
            block
            className={styles.registerButton}
          >
            注册
          </Button>
        </Form.Item>

        <div className={styles.loginLink}>
          已有账户？ <a href="#" onClick={(e) => {
            e.preventDefault();
            if (onTabChange) {
              onTabChange('login');
            }
          }}>立即登录</a>
        </div>
      </Form>
    </div>
  );
};

export default RegisterForm;
