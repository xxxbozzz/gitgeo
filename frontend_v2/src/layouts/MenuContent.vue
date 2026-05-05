<template>
  <el-menu
    :default-active="activePath"
    class="!border-none !bg-transparent px-3"
    text-color="var(--text-muted)"
    active-text-color="var(--text-main)"
    router
    @select="$emit('navigated')"
  >
    <!-- 监控 -->
    <div class="px-4 py-2 text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">监控</div>
    <el-menu-item index="/dashboard" class="geo-menu-item">
      <LayoutDashboard class="w-4 h-4 mr-3" /><template #title>仪表盘</template>
    </el-menu-item>
    <el-menu-item index="/runs" class="geo-menu-item">
      <Activity class="w-4 h-4 mr-3" /><template #title>运行记录</template>
    </el-menu-item>
    <el-menu-item index="/system" class="geo-menu-item">
      <Server class="w-4 h-4 mr-3" /><template #title>系统状态</template>
    </el-menu-item>

    <div class="my-4 mx-4 h-px bg-[var(--border-subtle)]"></div>

    <!-- 管理 -->
    <div class="px-4 py-2 text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">管理</div>
    <el-menu-item index="/materials" class="geo-menu-item">
      <Database class="w-4 h-4 mr-3" /><template #title>素材库</template>
    </el-menu-item>
    <el-menu-item index="/prompts" class="geo-menu-item">
      <FileEdit class="w-4 h-4 mr-3" /><template #title>提示词库</template>
    </el-menu-item>
    <el-menu-item index="/models" class="geo-menu-item">
      <Cpu class="w-4 h-4 mr-3" /><template #title>模型配置</template>
    </el-menu-item>
    <el-menu-item index="/tasks" class="geo-menu-item">
      <CalendarCheck class="w-4 h-4 mr-3" /><template #title>任务调度</template>
    </el-menu-item>

    <div class="my-4 mx-4 h-px bg-[var(--border-subtle)]"></div>

    <!-- 内容运营 -->
    <div class="px-4 py-2 text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">内容运营</div>
    <el-menu-item index="/articles" class="geo-menu-item">
      <FileText class="w-4 h-4 mr-3" /><template #title>文章管理</template>
    </el-menu-item>
    <el-menu-item index="/keywords" class="geo-menu-item">
      <Hash class="w-4 h-4 mr-3" /><template #title>关键词</template>
    </el-menu-item>
    <el-menu-item index="/capabilities" class="geo-menu-item">
      <Wrench class="w-4 h-4 mr-3" /><template #title>能力库</template>
    </el-menu-item>

    <div class="my-4 mx-4 h-px bg-[var(--border-subtle)]"></div>

    <!-- 分发 -->
    <div class="px-4 py-2 text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">分发</div>
    <el-menu-item index="/publications" class="geo-menu-item">
      <Send class="w-4 h-4 mr-3" /><template #title>发布中心</template>
    </el-menu-item>
    <el-menu-item index="/graph" class="geo-menu-item">
      <Network class="w-4 h-4 mr-3" /><template #title>知识图谱</template>
    </el-menu-item>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  LayoutDashboard, Activity, FileText, Send, Server,
  Hash, Wrench, Network, Database, FileEdit, Cpu, CalendarCheck
} from 'lucide-vue-next'

defineEmits(['navigated'])

const route = useRoute()
const activePath = computed(() => {
  const path = route.path
  const pages = ['/dashboard','/runs','/system','/materials','/prompts','/models','/tasks','/articles','/keywords','/capabilities','/publications','/graph']
  return pages.find(p => path.startsWith(p)) || path
})
</script>

<style scoped>
.geo-menu-item {
  height: 40px; line-height: 40px; border-radius: 6px; margin-bottom: 2px;
}
.geo-menu-item.is-active {
  background-color: rgba(37, 99, 235, 0.15) !important;
  color: var(--text-main) !important;
  font-weight: 600;
  border-left: 3px solid var(--color-primary);
}
</style>
