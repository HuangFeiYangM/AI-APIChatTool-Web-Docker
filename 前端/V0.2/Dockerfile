# 阶段1：构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 复制包管理文件
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./

# 安装依赖
RUN npm ci --no-audit --prefer-offline

# 复制源代码
COPY src ./src
COPY public ./public
COPY index.html ./

# 构建应用（传入环境变量）
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# 阶段2：运行阶段 - 使用nginx
FROM nginx:alpine

# 复制自定义nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
