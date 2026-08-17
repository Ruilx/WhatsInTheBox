// 登录页（dev-plan v4 §3.3 / §7.8）。
// 用户名 + 密码登录；成功后跳活动列表（或 redirect）。无注册入口。

<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">箱子里面有什么</h1>
      <p class="login-sub">登录以管理你的活动、箱子与物品</p>

      <a-form layout="vertical" @submit.prevent="onSubmit">
        <a-form-item label="用户名" :validate-status="error ? 'error' : ''">
          <a-input
            v-model:value="form.username"
            placeholder="用户名"
            :maxlength="64"
            autofocus
          />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password
            v-model:value="form.password"
            placeholder="密码"
            :maxlength="128"
            @press-enter="onSubmit"
          />
        </a-form-item>
        <IconButton
          variant="primary"
          block
          label="登录"
          :disabled="loading"
          @click="onSubmit"
        >
          <template #icon><Icon name="power" /></template>
        </IconButton>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import { GLOBAL_PREFIX } from '@/utils/url'
import IconButton from '@/components/IconButton.vue'
import Icon from '@/components/Icon.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref(false)

async function onSubmit(): Promise<void> {
  if (!form.username || !form.password) {
    error.value = true
    message.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  error.value = false
  try {
    await auth.login(form.username, form.password)
    message.success('登录成功')
    const redirect = (route.query.redirect as string) || `/${GLOBAL_PREFIX}/activities`
    router.replace(redirect)
  } catch {
    error.value = true
    // 错误提示由 api 拦截器统一弹出
  } finally {
    loading.value = false
  }
}
</script>
