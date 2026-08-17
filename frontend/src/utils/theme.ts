// 主题工具：深浅色切换（dev-plan v4 §1.1 页面风格）。
// 随系统或手动；持久化到 localStorage；通过 <html class="dark"> 驱动 CSS 变量。
import { reactive } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'wb-theme'

export function getTheme(): Theme {
  const t = localStorage.getItem(STORAGE_KEY)
  return t === 'dark' ? 'dark' : 'light'
}

export function applyTheme(theme: Theme): void {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// 全局响应式主题状态，供 App 与 ThemeToggle 共享
export const themeState = reactive<{ mode: Theme }>({ mode: getTheme() })

export function initTheme(): void {
  applyTheme(themeState.mode)
}

export function toggleTheme(): Theme {
  const next: Theme = themeState.mode === 'dark' ? 'light' : 'dark'
  themeState.mode = next
  applyTheme(next)
  localStorage.setItem(STORAGE_KEY, next)
  return next
}

/** 跟随系统偏好（仅当未手动设置过时） */
export function syncSystemTheme(): void {
  if (!localStorage.getItem(STORAGE_KEY)) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    themeState.mode = prefersDark ? 'dark' : 'light'
    applyTheme(themeState.mode)
  }
}
