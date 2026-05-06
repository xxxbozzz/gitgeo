<template>
  <n-layout has-sider class="h-screen">
    <n-layout-sider bordered :collapsed="appStore.sidebarCollapsed" :width="220" collapse-mode="width">
      <div class="sidebar-brand">
        <span v-if="!appStore.sidebarCollapsed" class="brand-text">⚡ gitgeo</span>
        <span v-else class="brand-text-sm">⚡</span>
      </div>
      <n-menu :value="activeKey" :collapsed="appStore.sidebarCollapsed" :options="menuOptions"
        :collapsed-width="64" @update:value="onMenuSelect" />
      <div class="sidebar-footer">
        <n-button quaternary size="small" @click="appStore.toggleDark">{{ appStore.darkMode ? '☀️ 亮' : '🌙 暗' }}</n-button>
      </div>
    </n-layout-sider>
    <n-layout>
      <n-layout-header bordered class="top-header">
        <div class="header-left">
          <n-button quaternary size="small" @click="appStore.toggleSidebar">☰</n-button>
          <n-breadcrumb><n-breadcrumb-item v-for="b in breadcrumbs" :key="b">{{ b }}</n-breadcrumb-item></n-breadcrumb>
        </div>
        <n-tag size="small" type="success">v5.0</n-tag>
      </n-layout-header>
      <n-layout-content class="main-content">
        <transition name="fade" mode="out-in"><router-view /></transition>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { computed, h, type Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '../store/app'
import { NIcon } from 'naive-ui'
import { BarChartOutlined, ToolOutlined, BulbOutlined, CloudServerOutlined, DashboardOutlined, DatabaseOutlined, FileTextOutlined, ClockCircleOutlined, SendOutlined, SettingOutlined, ShareAltOutlined, TagOutlined } from '@vicons/antd'

const router = useRouter(); const route = useRoute(); const appStore = useAppStore()
const icon = (c: Component) => () => h(NIcon, null, { default: () => h(c) })

const menuOptions = [
  { label: '仪表盘', key: '/dashboard', icon: icon(DashboardOutlined) },
  { type: 'divider' as const, key: 'd1' },
  { label: '素材库', key: '/materials', icon: icon(DatabaseOutlined) },
  { label: '提示词库', key: '/prompts', icon: icon(BulbOutlined) },
  { label: '模型配置', key: '/models', icon: icon(CloudServerOutlined) },
  { label: '任务调度', key: '/tasks', icon: icon(ClockCircleOutlined) },
  { type: 'divider' as const, key: 'd2' },
  { label: '文章管理', key: '/articles', icon: icon(FileTextOutlined) },
  { label: '关键词中心', key: '/keywords', icon: icon(TagOutlined) },
  { label: '能力库', key: '/capabilities', icon: icon(ToolOutlined) },
  { type: 'divider' as const, key: 'd3' },
  { label: '发布中心', key: '/publications', icon: icon(SendOutlined) },
  { label: '知识图谱', key: '/graph', icon: icon(ShareAltOutlined) },
  { label: '运行记录', key: '/runs', icon: icon(BarChartOutlined) },
  { label: '系统状态', key: '/system', icon: icon(SettingOutlined) },
]

const activeKey = computed(() => (menuOptions.find(o => 'key' in o && typeof o.key === 'string' && route.path.startsWith(o.key)) as any)?.key || '/dashboard')
const breadcrumbs = computed(() => ['首页', (menuOptions.find(o => 'key' in o && o.key === activeKey.value) as any)?.label || ''])
function onMenuSelect(k: string) { router.push(k) }
</script>

<style scoped>
.sidebar-brand { padding: 20px 18px; }
.brand-text { font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em; background: linear-gradient(135deg, #2563eb, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.brand-text-sm { font-size: 1.4rem; }
.sidebar-footer { padding: 12px 18px; border-top: 1px solid var(--n-border-color); margin-top: auto; }
.top-header { display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 52px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.main-content { padding: 24px 28px; max-width: 1400px; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.12s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
