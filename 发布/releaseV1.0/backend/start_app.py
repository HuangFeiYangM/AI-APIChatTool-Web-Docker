# start_app.py（修改版）
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    # 使用配置中的主机和端口
    host = settings.SERVER_HOST
    port = settings.SERVER_PORT
    reload = settings.DEBUG  # 调试模式下启用热重载
    
    print(f"🚀 启动服务器: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print(f"📊 健康检查: http://{host}:{port}/health")
    
    uvicorn.run(
        "app.main:app",  # 应用的位置（模块:应用实例）
        host=host,
        port=port,
        reload=reload,
        log_level="info" if settings.DEBUG else "warning",
        access_log=settings.DEBUG  # 调试模式时显示访问日志
    )
