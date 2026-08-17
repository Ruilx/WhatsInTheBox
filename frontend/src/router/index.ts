// 前端路由（dev-plan v4 §3.3）。
// 约定：
//  - 先注册 /{GLOBAL_PREFIX}/* 静态段（全局页），再注册 /:activityName 参数段（活动页），
//    避免 /_wb/... 被 /:activityName/:boxName 吞掉（nginx 亦按首段是否等于前缀分流）。
//  - 活动内更具体的路由（已取出 / 编辑）须在 /:activityName/:boxName 之前注册。
//  - 通配 * 交由 NotFound 尝试按活动名解析，否则展示 404。
//  - 全局路由守卫：未登录访问受保护页跳登录；已登录访问登录页跳活动列表。

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { GLOBAL_PREFIX } from '@/utils/url'
import { useAuthStore } from '@/store/auth'

import Login from '@/views/Login.vue'
import ActivitiesList from '@/views/ActivitiesList.vue'
import ActivityDetail from '@/views/ActivityDetail.vue'
import ActivityEdit from '@/views/ActivityEdit.vue'
import BoxDetail from '@/views/BoxDetail.vue'
import BoxEdit from '@/views/BoxEdit.vue'
import ItemEdit from '@/views/ItemEdit.vue'
import ComboList from '@/views/ComboList.vue'
import ComboEdit from '@/views/ComboEdit.vue'
import Logs from '@/views/Logs.vue'
import Search from '@/views/Search.vue'
import TakenOut from '@/views/TakenOut.vue'
import NotFound from '@/views/NotFound.vue'

const P = GLOBAL_PREFIX

const routes: RouteRecordRaw[] = [
  // ---------------- 全局页（静态前缀，先注册） ----------------
  { path: `/${P}/login`, name: 'login', component: Login },
  { path: `/${P}/activities`, name: 'activities', component: ActivitiesList },
  { path: `/${P}/combos`, name: 'combos', component: ComboList },
  { path: `/${P}/combos/:id?/edit`, name: 'comboEdit', component: ComboEdit },
  { path: `/${P}/logs`, name: 'logs', component: Logs },
  { path: `/${P}/search`, name: 'search', component: Search },
  { path: `/${P}/activity/edit/:id?`, name: 'activityEdit', component: ActivityEdit },

  // ---------------- 活动页（动态段，后注册） ----------------
  { path: `/:activityName/已取出`, name: 'takenOut', component: TakenOut },
  { path: `/:activityName/box/edit/:id?`, name: 'boxEdit', component: BoxEdit },
  { path: `/:activityName/item/edit/:id?`, name: 'itemEdit', component: ItemEdit },
  { path: `/:activityName/:boxName`, name: 'boxDetail', component: BoxDetail },
  { path: `/:activityName`, name: 'activityDetail', component: ActivityDetail },

  // ---------------- 通配 ----------------
  { path: '/:pathMatch(.*)*', name: 'notFound', component: NotFound },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  const publicNames = ['login']
  if (!auth.isLoggedIn && !publicNames.includes(to.name as string)) {
    return { path: `/${P}/login`, query: { redirect: to.fullPath } }
  }
  if (auth.isLoggedIn && to.name === 'login') {
    return { path: `/${P}/activities` }
  }
  return true
})

export default router
