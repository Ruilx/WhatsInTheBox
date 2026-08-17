// 联合物品列表（dev-plan v4 §3.3）。
// 搜索 + 状态筛选 + 分页；「新建联合物品」仅 rw 可见；行操作：编辑 / 删除。

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">联合物品</h2>
      <IconButton v-if="auth.isRw" variant="primary" label="新建联合物品" @click="goCreate">
        <template #icon><Icon name="plus" /></template>
      </IconButton>
    </div>

    <div class="toolbar">
      <a-input
        v-model:value="kw"
        placeholder="搜索名称"
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
        <a-select-option v-for="(t, i) in COMBO_STATUS" :key="i" :value="i">{{ t }}</a-select-option>
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
          <RouterLink :to="`/${GLOBAL_PREFIX}/combos/${record.id}/edit`">{{ record.name }}</RouterLink>
          <span v-if="record.type" class="muted">· {{ record.type }}</span>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="record.status === 0 ? 'green' : 'default'">
            {{ comboStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <span class="row-actions">
            <IconButton variant="ghost" title="编辑" @click="goEdit(record)">
              <template #icon><Icon name="edit" /></template>
            </IconButton>
            <a-popconfirm
              v-if="auth.isRw"
              title="确认删除该联合物品？"
              ok-text="删除"
              cancel-text="取消"
              @confirm="remove(record)"
            >
              <IconButton variant="ghost" title="删除">
                <template #icon><Icon name="trash" /></template>
              </IconButton>
            </a-popconfirm>
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
import { listCombos, deleteCombo, type ComboListParams } from '@/api'
import { useAuthStore } from '@/store/auth'
import { GLOBAL_PREFIX } from '@/utils/url'
import type { TableColumnsType } from 'ant-design-vue'
import { COMBO_STATUS, comboStatusText } from '@/utils/format'
import type { Combo } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const auth = useAuthStore()
const router = useRouter()

const list = ref<Combo[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(50)
const kw = ref('')
const statusFilter = ref<number | undefined>(undefined)
const loading = ref(false)

const columns: TableColumnsType = [
  { title: '名称', key: 'name', width: '28%' },
  { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true, className: 'hide-mobile' },
  { title: '状态', key: 'status', width: 110 },
  { title: '操作', key: 'action', width: 140, align: 'right' },
]

async function reload(p?: number): Promise<void> {
  if (p) page.value = p
  loading.value = true
  try {
    const params: ComboListParams = {
      page: page.value,
      size: size.value,
      keyword: kw.value,
      status: statusFilter.value,
    }
    const data = await listCombos(params)
    list.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function goCreate(): void {
  router.push(`/${GLOBAL_PREFIX}/combos/edit`)
}
function goEdit(record: Combo): void {
  router.push(`/${GLOBAL_PREFIX}/combos/${record.id}/edit`)
}
async function remove(record: Combo): Promise<void> {
  try {
    await deleteCombo(record.id)
    message.success('已删除')
    reload()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(reload)
</script>
