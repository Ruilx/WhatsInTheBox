// API 封装（dev-plan v4 §3.2 / §7.4 / §7.5）。
//
// - baseURL 取自 import.meta.env.VITE_API_BASE（默认 /whatsinthebox），
//   与后端 API_PREFIX 一致；开发期由 vite 代理转发到 127.0.0.1:8004（见 frontend/vite.config.ts 的 PROXY_TARGET）。
// - withCredentials: true 携带 HttpOnly cookie（wb_session）实现登录态。
// - 响应拦截：后端恒返回 HTTP 200 + {code,msg,data}（异常亦 200，见 main.py）。
//   code===0 取 data；否则 message 报错并 reject；code===1002（未登录）清登录态跳登录。
// - 统一封装 get/post 便捷方法，自动剔除空参数（避免后端 Optional[int] 收到 '' 校验失败）。

import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { message } from 'ant-design-vue'
import { GLOBAL_PREFIX } from '@/utils/url'
import { useAuthStore } from '@/store/auth'
import type { Activity, Box, Item, Combo, ComboItem, Log, Page } from '@/types'

const BASE_URL: string = import.meta.env.VITE_API_BASE || '/whatsinthebox'

export const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  timeout: 15000,
})

function redirectLogin(): void {
  const auth = useAuthStore()
  auth.clear()
  const loginPath = `/${GLOBAL_PREFIX}/login`
  if (!window.location.pathname.startsWith(loginPath)) {
    window.location.href = loginPath
  }
}

http.interceptors.response.use(
  (resp: AxiosResponse) => {
    const body = resp.data
    if (body && typeof body.code === 'number') {
      if (body.code === 0) {
        return body.data
      }
      if (body.code === 1002) {
        message.error(body.msg || '登录已过期，请重新登录')
        redirectLogin()
        return Promise.reject(new Error(body.msg || '未登录'))
      }
      message.error(body.msg || '请求失败')
      return Promise.reject(new Error(body.msg || 'error'))
    }
    return body
  },
  (error: unknown) => {
    const err = error as { response?: AxiosResponse; message?: string }
    const status = err?.response?.status
    if (status === 401) {
      message.error('登录已过期，请重新登录')
      redirectLogin()
    } else {
      const msg = err?.response?.data?.msg || err?.message || '网络错误'
      message.error(msg)
    }
    return Promise.reject(error)
  },
)

/** 剔除 undefined / null / '' 参数，避免后端 Optional 校验失败。 */
function clean(obj: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const k of Object.keys(obj)) {
    const v = obj[k]
    if (v === undefined || v === null || v === '') continue
    out[k] = v
  }
  return out
}

export async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const data = await http.get(url, { params: params ? clean(params) : undefined })
  return data as unknown as T
}

export async function post<T>(url: string, body?: unknown): Promise<T> {
  const data = await http.post(url, body)
  return data as unknown as T
}

/** 照片相对路径补全为可访问 URL（后端存 uploads/ 下相对路径）。 */
export function uploadUrl(path?: string | null): string {
  if (!path) return ''
  if (
    path.startsWith('http://') ||
    path.startsWith('https://') ||
    path.startsWith('//')
  ) {
    return path
  }
  return path.startsWith('/uploads') ? path : `/uploads/${path}`
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export interface LoginResult {
  token: string
  user: { id: number; username: string; nickname: string; role: string }
}
export function login(username: string, password: string): Promise<LoginResult> {
  return post('/auth/login', { username, password })
}
export function logout(): Promise<void> {
  return post('/auth/logout')
}
export function fetchMe(): Promise<{ id: number; username: string; role: string }> {
  return get('/auth/me')
}
export function changePassword(oldPwd: string, newPwd: string): Promise<void> {
  return post('/auth/change_password', { old_pwd: oldPwd, new_pwd: newPwd })
}

// ---------------------------------------------------------------------------
// Activity
// ---------------------------------------------------------------------------
export interface ActivityListParams {
  page?: number
  size?: number
  keyword?: string
  type?: string
  status?: number | null
}
export function listActivities(params: ActivityListParams): Promise<Page<Activity>> {
  return get('/activity/list', {
    page: params.page ?? 1,
    size: params.size ?? 50,
    keyword: params.keyword ?? '',
    type: params.type ?? '',
    status: params.status ?? null,
  })
}
export function getActivity(id?: number, name?: string): Promise<Activity> {
  const p: Record<string, unknown> = {}
  if (id) p.id = id
  if (name) p.name = name
  return get('/activity/detail', p)
}
export interface ActivityPayload {
  id?: number
  name: string
  desc?: string
  type?: string
  start_time?: string | null
  end_time?: string | null
  status?: number
  note?: string
}
export function createActivity(payload: ActivityPayload): Promise<{ id: number }> {
  return post('/activity/create', payload)
}
export function updateActivity(payload: ActivityPayload): Promise<{ id: number }> {
  return post('/activity/update', payload)
}
export function deleteActivity(id: number): Promise<void> {
  return post('/activity/delete', { id })
}
export function toggleActivityStatus(id: number, status: number): Promise<void> {
  return post('/activity/toggle_status', { id, status })
}

// ---------------------------------------------------------------------------
// Box
// ---------------------------------------------------------------------------
export interface BoxListParams {
  activity_id: number
  page?: number
  size?: number
  keyword?: string
  type?: string
  status?: number | null
}

/**
 * box.type 归一化：部分接口（如 /box/detail）返回的是 JSON 字符串（`["主要"]`）
 * 而非数组，若直接 v-for 会把字符串按字符遍历，渲染出 `[`、`"`、`主`… 等碎片标签。
 * 统一在 API 层收敛为 string[]，视图层无需再判断类型（禁止在模板里 JSON.parse）。
 */
function parseTypeField(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw.filter((t): t is string => typeof t === 'string' && t !== '')
  }
  if (typeof raw !== 'string') return []
  const text = raw.trim()
  if (!text) return []
  try {
    const parsed: unknown = JSON.parse(text)
    if (Array.isArray(parsed)) {
      return parsed.map((t) => String(t)).filter((t) => t !== '')
    }
    // JSON 合法但非数组（如 `"主要"` / `123`）：按单标签处理
    return [String(parsed)].filter((t) => t !== '')
  } catch {
    // 非 JSON（如后端历史脏数据 `主要`）：整体作为单个标签，避免逐字符渲染
    return [text]
  }
}

/** 归一化单个箱子对象（就地返回新对象，保持 Box 类型契约：type 恒为 string[]）。 */
function normalizeBox(raw: unknown): Box {
  const box = (raw ?? {}) as Box & { type?: unknown }
  return { ...box, type: parseTypeField(box.type) }
}

/** 归一化箱子列表（null / 非数组一律回退为空列表）。 */
function normalizeBoxes(raw: unknown): Box[] {
  return Array.isArray(raw) ? raw.map(normalizeBox) : []
}

export async function listBoxes(params: BoxListParams): Promise<Page<Box>> {
  const res = await get<Page<Box>>('/box/list', {
    activity_id: params.activity_id,
    page: params.page ?? 1,
    size: params.size ?? 50,
    keyword: params.keyword ?? '',
    type: params.type ?? '',
    status: params.status ?? null,
  })
  return { ...res, list: normalizeBoxes(res?.list) }
}
export interface BoxDetailData {
  box: Box
  items: Item[]
  child_boxes: Box[]
}
export async function getBoxDetail(
  activityName: string,
  boxName: string,
): Promise<BoxDetailData> {
  const res = await get<BoxDetailData>('/box/detail', {
    activity_name: activityName,
    box_name: boxName,
  })
  return {
    ...res,
    box: normalizeBox(res?.box),
    items: Array.isArray(res?.items) ? res.items : [],
    child_boxes: normalizeBoxes(res?.child_boxes),
  }
}
export interface BoxPayload {
  id?: number
  activity_id: number
  name: string
  desc?: string
  type?: string[]
  size?: string
  material?: string
  parent_box_id?: number | null
  status?: number
  serial_no?: string
  note?: string
  first_using_time?: string | null
  photo?: string
  thumb?: string
}
export function createBox(payload: BoxPayload): Promise<{ id: number }> {
  return post('/box/create', payload)
}
export function updateBox(payload: BoxPayload): Promise<{ id: number }> {
  return post('/box/update', payload)
}
export function deleteBox(id: number): Promise<void> {
  return post('/box/delete', { id })
}
export function foldBox(id: number, status: number): Promise<void> {
  return post('/box/fold', { id, status })
}

// ---------------------------------------------------------------------------
// Item
// ---------------------------------------------------------------------------
export interface ItemListParams {
  box_id: number
  page?: number
  size?: number
  keyword?: string
  status?: number | null
}
export function listItems(params: ItemListParams): Promise<Page<Item>> {
  return get('/item/list', {
    box_id: params.box_id,
    page: params.page ?? 1,
    size: params.size ?? 50,
    keyword: params.keyword ?? '',
    status: params.status ?? null,
  })
}
export interface TakenOutParams {
  activity_id?: number
  activity_name?: string
  page?: number
  size?: number
  keyword?: string
}
export function listTakenOut(params: TakenOutParams): Promise<Page<Item>> {
  return get('/item/taken_out_list', {
    activity_id: params.activity_id ?? 0,
    activity_name: params.activity_name ?? '',
    page: params.page ?? 1,
    size: params.size ?? 50,
    keyword: params.keyword ?? '',
  })
}
export function getItem(id: number): Promise<Item> {
  return get('/item/detail', { id })
}
export interface ItemPayload {
  id?: number
  box_id?: number
  name: string
  desc?: string
  type?: string
  activity_id?: number
  status?: number
  note?: string
  photo?: string
  thumb?: string
}
export function createItem(payload: ItemPayload): Promise<{ id: number }> {
  return post('/item/create', payload)
}
export function updateItem(payload: ItemPayload): Promise<{ id: number }> {
  return post('/item/update', payload)
}
export function deleteItem(id: number): Promise<void> {
  return post('/item/delete', { id })
}
export function takeOutItem(id: number): Promise<void> {
  return post('/item/take_out', { id })
}

// ---------------------------------------------------------------------------
// Combo
// ---------------------------------------------------------------------------
export interface ComboListParams {
  page?: number
  size?: number
  keyword?: string
  status?: number | null
}
export function listCombos(params: ComboListParams = {}): Promise<Page<Combo>> {
  return get('/combo/list', {
    page: params.page ?? 1,
    size: params.size ?? 50,
    keyword: params.keyword ?? '',
    status: params.status ?? null,
  })
}
export interface ComboDetailData {
  combo: Combo
  items: ComboItem[]
}
export function getComboDetail(id: number): Promise<ComboDetailData> {
  return get('/combo/detail', { id })
}
export interface ComboPayload {
  id?: number
  name: string
  type?: string
  status?: number
  note?: string
}
export function createCombo(payload: ComboPayload): Promise<{ id: number }> {
  return post('/combo/create', payload)
}
export function updateCombo(payload: ComboPayload): Promise<{ id: number }> {
  return post('/combo/update', payload)
}
export function deleteCombo(id: number): Promise<void> {
  return post('/combo/delete', { id })
}
export function addComboItem(payload: {
  combo_id: number
  item_id: number
  item_status?: string
  join_method?: number
}): Promise<{ id: number }> {
  return post('/combo_item/add', {
    combo_id: payload.combo_id,
    item_id: payload.item_id,
    item_status: payload.item_status ?? '',
    join_method: payload.join_method ?? 0,
  })
}
export function removeComboItem(comboItemId: number): Promise<void> {
  return post('/combo_item/remove', { combo_item_id: comboItemId })
}

// ---------------------------------------------------------------------------
// Log
// ---------------------------------------------------------------------------
export interface LogListParams {
  page?: number
  size?: number
  action?: string
  object_type?: string
}
export function listLogs(params: LogListParams = {}): Promise<Page<Log>> {
  return get('/log/list', {
    page: params.page ?? 1,
    size: params.size ?? 50,
    action: params.action ?? '',
    object_type: params.object_type ?? '',
  })
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------
export interface SearchParams {
  keyword?: string
  type?: string
  page?: number
  size?: number
}
export function searchItems(params: SearchParams = {}): Promise<Page<Item>> {
  return get('/search/keyword', {
    keyword: params.keyword ?? '',
    type: params.type ?? '',
    page: params.page ?? 1,
    size: params.size ?? 50,
  })
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------
export function uploadPhoto(file: File): Promise<{ path: string; thumb: string }> {
  const form = new FormData()
  form.append('file', file)
  return post('/upload/photo', form)
}
