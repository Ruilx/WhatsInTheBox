// 活动新建 / 编辑（dev-plan v4 §3.3 / §8.1）。
// 路由 /{GLOBAL_PREFIX}/activity/edit/:id?（id 缺省为新建）。
// 仅 rw 可进入（按钮已隐藏；API 二次校验）。

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <RouterLink :to="`/${GLOBAL_PREFIX}/activities`" class="back-link">
          <Icon name="back" /> 活动列表
        </RouterLink>
        <h2 class="page-title">{{ isEdit ? '编辑活动' : '新建活动' }}</h2>
      </div>
    </div>

    <div class="wb-card form-grid">
      <a-form layout="vertical">
        <a-form-item label="活动名" required>
          <a-input v-model:value="form.name" placeholder="全局唯一，不可等于系统保留前缀" :maxlength="128" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.desc" :rows="2" placeholder="活动描述" />
        </a-form-item>
        <a-form-item label="类型">
          <a-input v-model:value="form.type" placeholder="活动类型（自由文本）" :maxlength="64" />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="form.status">
            <a-select-option v-for="(t, i) in ACTIVITY_STATUS" :key="i" :value="i">
              {{ t }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="开始时间">
          <a-date-picker
            :value="startTime"
            show-time
            allow-clear
            class="full-width"
            :format="DATETIME_FORMAT"
            placeholder="选择日期与时间（可选）"
            @change="onStartTimeChange"
          />
        </a-form-item>
        <a-form-item label="结束时间">
          <a-date-picker
            :value="endTime"
            show-time
            allow-clear
            class="full-width"
            :format="DATETIME_FORMAT"
            placeholder="选择日期与时间（可选）"
            @change="onEndTimeChange"
          />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="form.note" :rows="2" placeholder="备注" />
        </a-form-item>

        <div class="form-actions">
          <IconButton variant="primary" label="保存" :disabled="saving" @click="save">
            <template #icon><Icon name="edit" /></template>
          </IconButton>
          <RouterLink :to="`/${GLOBAL_PREFIX}/activities`">
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
import { getActivity, createActivity, updateActivity, type ActivityPayload } from '@/api'
import { GLOBAL_PREFIX } from '@/utils/url'
import { ACTIVITY_STATUS } from '@/utils/format'
import { DATETIME_FORMAT, toDatetimeValue, fromDatetimeValue } from '@/utils/datetime'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id ? Number(route.params.id) : undefined
const isEdit = id !== undefined

const form = reactive<ActivityPayload>({
  name: '',
  desc: '',
  type: '',
  start_time: null,
  end_time: null,
  status: 0,
  note: '',
})
const saving = ref(false)

// 开始 / 结束时间：picker 用 dayjs 对象，payload 仍是 `YYYY-MM-DD HH:mm:ss` 字符串或 null
const startTime = computed(() => toDatetimeValue(form.start_time))
const endTime = computed(() => toDatetimeValue(form.end_time))

function onStartTimeChange(v: unknown): void {
  form.start_time = fromDatetimeValue(v)
}
function onEndTimeChange(v: unknown): void {
  form.end_time = fromDatetimeValue(v)
}

onMounted(async () => {
  if (id) {
    try {
      const a = await getActivity(id)
      form.name = a.name
      form.desc = a.desc
      form.type = a.type
      form.start_time = a.start_time ?? null
      form.end_time = a.end_time ?? null
      form.status = a.status
      form.note = a.note
    } catch {
      message.error('活动不存在')
    }
  }
})

async function save(): Promise<void> {
  if (!form.name) {
    message.warning('请填写活动名')
    return
  }
  saving.value = true
  try {
    const payload: ActivityPayload = { ...form }
    if (id) payload.id = id
    const res = await (id ? updateActivity(payload) : createActivity(payload))
    message.success('已保存')
    router.push(`/${GLOBAL_PREFIX}/activities`)
    void res
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}
</script>
