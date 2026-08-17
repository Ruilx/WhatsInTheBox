// 物品新建 / 编辑（dev-plan v4 §3.3 / §7.13 / §7.14）。
// 路由 /:activityName/item/edit/:id?（query: box, activity 用于新建预填）。
// type 自由文本；照片上传；可改所属箱（重新放入）；编辑态提供「取出」动作。

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <RouterLink :to="activityUrl(activityName)" class="back-link">
          <Icon name="back" /> {{ activityName }}
        </RouterLink>
        <h2 class="page-title">{{ isEdit ? '编辑物品' : '新建物品' }}</h2>
      </div>
    </div>

    <div class="wb-card form-grid">
      <a-form layout="vertical">
        <a-form-item label="物品名" required>
          <a-input v-model:value="form.name" placeholder="物品名称" :maxlength="128" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.desc" :rows="2" placeholder="物品描述" />
        </a-form-item>
        <a-form-item label="类型（自由文本）">
          <a-input v-model:value="form.type" placeholder="如 电子设备 / 工具" />
        </a-form-item>
        <a-form-item label="所属箱子">
          <a-select
            v-model:value="form.box_id"
            placeholder="选择箱子（空表示直接已取出）"
            allow-clear
            :options="boxOptions"
          />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="form.status">
            <a-select-option v-for="(t, i) in ITEM_STATUS" :key="i" :value="i">{{ t }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="form.note" :rows="2" placeholder="备注" />
        </a-form-item>
        <a-form-item label="照片">
          <div class="photo-row">
            <a-upload
              list-type="picture-card"
              :show-upload-list="false"
              :before-upload="onPhoto"
              accept="image/jpeg,image/png,image/webp,.heic"
            >
              <div v-if="form.photo">
                <img class="photo-thumb" :src="uploadUrl(form.photo)" alt="照片" />
              </div>
              <div v-else class="photo-placeholder">
                <Icon name="camera" />
                <div>上传</div>
              </div>
            </a-upload>
            <span class="muted">支持 jpg/png/webp，HEIC 由服务端转换，≤5MB</span>
          </div>
        </a-form-item>

        <div class="form-actions">
          <IconButton variant="primary" label="保存" :disabled="saving" @click="save">
            <template #icon><Icon name="edit" /></template>
          </IconButton>
          <IconButton
            v-if="isEdit && auth.isRw && form.status !== 1 && form.box_id"
            variant="default"
            label="取出"
            @click="takeOut"
          >
            <template #icon><Icon name="out" /></template>
          </IconButton>
          <RouterLink :to="backUrl">
            <IconButton variant="default" label="取消" />
          </RouterLink>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  getActivity,
  getItem,
  listBoxes,
  createItem,
  updateItem,
  takeOutItem,
  uploadPhoto,
  uploadUrl as toUrl,
  type ItemPayload,
} from '@/api'
import { useAuthStore } from '@/store/auth'
import { encodeSeg, activityUrl, boxUrl } from '@/utils/url'
import { ITEM_STATUS } from '@/utils/format'
import type { Box, Item } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const uploadUrl = toUrl
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const activityName = decodeURIComponent((route.params.activityName as string) || '')
const id = route.params.id ? Number(route.params.id) : undefined
const isEdit = id !== undefined

const form = reactive<ItemPayload>({
  box_id: undefined,
  name: '',
  desc: '',
  type: '',
  activity_id: 0,
  status: 0,
  note: '',
  photo: '',
  thumb: '',
})
const saving = ref(false)
const uploading = ref(false)
const boxOptions = ref<{ label: string; value: number }[]>([])

// 返回地址：物品归属某箱子时回到该箱子内物品列表，否则回到活动（箱子列表）页。
// 保存与取消共用，保证行为一致（dev-plan v4 §7.13 / 用户反馈：新建物品应跳回箱子内物品列表）。
const backUrl = computed(() => {
  const box = boxOptions.value.find((o) => o.value === form.box_id)
  return box ? boxUrl(activityName, box.label) : activityUrl(activityName)
})

async function loadContext(): Promise<void> {
  const act = await getActivity(undefined, activityName)
  form.activity_id = act.id
  const boxes = await listBoxes({ activity_id: act.id, page: 1, size: 200 })
  boxOptions.value = boxes.list.map((b: Box) => ({ label: b.name, value: b.id }))

  if (id) {
    const item = await getItem(id)
    form.name = item.name
    form.desc = item.desc
    form.type = item.type
    form.box_id = item.box_id || undefined
    form.activity_id = item.activity_id
    form.status = item.status
    form.note = item.note
    form.photo = item.photo || ''
    form.thumb = item.thumb || ''
  } else {
    const qBox = route.query.box ? Number(route.query.box) : undefined
    if (qBox) form.box_id = qBox
    const qAct = route.query.activity ? Number(route.query.activity) : undefined
    if (qAct) form.activity_id = qAct
  }
}

async function onPhoto(file: File): Promise<boolean> {
  uploading.value = true
  try {
    const r = await uploadPhoto(file)
    form.photo = r.path
    form.thumb = r.thumb
    message.success('已上传')
  } catch {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
  }
  return false
}

async function save(): Promise<void> {
  if (!form.name) {
    message.warning('请填写物品名')
    return
  }
  if (!form.activity_id) {
    message.error('所属活动不存在')
    return
  }
  saving.value = true
  try {
    const payload: ItemPayload = { ...form }
    if (id) payload.id = id
    await (id ? updateItem(payload) : createItem(payload))
    message.success('已保存')
    router.push(backUrl.value)
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function takeOut(): Promise<void> {
  if (!id) return
  try {
    await takeOutItem(id)
    message.success('已取出，物品进入「已取出」')
    router.push(`/${encodeSeg(activityName)}/已取出`)
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(loadContext)
</script>

<style scoped>
.photo-row {
  display: flex;
  align-items: center;
  gap: var(--space);
}
.photo-thumb {
  width: 86px;
  height: 86px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}
.photo-placeholder {
  width: 86px;
  height: 86px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: var(--color-text-secondary);
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-sm);
}
</style>
