// 联合物品新建 / 编辑（dev-plan v4 §3.3 / §7.13）。
// 路由 /{GLOBAL_PREFIX}/combos/:id?/edit（id 缺省为新建）。
// 成员（combo_item）：增删、join_method（原装/补配/已替代）。

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <RouterLink :to="`/${GLOBAL_PREFIX}/combos`" class="back-link">
          <Icon name="back" /> 联合物品
        </RouterLink>
        <h2 class="page-title">{{ isEdit ? '编辑联合物品' : '新建联合物品' }}</h2>
      </div>
    </div>

    <div class="wb-card form-grid">
      <a-form layout="vertical">
        <a-form-item label="名称" required>
          <a-input v-model:value="form.name" placeholder="联合物品名称" :maxlength="128" />
        </a-form-item>
        <a-form-item label="类型">
          <a-input v-model:value="form.type" placeholder="类型（自由文本）" />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="form.status">
            <a-select-option v-for="(t, i) in COMBO_STATUS" :key="i" :value="i">{{ t }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="form.note" :rows="2" placeholder="备注" />
        </a-form-item>

        <!-- 成员管理（仅编辑已有联合物品时） -->
        <template v-if="isEdit">
          <a-divider orientation="left">成员</a-divider>
          <div class="members">
            <div v-for="m in members" :key="m.combo_item_id" class="member-row">
              <span class="member-name">{{ m.item_name || ('物品 #' + m.item_id) }}</span>
              <a-tag :color="joinColor(m.join_method)">{{ joinMethodText(m.join_method) }}</a-tag>
              <span class="muted" v-if="m.item_status">· {{ m.item_status }}</span>
              <span class="row-actions member-actions" v-if="auth.isRw">
                <IconButton variant="ghost" title="移除成员" @click="removeMember(m)">
                  <template #icon><Icon name="trash" /></template>
                </IconButton>
              </span>
            </div>
            <div v-if="members.length === 0" class="muted">暂无成员</div>
          </div>

          <div v-if="auth.isRw" class="add-member">
            <span class="muted">新增成员：</span>
            <a-input-number v-model:value="newItemId" :min="1" placeholder="物品 ID" />
            <a-select v-model:value="newJoin" class="add-member__join">
              <a-select-option v-for="(t, i) in JOIN_METHOD" :key="i" :value="i">{{ t }}</a-select-option>
            </a-select>
            <IconButton variant="primary" label="添加" :disabled="!newItemId" @click="addMember">
              <template #icon><Icon name="plus" /></template>
            </IconButton>
          </div>
        </template>

        <div class="form-actions">
          <IconButton variant="primary" label="保存" :disabled="saving" @click="save">
            <template #icon><Icon name="edit" /></template>
          </IconButton>
          <RouterLink :to="`/${GLOBAL_PREFIX}/combos`">
            <IconButton variant="default" label="取消" />
          </RouterLink>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  getComboDetail,
  createCombo,
  updateCombo,
  addComboItem,
  removeComboItem,
  type ComboPayload,
} from '@/api'
import { useAuthStore } from '@/store/auth'
import { GLOBAL_PREFIX } from '@/utils/url'
import { COMBO_STATUS, JOIN_METHOD, joinMethodText } from '@/utils/format'
import type { ComboItem } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const id = route.params.id ? Number(route.params.id) : undefined
const isEdit = id !== undefined

const form = reactive<ComboPayload>({
  name: '',
  type: '',
  status: 0,
  note: '',
})
const saving = ref(false)

const members = ref<ComboItem[]>([])
const newItemId = ref<number | null>(null)
const newJoin = ref<number>(0)

function joinColor(j: number): string {
  return (['green', 'blue', 'default'] as const)[j] ?? 'default'
}

async function load(): Promise<void> {
  if (!id) return
  try {
    const data = await getComboDetail(id)
    form.name = data.combo.name
    form.type = data.combo.type
    form.status = data.combo.status
    form.note = data.combo.note
    members.value = data.items || []
  } catch {
    message.error('联合物品不存在')
  }
}

async function save(): Promise<void> {
  if (!form.name) {
    message.warning('请填写名称')
    return
  }
  saving.value = true
  try {
    const payload: ComboPayload = { ...form }
    if (id) payload.id = id
    const res = await (id ? updateCombo(payload) : createCombo(payload))
    message.success('已保存')
    const targetId = id ?? res.id
    if (targetId) router.push(`/${GLOBAL_PREFIX}/combos/${targetId}/edit`)
    else router.push(`/${GLOBAL_PREFIX}/combos`)
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function addMember(): Promise<void> {
  if (!id || !newItemId.value) return
  try {
    await addComboItem({
      combo_id: id,
      item_id: newItemId.value,
      join_method: newJoin.value,
    })
    message.success('已添加成员')
    newItemId.value = null
    newJoin.value = 0
    await load()
  } catch {
    /* 拦截器已提示 */
  }
}

async function removeMember(m: ComboItem): Promise<void> {
  try {
    await removeComboItem(m.combo_item_id)
    message.success('已移除')
    await load()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(load)
</script>

<style scoped>
.members {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: var(--space);
}
.member-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg-hover);
}
.member-name {
  font-weight: 500;
}
.member-actions {
  margin-left: auto;
}
.add-member {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.add-member__join {
  width: 140px;
}
</style>
