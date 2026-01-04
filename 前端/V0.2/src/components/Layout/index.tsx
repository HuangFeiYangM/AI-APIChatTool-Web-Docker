import React from 'react';
import { Layout } from 'antd';
import Header from './Header';
import Sider from './Sider';
import Footer from './Footer';
import styles from './Layout.module.css';

const { Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
  showSider?: boolean;
}

const MainLayout: React.FC<MainLayoutProps> = ({ 
  children, 
  showSider = true 
}) => {
  return (
    <Layout className={styles.layout}>
      <Header />
      <Layout>
        {showSider && <Sider />}
        <Layout>
          <Content className={styles.content}>
            {children}
          </Content>
          <Footer />
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
