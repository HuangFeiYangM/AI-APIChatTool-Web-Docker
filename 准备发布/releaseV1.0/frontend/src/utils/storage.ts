/**
 * 本地存储工具函数
 */

// Token相关
export const setToken = (token: string): void => {
  localStorage.setItem('token', token);
};

export const getToken = (): string | null => {
  return localStorage.getItem('token');
};

export const removeToken = (): void => {
  localStorage.removeItem('token');
};

// 用户信息相关
export const setUser = (user: any): void => {
  localStorage.setItem('user', JSON.stringify(user));
};

export const getUser = (): any | null => {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};

export const removeUser = (): void => {
  localStorage.removeItem('user');
};

// 通用存储
export const setItem = (key: string, value: any): void => {
  localStorage.setItem(key, JSON.stringify(value));
};

export const getItem = <T = any>(key: string): T | null => {
  const value = localStorage.getItem(key);
  return value ? JSON.parse(value) : null;
};

export const removeItem = (key: string): void => {
  localStorage.removeItem(key);
};

// 清空所有存储
export const clearStorage = (): void => {
  localStorage.clear();
};
