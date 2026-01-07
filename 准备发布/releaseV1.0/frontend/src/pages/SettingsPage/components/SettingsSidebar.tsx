// src/pages/SettingsPage/components/SettingsSidebar.tsx
import React from 'react';
import { Menu } from 'antd';
import {
  ApiOutlined,
  TeamOutlined,
  DashboardOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import styles from '../SettingsPage.module.css';

interface SettingsSidebarProps {
  activeKey: string;
  onSelect: (key: string) => void;
  isAdmin: boolean;
}

const SettingsSidebar: React.FC<SettingsSidebarProps> = ({ activeKey, onSelect, isAdmin }) => {
  const menuItems = [
    {
      key: 'general',
      icon: <SettingOutlined />,
      label: '通用设置',
    },
    {
      key: 'api',
      icon: <ApiOutlined />,
      label: 'API配置',
    },
    ...(isAdmin ? [
      {
        key: 'users',
        icon: <TeamOutlined />,
        label: '用户管理',
      },
      {
        key: 'stats',
        icon: <DashboardOutlined />,
        label: '系统统计',
      },
    ] : []),
  ];

  return (
    <div className={styles.sidebar}>
      <div className={styles.sidebarHeader}>
        <h3 className={styles.sidebarTitle}>设置</h3>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[activeKey]}
        onClick={(e) => onSelect(e.key)}
        items={menuItems}
        className={styles.settingsMenu}
      />
    </div>
  );
};

export default SettingsSidebar;
