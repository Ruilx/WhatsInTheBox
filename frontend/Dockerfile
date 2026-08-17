# 「箱子里面有什么」前端镜像（多阶段构建）
# 阶段一：node:22-alpine 构建产物
FROM node:22-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# VITE_API_BASE 默认 /whatsinthebox（相对路径，由 nginx 反代到后端），可按需覆盖
ARG VITE_API_BASE=/whatsinthebox
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# 阶段二：nginx 提供静态产物
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
