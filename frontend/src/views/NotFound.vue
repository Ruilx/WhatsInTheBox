// 404 / 通配解析（dev-plan v4 §3.3 通配 *）。
// 未知路径先尝试按首段当作活动名解析；命中则跳活动详情，否则展示 404。
// 首段等于系统保留前缀（GLOBAL_PREFIX）不算活动名。

<template>
  <div class="page-container notfound">
    <template v-if="resolving">
      <a-spin tip="正在解析活动…" />
    </template>
    <template v-else>
      <Icon name="box" :size="48" />
      <h2 class="notfound__title">页面不存在</h2>
      <p class="muted">未找到「{{ raw }}」对应的内容。</p>
      <RouterLink :to="`/${GLOBAL_PREFIX}/activities`">
        <IconButton variant="primary" label="返回活动列表" />
      </RouterLink>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getActivity } from '@/api'
import { activityUrl, GLOBAL_PREFIX } from '@/utils/url'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const resolving = ref(true)
const raw = ref(window.location.pathname)
const seg = window.location.pathname.split('/').filter(Boolean)[0] || ''

onMounted(async () => {
  if (!seg || seg === GLOBAL_PREFIX) {
    resolving.value = false
    return
  }
  try {
    const act = await getActivity(undefined, decodeURIComponent(seg))
    router.replace(activityUrl(act.name))
  } catch {
    resolving.value = false
  }
})
</script>

<style scoped>
.notfound {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  padding-top: 96px;
}
.notfound__title {
  margin: var(--space-xs) 0 0;
}
</style>
