import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 开发代理：/whatsinthebox（后端 API）与 /uploads（上传文件）转发到后端 8004
// 注：本地启动后端 8004 / 前端 5176（原默认 8000 / 5173）。
//
// 请求体（POST/PUT/PATCH 的 JSON 与 multipart 上传）由 http-proxy 原生 pipe 转发，
// 无需自定义中间件。历史上误加的 configureServer 中间件从未被 Vite 调用（它是插件钩子
// 而非 defineConfig 根级选项），且会消费请求流导致 multipart 上传失败，已删除。
// 代理目标：默认回退本地 127.0.0.1:8004（保持原生开发行为不变）；
// 在容器联网时由环境变量覆盖（docker-compose 注入 API_PROXY_TARGET=http://backend:8004）。
const PROXY_TARGET = process.env.API_PROXY_TARGET || 'http://127.0.0.1:8004'

export default defineConfig({
  // 相对路径产物：index.html 内资源写为 ./assets/...，由浏览器按当前文档前缀
  // （/2026trip/ 或 /_wb/）解析，使资源自动落在外层 nginx 已路由的前缀内，
  // 避开 base:'/' 时“外层无 /assets 路由 → 资源 404”的问题。
  // 与 VITE_API_BASE 正交：base 只管构建期资源 URL，不影响运行时 API 绝对路径。
  base: './',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5176,
    proxy: {
      '/whatsinthebox': {
        target: PROXY_TARGET,
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes, req) => {
            console.log('[proxy] <=', req.method, req.url, proxyRes.statusCode)
          })
          proxy.on('error', (err, req) => {
            console.log('[proxy] ERROR', req.method, req.url, err.message)
          })
        },
      },
      '/uploads': {
        target: PROXY_TARGET,
        changeOrigin: true,
      },
    },
  },
})
