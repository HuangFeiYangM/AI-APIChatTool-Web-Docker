// src/components/ErrorBoundary/index.tsx
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary 捕获错误:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // 如果有自定义 fallback，渲染它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 否则渲染默认错误页面
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h2>出错了！</h2>
          <p>抱歉，应用发生了错误。请尝试刷新页面。</p>
          <details style={{ whiteSpace: 'pre-wrap', textAlign: 'left' }}>
            <summary>错误详情</summary>
            {this.state.error?.toString()}
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
