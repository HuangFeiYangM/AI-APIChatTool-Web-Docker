import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import {
  MessageOutlined,
  SettingOutlined,
  UserOutlined,
  TeamOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import styles from './Layout.module.css';

const { Sider: AntSider } = Layout;

const Sider: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  const isAdmin = user?.is_admin === true;

  const menuItems = [
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: '聊天',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    // ... 管理员菜单项 ...
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  // ... 剩余代码保持不变 ...

  return (
    <AntSider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      className={styles.sider}
      width={200}
    >
      <div className={styles.siderHeader}>
        {!collapsed && (
          <div className={styles.siderTitle}>
            <UserOutlined className={styles.siderIcon} />
            <span className={styles.siderText}>导航菜单</span>
          </div>
        )}
      </div>
      
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        onClick={handleMenuClick}
        items={menuItems}
        className={styles.siderMenu}
      />
    </AntSider>
  );
};

export default Sider;
