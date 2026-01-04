// src/hooks/useSettings.ts - 修复版
import { useState, useCallback } from 'react';
import { message } from 'antd';
import settingsApi from '@/api/settings';
import { ModelConfig, SystemModel } from '@/types/settings';

export const useSettings = () => {
  const [loading, setLoading] = useState(false);

  // 获取用户模型配置
  const fetchUserModelConfigs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await settingsApi.getUserModelConfigs();
      if (response.success) {
        return {
          success: true,
          data: response.data as ModelConfig[],
        };
      } else {
        message.error(response.message || '获取配置失败');
        return {
          success: false,
          error: response.message,
        };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取配置失败';
      message.error(errorMessage);
      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      setLoading(false);
    }
  }, []);

  // 更新模型配置
  const updateModelConfig = useCallback(async (config: Partial<ModelConfig>) => {
    setLoading(true);
    try {
      const response = await settingsApi.updateModelConfig(config);
      if (response.success) {
        message.success('配置更新成功');
        return {
          success: true,
          data: response.data as ModelConfig,
        };
      } else {
        message.error(response.message || '更新配置失败');
        return {
          success: false,
          error: response.message,
        };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '更新配置失败';
      message.error(errorMessage);
      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取系统模型列表 - 修复：使用正确的方法名
  const fetchSystemModels = useCallback(async () => {
    setLoading(true);
    try {
      // 使用正确的方法名：getSystemModelsWithConfig
      const response = await settingsApi.getSystemModelsWithConfig();
      if (response.success) {
        return {
          success: true,
          data: response.data as SystemModel[],
        };
      } else {
        message.error(response.message || '获取系统模型失败');
        return {
          success: false,
          error: response.message,
        };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取系统模型失败';
      message.error(errorMessage);
      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取用户列表（管理员）
  const fetchUsers = useCallback(async (filters?: {
    username?: string;
    email?: string;
    is_active?: boolean;
    is_locked?: boolean;
    skip?: number;
    limit?: number;
  }) => {
    setLoading(true);
    try {
      const response = await settingsApi.getUsers(filters);
      if (response.success) {
        return {
          success: true,
          data: response.data,
          total: response.total,
        };
      } else {
        message.error(response.message || '获取用户列表失败');
        return {
          success: false,
          error: response.message,
        };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取用户列表失败';
      message.error(errorMessage);
      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取系统统计（管理员）
  const fetchSystemStats = useCallback(async () => {
    setLoading(true);
    try {
      const response = await settingsApi.getSystemStats();
      if (response.success) {
        return {
          success: true,
          data: response.data,
        };
      } else {
        message.error(response.message || '获取系统统计失败');
        return {
          success: false,
          error: response.message,
        };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取系统统计失败';
      message.error(errorMessage);
      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      setLoading(false);
    }
  }, []);

  // 锁定用户
  const lockUser = useCallback(async (userId: number, reason: string = '管理员操作', lockHours: number = 24) => {
    setLoading(true);
    try {
      const response = await settingsApi.lockUser(userId, reason, lockHours);
      if (response.success) {
        message.success('用户锁定成功');
        return { success: true };
      } else {
        message.error(response.message || '锁定用户失败');
        return { success: false, error: response.message };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '锁定用户失败';
      message.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  // 解锁用户
  const unlockUser = useCallback(async (userId: number) => {
    setLoading(true);
    try {
      const response = await settingsApi.unlockUser(userId);
      if (response.success) {
        message.success('用户解锁成功');
        return { success: true };
      } else {
        message.error(response.message || '解锁用户失败');
        return { success: false, error: response.message };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '解锁用户失败';
      message.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    // 状态
    loading,
    
    // 操作方法
    fetchUserModelConfigs,
    updateModelConfig,
    fetchSystemModels,
    fetchUsers,
    fetchSystemStats,
    lockUser,
    unlockUser,
  };
};

export default useSettings;
