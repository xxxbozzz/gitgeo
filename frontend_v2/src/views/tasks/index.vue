<template>
  <div class="geo-page">
    <div class="hero">
      <h1>任务调度</h1>
      <p>创建定时任务，配置生成节奏和发布策略</p>
      <el-button type="primary">新建任务</el-button>
    </div>
    <div class="mt-6 glass-panel">
      <el-table :data="tasks" style="width:100%" class="industrial-table">
        <el-table-column prop="name" label="任务名称" />
        <el-table-column prop="schedule" label="调度" />
        <el-table-column prop="dailyLimit" label="日产量" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'running' ? 'success' : 'info'" size="small">{{ row.status === 'running' ? '运行中' : '已暂停' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上次运行">
          <template #default="{ row }">{{ row.lastRun || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="toggleTask(row)">
              {{ row.status === 'running' ? '暂停' : '启动' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const tasks = ref([
  { id: 1, name: '关键词消费生产', schedule: '持续运行', dailyLimit: 3, status: 'running', lastRun: '2026-05-06 10:30' },
  { id: 2, name: '低分文章修复', schedule: '每小时', dailyLimit: '-', status: 'running', lastRun: '2026-05-06 10:00' },
  { id: 3, name: 'AI平台探测', schedule: '每天 20:00', dailyLimit: 10, status: 'paused', lastRun: '-' },
  { id: 4, name: '官网HTML导出', schedule: '每天 06:00', dailyLimit: 5, status: 'running', lastRun: '2026-05-06 06:00' },
])

function toggleTask(t: any) { t.status = t.status === 'running' ? 'paused' : 'running' }
</script>
