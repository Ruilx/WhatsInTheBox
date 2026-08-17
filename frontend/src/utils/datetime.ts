// 时间字段与 dayjs 的双向转换（dev-plan v4 §7.13 时间原样展示，不做时区转换）。
//
// 背景：ant-design-vue 4.x 的 <a-date-picker> 使用 dayjs 对象作为值，
// 而接口契约（BoxPayload.first_using_time / ActivityPayload.start_time 等）
// 恒为 `YYYY-MM-DD HH:mm:ss` 字符串或 null。此处集中处理转换与边界：
// 空值、非法字符串一律降级为 undefined / null，绝不抛异常。

import dayjs, { type Dayjs } from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'

// 严格按约定格式解析（未启用该插件时 dayjs 会忽略第二个参数）
dayjs.extend(customParseFormat)

/** 后端约定的时间格式（与 MySQL DATETIME 展示一致）。 */
export const DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss'

/**
 * 字符串 -> picker 值。
 *
 * @param v 形如 `2024-05-01 12:00:00` 的字符串；空值 / 非法值返回 undefined
 *          （undefined 而非 null：picker 的空态用 undefined 表达更自然）
 */
export function toDatetimeValue(v?: string | null): Dayjs | undefined {
  if (!v) return undefined
  const raw = String(v).trim()
  if (!raw) return undefined
  // 1) 优先严格匹配约定格式
  const strict = dayjs(raw, DATETIME_FORMAT, true)
  if (strict.isValid()) return strict
  // 2) 兼容历史脏数据（仅日期 / ISO / 带 T 分隔符等），把空格换成 T 提升跨浏览器解析一致性
  const loose = dayjs(raw.replace(' ', 'T'))
  return loose.isValid() ? loose : undefined
}

/**
 * picker 值 -> 字符串（提交给后端）。
 *
 * @param v picker 抛出的值，可能是 Dayjs、字符串（配置了 valueFormat 时）或 null/undefined（清空）
 * @returns 合法时间返回 `YYYY-MM-DD HH:mm:ss`；空值 / 非法值返回 null
 */
export function fromDatetimeValue(v: unknown): string | null {
  if (v === null || v === undefined || v === '') return null
  if (dayjs.isDayjs(v)) return v.isValid() ? v.format(DATETIME_FORMAT) : null
  if (typeof v === 'string') {
    const parsed = toDatetimeValue(v)
    return parsed ? parsed.format(DATETIME_FORMAT) : null
  }
  return null
}
