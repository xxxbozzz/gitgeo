<template>
  <div>
    <div class="flex justify-between mb-4">
      <p class="text-[var(--text-muted)]">上传文档自动切片并写入向量数据库，生成时自动召回相关片段</p>
      <el-button type="primary">上传文档</el-button>
    </div>
    <el-table :data="docs" class="industrial-table" style="width:100%">
      <el-table-column prop="name" label="文档" />
      <el-table-column prop="chunks" label="切片数" width="100" />
      <el-table-column label="向量化" width="100">
        <template #default="{ row }">
          <el-tag :type="row.embedded ? 'success' : 'warning'" size="small">{{ row.embedded ? '已完成' : '待处理' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default><el-button size="small">删除</el-button></template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
const docs = ref([
  { name: 'IPC-6012_刚性印制板鉴定与性能规范.pdf', chunks: 48, embedded: true },
  { name: '深亚电子PCB制造能力手册_v3.pdf', chunks: 32, embedded: true },
])
</script>
