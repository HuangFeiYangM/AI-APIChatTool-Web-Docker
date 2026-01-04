import React from 'react';
import { Layout, Space, Typography } from 'antd';
import { HeartOutlined } from '@ant-design/icons';
import styles from './Layout.module.css';

const { Footer: AntFooter } = Layout;
const { Text, Link } = Typography;

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <AntFooter className={styles.footer}>
      <Space direction="vertical" size="small" align="center">
        <Text type="secondary">
          © {currentYear} AI Chat System
        </Text>
        <Space size="middle">
          <Link href="#" target="_blank">用户协议</Link>
          <Link href="#" target="_blank">隐私政策</Link>
          <Link href="#" target="_blank">联系我们</Link>
        </Space>
        <Text type="secondary">
          Made with <HeartOutlined style={{ color: '#ff4d4f', margin: '0 4px' }} /> by AI Chat Team
        </Text>
      </Space>
    </AntFooter>
  );
};

export default Footer;
