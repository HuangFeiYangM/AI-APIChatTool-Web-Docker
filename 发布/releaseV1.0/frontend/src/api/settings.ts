// src/api/settings.ts - 包含管理员功能的最终版
import request from '@/utils/request';

export const settingsApi = {
  // 获取系统模型（包括用户配置状态）
  getSystemModelsWithConfig: async () => {
    const response = await request.get('/models/system-models/available');
    return response;
  },
  
  // 获取用户模型配置
  getUserModelConfigs: async () => {
    const response = await request.get('/models/config');
    return response;
  },
  
  // 获取特定模型配置
  // 修改 getModelConfig 方法，处理404错误
  getModelConfig: async (modelId: number) => {
    try {
      const response = await request.get(`/models/config/${modelId}`);
      return response;
    } catch (error: any) {
      // 如果是模型未配置的404错误，返回一个标准格式的响应
      if (error.status === 404 || error.isModelNotConfigured || error.silent) {
        return {
          success: false,
          message: '模型未配置',
          data: null,
          isModelNotConfigured: true // 添加标志，表示是未配置而非其他错误
        };
      }
      // 其他错误重新抛出
      throw error;
    }
  },
  
  // 更新模型配置
  updateModelConfig: async (data: any) => {
    const response = await request.post('/models/config', data);
    return response;
  },
  
  // 创建模型配置
  createModelConfig: async (data: any) => {
    const response = await request.post('/models/config/create', data);
    return response;
  },
  
  // 删除模型配置
  deleteModelConfig: async (modelId: number) => {
    const response = await request.delete(`/models/config/${modelId}`);
    return response;
  },
  
  // 启用模型配置
  enableModelConfig: async (modelId: number) => {
    const response = await request.post(`/models/config/${modelId}/enable`);
    return response;
  },
  
  // 禁用模型配置
  disableModelConfig: async (modelId: number) => {
    const response = await request.post(`/models/config/${modelId}/disable`);
    return response;
  },
  
  // 批量更新模型配置
  batchUpdateModelConfigs: async (data: { model_ids: number[]; is_enabled?: boolean; priority?: number }) => {
    const response = await request.post('/models/config/batch-update', data);
    return response;
  },

  // 获取 API 使用情况
  getApiUsage: async (params?: { days?: number; model_id?: number }) => {
    const response = await request.get('/models/usage', { params });
    return response;
  },

  // 验证 API 密钥
  validateApiKey: async (modelId: number, apiKey: string) => {
    const response = await request.post('/models/config/validate-api-key', {
      model_id: modelId,
      api_key: apiKey
    });
    return response;
  },

  // 获取已配置的模型（简单列表，用于聊天页面）
  getConfiguredModels: async () => {
    try {
      const response = await request.get('/models/config');
      
      if (response && response.success && response.data) {
        const configs = Array.isArray(response.data) ? response.data : [];
        const configuredModels = configs
          .filter((config: any) => config.is_enabled)
          .map((config: any) => ({
            model_id: config.model_id,
            model_name: config.model_name,
            model_provider: config.model_provider
          }));
        
        return {
          success: true,
          data: configuredModels,
          message: response.message || '获取成功'
        };
      }
      
      return {
        success: false,
        message: response?.message || '获取配置失败',
        data: []
      };
    } catch (error: any) {
      console.error('获取已配置模型失败:', error);
      return {
        success: false,
        message: error.message || '获取配置失败',
        data: []
      };
    }
  }
};

// 在现有代码后添加以下管理员相关API

// 管理员API
export const adminApi = {
  // 获取用户列表（带分页和筛选）
  getUsers: async (params?: {
    username?: string;
    email?: string;
    is_active?: boolean;
    is_locked?: boolean;
    skip?: number;
    limit?: number;
  }) => {
    const response = await request.get('/admin/users', { params });
    return response;
  },

  // 获取用户详情
  getUserDetail: async (userId: number) => {
    const response = await request.get(`/admin/users/${userId}`);
    return response;
  },

  // 锁定用户
  lockUser: async (userId: number, reason?: string, lockHours?: number) => {
    const response = await request.post(`/admin/users/${userId}/lock`, {
      reason: reason || '管理员操作',
      lock_hours: lockHours || 24
    });
    return response;
  },

  // 解锁用户
  unlockUser: async (userId: number) => {
    const response = await request.post(`/admin/users/${userId}/unlock`);
    return response;
  },

  // 更新用户信息
  updateUser: async (userId: number, data: any) => {
    const response = await request.put(`/admin/users/${userId}`, data);
    return response;
  },

  // 获取系统统计
  getSystemStats: async () => {
    const response = await request.get('/admin/stats');
    return response;
  },

  // 获取每日统计
  getDailyStats: async (days: number = 7) => {
    const response = await request.get('/admin/daily-stats', {
      params: { days }
    });
    return response;
  },

  // 获取系统健康状态
  getSystemHealth: async () => {
    const response = await request.get('/admin/health');
    return response;
  },

  // 获取API调用日志
  getApiLogs: async (params?: {
    user_id?: number;
    model_id?: number;
    start_date?: string;
    end_date?: string;
    is_success?: boolean;
    skip?: number;
    limit?: number;
  }) => {
    const response = await request.get('/admin/api-logs', { params });
    return response;
  }
};

// 导出合并的API对象
export default {
  ...settingsApi,
  ...adminApi
};
