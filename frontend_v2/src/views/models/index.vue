<template>
  <div><div class="page-hero"><h1 class="page-title">模型配置</h1><p class="page-sub">管理 AI 模型接入与主备切换策略</p></div>
    <n-space style="margin-bottom:16px"><n-button type="primary" size="small">添加模型</n-button></n-space>
    <n-grid :cols="1" :y-gap="12">
      <n-gi v-for="m in models" :key="m.name">
        <n-card size="small"><div style="display:flex;justify-content:space-between;align-items:center">
          <div><strong>{{ m.name }}</strong> <span style="color:var(--n-text-color-3);font-size:0.82rem">{{ m.provider }} · {{ m.type }}</span>
          <div style="color:var(--n-text-color-3);font-size:0.75rem;margin-top:4px">{{ m.endpoint }}</div></div>
          <div style="display:flex;align-items:center;gap:12px">
            <n-tag :type="m.primary?'success':'warning'" size="small">{{ m.primary?'主模型':'备用' }}</n-tag>
            <n-switch :value="m.enabled" size="small" />
          </div></div></n-card>
      </n-gi>
    </n-grid>
  </div>
</template>
<script setup lang="ts">
import { NCard, NButton, NTag, NSpace, NGrid, NGi, NSwitch } from 'naive-ui'
const models = [
  { name:'deepseek-chat', provider:'DeepSeek', type:'chat', endpoint:'https://api.deepseek.com', primary:true, enabled:true },
  { name:'gpt-4o', provider:'OpenAI', type:'chat', endpoint:'https://api.openai.com/v1', primary:false, enabled:false },
]
</script>
