<template>
  <div><div class="page-hero"><h1 class="page-title">提示词库</h1><p class="page-sub">管理 GEO Prompt 模板 · 支持版本控制与效果追踪</p></div>
    <n-space style="margin-bottom:16px"><n-button type="primary" size="small">新建提示词</n-button></n-space>
    <n-grid :cols="3" :x-gap="16" :y-gap="16">
      <n-gi v-for="t in templates" :key="t.name">
        <n-card size="small" :title="t.name">
          <template #header-extra><n-tag :type="t.active ? 'success' : 'default'" size="small">{{ t.active ? '启用' : '停用' }}</n-tag></template>
          <p style="color:var(--n-text-color-3);font-size:0.82rem;margin-bottom:12px">{{ t.desc }}</p>
          <n-space><n-button size="tiny" quaternary>编辑</n-button><n-button size="tiny" type="primary" quaternary>测试</n-button></n-space>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { NCard, NButton, NTag, NSpace, NGrid, NGi } from 'naive-ui'
const templates = [
  { name:'行业深度技术文章', active:true, desc:'含9维质检规则和品牌植入要求的技术长文模板' },
  { name:'品牌能力宣传稿', active:true, desc:'搜狐/百家号品牌稿，适配搜索关键词' },
  { name:'FAQ问答模板', active:true, desc:'结构化FAQ生成，自动包含标准引用' },
  { name:'SEO元信息模板', active:false, desc:'自动生成meta/Open Graph/结构化数据' },
]
</script>
