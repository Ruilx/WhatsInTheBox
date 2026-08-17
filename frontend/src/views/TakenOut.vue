// 活动内「已取出」列表（dev-plan v4 §3.3 / §7.14）。
// 路由 /:activityName/已取出：按活动归集 box_id=0 的物品。
// 行操作：编辑（可在 ItemEdit 中重新指定所属箱以放回）。

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <RouterLink :to="activityUrl(activityName)" class="back-link">
          <Icon name="back" /> {{ activityName }}
        </RouterLink>
        <h2 class="page-title">已取出</h2>
        <p class="muted">本活动中已取出（未放入任何箱子）的物品</p>
      </div>
      <CopyUrlButton :url="windowOrigin + takenOutUrl(activityName)" />
    </div>

    <div class="toolbar">
      <a-input
        v-model:value="kw"
        placeholder="搜索物品名 / 描述 / 备注"
        allow-clear
        class="toolbar__search"
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
          <a-tag color="blue">{{ itemStatusText(record.status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <span class="row-actions">
            <IconButton
              v-if="auth.isRw"
              variant="ghost"
              title="编辑 / 重新放入"
              @click="goEdit(record)"
            >
              <template #icon><Icon name="edit" /></template>
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
    <a-empty v-if="!loading && total === 0" description="暂无已取出物品" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getActivity, listTakenOut, type TakenOutParams } from '@/api'
import { useAuthStore } from '@/store/auth'
import { encodeSeg, takenOutUrl, activityUrl } from '@/utils/url'
import type { TableColumnsType } from 'ant-design-vue'
import { itemStatusText } from '@/utils/format'
import type { Item } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'
import CopyUrlButton from '@/components/CopyUrlButton.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const activityName = decodeURIComponent((route.params.activityName as string) || '')
const windowOrigin = window.location.origin

const list = ref<Item[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(50)
const kw = ref('')
const loading = ref(false)
const activityId = ref(0)

const columns: TableColumnsType = [
  { title: '名称', key: 'name', width: '30%' },
  { title: '状态', key: 'status', width: 110 },
  { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true, className: 'hide-mobile' },
  { title: '操作', key: 'action', width: 120, align: 'right' },
]

async function reload(p?: number): Promise<void> {
  if (p) page.value = p
  loading.value = true
  try {
    const params: TakenOutParams = {
      activity_id: activityId.value,
      page: page.value,
      size: size.value,
      keyword: kw.value,
    }
    const data = await listTakenOut(params)
    list.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function loadActivity(): Promise<void> {
  try {
    const act = await getActivity(undefined, activityName)
    activityId.value = act.id
    await reload(1)
  } catch {
    message.error('活动不存在')
  }
}

function goEdit(item: Item): void {
  router.push(`/${encodeSeg(activityName)}/item/edit/${item.id}`)
}

onMounted(loadActivity)
</script>
