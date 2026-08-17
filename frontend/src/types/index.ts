// 共享类型定义

export interface UserInfo {
  id: number
  username: string
  role: string
}

export interface Activity {
  id: number
  name: string
  desc: string
  type: string
  start_time?: string | null
  end_time?: string | null
  status: number
  note: string
}

export interface Box {
  id: number
  activity_id: number
  name: string
  desc: string
  type: string[]
  size: string
  material: string
  parent_box_id?: number | null
  status: number
  serial_no: string
  note: string
  photo?: string
  thumb?: string
  first_using_time?: string | null
}

export interface Item {
  id: number
  name: string
  desc: string
  type: string
  activity_id: number
  box_id: number
  status: number
  note: string
  photo?: string
  thumb?: string
}

export interface Combo {
  id: number
  name: string
  type: string
  status: number
  note: string
}

export interface ComboItem {
  combo_item_id: number
  combo_id: number
  item_id: number
  item_status: string
  join_method: number
  item_name?: string
  item_type?: string
}

export interface Log {
  id: number
  action: string
  object_type: string
  object_id: number
  user_id: number
  detail: string
  ip?: string | null
  create_time?: string
}

export interface Page<T> {
  list: T[]
  total: number
  page: number
  size: number
}
