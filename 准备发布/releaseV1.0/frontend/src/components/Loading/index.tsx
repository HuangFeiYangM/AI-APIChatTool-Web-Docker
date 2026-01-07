import React from 'react';
import { Spin, Space } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

interface LoadingProps {
  fullScreen?: boolean;
  text?: string;
  size?: 'small' | 'default' | 'large';
}

const Loading: React.FC<LoadingProps> = ({ 
  fullScreen = false, 
  text = '加载中...', 
  size = 'default' 
}) => {
  const antIcon = <LoadingOutlined style={{ fontSize: 24 }} spin />;
  
  const content = (
    <Space direction="vertical" align="center">
      <Spin indicator={antIcon} size={size} />
      {text && <span style={{ color: '#666', marginTop: 8 }}>{text}</span>}
    </Space>
  );
  
  if (fullScreen) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        width: '100vw',
        position: 'fixed',
        top: 0,
        left: 0,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        zIndex: 9999,
      }}>
        {content}
      </div>
    );
  }
  
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: 40,
    }}>
      {content}
    </div>
  );
};

export default Loading;
