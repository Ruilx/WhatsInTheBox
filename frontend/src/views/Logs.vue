// 日志列表（dev-plan v4 §3.3 / §7.21）。
// 按 action / object_type 筛选 + 分页（每页 50）。读操作也全量记录。

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
    </div>

    <div class="toolbar">
      <a-select
        v-model:value="actionFilter"
        placeholder="操作类型"
        allow-clear
        class="toolbar__select"
        @change="reload(1)"
      >
        <a-select-option v-for="a in ACTIONS" :key="a" :value="a">{{ a }}</a-select-option>
      </a-select>
      <a-select
        v-model:value="typeFilter"
        placeholder="对象类型"
        allow-clear
        class="toolbar__select"
        @change="reload(1)"
      >
        <a-select-option v-for="t in OBJECT_TYPES" :key="t" :value="t">{{ t }}</a-select-option>
      </a-select>
      <IconButton variant="primary" label="刷新" @click="reload(1)">
        <template #icon><Icon name="log" /></template>
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
        <template v-if="column.key === 'action'">
          <a-tag :color="actionColor(record.action)">{{ record.action }}</a-tag>
        </template>
        <template v-else-if="column.key === 'object_type'">
          <span class="muted">{{ record.object_type || '—' }}</span>
        </template>
        <template v-else-if="column.key === 'object_id'">
          <span class="muted">{{ record.object_id }}</span>
        </template>
        <template v-else-if="column.key === 'user_id'">
          <span class="muted">{{ record.user_id }}</span>
        </template>
        <template v-else-if="column.key === 'detail'">
          <span class="log-detail">{{ record.detail }}</span>
        </template>
        <template v-else-if="column.key === 'create_time'">
          <span class="muted">{{ fmtTime(record.create_time) }}</span>
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
import { listLogs, type LogListParams } from '@/api'
import type { TableColumnsType } from 'ant-design-vue'
import { fmtTime } from '@/utils/format'
import type { Log } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const ACTIONS = [
  'query',
  'view',
  'create',
  'update',
  'delete',
  'take_out',
  'place',
  'login',
  'logout',
  'scan',
]
const OBJECT_TYPES = ['activity', 'box', 'item', 'combo']

const list = ref<Log[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(50)
const actionFilter = ref<string | undefined>(undefined)
const typeFilter = ref<string | undefined>(undefined)
const loading = ref(false)

const columns: TableColumnsType = [
  { title: '时间', key: 'create_time', width: 170, className: 'hide-mobile' },
  { title: '操作', key: 'action', width: 110 },
  { title: '对象', key: 'object_type', width: 100, className: 'hide-mobile' },
  { title: '对象ID', key: 'object_id', width: 90, className: 'hide-mobile' },
  { title: '用户', key: 'user_id', width: 80, className: 'hide-mobile' },
  { title: '详情', key: 'detail' },
]

function actionColor(a: string): string {
  const map: Record<string, string> = {
    create: 'green',
    update: 'blue',
    delete: 'red',
    take_out: 'gold',
    query: 'default',
    view: 'default',
    scan: 'default',
    login: 'cyan',
    logout: 'cyan',
    place: 'geekblue',
  }
  return map[a] ?? 'default'
}

async function reload(p?: number): Promise<void> {
  if (p) page.value = p
  loading.value = true
  try {
    const params: LogListParams = {
      page: page.value,
      size: size.value,
      action: actionFilter.value,
      object_type: typeFilter.value,
    }
    const data = await listLogs(params)
    list.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>

<style scoped>
.log-detail {
  color: var(--color-text-secondary);
  word-break: break-all;
}
</style>
