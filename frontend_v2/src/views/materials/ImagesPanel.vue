<template>
  <div>
    <div class="flex justify-between mb-4">
      <el-radio-group v-model="view">
        <el-radio-button value="grid">网格</el-radio-button>
        <el-radio-button value="list">列表</el-radio-button>
      </el-radio-group>
      <el-button type="primary">上传图片</el-button>
    </div>
    <div class="grid grid-cols-4 gap-4" v-if="view === 'grid'">
      <div v-for="img in images" :key="img.name" class="glass-panel p-2 text-center">
        <div class="h-32 bg-[var(--bg-dark)] rounded flex items-center justify-center text-2xl">🖼</div>
        <p class="text-xs mt-2 truncate">{{ img.name }}</p>
      </div>
    </div>
    <el-table v-else :data="images" class="industrial-table">
      <el-table-column prop="name" label="文件名" />
      <el-table-column prop="size" label="大小" width="100" />
      <el-table-column label="操作" width="120">
        <template #default><el-button size="small">使用</el-button></template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
const view = ref('grid')
const images = ref([
  { name: 'workshop-01.jpg', size: '2.4 MB' },
  { name: 'workshop-02.jpg', size: '1.8 MB' },
  { name: 'pcb-layer-stack.png', size: '856 KB' },
  { name: 'impedance-chart.png', size: '412 KB' },
])
</script>
