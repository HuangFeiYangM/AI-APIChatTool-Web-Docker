import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import authApi from '@/api/auth';
import styles from '../SettingsPage.module.css';

const ChangePasswordForm: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const validatePassword = (_: any, value: string) => {
    if (!value) {
      return Promise.reject(new Error('请输入密码'));
    }
    if (value.length < 6) {
      return Promise.reject(new Error('密码至少6个字符'));
    }
    return Promise.resolve();
  };

  const validateConfirmPassword = ({ getFieldValue }: any) => ({
    validator(_: any, value: string) {
      if (!value || getFieldValue('new_password') === value) {
        return Promise.resolve();
      }
      return Promise.reject(new Error('两次输入的密码不一致'));
    },
  });

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const response = await authApi.changePassword({
        current_password: values.current_password,
        new_password: values.new_password,
        confirm_password: values.confirm_password,
      });

      if (response.success) {
        message.success('密码修改成功');
        form.resetFields();
      } else {
        message.error(response.message || '密码修改失败');
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.changePasswordForm}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Form.Item
          name="current_password"
          label="当前密码"
          rules={[{ required: true, message: '请输入当前密码' }]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请输入当前密码"
          />
        </Form.Item>

        <Form.Item
          name="new_password"
          label="新密码"
          rules={[
            { required: true, validator: validatePassword },
          ]}
          hasFeedback
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请输入新密码（至少6个字符）"
          />
        </Form.Item>

        <Form.Item
          name="confirm_password"
          label="确认新密码"
          dependencies={['new_password']}
          rules={[
            { required: true, message: '请确认新密码' },
            validateConfirmPassword,
          ]}
          hasFeedback
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请再次输入新密码"
          />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            修改密码
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default ChangePasswordForm;
