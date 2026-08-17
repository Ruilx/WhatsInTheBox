// 活动列表（dev-plan v4 §3.3）。
// 搜索框 + 状态筛选 + 分页（每页 50）。「新建活动」仅 rw 可见；
// 行操作：查看箱子 / 编辑 / 开始·停止（rw）。

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">活动列表</h2>
      <IconButton v-if="auth.isRw" variant="primary" label="新建活动" @click="goCreate">
        <template #icon><Icon name="plus" /></template>
      </IconButton>
    </div>

    <div class="toolbar">
      <a-input
        v-model:value="kw"
        placeholder="搜索名称 / 描述 / 备注"
        allow-clear
        class="toolbar__search"
        @press-enter="reload(1)"
      />
      <a-select
        v-model:value="statusFilter"
        placeholder="状态"
        allow-clear
        class="toolbar__select"
        @change="reload(1)"
      >
        <a-select-option v-for="(t, i) in ACTIVITY_STATUS" :key="i" :value="i">
          {{ t }}
        </a-select-option>
      </a-select>
      <IconButton variant="primary" label="搜索" @click="reload(1)">
        <template #icon><Icon name="search" /></template>
      </IconButton>
    </div>

    <a-table
      :columns="columns"
      :data-source="list"
      :loading="loading"
      :pagination="false"
      row-key="id"
      size="middle"
      class="wb-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <RouterLink :to="activityUrl(record.name)">{{ record.name }}</RouterLink>
          <span v-if="record.type" class="muted">· {{ record.type }}</span>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">
            {{ activityStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <span class="row-actions">
            <IconButton variant="ghost" title="查看箱子" @click="open(record)">
              <template #icon><Icon name="box" /></template>
            </IconButton>
            <IconButton v-if="auth.isRw" variant="ghost" title="编辑" @click="goEdit(record)">
              <template #icon><Icon name="edit" /></template>
            </IconButton>
            <IconButton
              v-if="auth.isRw"
              variant="ghost"
              title="开始 / 停止"
              @click="toggle(record)"
            >
              <template #icon><Icon name="power" /></template>
            </IconButton>
          </span>
        </template>
      </template>
    </a-table>

    <div class="pager" v-if="total > 0">
      <a-pagination
        v-model:current="page"
        :total="total"
        :page-size="size"
        show-less-items
        @change="reload"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  listActivities,
  toggleActivityStatus,
  type ActivityListParams,
} from '@/api'
import { useAuthStore } from '@/store/auth'
import { GLOBAL_PREFIX, activityUrl } from '@/utils/url'
import type { TableColumnsType } from 'ant-design-vue'
import { ACTIVITY_STATUS, activityStatusText } from '@/utils/format'
import type { Activity } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const auth = useAuthStore()
const router = useRouter()

const list = ref<Activity[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(50)
const kw = ref('')
const statusFilter = ref<number | undefined>(undefined)
const loading = ref(false)

const columns: TableColumnsType = [
  { title: '名称', key: 'name', width: '28%' },
  { title: '描述', dataIndex: 'desc', key: 'desc', ellipsis: true, className: 'hide-mobile' },
  { title: '状态', key: 'status', width: 110 },
  { title: '操作', key: 'action', width: 170, align: 'right' },
]

function statusColor(s: number): string {
  return (['default', 'green', 'red', 'default'] as const)[s] ?? 'default'
}

async function reload(p?: number): Promise<void> {
  if (p) page.value = p
  loading.value = true
  try {
    const params: ActivityListParams = {
      page: page.value,
      size: size.value,
      keyword: kw.value,
      type: '',
      status: statusFilter.value,
    }
    const data = await listActivities(params)
    list.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function open(record: Activity): void {
  router.push(activityUrl(record.name))
}
function goCreate(): void {
  router.push(`/${GLOBAL_PREFIX}/activity/edit`)
}
function goEdit(record: Activity): void {
  router.push(`/${GLOBAL_PREFIX}/activity/edit/${record.id}`)
}
async function toggle(record: Activity): Promise<void> {
  const next = record.status === 1 ? 2 : 1
  try {
    await toggleActivityStatus(record.id, next)
    message.success('状态已更新')
    reload()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(reload)
</script>
