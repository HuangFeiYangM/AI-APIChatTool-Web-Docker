# Docker 部署指南

## 前置要求
1. 安装 Docker 和 Docker Compose
2. 确保项目的 `requirements.txt` 文件存在

## 部署步骤

### 1. 准备文件
确保以下文件在项目根目录：
- Dockerfile
- docker-compose.yml
- .env.docker
- entrypoint.sh
- buildDB/init_v1.0.sql (数据库初始化文件)

### 2. 构建和启动
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
