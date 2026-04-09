<template>
  <div class="system-page">
    <header class="system-hero">
      <div class="system-hero__main">
        <span class="system-hero__eyebrow">Core Operations Status</span>
        <h1 class="system-hero__title">系统状态</h1>
        <p class="system-hero__description">
          汇总当前环境、数据库、LLM 提供方接入和 build 版本，为后续预算、调度器和容器状态扩展预留位置。
        </p>
      </div>

      <div class="system-hero__meta">
        <div class="system-pill">
          <span class="system-pill__label">轮询频率</span>
          <span class="system-pill__value">30s / 次</span>
        </div>
        <div class="system-pill" :class="isSystemHealthy ? 'system-pill--healthy' : 'system-pill--warning'">
          <span class="system-pill__label">当前判定</span>
          <span class="system-pill__value">{{ isSystemHealthy ? '基础健康' : '需要检查' }}</span>
        </div>
      </div>
    </header>

    <section class="system-status-grid">
      <el-skeleton
        v-if="isStatusPending"
        :rows="6"
        animated
        class="system-status-grid__skeleton"
      />

      <div v-else-if="isStatusError" class="system-state-card system-state-card--error">
        <h2>系统状态加载失败</h2>
        <p>{{ statusErrorMessage }}</p>
      </div>

      <template v-else>
        <article class="system-card">
          <div class="system-card__header">
            <span class="system-card__eyebrow">Environment</span>
            <StatusLabel :status="environmentMeta.status" :text="environmentMeta.label" />
          </div>
          <div class="system-card__value">{{ environmentLabel }}</div>
          <p class="system-card__description">当前后端运行环境。</p>
        </article>

        <article class="system-card">
          <div class="system-card__header">
            <span class="system-card__eyebrow">Debug</span>
            <StatusLabel :status="debugMeta.status" :text="debugMeta.label" />
          </div>
          <div class="system-card__value">{{ status.debug ? 'ON' : 'OFF' }}</div>
          <p class="system-card__description">生产环境应保持关闭。</p>
        </article>

        <article class="system-card">
          <div class="system-card__header">
            <span class="system-card__eyebrow">Database</span>
            <StatusLabel :status="databaseMeta.status" :text="databaseMeta.label" />
          </div>
          <div class="system-card__value">{{ databaseLabel }}</div>
          <p class="system-card__description">由后端 `/system/status` 直接返回数据库探活结果。</p>
        </article>

        <article class="system-card">
          <div class="system-card__header">
            <span class="system-card__eyebrow">LLM API</span>
            <StatusLabel :status="llmMeta.status" :text="llmMeta.label" />
          </div>
          <div class="system-card__value">{{ status.llm_api_configured ? 'READY' : 'MISSING' }}</div>
          <p class="system-card__description">生成、返修和部分探测动作依赖此项。</p>
        </article>
      </template>
    </section>

    <section class="system-layout">
      <article class="system-panel system-panel--build">
        <div class="system-panel__header">
          <div>
            <span class="system-panel__eyebrow">Build Metadata</span>
            <h2 class="system-panel__title">当前 Build 版本</h2>
          </div>
          <button class="system-refresh-button" type="button" @click="handleRefresh">
            <RefreshCcw class="h-4 w-4" />
            刷新
          </button>
        </div>

        <div v-if="isStatusError" class="system-state-card system-state-card--error">
          <h3>Build 信息不可用</h3>
          <p>{{ statusErrorMessage }}</p>
        </div>
        <div v-else class="system-build-card">
          <pre class="system-build-card__value">{{ status.build || 'unknown-build' }}</pre>
          <p class="system-build-card__hint">
            当前 build 标签由后端 `format_build_label()` 生成，适合用于快速确认线上部署版本。
          </p>
        </div>
      </article>

      <article class="system-panel">
        <div class="system-panel__header">
          <div>
            <span class="system-panel__eyebrow">Future Observability</span>
            <h2 class="system-panel__title">已预留观测项</h2>
          </div>
        </div>

        <ul class="system-notes">
          <li>budget / token 用量面板</li>
          <li>scheduler 运行状态</li>
          <li>发布器状态与平台连通性</li>
          <li>容器级 build / health 视图</li>
        </ul>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RefreshCcw } from 'lucide-vue-next'

import StatusLabel from '../../components/StatusLabel.vue'
import { useSystemStatusQuery } from '../../composables/useSystem'

const statusQuery = useSystemStatusQuery()

const status = computed(() => statusQuery.data.value ?? {
  environment: 'unknown',
  debug: false,
  database: 'unknown',
  llm_api_configured: false,
  build: 'unknown-build',
})

const isStatusPending = computed(() => statusQuery.isPending.value)
const isStatusError = computed(() => statusQuery.isError.value)
const statusErrorMessage = computed(() => getErrorMessage(statusQuery.error.value))

const environmentLabel = computed(() => formatEnvironment(status.value.environment))
const databaseLabel = computed(() => formatDatabase(status.value.database))

const environmentMeta = computed(() => {
  const env = status.value.environment

  if (env === 'prod' || env === 'production') {
    return { status: 'success' as const, label: '生产' }
  }

  if (env === 'staging') {
    return { status: 'warning' as const, label: '预发' }
  }

  return { status: 'info' as const, label: '开发/其他' }
})

const debugMeta = computed(() =>
  status.value.debug
    ? { status: 'warning' as const, label: '开启' }
    : { status: 'success' as const, label: '关闭' },
)

const databaseMeta = computed(() =>
  status.value.database === 'ok'
    ? { status: 'success' as const, label: '正常' }
    : { status: 'danger' as const, label: '异常' },
)

const llmMeta = computed(() =>
  status.value.llm_api_configured
    ? { status: 'success' as const, label: '已配置' }
    : { status: 'danger' as const, label: '未配置' },
)

const isSystemHealthy = computed(
  () => status.value.database === 'ok' && status.value.llm_api_configured && !status.value.debug,
)

function handleRefresh() {
  statusQuery.refetch()
}

function formatEnvironment(value: string | null | undefined) {
  if (!value) {
    return '未知环境'
  }

  const normalized = value.toLowerCase()
  const map: Record<string, string> = {
    prod: 'Production',
    production: 'Production',
    staging: 'Staging',
    dev: 'Development',
    development: 'Development',
    test: 'Test',
  }

  return map[normalized] || value
}

function formatDatabase(value: string | null | undefined) {
  if (!value) {
    return 'Unknown'
  }

  return value === 'ok' ? 'Connected' : 'Disconnected'
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }

  return '请求失败，请稍后重试。'
}
</script>

<style scoped>
.system-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%;
}

.system-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 360px);
  align-items: start;
  gap: 20px;
  padding: 28px 32px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: 
    linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, transparent 100%),
    var(--bg-panel);
  position: relative;
  isolation: isolate;
}

.system-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background-color: var(--color-primary);
}

.system-hero__main {
  min-width: 0;
  max-width: 720px;
}

.system-hero__eyebrow,
.system-panel__eyebrow,
.system-card__eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

.system-hero__title {
  margin: 10px 0 12px;
  font-size: 30px;
  line-height: 1.1;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.system-hero__description {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: rgba(241, 243, 249, 0.78);
}

.system-hero__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  min-width: 0;
  width: 100%;
  max-width: 360px;
  align-self: start;
}

.system-pill {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-height: 84px;
  padding: 14px 20px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  background: var(--bg-dark);
}

.system-pill--warning {
  border-color: rgba(245, 158, 11, 0.18);
}

.system-pill--healthy {
  border-color: rgba(34, 197, 94, 0.18);
}

.system-pill__label {
  font-size: 12px;
  color: var(--text-muted);
}

.system-pill__value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
}

.system-status-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.system-status-grid__skeleton {
  grid-column: 1 / -1;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
}

.system-card,
.system-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
  min-height: 0;
  position: relative;
}

.system-card__header,
.system-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.system-card__value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-main);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  line-height: 1.2;
}

.system-card__description {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.system-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.8fr);
  gap: 20px;
}

.system-panel__title {
  margin: 6px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.system-refresh-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: rgba(7, 10, 19, 0.5);
  color: var(--text-main);
  cursor: pointer;
  transition: 0.2s ease;
  font: inherit;
}

.system-refresh-button:hover {
  border-color: var(--border-focus);
  transform: translateY(-1px);
}

.system-build-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  background: rgba(7, 10, 19, 0.52);
}

.system-build-card__value {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #d6e0f8;
  font-size: 13px;
  line-height: 1.7;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.system-build-card__hint {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.system-notes {
  margin: 0;
  padding-left: 18px;
  color: var(--text-muted);
  line-height: 1.9;
}

.system-state-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  gap: 12px;
  min-height: 160px;
  padding: 24px;
  border: 1px dashed var(--border-subtle);
  border-radius: 8px;
  background: rgba(10, 14, 26, 0.3);
  margin: auto 0;
}

.system-state-card--error {
  border-color: rgba(239, 68, 68, 0.22);
  background: rgba(239, 68, 68, 0.06);
}

.system-state-card h2,
.system-state-card h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
}

.system-state-card p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

@media (max-width: 1280px) {
  .system-status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .system-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 920px) {
  .system-hero {
    grid-template-columns: 1fr;
  }

  .system-hero__meta {
    grid-template-columns: 1fr;
    min-width: 0;
  }
}

@media (max-width: 640px) {
  .system-page {
    gap: 18px;
  }

  .system-hero,
  .system-card,
  .system-panel {
    padding: 16px;
  }

  .system-status-grid {
    grid-template-columns: 1fr;
  }

  .system-card__header,
  .system-panel__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
