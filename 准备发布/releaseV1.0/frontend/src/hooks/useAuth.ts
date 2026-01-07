// src/hooks/useAuth.ts
import { useState } from 'react';
import { message } from 'antd';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { ApiResponse, AuthResponseData, UserInfoResponse, FrontendUser } from '@/types/api';

export const useAuth = () => {
  const { login: storeLogin, logout: storeLogout, setLoading: setStoreLoading } = useAuthStore();
  const [loading, setLoading] = useState(false);

  // 转换用户信息为前端格式
  const convertToFrontendUser = (userInfo: UserInfoResponse): FrontendUser => {
    return {
      id: userInfo.user_id,
      user_id: userInfo.user_id,
      username: userInfo.username || '用户',
      email: userInfo.email,
      is_active: userInfo.is_active !== undefined ? userInfo.is_active : true,
      is_locked: userInfo.is_locked !== undefined ? userInfo.is_locked : false,
      role: userInfo.is_active ? (userInfo.is_locked ? 'locked' : 'user') : 'inactive',
      created_at: userInfo.created_at || new Date().toISOString(),
      updated_at: userInfo.created_at || new Date().toISOString(),
      last_login_at: userInfo.last_login_at,
    };
  };

  const login = async (username: string, password: string): Promise<ApiResponse<AuthResponseData>> => {
    setStoreLoading(true);
    setLoading(true);
    
    try {
      console.log('🚀 开始登录请求:', { username });
      const response = await authApi.login({ username, password });
      
      console.log('📥 登录响应:', response);
      
      if (response.success && response.data) {
        const { access_token, user_id, username: respUsername, email } = response.data;
        
        console.log('✅ 登录成功，获取到token和用户ID:', { 
          hasAccessToken: !!access_token,
          user_id, 
          username: respUsername,
          email
        });
        
        // 1. 先存储token
        localStorage.setItem('token', access_token);
        
        // 2. 获取完整的用户信息
        try {
          console.log('🔄 正在获取完整的用户信息...');
          const userResponse = await authApi.getCurrentUser();
          
          if (userResponse.success && userResponse.data) {
            const userInfo = userResponse.data;
            console.log('👤 获取到完整的用户信息:', userInfo);
            
            // 转换为前端用户格式
            const frontendUser = convertToFrontendUser(userInfo);
            console.log('🔄 转换后的前端用户:', frontendUser);
            
            // 3. 存储用户信息
            localStorage.setItem('user', JSON.stringify(frontendUser));
            
            // 4. 更新store状态
            storeLogin(access_token, frontendUser);
            
            message.success(response.message || '登录成功');
            
            // 5. 跳转到聊天页面
            setTimeout(() => {
              window.location.href = '/chat';
            }, 300);
            
            return response;
          } else {
            throw new Error('获取用户信息失败');
          }
        } catch (userInfoError) {
          console.warn('⚠️ 获取完整用户信息失败，使用登录返回的基本信息:', userInfoError);
          
          // 使用登录返回的基本信息创建用户对象
          const basicUser: FrontendUser = {
            id: user_id,
            user_id,
            username: respUsername || username,
            email: email,
            is_active: true,
            is_locked: false,
            role: 'user',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          
          localStorage.setItem('user', JSON.stringify(basicUser));
          storeLogin(access_token, basicUser);
          
          message.success(response.message || '登录成功');
          
          setTimeout(() => {
            window.location.href = '/chat';
          }, 300);
          
          return response;
        }
      } else {
        console.error('❌ 登录失败响应:', response);
        const errorMsg = response.message || response.error || '登录失败';
        message.error(typeof errorMsg === 'string' ? errorMsg : '登录失败');
        setStoreLoading(false);
        return {
          success: false,
          error: errorMsg
        };
      }
    } catch (error: any) {
      console.error('💥 登录异常:', error);
      console.error('异常详情:', error);
      
      const errorMsg = error?.error || error?.message || '登录失败，请稍后重试';
      message.error(typeof errorMsg === 'string' ? errorMsg : '登录失败');
      setStoreLoading(false);
      return {
        success: false,
        error: errorMsg
      };
    } finally {
      setLoading(false);
    }
  };

  const register = async (username: string, email: string, password: string, confirmPassword?: string): Promise<ApiResponse<AuthResponseData>> => {
    setStoreLoading(true);
    setLoading(true);
    
    try {
      console.log('🚀 开始注册请求:', { username, email });
      const response = await authApi.register({ 
        username, 
        email, 
        password,
        confirm_password: confirmPassword || password
      });
      
      console.log('📥 注册响应:', response);
      
      if (response.success && response.data) {
        const { access_token, user_id, username: respUsername, email: respEmail } = response.data;
        
        console.log('✅ 注册成功，获取到token和用户ID:', { 
          hasAccessToken: !!access_token,
          user_id, 
          username: respUsername,
          email: respEmail
        });
        
        // 1. 先存储token
        localStorage.setItem('token', access_token);
        
        // 2. 获取完整的用户信息
        try {
          console.log('🔄 正在获取完整的用户信息...');
          const userResponse = await authApi.getCurrentUser();
          
          if (userResponse.success && userResponse.data) {
            const userInfo = userResponse.data;
            console.log('👤 获取到完整的用户信息:', userInfo);
            
            // 转换为前端用户格式
            const frontendUser = convertToFrontendUser(userInfo);
            console.log('🔄 转换后的前端用户:', frontendUser);
            
            // 3. 存储用户信息
            localStorage.setItem('user', JSON.stringify(frontendUser));
            
            // 4. 更新store状态
            storeLogin(access_token, frontendUser);
            
            message.success(response.message || '注册成功');
            
            // 5. 跳转到聊天页面
            setTimeout(() => {
              window.location.href = '/chat';
            }, 300);
            
            return response;
          } else {
            throw new Error('获取用户信息失败');
          }
        } catch (userInfoError) {
          console.warn('⚠️ 获取完整用户信息失败，使用注册返回的基本信息:', userInfoError);
          
          // 使用注册返回的基本信息创建用户对象
          const basicUser: FrontendUser = {
            id: user_id,
            user_id,
            username: respUsername || username,
            email: respEmail || email,
            is_active: true,
            is_locked: false,
            role: 'user',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          
          localStorage.setItem('user', JSON.stringify(basicUser));
          storeLogin(access_token, basicUser);
          
          message.success(response.message || '注册成功');
          
          setTimeout(() => {
            window.location.href = '/chat';
          }, 300);
          
          return response;
        }
      } else {
        console.error('❌ 注册失败响应:', response);
        const errorMsg = response.message || response.error || '注册失败';
        message.error(typeof errorMsg === 'string' ? errorMsg : '注册失败');
        setStoreLoading(false);
        return {
          success: false,
          error: errorMsg
        };
      }
    } catch (error: any) {
      console.error('💥 注册异常:', error);
      setStoreLoading(false);
      
      // 处理 422 验证错误
      if (error.status === 422) {
        const detail = error.data?.detail;
        if (Array.isArray(detail)) {
          detail.forEach((err: any) => {
            message.error(`${err.loc?.join('.')}: ${err.msg}`);
          });
        } else if (typeof detail === 'string') {
          message.error(detail);
        } else {
          message.error('数据验证失败，请检查输入');
        }
      } else {
        const errorMsg = error?.error || error?.message || '注册失败，请稍后重试';
        message.error(typeof errorMsg === 'string' ? errorMsg : '注册失败');
      }
      
      return {
        success: false,
        error: '注册失败',
        status: error.status
      };
    } finally {
      setLoading(false);
    }
  };

  // 在现有的 logout 函数中，添加更可靠的跳转逻辑
  const logout = async () => {
    try {
      console.log('开始执行登出流程...');
      // 调用后端登出接口
      await authApi.logout();
    } catch (error) {
      console.error('登出API调用异常（可能token已过期）:', error);
      // 即使后端登出失败，仍然清除本地状态
    } finally {
      // 1. 清除 store 状态
      storeLogout();
      
      // 2. 清除 localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // 3. 显示成功消息
      message.success('已退出登录');
      
      // 4. 强制刷新页面并跳转到登录页
      // 使用 window.location.replace 确保浏览器历史记录不会包含之前的页面
      setTimeout(() => {
        window.location.replace('/login');
      }, 300);
    }
  };

  return {
    login,
    register,
    logout,
    loading,
  };
};
