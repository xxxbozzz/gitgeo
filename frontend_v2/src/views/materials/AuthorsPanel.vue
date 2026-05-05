<template>
  <div>
    <div class="flex justify-between mb-4">
      <el-input v-model="search" placeholder="搜索作者…" class="!w-64" clearable />
      <el-button type="primary">添加作者</el-button>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div v-for="a in authors" :key="a.name" class="glass-panel p-4 flex items-center gap-4">
        <div class="w-12 h-12 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-white font-bold text-lg">{{ a.name[0] }}</div>
        <div>
          <p class="font-semibold">{{ a.name }}</p>
          <p class="text-xs text-[var(--text-muted)]">{{ a.bio }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
const search = ref('')
const authors = ref([
  { name: '深亚技术团队', bio: 'PCB制造工程团队，专注高多层/HDI/阻抗控制' },
  { name: 'GEO编辑部', bio: 'AI搜索引擎优化内容团队' },
])
</script>
