<template>
  <div class="geo-page">
    <div class="hero">
      <h1>模型配置</h1>
      <p>管理 AI 模型接入、切换策略和 fallback 配置</p>
      <el-button type="primary">添加模型</el-button>
    </div>
    <div class="mt-6 space-y-4">
      <div v-for="m in models" :key="m.id" class="glass-panel p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <Cpu class="w-5 h-5 text-[var(--color-primary)]" />
            <div>
              <span class="font-semibold">{{ m.name }}</span>
              <span class="text-xs text-[var(--text-muted)] ml-2">{{ m.provider }} · {{ m.type }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <el-tag :type="m.status === 'active' ? 'success' : 'warning'" size="small">{{ m.status === 'active' ? '主模型' : '备用' }}</el-tag>
            <el-switch v-model="m.enabled" />
          </div>
        </div>
        <div class="mt-2 grid grid-cols-3 gap-4 text-xs text-[var(--text-muted)]">
          <span>端点: {{ m.baseUrl }}</span>
          <span>温度: {{ m.temperature }}</span>
          <span>最大 Token: {{ m.maxTokens }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Cpu } from 'lucide-vue-next'

const models = ref([
  { id: 1, name: 'deepseek-chat', provider: 'DeepSeek', type: 'chat', status: 'active', baseUrl: 'https://api.deepseek.com', temperature: 0.1, maxTokens: 8000, enabled: true },
  { id: 2, name: 'gpt-4o', provider: 'OpenAI', type: 'chat', status: 'fallback', baseUrl: 'https://api.openai.com/v1', temperature: 0.3, maxTokens: 16000, enabled: false },
  { id: 3, name: 'text-embedding-3', provider: 'OpenAI', type: 'embedding', status: 'active', baseUrl: 'https://api.openai.com/v1', temperature: 0, maxTokens: 8191, enabled: true },
])
</script>
