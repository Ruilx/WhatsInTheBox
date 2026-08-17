// 活动详情（dev-plan v4 §3.3 / §8.1）。
// 活动信息 + 其下箱子列表（搜索 / 类型标签筛选 / 状态筛选 / 分页）。
// 子箱作为特殊行 + 「查看」钻取；行操作：查看物品 / 编辑 / 折叠（仅标志）。
// 「新建箱子」「已取出」入口 + 「复制活动 URL」。

<template>
  <div class="page-container" v-if="activity">
    <div class="page-header">
      <div>
        <RouterLink :to="`/${GLOBAL_PREFIX}/activities`" class="back-link">
          <Icon name="back" /> 活动列表
        </RouterLink>
        <h2 class="page-title">{{ activity.name }}</h2>
        <p class="muted" v-if="activity.desc">{{ activity.desc }}</p>
        <div class="meta">
          <a-tag :color="statusColor(activity.status)">
            {{ activityStatusText(activity.status) }}
          </a-tag>
          <span v-if="activity.type" class="muted">类型：{{ activity.type }}</span>
          <span v-if="activity.note" class="muted">备注：{{ activity.note }}</span>
        </div>
      </div>
      <div class="page-header__actions">
        <CopyUrlButton :url="activityAbsoluteUrl" />
        <RouterLink :to="takenOutUrl(activity.name)">
          <IconButton variant="default" label="已取出">
            <template #icon><Icon name="out" /></template>
          </IconButton>
        </RouterLink>
        <IconButton
          v-if="auth.isRw"
          variant="primary"
          label="新建箱子"
          @click="goCreateBox"
        >
          <template #icon><Icon name="plus" /></template>
        </IconButton>
      </div>
    </div>

    <div class="toolbar">
      <a-input
        v-model:value="kw"
        placeholder="搜索箱子名 / 描述 / 备注"
        allow-clear
        class="toolbar__search"
        @press-enter="reload(1)"
      />
      <a-select
        v-model:value="typeFilter"
        mode="multiple"
        placeholder="类型标签"
        :options="typeOptions"
        class="toolbar__select"
        @change="reload(1)"
      />
      <a-select
        v-model:value="statusFilter"
        placeholder="状态"
        allow-clear
        class="toolbar__select"
        @change="reload(1)"
      >
        <a-select-option v-for="(t, i) in BOX_STATUS" :key="i" :value="i">
          {{ t }}
        </a-select-option>
      </a-select>
      <IconButton variant="primary" label="搜索" @click="reload(1)">
        <template #icon><Icon name="search" /></template>
      </IconButton>
    </div>

    <div class="table-scroll">
      <table class="wb-grid">
        <thead>
          <tr>
            <th>名称</th>
            <th class="hide-mobile">类型</th>
            <th>状态</th>
            <th class="hide-mobile">父箱</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="box in topBoxes" :key="box.id">
            <tr>
              <td>
                <RouterLink :to="boxUrl(activity.name, box.name)">{{ box.name }}</RouterLink>
              </td>
              <td class="hide-mobile">
                <a-tag v-for="t in box.type" :key="t" color="blue">{{ t }}</a-tag>
              </td>
              <td>
                <a-tag :color="boxStatusColor(box.status)">{{ boxStatusText(box.status) }}</a-tag>
              </td>
              <td class="muted hide-mobile">—</td>
              <td class="col-actions">
                <span class="row-actions">
                  <IconButton variant="ghost" title="查看物品" @click="openBox(box)">
                    <template #icon><Icon name="box" /></template>
                  </IconButton>
                  <IconButton
                    v-if="auth.isRw"
                    variant="ghost"
                    title="编辑"
                    @click="goEditBox(box)"
                  >
                    <template #icon><Icon name="edit" /></template>
                  </IconButton>
                  <IconButton
                    v-if="auth.isRw"
                    variant="ghost"
                    title="折叠 / 展开"
                    @click="toggleFold(box)"
                  >
                    <template #icon><Icon name="fold" /></template>
                  </IconButton>
                </span>
              </td>
            </tr>
            <tr v-for="child in childrenOf(box.id)" :key="child.id" class="row--sub">
              <td class="sub-name">
                <span class="sub-badge">子箱</span>
                <RouterLink :to="boxUrl(activity.name, child.name)">{{ child.name }}</RouterLink>
              </td>
              <td class="hide-mobile">
                <a-tag v-for="t in child.type" :key="t" color="blue">{{ t }}</a-tag>
              </td>
              <td>
                <a-tag :color="boxStatusColor(child.status)">
                  {{ boxStatusText(child.status) }}
                </a-tag>
              </td>
              <td class="muted hide-mobile">{{ box.name }}</td>
              <td class="col-actions">
                <span class="row-actions">
                  <IconButton variant="ghost" title="查看钻取" @click="openBox(child)">
                    <template #icon><Icon name="eye" /></template>
                  </IconButton>
                  <IconButton
                    v-if="auth.isRw"
                    variant="ghost"
                    title="编辑"
                    @click="goEditBox(child)"
                  >
                    <template #icon><Icon name="edit" /></template>
                  </IconButton>
                </span>
              </td>
            </tr>
          </template>
          <tr v-if="!loading && topBoxes.length === 0">
            <td colspan="5" class="empty">暂无箱子</td>
          </tr>
        </tbody>
      </table>
    </div>

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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getActivity, listBoxes, foldBox, type BoxListParams } from '@/api'
import { useAuthStore } from '@/store/auth'
import { encodeSeg, boxUrl, takenOutUrl, activityUrl, GLOBAL_PREFIX } from '@/utils/url'
import {
  BOX_STATUS,
  BOX_TYPE_PRESETS,
  boxStatusText,
  activityStatusText,
} from '@/utils/format'
import type { Activity, Box } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'
import CopyUrlButton from '@/components/CopyUrlButton.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const activityName = decodeURIComponent((route.params.activityName as string) || '')

const activity = ref<Activity | null>(null)
const allBoxes = ref<Box[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(50)
const kw = ref('')
const typeFilter = ref<string[]>([])
const statusFilter = ref<number | undefined>(undefined)
const loading = ref(false)

const typeOptions = BOX_TYPE_PRESETS.map((t) => ({ label: t, value: t }))
const activityAbsoluteUrl = computed(() =>
  activity.value ? window.location.origin + activityUrl(activity.value.name) : '',
)

function statusColor(s: number): string {
  return (['default', 'green', 'red', 'default'] as const)[s] ?? 'default'
}
function boxStatusColor(s: number): string {
  return (['green', 'default', 'blue', 'gold', 'red', 'default'] as const)[s] ?? 'default'
}

const topBoxes = computed(() => allBoxes.value.filter((b) => !b.parent_box_id))
function childrenOf(id: number): Box[] {
  return allBoxes.value.filter((b) => b.parent_box_id === id)
}

async function reload(p?: number): Promise<void> {
  if (!activity.value) return
  if (p) page.value = p
  loading.value = true
  try {
    const params: BoxListParams = {
      activity_id: activity.value.id,
      page: page.value,
      size: size.value,
      keyword: kw.value,
      type: typeFilter.value.join(','),
      status: statusFilter.value,
    }
    const data = await listBoxes(params)
    allBoxes.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function loadActivity(): Promise<void> {
  try {
    activity.value = await getActivity(undefined, activityName)
    await reload(1)
  } catch {
    message.error('活动不存在')
  }
}

function openBox(box: Box): void {
  router.push(boxUrl(activity.value!.name, box.name))
}
function goCreateBox(): void {
  router.push(`/${encodeSeg(activity.value!.name)}/box/edit`)
}
function goEditBox(box: Box): void {
  router.push(`/${encodeSeg(activity.value!.name)}/box/edit/${box.id}`)
}
async function toggleFold(box: Box): Promise<void> {
  const next = box.status === 1 ? 0 : 1
  try {
    await foldBox(box.id, next)
    message.success('已更新')
    reload()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(loadActivity)
</script>
