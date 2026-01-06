import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { UserOutlined, MailOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';
import authApi from '@/api/auth';
import styles from '../SettingsPage.module.css';

const UserInfoForm: React.FC<{ onSuccess?: () => void }> = ({ onSuccess }) => {
  const { user, updateUser } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  React.useEffect(() => {
    if (user) {
      form.setFieldsValue({
        username: user.username,
        email: user.email,
      });
    }
  }, [user, form]);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      // 这里应该调用更新用户信息的API
      // 暂时模拟成功
      message.success('用户信息更新成功');
      updateUser(values);
      if (onSuccess) onSuccess();
    } catch (error) {
      message.error('更新用户信息失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.userInfoForm}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          username: user?.username,
          email: user?.email,
        }}
      >
        <Form.Item
          name="username"
          label="用户名"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, message: '用户名至少3个字符' },
            { max: 20, message: '用户名最多20个字符' },
          ]}
        >
          <Input prefix={<UserOutlined />} placeholder="请输入用户名" />
        </Form.Item>

        <Form.Item
          name="email"
          label="邮箱"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' },
          ]}
        >
          <Input prefix={<MailOutlined />} placeholder="请输入邮箱" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            保存修改
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default UserInfoForm;
