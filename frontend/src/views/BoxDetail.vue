// 箱子详情（dev-plan v4 §3.3 / §7.14）。
// 箱子信息 + 其下物品列表（搜索 / 状态筛选 / 分页）。
// 行操作：编辑 / 取出 / 删除（rw）；取出后进该活动「已取出」。
// 子箱作为特殊行 + 「查看」钻取。提供「新建物品」「复制箱子 URL」（无二维码）。

<template>
  <div class="page-container" v-if="box">
    <div class="page-header">
      <div>
        <RouterLink :to="activityUrl(activityName)" class="back-link">
          <Icon name="back" /> {{ activityName }}
        </RouterLink>
        <h2 class="page-title">{{ box.name }}</h2>
        <div class="meta">
          <a-tag :color="boxStatusColor(box.status)">{{ boxStatusText(box.status) }}</a-tag>
          <a-tag v-for="t in box.type" :key="t" color="blue">{{ t }}</a-tag>
        </div>
        <p class="muted" v-if="box.desc">{{ box.desc }}</p>
        <div class="meta" v-if="box.size || box.material || box.serial_no || box.note">
          <span v-if="box.size" class="muted">尺寸：{{ box.size }}</span>
          <span v-if="box.material" class="muted">材质：{{ box.material }}</span>
          <span v-if="box.serial_no" class="muted">串号：{{ box.serial_no }}</span>
          <span v-if="box.note" class="muted">备注：{{ box.note }}</span>
        </div>
      </div>
      <div class="page-header__actions">
        <CopyUrlButton :url="boxAbsoluteUrl" />
        <IconButton v-if="auth.isRw" variant="primary" label="新建物品" @click="goCreateItem">
          <template #icon><Icon name="plus" /></template>
        </IconButton>
      </div>
    </div>

    <div v-if="box.photo" class="box-photo">
      <img :src="uploadUrl(box.photo)" alt="箱子照片" />
    </div>

    <div class="toolbar">
      <a-input
        v-model:value="kw"
        placeholder="搜索物品名 / 描述 / 备注"
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
        <a-select-option v-for="(t, i) in ITEM_STATUS" :key="i" :value="i">
          {{ t }}
        </a-select-option>
      </a-select>
      <IconButton variant="primary" label="搜索" @click="reload(1)">
        <template #icon><Icon name="search" /></template>
      </IconButton>
    </div>

    <!-- 子箱特殊行 + 物品列表 -->
    <div class="table-scroll">
      <table class="wb-grid">
        <thead>
          <tr>
            <th>名称</th>
            <th class="hide-mobile">类型</th>
            <th>状态</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cb in childBoxes" :key="'cb-' + cb.id" class="row--sub">
            <td class="sub-name">
              <span class="sub-badge">子箱</span>
              <RouterLink :to="boxUrl(activityName, cb.name)">{{ cb.name }}</RouterLink>
            </td>
            <td class="hide-mobile">
              <a-tag v-for="t in cb.type" :key="t" color="blue">{{ t }}</a-tag>
            </td>
            <td>
              <a-tag :color="boxStatusColor(cb.status)">{{ boxStatusText(cb.status) }}</a-tag>
            </td>
            <td class="col-actions">
              <span class="row-actions">
                <IconButton variant="ghost" title="查看钻取" @click="openBox(cb)">
                  <template #icon><Icon name="eye" /></template>
                </IconButton>
              </span>
            </td>
          </tr>

          <tr v-for="item in items" :key="item.id">
            <td>
              <RouterLink
                v-if="item.box_id"
                :to="`/${encodeSeg(activityName)}/item/edit/${item.id}`"
                >{{ item.name }}</RouterLink
              >
              <span v-else>{{ item.name }}</span>
            </td>
            <td class="hide-mobile muted">{{ item.type || '—' }}</td>
            <td>
              <a-tag :color="itemStatusColor(item.status)">{{ itemStatusText(item.status) }}</a-tag>
            </td>
            <td class="col-actions">
              <span class="row-actions">
                <IconButton
                  v-if="auth.isRw"
                  variant="ghost"
                  title="编辑"
                  @click="goEditItem(item)"
                >
                  <template #icon><Icon name="edit" /></template>
                </IconButton>
                <IconButton
                  v-if="auth.isRw && item.status !== 1"
                  variant="ghost"
                  title="取出"
                  @click="takeOut(item)"
                >
                  <template #icon><Icon name="out" /></template>
                </IconButton>
                <a-popconfirm
                  v-if="auth.isRw"
                  title="确认删除该物品？"
                  ok-text="删除"
                  cancel-text="取消"
                  @confirm="remove(item)"
                >
                  <IconButton variant="ghost" title="删除">
                    <template #icon><Icon name="trash" /></template>
                  </IconButton>
                </a-popconfirm>
              </span>
            </td>
          </tr>

          <tr v-if="!loading && items.length === 0 && childBoxes.length === 0">
            <td colspan="4" class="empty">暂无物品或子箱</td>
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
import {
  getBoxDetail,
  listItems,
  takeOutItem,
  deleteItem,
  uploadUrl as toUrl,
  type ItemListParams,
} from '@/api'
import { useAuthStore } from '@/store/auth'
import { encodeSeg, boxUrl, activityUrl } from '@/utils/url'
import { BOX_STATUS, ITEM_STATUS, boxStatusText, itemStatusText } from '@/utils/format'
import type { Box, Item } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'
import CopyUrlButton from '@/components/CopyUrlButton.vue'

// 局部别名，避免与模板中同名导入冲突
const uploadUrl = toUrl

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const activityName = decodeURIComponent((route.params.activityName as string) || '')
const boxName = decodeURIComponent((route.params.boxName as string) || '')

const box = ref<Box | null>(null)
const childBoxes = ref<Box[]>([])
const items = ref<Item[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(50)
const kw = ref('')
const statusFilter = ref<number | undefined>(undefined)
const loading = ref(false)

const boxAbsoluteUrl = computed(() =>
  box.value ? window.location.origin + boxUrl(activityName, box.value.name) : '',
)

function boxStatusColor(s: number): string {
  return (['green', 'default', 'blue', 'gold', 'red', 'default'] as const)[s] ?? 'default'
}
function itemStatusColor(s: number): string {
  return (['green', 'blue', 'gold', 'red', 'red'] as const)[s] ?? 'default'
}

async function reload(p?: number): Promise<void> {
  if (!box.value) return
  if (p) page.value = p
  loading.value = true
  try {
    const params: ItemListParams = {
      box_id: box.value.id,
      page: page.value,
      size: size.value,
      keyword: kw.value,
      status: statusFilter.value,
    }
    const data = await listItems(params)
    items.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function loadBox(): Promise<void> {
  try {
    const data = await getBoxDetail(activityName, boxName)
    box.value = data.box
    childBoxes.value = data.child_boxes || []
    await reload(1)
  } catch {
    message.error('箱子不存在')
  }
}

function openBox(cb: Box): void {
  router.push(boxUrl(activityName, cb.name))
}
function goCreateItem(): void {
  router.push(
    `/${encodeSeg(activityName)}/item/edit?box=${box.value!.id}&activity=${box.value!.activity_id}`,
  )
}
function goEditItem(item: Item): void {
  router.push(`/${encodeSeg(activityName)}/item/edit/${item.id}`)
}
async function takeOut(item: Item): Promise<void> {
  try {
    await takeOutItem(item.id)
    message.success('已取出')
    reload()
  } catch {
    /* 拦截器已提示 */
  }
}
async function remove(item: Item): Promise<void> {
  try {
    await deleteItem(item.id)
    message.success('已删除')
    reload()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(loadBox)
</script>

<style scoped>
.box-photo {
  margin-bottom: var(--space);
}
.box-photo img {
  max-height: 220px;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}
</style>
