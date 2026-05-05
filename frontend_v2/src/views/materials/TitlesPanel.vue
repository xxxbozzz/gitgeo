<template>
  <div>
    <div class="flex justify-between mb-4">
      <el-input v-model="search" placeholder="搜索标题…" class="!w-64" clearable />
      <el-button type="primary">添加标题</el-button>
    </div>
    <el-table :data="titles" class="industrial-table" style="width:100%">
      <el-table-column prop="title" label="标题模板" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="usage" label="使用次数" width="100" />
      <el-table-column label="操作" width="120">
        <template #default><el-button size="small">编辑</el-button></template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
const search = ref('')
const titles = ref([
  { title: '{{keyword}}技术深度解析：从标准合规到工程实践', category: '技术动态', usage: 45 },
  { title: '{{keyword}}怎么选？从高端PCB制造能力看深亚电子', category: '行业资讯', usage: 23 },
])
</script>
