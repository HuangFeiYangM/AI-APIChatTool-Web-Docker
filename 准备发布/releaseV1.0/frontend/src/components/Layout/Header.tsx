import React from 'react';
import { Layout, Avatar, Dropdown, Menu, Space, Typography } from 'antd';
import { UserOutlined, LogoutOutlined, SettingOutlined } from '@ant-design/icons';
// 删除 useNavigate 导入，因为 useAuth 的 logout 会处理重定向
import { useAuthStore } from '@/store/authStore';
import { useAuth } from '@/hooks/useAuth'; // 导入 useAuth hook
import styles from './Layout.module.css';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

const Header: React.FC = () => {
  const { user } = useAuthStore();
  const { logout } = useAuth(); // 使用 useAuth 的 logout 方法

  const handleMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'settings':
        // 设置页面的跳转已经在 Sider.tsx 中处理
        // 这里不需要处理，或者可以跳转到设置页面
        break;
      case 'logout':
        logout(); // 调用 useAuth 的 logout 方法
        break;
    }
  };

  const menu = (
    <Menu onClick={handleMenuClick}>
      <Menu.Item key="settings">
        <Space>
          <SettingOutlined />
          <span>设置</span>
        </Space>
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" danger>
        <Space>
          <LogoutOutlined />
          <span>退出登录</span>
        </Space>
      </Menu.Item>
    </Menu>
  );

  return (
    <AntHeader className={styles.header}>
      <div className={styles.logo}>
        <h1 className={styles.logoText}>AI Chat</h1>
      </div>
      
      <div className={styles.rightSection}>
        {user && (
          <Dropdown overlay={menu} placement="bottomRight" arrow>
            <div className={styles.userInfo}>
              <Avatar 
                icon={<UserOutlined />}
                className={styles.avatar}
              />
              <div className={styles.userDetails}>
                <Text strong className={styles.username}>
                  {user.username}
                </Text>
                <Text type="secondary" className={styles.userEmail}>
                  {user.email}
                </Text>
              </div>
            </div>
          </Dropdown>
        )}
      </div>
    </AntHeader>
  );
};

export default Header;
