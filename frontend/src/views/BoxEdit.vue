// 箱子新建 / 编辑（dev-plan v4 §3.3 / §8.1）。
// 路由 /:activityName/box/edit/:id?（id 缺省为新建）。
// type 多标签；parent_box_id 可选（多层嵌套）；照片上传（rw）。

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <RouterLink :to="activityUrl(activityName)" class="back-link">
          <Icon name="back" /> {{ activityName }}
        </RouterLink>
        <h2 class="page-title">{{ isEdit ? '编辑箱子' : '新建箱子' }}</h2>
      </div>
    </div>

    <div class="wb-card form-grid">
      <a-form layout="vertical">
        <a-form-item label="箱子名（编号）" required>
          <a-input v-model:value="form.name" placeholder="活动内唯一，用户手填" :maxlength="128" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.desc" :rows="2" placeholder="箱子描述" />
        </a-form-item>
        <a-form-item label="类型标签">
          <a-select
            v-model:value="form.type"
            mode="multiple"
            :options="typeOptions"
            placeholder="可多选（主要/次要/易碎/...）"
          />
        </a-form-item>
        <a-form-item label="尺寸">
          <!-- 预置 + 本机记忆（按使用频率排序），允许自由输入（AutoComplete 最贴合）。 -->
          <a-auto-complete
            v-model:value="form.size"
            allow-clear
            :options="sizeOptions"
            :filter-option="filterSizeOption"
            placeholder="选择常用尺寸，或直接输入（如 60x40x50cm）"
          />
        </a-form-item>
        <a-form-item label="材质">
          <a-input v-model:value="form.material" placeholder="如 纸箱 / 塑料" />
        </a-form-item>
        <a-form-item label="父箱">
          <a-select
            v-model:value="form.parent_box_id"
            placeholder="无（顶层箱）"
            allow-clear
            :options="parentOptions"
          />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="form.status">
            <a-select-option v-for="(t, i) in BOX_STATUS" :key="i" :value="i">{{ t }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="物理串号">
          <a-input v-model:value="form.serial_no" placeholder="全局唯一（软删后可重用）" />
        </a-form-item>
        <a-form-item label="首次启用时间">
          <a-date-picker
            :value="firstUsingTime"
            show-time
            allow-clear
            class="full-width"
            :format="DATETIME_FORMAT"
            placeholder="选择日期与时间（可选）"
            @change="onFirstUsingTimeChange"
          />
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
          <RouterLink :to="activityUrl(activityName)">
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
  listBoxes,
  createBox,
  updateBox,
  uploadPhoto,
  uploadUrl as toUrl,
  type BoxPayload,
} from '@/api'
import { activityUrl } from '@/utils/url'
import { BOX_STATUS, BOX_TYPE_PRESETS } from '@/utils/format'
import { DATETIME_FORMAT, toDatetimeValue, fromDatetimeValue } from '@/utils/datetime'
import { listBoxSizes, rememberBoxSize } from '@/utils/boxSize'
import type { Box } from '@/types'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const uploadUrl = toUrl

const route = useRoute()
const router = useRouter()
const activityName = decodeURIComponent((route.params.activityName as string) || '')
const id = route.params.id ? Number(route.params.id) : undefined
const isEdit = id !== undefined

const form = reactive<BoxPayload>({
  activity_id: 0,
  name: '',
  desc: '',
  type: [],
  size: '',
  material: '',
  parent_box_id: null,
  status: 0,
  serial_no: '',
  note: '',
  first_using_time: null,
  photo: '',
  thumb: '',
})
const saving = ref(false)
const uploading = ref(false)
const allBoxes = ref<Box[]>([])

const typeOptions = BOX_TYPE_PRESETS.map((t) => ({ label: t, value: t }))
const parentOptions = computed(() =>
  allBoxes.value
    .filter((b) => b.id !== id)
    .map((b) => ({ label: b.name, value: b.id })),
)

// ---------------- 尺寸：预置 + 本机记忆（频率排序）+ 自由输入 ----------------
/** 已记忆的候选尺寸（挂载时读取一次；保存后刷新） */
const sizeHistory = ref<string[]>(listBoxSizes())

const sizeOptions = computed(() =>
  sizeHistory.value.map((s) => ({ label: s, value: s })),
)

/** 按 value 模糊匹配，输入任意文本都能即时过滤候选。 */
function filterSizeOption(input: string, option: { value?: unknown }): boolean {
  const kw = input.trim().toLowerCase()
  if (!kw) return true
  return String(option?.value ?? '').toLowerCase().includes(kw)
}

// ---------------- 首次启用时间：picker(dayjs) <-> payload(string) ----------------
const firstUsingTime = computed(() => toDatetimeValue(form.first_using_time))

function onFirstUsingTimeChange(v: unknown): void {
  form.first_using_time = fromDatetimeValue(v)
}

async function loadActivity(): Promise<void> {
  const act = await getActivity(undefined, activityName)
  form.activity_id = act.id
  const boxes = await listBoxes({ activity_id: act.id, page: 1, size: 200 })
  allBoxes.value = boxes.list
  if (id) {
    const found = boxes.list.find((b) => b.id === id)
    if (!found) {
      message.error('箱子不存在')
      return
    }
    form.name = found.name
    form.desc = found.desc
    form.type = found.type || []
    form.size = found.size
    form.material = found.material
    form.parent_box_id = found.parent_box_id ?? null
    form.status = found.status
    form.serial_no = found.serial_no
    form.note = found.note
    form.first_using_time = found.first_using_time ?? null
    form.photo = found.photo || ''
    form.thumb = found.thumb || ''
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
    message.warning('请填写箱子名')
    return
  }
  if (!form.activity_id) {
    message.error('所属活动不存在')
    return
  }
  saving.value = true
  try {
    // size 允许清空（a-select allow-clear 会置为 undefined），统一收敛为空串保持契约
    const payload: BoxPayload = { ...form, size: (form.size ?? '').trim() }
    if (id) payload.id = id
    await (id ? updateBox(payload) : createBox(payload))
    // 保存成功才计入使用频率，避免误触污染候选排序
    rememberBoxSize(payload.size)
    sizeHistory.value = listBoxSizes()
    message.success('已保存')
    router.push(activityUrl(activityName))
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

onMounted(loadActivity)
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
