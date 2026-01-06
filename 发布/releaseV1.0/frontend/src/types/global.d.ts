// 扩展 Window 类型以包含调试工具
interface Window {
  // 添加全局类型声明
  __REDUX_DEVTOOLS_EXTENSION__?: any;
}

// 声明 process 对象用于环境变量
declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test';
  }
}

// 声明 process 对象
declare const process: {
  env: {
    NODE_ENV: string;
  };
};
