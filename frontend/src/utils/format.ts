// 枚举文案映射（dev-plan v4 §7.13 / §8.1）。时间原样展示，不做时区转换。

export function fmtTime(v?: string | null): string {
  if (!v) return ''
  return v
}

export const ACTIVITY_STATUS = ['草稿', '进行中', '已停止', '已归档']
export const BOX_STATUS = ['打开', '折叠', '封存', '运输中', '损伤', '淘汰']
export const ITEM_STATUS = ['在箱', '已取出', '借出', '损坏', '遗失']
export const COMBO_STATUS = ['正常', '失效']
export const JOIN_METHOD = ['原装', '补配', '已替代']

export function activityStatusText(s: number): string {
  return ACTIVITY_STATUS[s] ?? String(s)
}
export function boxStatusText(s: number): string {
  return BOX_STATUS[s] ?? String(s)
}
export function itemStatusText(s: number): string {
  return ITEM_STATUS[s] ?? String(s)
}
export function comboStatusText(s: number): string {
  return COMBO_STATUS[s] ?? String(s)
}
export function joinMethodText(s: number): string {
  return JOIN_METHOD[s] ?? String(s)
}

/** 箱子默认多标签（dev-plan v4 §8.1） */
export const BOX_TYPE_PRESETS = [
  '主要',
  '次要',
  '易碎',
  '需保护',
  '防水',
  '要求向上',
  '旧箱',
]
