<template>
  <div>
    <div class="flex justify-between mb-4">
      <el-input v-model="search" placeholder="搜索关键词…" class="!w-64" clearable />
      <div class="flex gap-2">
        <el-button>批量导入</el-button>
        <el-button type="primary">添加关键词</el-button>
      </div>
    </div>
    <el-table :data="keywords" class="industrial-table" style="width:100%">
      <el-table-column prop="keyword" label="关键词" />
      <el-table-column prop="searchVolume" label="搜索量" width="100" />
      <el-table-column label="难度" width="120">
        <template #default="{ row }">
          <el-progress :percentage="row.difficulty" :color="row.difficulty > 60 ? '#ef4444' : '#22c55e'" />
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="操作" width="120">
        <template #default>
          <el-button size="small">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
const search = ref('')
const keywords = ref([
  { keyword: 'PCB阻抗控制', searchVolume: 2800, difficulty: 65, status: '已消费' },
  { keyword: 'HDI盲孔工艺', searchVolume: 1200, difficulty: 45, status: '待处理' },
  { keyword: 'ENIG沉金厚度标准', searchVolume: 850, difficulty: 30, status: '待处理' },
])
</script>
