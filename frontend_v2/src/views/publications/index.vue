<template>
  <div class="publications-page">
    <header class="publications-hero">
      <div class="publications-hero__main">
        <span class="publications-hero__eyebrow">Publication Audit Center</span>
        <h1 class="publications-hero__title">发布中心</h1>
        <p class="publications-hero__description">
          从“文章是否已发布”升级为渠道级发布审计，集中排查草稿、正式发布和重试结果。
        </p>
      </div>

      <div class="publications-hero__meta">
        <div class="publications-pill">
          <span class="publications-pill__label">当前结果集</span>
          <span class="publications-pill__value">{{ formatNumber(totalPublications) }}</span>
        </div>
        <div class="publications-pill" :class="hasWarnings ? 'publications-pill--warning' : 'publications-pill--healthy'">
          <span class="publications-pill__label">页面状态</span>
          <span class="publications-pill__value">{{ hasWarnings ? '部分降级' : '正常轮询' }}</span>
        </div>
      </div>
    </header>

    <section v-if="hasWarnings" class="publications-alerts">
      <el-alert
        v-for="warning in warningMessages"
        :key="warning"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #title>{{ warning }}</template>
      </el-alert>
    </section>

    <section class="publications-summary">
      <el-skeleton
        v-if="isListPending"
        :rows="3"
        animated
        class="publications-summary__skeleton"
      />
      <template v-else-if="isListError">
        <div class="publications-state-card publications-state-card--error">
          <h2>发布记录加载失败</h2>
          <p>{{ listErrorMessage }}</p>
        </div>
      </template>
      <template v-else>
        <StatCard title="正式发布" :value="formatNumber(pagePublishedCount)">
          <template #icon>
            <Send class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="草稿保存" :value="formatNumber(pageDraftCount)">
          <template #icon>
            <FilePenLine class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="失败记录" :value="formatNumber(pageFailedCount)">
          <template #icon>
            <CircleX class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="可重试" :value="formatNumber(pageRetryableCount)">
          <template #icon>
            <RotateCcw class="h-5 w-5" />
          </template>
        </StatCard>
      </template>
    </section>

    <section class="publications-panel">
      <div class="publications-panel__header">
        <div>
          <span class="publications-panel__eyebrow">检索与筛选</span>
          <h2 class="publications-panel__title">发布记录列表</h2>
        </div>
        <button class="publications-refresh-button" type="button" @click="handleRefresh">
          <RefreshCcw class="h-4 w-4" />
          刷新
        </button>
      </div>

      <div class="publications-filters">
        <label class="publications-field">
          <span class="publications-field__label">渠道</span>
          <el-select
            v-model="draftFilters.channel"
            placeholder="全部渠道"
            clearable
            class="publications-field__control"
          >
            <el-option
              v-for="option in channelOptions"
              :key="option.value || 'all-channel'"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </label>

        <label class="publications-field">
          <span class="publications-field__label">状态</span>
          <el-select
            v-model="draftFilters.status"
            placeholder="全部状态"
            clearable
            class="publications-field__control"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value || 'all-status'"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </label>

        <label class="publications-field">
          <span class="publications-field__label">触发方式</span>
          <el-select
            v-model="draftFilters.trigger_mode"
            placeholder="全部触发方式"
            clearable
            class="publications-field__control"
          >
            <el-option
              v-for="option in triggerModeOptions"
              :key="option.value || 'all-trigger'"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </label>

        <label class="publications-field publications-field--query">
          <span class="publications-field__label">搜索</span>
          <el-input
            v-model="draftFilters.query"
            class="publications-field__control"
            placeholder="标题 / slug / external id"
            clearable
            @keyup.enter="applyFilters"
          />
        </label>

        <div class="publications-actions">
          <button class="publications-action-button publications-action-button--primary" type="button" @click="applyFilters">
            应用筛选
          </button>
          <button class="publications-action-button" type="button" @click="resetFilters">
            重置
          </button>
        </div>
      </div>

      <div class="publications-list-state">
        <el-skeleton v-if="isListPending" :rows="8" animated />
        <div v-else-if="isListError" class="publications-state-card publications-state-card--error">
          <h3>发布列表加载失败</h3>
          <p>{{ listErrorMessage }}</p>
        </div>
        <div v-else-if="!publications.length" class="publications-state-card">
          <h3>没有匹配的发布记录</h3>
          <p>当前筛选条件下没有命中结果，可以调整渠道、状态或搜索词后重试。</p>
        </div>
        <template v-else>
          <IndustrialTable :data="publications">
            <el-table-column min-width="220" label="文章">
              <template #default="{ row }">
                <div class="publication-article-cell">
                  <button
                    class="publication-link-button"
                    type="button"
                    @click="openPublicationDetail(row.id)"
                  >
                    {{ row.article_title || `文章 #${row.article_id}` }}
                  </button>
                  <span class="publication-article-cell__meta">
                    {{ row.article_slug || `ID ${row.article_id}` }}
                  </span>
                </div>
              </template>
            </el-table-column>

            <el-table-column width="110" label="渠道">
              <template #default="{ row }">
                {{ row.channel_label }}
              </template>
            </el-table-column>

            <el-table-column width="110" label="模式">
              <template #default="{ row }">
                {{ formatPublishMode(row.publish_mode) }}
              </template>
            </el-table-column>

            <el-table-column width="120" align="center" label="状态">
              <template #default="{ row }">
                <StatusLabel
                  :status="publicationStatusMeta(row.status, row.publish_mode).status"
                  :text="publicationStatusMeta(row.status, row.publish_mode).label"
                />
              </template>
            </el-table-column>

            <el-table-column width="120" label="触发方式">
              <template #default="{ row }">
                {{ formatTriggerMode(row.trigger_mode) }}
              </template>
            </el-table-column>

            <el-table-column width="92" align="center" label="尝试">
              <template #default="{ row }">
                #{{ row.attempt_no }}
              </template>
            </el-table-column>

            <el-table-column min-width="220" label="结果">
              <template #default="{ row }">
                <div class="publication-result-cell">
                  <a
                    v-if="row.external_url"
                    :href="row.external_url"
                    target="_blank"
                    rel="noreferrer"
                    class="publication-external-link"
                  >
                    {{ row.external_url }}
                  </a>
                  <span v-else class="publication-result-cell__placeholder">未返回外链</span>
                  <span class="publication-result-cell__message">
                    {{ row.error_message || row.message || '无额外信息' }}
                  </span>
                </div>
              </template>
            </el-table-column>

            <el-table-column width="156" label="更新时间">
              <template #default="{ row }">
                {{ formatDateTime(row.updated_at || row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column width="156" fixed="right" label="操作">
              <template #default="{ row }">
                <div class="publication-actions-cell">
                  <button
                    class="publications-table-action"
                    type="button"
                    @click="openPublicationDetail(row.id)"
                  >
                    详情
                  </button>
                  <button
                    v-if="row.retryable"
                    class="publications-table-action publications-table-action--primary"
                    type="button"
                    :disabled="retryMutation.isPending.value"
                    @click="handleRetry(row.id)"
                  >
                    重试
                  </button>
                </div>
              </template>
            </el-table-column>
          </IndustrialTable>

          <div class="publications-pagination">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="totalPublications"
              layout="total, prev, pager, next"
              background
            />
          </div>
        </template>
      </div>
    </section>

    <DetailPanel
      v-model="detailPanelOpen"
      title="发布详情"
      size="780px"
    >
      <div class="publication-detail">
        <div v-if="isDetailPending" class="publication-detail__loading">
          <el-skeleton :rows="8" animated />
        </div>

        <div v-else-if="isDetailError" class="publications-state-card publications-state-card--error">
          <h3>发布详情加载失败</h3>
          <p>{{ detailErrorMessage }}</p>
        </div>

        <div v-else-if="!selectedPublication" class="publications-state-card">
          <h3>未找到发布记录</h3>
          <p>该记录可能已不存在，或当前接口没有返回详情。</p>
        </div>

        <template v-else>
          <section class="publication-detail__summary">
            <div class="publication-detail__summary-header">
              <div>
                <span class="publication-detail__eyebrow">Publication Overview</span>
                <h3 class="publication-detail__title">
                  {{ selectedPublication.article_title || `文章 #${selectedPublication.article_id}` }}
                </h3>
              </div>

              <div class="publication-detail__header-actions">
                <StatusLabel
                  :status="publicationStatusMeta(selectedPublication.status, selectedPublication.publish_mode).status"
                  :text="publicationStatusMeta(selectedPublication.status, selectedPublication.publish_mode).label"
                />
                <button
                  v-if="selectedPublication.retryable"
                  class="publications-table-action publications-table-action--primary"
                  type="button"
                  :disabled="retryMutation.isPending.value"
                  @click="handleRetry(selectedPublication.id)"
                >
                  重试当前记录
                </button>
              </div>
            </div>

            <el-descriptions :column="2" border class="publication-detail__descriptions">
              <el-descriptions-item label="文章 ID">
                {{ selectedPublication.article_id }}
              </el-descriptions-item>
              <el-descriptions-item label="slug">
                {{ selectedPublication.article_slug || '无' }}
              </el-descriptions-item>
              <el-descriptions-item label="渠道">
                {{ selectedPublication.channel_label }}
              </el-descriptions-item>
              <el-descriptions-item label="适配器">
                {{ selectedPublication.adapter_label }}
              </el-descriptions-item>
              <el-descriptions-item label="发布模式">
                {{ formatPublishMode(selectedPublication.publish_mode) }}
              </el-descriptions-item>
              <el-descriptions-item label="触发方式">
                {{ formatTriggerMode(selectedPublication.trigger_mode) }}
              </el-descriptions-item>
              <el-descriptions-item label="尝试次数">
                #{{ selectedPublication.attempt_no }}
              </el-descriptions-item>
              <el-descriptions-item label="重试来源">
                {{ selectedPublication.retry_of_publication_id ? `#${selectedPublication.retry_of_publication_id}` : '无' }}
              </el-descriptions-item>
              <el-descriptions-item label="重试分支数">
                {{ selectedPublication.retry_attempts_total }}
              </el-descriptions-item>
              <el-descriptions-item label="外部 ID">
                {{ selectedPublication.external_id || '无' }}
              </el-descriptions-item>
              <el-descriptions-item label="发布时间">
                {{ formatDateTime(selectedPublication.published_at) }}
              </el-descriptions-item>
            </el-descriptions>

            <a
              v-if="selectedPublication.external_url"
              :href="selectedPublication.external_url"
              target="_blank"
              rel="noreferrer"
              class="publication-detail__external-link"
            >
              打开渠道结果页
            </a>
          </section>

          <section v-if="selectedPublication.error_message" class="publication-detail__error-panel">
            <div class="publication-detail__section-head">
              <h4>错误信息</h4>
            </div>
            <p>{{ selectedPublication.error_message }}</p>
          </section>

          <section v-if="selectedPublication.message" class="publication-detail__message-panel">
            <div class="publication-detail__section-head">
              <h4>适配器消息</h4>
            </div>
            <p>{{ selectedPublication.message }}</p>
          </section>

          <section v-if="selectedPublication.request_payload_json" class="publication-detail__json-panel">
            <div class="publication-detail__section-head">
              <h4>请求载荷</h4>
            </div>
            <pre>{{ formatJson(selectedPublication.request_payload_json) }}</pre>
          </section>

          <section v-if="selectedPublication.response_payload_json" class="publication-detail__json-panel">
            <div class="publication-detail__section-head">
              <h4>适配器响应</h4>
            </div>
            <pre>{{ formatJson(selectedPublication.response_payload_json) }}</pre>
          </section>
        </template>
      </div>
    </DetailPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleX, FilePenLine, RefreshCcw, RotateCcw, Send } from 'lucide-vue-next'

import DetailPanel from '../../components/DetailPanel.vue'
import IndustrialTable from '../../components/IndustrialTable.vue'
import StatCard from '../../components/StatCard.vue'
import StatusLabel from '../../components/StatusLabel.vue'
import {
  usePublicationDetailQuery,
  usePublicationsQuery,
  useRetryPublicationMutation,
} from '../../composables/usePublications'

const pageSize = 20
const pollingIntervalMs = 20_000

const route = useRoute()
const router = useRouter()

const channelOptions = [
  { label: '全部渠道', value: '' },
  { label: '长文渠道', value: 'longform_channel' },
  { label: '移动渠道', value: 'mobile_channel' },
]

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '草稿已保存', value: 'draft_saved' },
  { label: '已正式发布', value: 'published' },
  { label: '失败', value: 'failed' },
  { label: '处理中', value: 'pending' },
]

const triggerModeOptions = [
  { label: '全部触发方式', value: '' },
  { label: '手动', value: 'manual' },
  { label: '自动', value: 'auto' },
  { label: '重试', value: 'retry' },
]

const initialQuery = typeof route.query.query === 'string' ? route.query.query : ''

const draftFilters = reactive({
  channel: '',
  status: '',
  trigger_mode: '',
  query: initialQuery,
})

const appliedFilters = ref({
  channel: '',
  status: '',
  trigger_mode: '',
  query: initialQuery,
})

const currentPage = ref(1)
const selectedPublicationId = ref<number | null>(null)
const detailPanelOpen = ref(false)

const queryFilters = computed(() => ({
  ...(appliedFilters.value.channel ? { channel: appliedFilters.value.channel } : {}),
  ...(appliedFilters.value.status ? { status: appliedFilters.value.status } : {}),
  ...(appliedFilters.value.trigger_mode ? { trigger_mode: appliedFilters.value.trigger_mode } : {}),
  ...(appliedFilters.value.query ? { query: appliedFilters.value.query.trim() } : {}),
  limit: pageSize,
  offset: (currentPage.value - 1) * pageSize,
}))

const publicationsQuery = usePublicationsQuery(queryFilters)
const detailQuery = usePublicationDetailQuery(selectedPublicationId)
const retryMutation = useRetryPublicationMutation()

const publications = computed(() => publicationsQuery.data.value?.items ?? [])
const totalPublications = computed(() => publicationsQuery.data.value?.total ?? 0)
const selectedPublication = computed(() => detailQuery.data.value?.publication ?? null)
const pagePublishedCount = computed(() =>
  publications.value.filter((item) => item.status === 'published').length,
)
const pageDraftCount = computed(() =>
  publications.value.filter((item) => item.status === 'draft_saved').length,
)
const pageFailedCount = computed(() =>
  publications.value.filter((item) => item.status === 'failed').length,
)
const pageRetryableCount = computed(() =>
  publications.value.filter((item) => item.retryable).length,
)

const isListPending = computed(() => publicationsQuery.isPending.value)
const isListError = computed(() => publicationsQuery.isError.value)
const isDetailPending = computed(() => detailQuery.isPending.value)
const isDetailError = computed(() => detailQuery.isError.value)

const warningMessages = computed(() =>
  [
    publicationsQuery.data.value?.warning,
    detailQuery.data.value?.warning,
  ].filter((item): item is string => Boolean(item)),
)

const hasWarnings = computed(() => warningMessages.value.length > 0)
const listErrorMessage = computed(() => getErrorMessage(publicationsQuery.error.value))
const detailErrorMessage = computed(() => getErrorMessage(detailQuery.error.value))

let pollingTimer: number | null = null

watch(
  () => route.query.query,
  (value) => {
    const nextValue = typeof value === 'string' ? value : ''
    draftFilters.query = nextValue
    appliedFilters.value = {
      ...appliedFilters.value,
      query: nextValue,
    }
    currentPage.value = 1
  },
)

watch(detailPanelOpen, (open) => {
  if (!open) {
    return
  }

  detailQuery.refetch()
})

onMounted(() => {
  pollingTimer = window.setInterval(() => {
    publicationsQuery.refetch()

    if (detailPanelOpen.value && selectedPublicationId.value) {
      detailQuery.refetch()
    }
  }, pollingIntervalMs)
})

onBeforeUnmount(() => {
  if (pollingTimer !== null) {
    window.clearInterval(pollingTimer)
  }
})

function applyFilters() {
  currentPage.value = 1
  appliedFilters.value = {
    channel: draftFilters.channel,
    status: draftFilters.status,
    trigger_mode: draftFilters.trigger_mode,
    query: draftFilters.query,
  }

  void router.replace({
    query: {
      ...route.query,
      ...(draftFilters.query ? { query: draftFilters.query } : { query: undefined }),
    },
  })
}

function resetFilters() {
  draftFilters.channel = ''
  draftFilters.status = ''
  draftFilters.trigger_mode = ''
  draftFilters.query = ''
  currentPage.value = 1
  appliedFilters.value = {
    channel: '',
    status: '',
    trigger_mode: '',
    query: '',
  }

  void router.replace({
    query: {
      ...route.query,
      query: undefined,
    },
  })
}

function handleRefresh() {
  publicationsQuery.refetch()

  if (detailPanelOpen.value && selectedPublicationId.value) {
    detailQuery.refetch()
  }
}

function openPublicationDetail(publicationId: number) {
  selectedPublicationId.value = publicationId
  detailPanelOpen.value = true
}

async function handleRetry(publicationId: number) {
  try {
    await ElMessageBox.confirm(
      '将基于当前发布记录重新发起一次渠道发布尝试。是否继续？',
      '确认重试',
      {
        confirmButtonText: '确认重试',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    await retryMutation.mutateAsync(publicationId)
    ElMessage.success('已发起重试请求。')

    if (selectedPublicationId.value === publicationId) {
      detailQuery.refetch()
    }
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }

    ElMessage.error(getErrorMessage(error))
  }
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '--'
  }

  return new Intl.NumberFormat('zh-CN').format(value)
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return '暂无'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function formatPublishMode(value: string | null | undefined) {
  if (!value) {
    return '未知'
  }

  const map: Record<string, string> = {
    draft: '草稿',
    live: '正式发布',
  }

  return map[value] || value
}

function formatTriggerMode(value: string | null | undefined) {
  if (!value) {
    return '未知'
  }

  const map: Record<string, string> = {
    manual: '手动',
    auto: '自动',
    retry: '重试',
  }

  return map[value] || value
}

function publicationStatusMeta(status: string | null | undefined, publishMode: string | null | undefined) {
  if (status === 'published') {
    return { status: 'success' as const, label: '已发布' }
  }

  if (status === 'draft_saved') {
    return {
      status: publishMode === 'live' ? 'warning' as const : 'primary' as const,
      label: publishMode === 'live' ? '已存草稿/未发布' : '草稿已保存',
    }
  }

  if (status === 'failed') {
    return { status: 'danger' as const, label: '失败' }
  }

  if (status === 'pending') {
    return { status: 'info' as const, label: '处理中' }
  }

  return { status: 'info' as const, label: status || '未知' }
}

function formatJson(value: Record<string, unknown> | unknown[] | null | undefined) {
  if (!value) {
    return ''
  }

  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }

  return '请求失败，请稍后重试。'
}
</script>

<style scoped>
.publications-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%;
}

.publications-hero {
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

.publications-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background-color: var(--color-primary);
}

.publications-hero__main {
  min-width: 0;
  max-width: 720px;
}

.publications-hero__eyebrow,
.publications-panel__eyebrow,
.publication-detail__eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

.publications-hero__title {
  margin: 10px 0 12px;
  font-size: 30px;
  line-height: 1.1;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.publications-hero__description {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: rgba(241, 243, 249, 0.78);
}

.publications-hero__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  min-width: 0;
  width: 100%;
  max-width: 360px;
  align-self: start;
}

.publications-pill {
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

.publications-pill--warning {
  border-color: rgba(245, 158, 11, 0.18);
}

.publications-pill--healthy {
  border-color: rgba(34, 197, 94, 0.18);
}

.publications-pill__label {
  font-size: 12px;
  color: var(--text-muted);
}

.publications-pill__value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
}

.publications-alerts {
  display: grid;
  gap: 12px;
}

.publications-alerts :deep(.el-alert) {
  --el-alert-bg-color: rgba(245, 158, 11, 0.1);
  --el-alert-border-color: rgba(245, 158, 11, 0.2);
  --el-alert-text-color: #f7d089;
  border: 1px solid var(--el-alert-border-color);
  border-radius: 8px;
}

.publications-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.publications-summary__skeleton {
  grid-column: 1 / -1;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
}

.publications-panel {
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

.publications-panel__header,
.publication-detail__summary-header,
.publication-detail__section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.publications-panel__title {
  margin: 6px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.publications-refresh-button,
.publications-action-button,
.publications-table-action,
.publication-link-button {
  border: none;
  background: transparent;
  font: inherit;
}

.publications-refresh-button,
.publications-action-button,
.publications-table-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s ease;
}

.publications-refresh-button,
.publications-action-button {
  border: 1px solid var(--border-subtle);
  color: var(--text-main);
  background: rgba(7, 10, 19, 0.5);
}

.publications-action-button--primary,
.publications-table-action--primary {
  background: rgba(37, 99, 235, 0.18);
  border: 1px solid rgba(37, 99, 235, 0.28);
  color: #c9d9ff;
}

.publications-refresh-button:hover,
.publications-action-button:hover,
.publications-table-action:hover {
  border-color: var(--border-focus);
  transform: translateY(-1px);
}

.publications-table-action:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.publications-filters {
  display: grid;
  grid-template-columns: 150px 150px 150px minmax(220px, 1fr) auto;
  gap: 12px;
  align-items: end;
}

.publications-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.publications-field__label {
  font-size: 12px;
  color: var(--text-muted);
}

.publications-field__control {
  width: 100%;
}

.publications-filters :deep(.el-input__wrapper),
.publications-filters :deep(.el-select__wrapper) {
  background: rgba(7, 10, 19, 0.72);
  box-shadow: inset 0 0 0 1px var(--border-subtle);
}

.publications-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.publications-list-state {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.publications-pagination {
  display: flex;
  justify-content: flex-end;
}

.publications-pagination :deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background-color: var(--color-primary);
}

.publications-pagination :deep(.el-pagination.is-background .btn-next),
.publications-pagination :deep(.el-pagination.is-background .btn-prev),
.publications-pagination :deep(.el-pagination.is-background .el-pager li) {
  background-color: var(--bg-panel);
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
}

.publication-article-cell,
.publication-result-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.publication-link-button {
  color: #d8e5ff;
  cursor: pointer;
  padding: 0;
  text-align: left;
}

.publication-link-button:hover {
  color: #8db2ff;
}

.publication-article-cell__meta,
.publication-result-cell__message,
.publication-result-cell__placeholder {
  color: var(--text-muted);
  font-size: 12px;
}

.publication-external-link {
  color: #9fc0ff;
  text-decoration: none;
  word-break: break-all;
}

.publication-external-link:hover,
.publication-detail__external-link:hover {
  color: #d7e4ff;
}

.publication-actions-cell {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.publications-state-card {
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

.publications-state-card--error {
  border-color: rgba(239, 68, 68, 0.22);
  background: rgba(239, 68, 68, 0.06);
}

.publications-state-card h2,
.publications-state-card h3,
.publication-detail__section-head h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
}

.publications-state-card p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  opacity: 0.8;
  line-height: 1.5;
}

.publication-detail {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.publication-detail__summary,
.publication-detail__error-panel,
.publication-detail__message-panel,
.publication-detail__json-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: rgba(7, 10, 19, 0.5);
}

.publication-detail__title {
  margin: 8px 0 0;
  color: var(--text-main);
  font-size: 20px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-weight: 600;
}

.publication-detail__header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.publication-detail__descriptions :deep(.el-descriptions__label) {
  width: 108px;
}

.publication-detail__descriptions :deep(.el-descriptions__table) {
  --el-descriptions-table-border: var(--border-subtle);
  --el-descriptions-item-bordered-label-background: rgba(255, 255, 255, 0.03);
  --el-fill-color-blank: transparent;
  --el-text-color-primary: var(--text-main);
  --el-text-color-regular: var(--text-muted);
}

.publication-detail__external-link {
  color: #9fc0ff;
  text-decoration: none;
}

.publication-detail__error-panel p {
  margin: 0;
  color: #f7c1c1;
  line-height: 1.7;
}

.publication-detail__message-panel p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.publication-detail__json-panel pre {
  margin: 0;
  padding: 14px;
  overflow-x: auto;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(0, 0, 0, 0.24);
  color: #d4def7;
  font-size: 12px;
  line-height: 1.6;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

@media (max-width: 1280px) {
  .publications-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .publications-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .publications-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

@media (max-width: 920px) {
  .publications-hero {
    grid-template-columns: 1fr;
  }

  .publications-hero__meta {
    grid-template-columns: 1fr;
    min-width: 0;
  }
}

@media (max-width: 640px) {
  .publications-page {
    gap: 18px;
  }

  .publications-hero,
  .publications-panel,
  .publication-detail__summary,
  .publication-detail__error-panel,
  .publication-detail__message-panel,
  .publication-detail__json-panel {
    padding: 16px;
  }

  .publications-summary,
  .publications-filters {
    grid-template-columns: 1fr;
  }

  .publications-panel__header,
  .publication-detail__summary-header,
  .publication-detail__section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .publication-detail__header-actions {
    justify-content: flex-start;
  }
}
</style>
