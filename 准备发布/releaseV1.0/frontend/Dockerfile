# 构建阶段
FROM node:18-alpine AS build
WORKDIR /app

# 1. 设置环境变量修复 npm bug
ENV ROLLUP_NATIVE=false
ENV NODE_OPTIONS="--max-old-space-size=4096"

# 2. 复制配置文件
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./

# 3. 清理并重新安装依赖（按照错误提示的方法）
RUN rm -rf node_modules package-lock.json && \
    npm install --no-audit --no-fund --legacy-peer-deps

# 4. 手动安装缺失的 rollup 二进制模块（如果需要）
RUN npm install @rollup/rollup-linux-x64-musl --no-save || true

# 5. 复制源代码
COPY . .

# 6. 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
