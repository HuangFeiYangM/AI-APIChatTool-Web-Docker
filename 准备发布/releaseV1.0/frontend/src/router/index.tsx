// src/router/index.tsx
import React, { Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '@/store/authStore';

// 加载组件
const LoadingFallback = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    <Spin size="large" />
  </div>
);

// 懒加载页面组件
const LoginPage = React.lazy(() => import('@/pages/LoginPage'));
const ChatPage = React.lazy(() => import('@/pages/ChatPage'));
const SettingsPage = React.lazy(() => import('@/pages/SettingsPage'));

// ✅ 修复：使用 Zustand store 状态的路由守卫
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, isAuthenticated, loading } = useAuthStore();
  
  console.log('ProtectedRoute 检查:', { token, isAuthenticated, loading });
  
  // 如果还在加载，显示加载状态
  if (loading) {
    return <LoadingFallback />;
  }
  
  // 如果没有 token 或未认证，跳转到登录页
  if (!token || !isAuthenticated) {
    console.log('ProtectedRoute: 未认证，跳转到登录页');
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, isAuthenticated, loading } = useAuthStore();
  
  console.log('PublicRoute 检查:', { token, isAuthenticated, loading });
  
  // 如果还在加载，显示加载状态
  if (loading) {
    return <LoadingFallback />;
  }
  
  // 如果有 token 且已认证，跳转到聊天页
  if (token && isAuthenticated) {
    console.log('PublicRoute: 已认证，跳转到聊天页');
    return <Navigate to="/chat" replace />;
  }
  
  return <>{children}</>;
};

// 路由配置
const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Navigate to="/login" replace />
      </Suspense>
    ),
  },
  {
    path: '/login',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      </Suspense>
    ),
  },
  {
    path: '/chat',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <ProtectedRoute>
          <ChatPage />
        </ProtectedRoute>
      </Suspense>
    ),
  },
  {
    path: '/settings',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <ProtectedRoute>
          <SettingsPage />
        </ProtectedRoute>
      </Suspense>
    ),
  },
  {
    path: '*',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Navigate to="/login" replace />
      </Suspense>
    ),
  },
]);

export default router;
