// src/store/authStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { FrontendUser } from '@/types/api';

interface AuthState {
  // 状态
  token: string | null;
  user: FrontendUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  initialized: boolean;
  
  // 操作
  login: (token: string, user: FrontendUser) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateUser: (user: Partial<FrontendUser>) => void;  // 添加这个方法
  setInitialized: (initialized: boolean) => void;
  syncFromLocalStorage: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      token: null,
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null,
      initialized: false,
      
      setInitialized: (initialized) => set({ initialized }),
      
      // 登录
      login: (token: string, user: FrontendUser) => {
        console.log('store.login 被调用:', { token, user });
        // 同时更新 localStorage 和 store
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        
        set({
          token,
          user,
          isAuthenticated: true,
          error: null,
          initialized: true,
          loading: false,
        });
      },
      
      logout: () => {
        console.log('store.logout 被调用');
        // 清除 localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          initialized: true,
          loading: false,
        });
      },
      
      setLoading: (loading: boolean) => set({ loading }),
      
      setError: (error: string | null) => set({ error }),
      
      // 更新用户信息
      updateUser: (updatedUser: Partial<FrontendUser>) => {
        const currentState = get();
        if (!currentState.user) return;
        
        const newUser = { ...currentState.user, ...updatedUser };
        
        // 同时更新 localStorage
        localStorage.setItem('user', JSON.stringify(newUser));
        
        set({ user: newUser });
      },
      
      // 从 localStorage 同步状态
      syncFromLocalStorage: () => {
        const token = localStorage.getItem('token');
        const userStr = localStorage.getItem('user');
        
        console.log('syncFromLocalStorage:', { token, userStr });
        
        if (token && userStr) {
          try {
            const user = JSON.parse(userStr);
            set({
              token,
              user,
              isAuthenticated: true,
              loading: false,
            });
          } catch (error) {
            console.error('解析 localStorage 用户信息失败:', error);
            // 清除无效数据
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            set({
              token: null,
              user: null,
              isAuthenticated: false,
              loading: false,
            });
          }
        } else {
          set({
            token: null,
            user: null,
            isAuthenticated: false,
            loading: false,
          });
        }
      },
    }),
    {
      name: 'auth-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        initialized: state.initialized,
      }),
      // 添加：当 store 从持久化存储中恢复时的回调
      onRehydrateStorage: () => {
        return (state) => {
          if (state) {
            console.log('store 从持久化恢复:', state);
            // 确保状态与 localStorage 同步
            setTimeout(() => {
              state.syncFromLocalStorage();
            }, 0);
          }
        };
      },
    }
  )
);
