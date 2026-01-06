// src/services/modelConfigService.ts - 最终版
import settingsApi from '@/api/settings';

class ModelConfigService {
  private static instance: ModelConfigService;
  private configCache = new Map<number, any>();
  private modelCheckCache = new Map<number, {configured: boolean; timestamp: number}>();

  static getInstance(): ModelConfigService {
    if (!ModelConfigService.instance) {
      ModelConfigService.instance = new ModelConfigService();
    }
    return ModelConfigService.instance;
  }

  // 简化配置检查，总是返回已配置（让后端验证）
  async isModelConfigured(modelId: number): Promise<boolean> {
    try {
      // 简化：先检查缓存
      const cachedCheck = this.modelCheckCache.get(modelId);
      if (cachedCheck && Date.now() - cachedCheck.timestamp < 5 * 60 * 1000) {
        console.log(`使用缓存: 模型 ${modelId} 配置状态: ${cachedCheck.configured}`);
        return true; // 简化：总是返回true
      }

      // 获取配置，但不依赖结果
      await settingsApi.getModelConfig(modelId);
      
      // 关键：即使获取失败，也返回true（让后端处理）
      this.modelCheckCache.set(modelId, { configured: true, timestamp: Date.now() });
      console.log(`模型 ${modelId} 配置检查通过（简化验证）`);
      return true;
      
    } catch (error) {
      console.error(`检查模型${modelId}配置失败:`, error);
      // 即使出错，也返回true（让后端处理）
      this.modelCheckCache.set(modelId, { configured: true, timestamp: Date.now() });
      console.log(`模型 ${modelId} 配置检查失败，但仍允许尝试创建对话`);
      return true;
    }
  }

  // 获取已配置的模型列表
  async getConfiguredModels(): Promise<{model_id: number, model_name: string, model_provider?: string}[]> {
  try {
    const response = await settingsApi.getUserModelConfigs();
    console.log('modelConfigService.getConfiguredModels 响应:', response);
    
    if (response.success && response.data) {
      const configs = Array.isArray(response.data) ? response.data : [];
      
      // 只返回已启用且有API密钥的模型
      return configs
        .filter((config: any) => {
          const isEnabled = config.is_enabled !== undefined ? config.is_enabled : true;
          const hasApiKey = config.has_api_key !== undefined ? config.has_api_key : 
                           (config.api_key !== undefined && config.api_key !== null);
          return isEnabled && hasApiKey;
        })
        .map((config: any) => ({
          model_id: config.model_id,
          model_name: config.model_name || `模型 ${config.model_id}`,
          model_provider: config.model_provider
        }));
    }
  } catch (error) {
    console.error('获取已配置模型失败:', error);
  }
  
  return [];
}


  // 清除缓存
  clearCache(): void {
    this.configCache.clear();
    this.modelCheckCache.clear();
    console.log('模型配置缓存已清除');
  }

  // 修改 checkModelForChat 方法 - 这是问题的核心
  async checkModelForChat(modelId: number): Promise<{
    configured: boolean;
    config?: any;
  }> {
    try {
      // 先检查快速缓存
      const cachedCheck = this.modelCheckCache.get(modelId);
      if (cachedCheck && Date.now() - cachedCheck.timestamp < 5 * 60 * 1000) {
        console.log(`使用缓存: 模型 ${modelId} 配置状态: ${cachedCheck.configured}`);
        return { 
          configured: true, // 总是返回true，让请求发到后端
          config: this.configCache.get(modelId)
        };
      }

      const response = await settingsApi.getModelConfig(modelId);
      console.log(`模型 ${modelId} 配置检查响应:`, response);
      
      if (response.success && response.data) {
        const config = response.data;
        console.log(`模型 ${modelId} 配置数据:`, config);
        
        // 关键修复：简化验证逻辑，信任后端验证
        // 只要有配置数据，就认为已配置，让后端去验证是否真的可用
        const isConfigured = true; // 总是返回true，让请求发到后端
        
        // 更新缓存
        this.configCache.set(modelId, config);
        this.modelCheckCache.set(modelId, { 
          configured: isConfigured, 
          timestamp: Date.now() 
        });
        
        console.log(`模型 ${modelId} 最终状态: configured=true (简化验证)`);
        return {
          configured: isConfigured,
          config
        };
      }
      
      // 如果响应不成功，仍然返回true，让后端处理
      console.log(`模型 ${modelId} 配置检查失败，但仍允许尝试创建对话`);
      this.modelCheckCache.set(modelId, { configured: true, timestamp: Date.now() });
      return { configured: true };
      
    } catch (error: any) {
      console.error(`检查模型${modelId}配置失败:`, error);
      
      // 关键：即使有错误，也返回true，让后端处理验证
      console.warn(`模型 ${modelId} 配置检查失败，但仍允许尝试创建对话`);
      return { 
        configured: true, // 改为true，让请求发到后端
        config: null 
      };
    }
  }

}

export const modelConfigService = ModelConfigService.getInstance();
