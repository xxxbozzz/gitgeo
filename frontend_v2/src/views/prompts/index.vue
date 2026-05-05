<template>
  <div class="geo-page">
    <div class="hero">
      <h1>提示词库</h1>
      <p>管理所有 GEO 提示词模板，支持版本控制和效果追踪</p>
      <el-button type="primary" @click="showCreate = true">新建提示词</el-button>
    </div>
    <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="tpl in templates" :key="tpl.id" class="glass-panel p-4">
        <div class="flex justify-between items-start mb-3">
          <div>
            <span class="text-sm text-[var(--text-muted)]">{{ tpl.category }}</span>
            <h3 class="text-base font-semibold mt-1">{{ tpl.name }}</h3>
          </div>
          <el-tag :type="tpl.active ? 'success' : 'info'" size="small">{{ tpl.active ? '启用' : '停用' }}</el-tag>
        </div>
        <p class="text-xs text-[var(--text-muted)] line-clamp-3 mb-4">{{ tpl.description }}</p>
        <div class="flex gap-2">
          <el-button size="small" @click="editTemplate(tpl)">编辑</el-button>
          <el-button size="small" type="primary" @click="testTemplate(tpl)">测试</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const showCreate = ref(false)

const templates = ref([
  { id: 1, name: '行业深度技术文章', category: '内容生成', active: true, description: '面向PCB/制造业的技术长文模板，含9维质检规则和品牌植入要求' },
  { id: 2, name: '品牌能力宣传稿', category: '站外GEO', active: true, description: '搜狐/百家号品牌稿，偏强势能力展示，适配搜索关键词' },
  { id: 3, name: 'FAQ问答模板', category: '内容生成', active: true, description: '结构化FAQ生成，自动包含标准引用和工程实践建议' },
  { id: 4, name: 'SEO元信息模板', category: '发布', active: false, description: '自动生成meta description/keywords/Open Graph' },
])

function editTemplate(_tpl: any) { showCreate.value = true }
function testTemplate(_tpl: any) { /* TODO */ }
</script>
