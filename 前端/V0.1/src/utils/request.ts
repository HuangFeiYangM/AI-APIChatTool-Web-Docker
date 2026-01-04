// src/utils/request.ts - 最终版
import axios from 'axios';
import { message } from 'antd';
import type { AxiosResponse, AxiosRequestConfig } from 'axios';

// 创建axios实例
const axiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
axiosInstance.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // 开发环境打印日志
    if (process.env.NODE_ENV === 'development') {
      console.log(`发送请求: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
      if (config.data) {
        console.log('请求数据:', config.data);
      }
    }
    
    return config;
  },
  (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 只处理错误，不修改成功响应
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`请求成功: ${response.status} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    console.error('请求失败:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message,
    });
    
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as any;
      
      // 处理422验证错误
      if (status === 422) {
        const detail = data?.detail;
        let errorMessage = '数据验证失败';
        
        if (Array.isArray(detail)) {
          errorMessage = detail.map((err: any) => {
            const loc = err.loc?.join('.');
            return loc ? `${loc}: ${err.msg}` : err.msg;
          }).join('; ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (data?.message) {
          errorMessage = data.message;
        }
        
        message.error(errorMessage);
        
        return Promise.reject({
          success: false,
          error: errorMessage,
          status: status,
          data: data,
        });
      }
      
      // 其他错误处理
      let errorMessage = data?.detail || data?.message || `请求失败: ${status}`;
      
      switch (status) {
        case 400:
          errorMessage = data?.detail || '请求参数错误';
          break;
        case 401:
          errorMessage = data?.detail || '登录已过期，请重新登录';
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          sessionStorage.removeItem('token');
          sessionStorage.removeItem('user');
          
          if (!window.location.pathname.includes('/login')) {
            setTimeout(() => {
              window.location.href = '/login';
            }, 100);
          }
          break;
        case 403:
          errorMessage = data?.detail || '没有权限访问该资源';
          break;
        case 404:
          // 在响应拦截器的404处理部分，添加对特定路径的静默处理
          // 检查是否是模型配置相关的请求
          const url = error.config?.url || '';
          const isModelConfigUrl = url.includes('/models/config/') && !url.includes('/models/config/create');
          
          // 对于模型配置的GET请求（且不是创建配置），静默处理，不显示错误
          if (isModelConfigUrl && error.config?.method === 'get') {
            if (process.env.NODE_ENV === 'development') {
              console.log(`模型配置不存在: ${url} - 这是正常现象，表示用户尚未配置该模型`);
            }
            
            return Promise.reject({
              success: false,
              error: '模型未配置',
              status: status,
              data: data,
              isModelNotConfigured: true,
              silent: true, // 添加静默标志
            });
          }
          
          errorMessage = error.config?.url?.includes('/auth/') 
            ? 'API路径错误，请检查后端是否启动或路径配置'
            : '请求的资源不存在';
          break;
        case 409:
          errorMessage = data?.detail || '资源冲突，请检查输入';
          break;
        case 423:
          errorMessage = data?.detail || '账户已被锁定，请联系管理员';
          break;
        case 500:
          errorMessage = data?.detail || '服务器内部错误';
          break;
      }
      
      message.error(errorMessage);
      
      return Promise.reject({
        success: false,
        error: errorMessage,
        status: status,
        data: data,
      });
    } else if (error.request) {
      message.error('网络错误，请检查网络连接或后端服务是否启动');
      return Promise.reject({
        success: false,
        error: '网络连接失败',
      });
    } else {
      message.error('请求配置错误');
      return Promise.reject({
        success: false,
        error: error.message,
      });
    }
  }
);

// 封装的请求方法，返回后端的标准响应格式
const request = {
  // 移除泛型参数
  get: async (url: string, config?: AxiosRequestConfig): Promise<any> => {
    const response = await axiosInstance.get(url, config);
    return response.data;
  },
  
  post: async (url: string, data?: any, config?: AxiosRequestConfig): Promise<any> => {
    const response = await axiosInstance.post(url, data, config);
    return response.data;
  },
  
  put: async (url: string, data?: any, config?: AxiosRequestConfig): Promise<any> => {
    const response = await axiosInstance.put(url, data, config);
    return response.data;
  },
  
  delete: async (url: string, config?: AxiosRequestConfig): Promise<any> => {
    const response = await axiosInstance.delete(url, config);
    return response.data;
  },
  
  patch: async (url: string, data?: any, config?: AxiosRequestConfig): Promise<any> => {
    const response = await axiosInstance.patch(url, data, config);
    return response.data;
  }
};

export default request;
