# 「箱子里面有什么（WhatsInTheBox）」前端 DEV 镜像
# 设计原则（按用户要求）：镜像里只烘焙「运行环境 + 依赖」，
# 源码（frontend/src、index.html、vite.config.ts 等）在运行时通过 bind mount 外挂进容器，
# 不 COPY 进镜像。依赖（node_modules）在构建期 npm install 进镜像的 /app/node_modules。
#
# 关键点：compose 里使用「选择性挂载」只挂源码文件，不整目录挂 ./frontend:/app，
# 否则宿主机（本地）的 node_modules 会被挂进去、甚至盖掉镜像里烘焙好的 /app/node_modules。
# 这里镜像内已装好 node_modules，运行时只挂源码即可热更新。
FROM node:22-slim

# 开发环境（dev server 用 vite）
ENV NODE_ENV=development

WORKDIR /app

# 仅拷依赖清单并安装（node_modules 烘焙进镜像 /app/node_modules，不拷源码）
COPY package.json package-lock.json ./
RUN npm install --no-audit --no-fund

# 注意：这里【不 COPY 任何源码】。源码在 compose 里通过选择性挂载挂进 /app。
# 例：docker run -v "$(pwd)/frontend/src:/app/src" ... whatsinthebox-frontend:latest

EXPOSE 5176

# DEV 取向：vite dev server，监听 0.0.0.0:5176（容器外可访问）。
# 代理目标由 vite.config.ts 读取环境变量 API_PROXY_TARGET，默认回退 127.0.0.1:8004；
# compose 里会注入 API_PROXY_TARGET=http://backend:8004 让前端容器打到后端容器。
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5176"]
