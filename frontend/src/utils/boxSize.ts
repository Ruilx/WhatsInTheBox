// 纸箱尺寸：常用预置 + 本机使用频率记忆（dev-plan v4 §8.1 箱子属性）。
//
// - 仅落 localStorage（不跨设备、不调接口、不进后端数据结构）。
// - 与 BOX_TYPE_PRESETS（类型标签预置）无关，两者互不影响。
// - 存储数据损坏 / 隐私模式写入失败时静默降级，仅丢失「记忆」能力，不影响表单主流程。

/** 常用纸箱尺寸预置（始终出现在候选列表中）。 */
export const BOX_SIZE_PRESETS: readonly string[] = [
  '60x40x50cm',
  '70x50x50cm',
  '80x60x50cm',
]

const STORAGE_KEY = 'wb-box-sizes'

/** 单条尺寸使用记录。 */
interface SizeUsage {
  /** 尺寸文本（用户可见即存储值） */
  size: string
  /** 累计使用次数，用于频率排序 */
  count: number
  /** 最近一次使用时间戳（ms），频率相同时用于次级排序 */
  last: number
}

/** 把任意来源的一条记录规整为 SizeUsage；不合法返回 null。 */
function normalizeUsage(raw: unknown): SizeUsage | null {
  if (!raw || typeof raw !== 'object') return null
  const rec = raw as Record<string, unknown>
  const size = typeof rec.size === 'string' ? rec.size.trim() : ''
  if (!size) return null
  const count =
    typeof rec.count === 'number' && Number.isFinite(rec.count) && rec.count > 0
      ? Math.floor(rec.count)
      : 1
  const last =
    typeof rec.last === 'number' && Number.isFinite(rec.last) && rec.last > 0 ? rec.last : 0
  return { size, count, last }
}

/** 读取本机历史记录（异常 / 脏数据一律回退为空列表）。 */
function readUsage(): SizeUsage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
      .map(normalizeUsage)
      .filter((it): it is SizeUsage => it !== null)
  } catch {
    return []
  }
}

/** 写回本机历史记录（写入失败静默忽略）。 */
function writeUsage(list: SizeUsage[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
  } catch {
    /* 隐私模式 / 配额不足：记忆功能降级，不影响保存流程 */
  }
}

/**
 * 记录一次尺寸使用（预置项同样计数，保证列表真正按「本机使用频率」排序）。
 *
 * @param size 用户最终提交的尺寸文本；空值直接忽略
 */
export function rememberBoxSize(size?: string | null): void {
  const value = (size ?? '').trim()
  if (!value) return
  const list = readUsage()
  const hit = list.find((it) => it.size === value)
  if (hit) {
    hit.count += 1
    hit.last = Date.now()
  } else {
    list.push({ size: value, count: 1, last: Date.now() })
  }
  writeUsage(list)
}

/**
 * 尺寸候选列表 = 预置 ∪ 本机历史。
 * 排序：使用次数降序 -> 最近使用降序 -> 字母序（保证无历史时预置顺序稳定）。
 */
export function listBoxSizes(): string[] {
  const usage = new Map<string, SizeUsage>()
  BOX_SIZE_PRESETS.forEach((size, idx) => {
    // last 用递减序号占位，使「零使用」的预置项保持声明顺序
    usage.set(size, { size, count: 0, last: BOX_SIZE_PRESETS.length - idx })
  })
  for (const it of readUsage()) {
    const hit = usage.get(it.size)
    if (hit) {
      hit.count += it.count
      hit.last = Math.max(hit.last, it.last)
    } else {
      usage.set(it.size, { ...it })
    }
  }
  return [...usage.values()]
    .sort((a, b) => b.count - a.count || b.last - a.last || a.size.localeCompare(b.size))
    .map((it) => it.size)
}
