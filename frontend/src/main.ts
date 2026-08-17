// 应用入口（dev-plan v4 §1.3）。
// 挂载顺序：pinia -> router -> ant-design-vue。初始化主题并启动登录态校验。

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

import App from './App.vue'
import router from './router'
import { initTheme, syncSystemTheme } from './utils/theme'
import { useAuthStore } from './store/auth'

import './styles/variables.css'
import './styles/global.css'

// 主题：先按系统偏好（未手动设置过），再应用已存主题
syncSystemTheme()
initTheme()

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Antd)

// 启动后校验 cookie 是否仍有效（过期/未登录会被拦截器清登录态并跳登录）
const auth = useAuthStore()
auth
  .refresh()
  .catch(() => {
    /* 未登录或已过期：由路由守卫 / 拦截器处理跳转 */
  })

app.mount('#app')
