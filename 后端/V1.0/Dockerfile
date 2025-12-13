# Dockerfile
# 使用官方 Python 3.11 镜像作为基础
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 复制环境变量文件（从 .env.example 复制为 .env）
COPY .env.example .env

# 创建数据库初始化脚本目录
RUN mkdir -p /app/buildDB

# 复制数据库初始化文件
COPY buildDB/init_v1.0.sql /app/buildDB/

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["python", "start_app.py"]
