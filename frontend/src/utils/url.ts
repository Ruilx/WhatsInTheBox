// URL 工具（dev-plan v4 §7.20 / §3.3）：URL 段统一 encodeURIComponent，
// 全局页前缀来自 VITE_GLOBAL_PREFIX（默认 _wb）。无二维码，仅复制完整 URL。

export const GLOBAL_PREFIX: string =
  (import.meta.env.VITE_GLOBAL_PREFIX as string) || '_wb'

export function encodeSeg(seg: string): string {
  return encodeURIComponent(seg || '')
}

/** 活动页：/活动名 */
export function activityUrl(activityName: string): string {
  return `/${encodeSeg(activityName)}`
}

/** 箱子页：/活动名/箱子名 */
export function boxUrl(activityName: string, boxName: string): string {
  return `/${encodeSeg(activityName)}/${encodeSeg(boxName)}`
}

/** 活动内已取出：/活动名/已取出 */
export function takenOutUrl(activityName: string): string {
  return `/${encodeSeg(activityName)}/已取出`
}

/** 登录页 */
export function loginUrl(): string {
  return `/${GLOBAL_PREFIX}/login`
}

/** 活动列表（全局页） */
export function activitiesUrl(): string {
  return `/${GLOBAL_PREFIX}/activities`
}

/** 联合物品列表（全局页） */
export function combosUrl(): string {
  return `/${GLOBAL_PREFIX}/combos`
}

/** 日志列表（全局页） */
export function logsUrl(): string {
  return `/${GLOBAL_PREFIX}/logs`
}

/** 搜索页（全局页） */
export function searchUrl(keyword = ''): string {
  return keyword
    ? `/${GLOBAL_PREFIX}/search?keyword=${encodeSeg(keyword)}`
    : `/${GLOBAL_PREFIX}/search`
}

/** 复制到剪贴板 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch (e) {
    // 降级到 execCommand
  }
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  } catch (e) {
    return false
  }
}
