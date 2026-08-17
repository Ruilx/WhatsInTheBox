// 登录态 store（dev-plan v4 §7.8 / §7.9）。
// 登录标记 / role / username 持久化到 localStorage（不存密码）。
// 后端用 Set-Cookie(wb_session) 维持会话；本 store 仅用于前端 UI 控制（写按钮可见性、路由守卫）。
// 收到 401（code 1002）由 api 拦截器调用 clear() 清除。

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { http, fetchMe } from '@/api'

const STORAGE_KEY = 'wb-auth'

interface AuthSnapshot {
  userId: number
  username: string
  role: string
}

function load(): AuthSnapshot {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw) as AuthSnapshot
  } catch {
    /* ignore */
  }
  return { userId: 0, username: '', role: '' }
}

export const useAuthStore = defineStore('auth', () => {
  const userId = ref<number>(0)
  const username = ref<string>('')
  const role = ref<string>('')

  const isLoggedIn = computed(() => role.value !== '')
  const isRw = computed(() => role.value === 'rw')

  function persist(): void {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        userId: userId.value,
        username: username.value,
        role: role.value,
      }),
    )
  }

  function apply(s: AuthSnapshot): void {
    userId.value = s.userId
    username.value = s.username
    role.value = s.role
  }

  function clear(): void {
    userId.value = 0
    username.value = ''
    role.value = ''
    localStorage.removeItem(STORAGE_KEY)
  }

  async function login(user: string, pass: string): Promise<void> {
    const data = await http.post('/auth/login', { username: user, password: pass })
    const result = data as unknown as {
      token: string
      user: { id: number; username: string; role: string }
    }
    apply({
      userId: result.user.id,
      username: result.user.username,
      role: result.user.role,
    })
    persist()
  }

  async function refresh(): Promise<void> {
    const me = await fetchMe()
    apply({ userId: me.id, username: me.username, role: me.role })
    persist()
  }

  async function logout(): Promise<void> {
    try {
      await http.post('/auth/logout')
    } catch {
      /* 即使请求失败也清除本地登录态 */
    }
    clear()
  }

  // 应用启动时从 localStorage 恢复（随后由 App 调 refresh() 校验 cookie 是否仍有效）
  const saved = load()
  if (saved.role) apply(saved)

  return {
    userId,
    username,
    role,
    isLoggedIn,
    isRw,
    login,
    refresh,
    logout,
    clear,
    apply,
    persist,
  }
})
