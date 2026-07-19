# ===== 构建阶段 =====
FROM node:20-alpine AS builder

WORKDIR /app

# 先复制 package.json 与 lockfile，利用 Docker 缓存
COPY package.json package-lock.json ./

# 安装全部依赖（含 devDependencies，Vite 等构建工具需要）
RUN npm ci || npm install

COPY . .

# 正式构建（若 TypeScript 类型检查失败会中止）
RUN npm run build

# ===== 运行阶段 =====
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
