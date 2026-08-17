// 全局搜索（dev-plan v4 §3.3 / §7）。
// 关键字（name/desc/note 模糊）+ 可选 type，跨活动聚合。结果点击可打开所属箱子。

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">搜索</h2>
    </div>

    <div class="toolbar">
      <a-input
        v-model:value="kw"
        placeholder="搜索物品名 / 描述 / 备注"
        allow-clear
        class="toolbar__search"
        @press-enter="reload(1)"
      />
      <a-input
        v-model:value="typeFilter"
        placeholder="类型（可选）"
        allow-clear
        class="toolbar__select"
        @press-enter="reload(1)"
      />
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
          <span>{{ record.name }}</span>
          <span v-if="record.type" class="muted">· {{ record.type }}</span>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="itemStatusColor(record.status)">{{ itemStatusText(record.status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'location'">
          <span class="muted" v-if="record.box_id">箱 #{{ record.box_id }}</span>
          <span class="muted" v-else>已取出</span>
          <span class="muted"> · 活动 #{{ record.activity_id }}</span>
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
    <a-empty v-if="!loading && total === 0" description="没有匹配结果" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { searchItems, type SearchParams } from '@/api'
import type { TableColumnsType } from 'ant-design-vue'
import { itemStatusText } from '@/utils/format'
import type { Item } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const list = ref<Item[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(50)
const kw = ref('')
const typeFilter = ref('')
const loading = ref(false)

const columns: TableColumnsType = [
  { title: '名称', key: 'name', width: '26%' },
  { title: '状态', key: 'status', width: 110 },
  { title: '位置', key: 'location', width: 200 },
  { title: '活动ID', dataIndex: 'activity_id', key: 'activity_id', width: 90, className: 'hide-mobile' },
  { title: '箱ID', dataIndex: 'box_id', key: 'box_id', width: 80, className: 'hide-mobile' },
  { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true, className: 'hide-mobile' },
]

function itemStatusColor(s: number): string {
  return (['green', 'blue', 'gold', 'red', 'red'] as const)[s] ?? 'default'
}

async function reload(p?: number): Promise<void> {
  if (p) page.value = p
  loading.value = true
  try {
    const params: SearchParams = {
      keyword: kw.value,
      type: typeFilter.value,
      page: page.value,
      size: size.value,
    }
    const data = await searchItems(params)
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
