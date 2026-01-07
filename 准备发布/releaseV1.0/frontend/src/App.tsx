// src/App.tsx
import React, { useEffect, useState } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import ErrorBoundary from '@/components/ErrorBoundary';
import Loading from '@/components/Loading';
import router from './router';
import { useAuthStore } from '@/store/authStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
    },
  },
});

const AppContent: React.FC = () => {
  const { syncFromLocalStorage, setInitialized } = useAuthStore();
  const [appReady, setAppReady] = useState(false);
  
  // ✅ 应用启动时初始化认证状态
  useEffect(() => {
    console.log('App 启动，初始化认证状态');
    
    // 1. 同步 localStorage 到 store
    syncFromLocalStorage();
    
    // 2. 标记 store 为已初始化
    setInitialized(true);
    
    // 3. 标记应用为就绪状态
    setTimeout(() => {
      setAppReady(true);
    }, 100);
    
    // 开发环境日志
    if (process.env.NODE_ENV === 'development') {
      console.log('开发模式：前端运行在 http://localhost:3000');
      console.log('请确保后端运行在 http://localhost:8002');
      
      // 检查 localStorage
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');
      console.log('App 启动时 localStorage 检查:', { token, user });
    }
  }, [syncFromLocalStorage, setInitialized]);
  
  // 如果应用还没就绪，显示加载状态
  if (!appReady) {
    return <Loading fullScreen />;
  }

  return (
    <RouterProvider 
      router={router} 
      fallbackElement={<Loading fullScreen />}
    />
  );
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider locale={zhCN}>
          <AppContent />
        </ConfigProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
