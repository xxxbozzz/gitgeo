<template>
  <el-menu
    :default-active="activePath"
    class="!border-none !bg-transparent px-3"
    text-color="var(--text-muted)"
    active-text-color="var(--text-main)"
    router
    @select="$emit('navigated')"
  >
    <el-menu-item index="/dashboard" class="geo-menu-item">
      <LayoutDashboard class="w-4 h-4 mr-3" />
      <template #title>总览</template>
    </el-menu-item>
    <el-menu-item index="/runs" class="geo-menu-item">
      <Activity class="w-4 h-4 mr-3" />
      <template #title>运行中心</template>
    </el-menu-item>
    <el-menu-item index="/articles" class="geo-menu-item">
      <FileText class="w-4 h-4 mr-3" />
      <template #title>内容中心</template>
    </el-menu-item>
    <el-menu-item index="/publications" class="geo-menu-item">
      <Send class="w-4 h-4 mr-3" />
      <template #title>发布中心</template>
    </el-menu-item>
    <el-menu-item index="/system" class="geo-menu-item">
      <Server class="w-4 h-4 mr-3" />
      <template #title>系统状态</template>
    </el-menu-item>

    <div class="my-4 mx-4 h-px bg-[var(--border-subtle)]"></div>

    <!-- Reserved Modules -->
    <el-menu-item index="/keywords" class="geo-menu-item">
      <Hash class="w-4 h-4 mr-3" />
      <template #title>关键词中心</template>
    </el-menu-item>
    <el-menu-item index="/capabilities" class="geo-menu-item">
      <Wrench class="w-4 h-4 mr-3" />
      <template #title>能力库</template>
    </el-menu-item>
    <el-menu-item index="/graph" class="geo-menu-item">
      <Network class="w-4 h-4 mr-3" />
      <template #title>知识图谱</template>
    </el-menu-item>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  LayoutDashboard, Activity, FileText, Send, Server, 
  Hash, Wrench, Network 
} from 'lucide-vue-next'

defineEmits(['navigated'])

const route = useRoute()
const activePath = computed(() => {
  const path = route.path
  if (path.startsWith('/dashboard')) return '/dashboard'
  if (path.startsWith('/runs')) return '/runs'
  if (path.startsWith('/articles')) return '/articles'
  if (path.startsWith('/publications')) return '/publications'
  if (path.startsWith('/system')) return '/system'
  if (path.startsWith('/keywords')) return '/keywords'
  if (path.startsWith('/capabilities')) return '/capabilities'
  if (path.startsWith('/graph')) return '/graph'
  return path
})
</script>

<style scoped>
:deep(.el-menu) {
  --el-menu-bg-color: transparent;
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.05);
}

.geo-menu-item {
  height: 40px;
  line-height: 40px;
  border-radius: 6px;
  margin-bottom: 4px;
}

.geo-menu-item.is-active {
  background-color: rgba(37, 99, 235, 0.15) !important;
  color: var(--text-main) !important;
  font-weight: 600;
  border-left: 3px solid var(--color-primary);
}
</style>
