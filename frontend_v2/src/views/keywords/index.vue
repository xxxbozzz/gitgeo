<template>
  <div class="keywords-page">
    <header class="keywords-hero">
      <div class="keywords-hero__main">
        <span class="keywords-hero__eyebrow">Keyword Operations Center</span>
        <h1 class="keywords-hero__title">关键词中心</h1>
        <p class="keywords-hero__description">
          统一查看关键词池、真空词池和技术集群分布，先把读页做成稳定运营视图。
        </p>
      </div>

      <div class="keywords-hero__meta">
        <div class="keywords-pill">
          <span class="keywords-pill__label">轮询频率</span>
          <span class="keywords-pill__value">30s / 次</span>
        </div>
        <div class="keywords-pill" :class="hasWarnings ? 'keywords-pill--warning' : 'keywords-pill--healthy'">
          <span class="keywords-pill__label">数据状态</span>
          <span class="keywords-pill__value">{{ hasWarnings ? '部分降级' : '正常' }}</span>
        </div>
      </div>
    </header>

    <section v-if="hasWarnings" class="keywords-alerts">
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

    <section class="keywords-summary">
      <el-skeleton
        v-if="isSummaryPending"
        :rows="3"
        animated
        class="keywords-summary__skeleton"
      />
      <template v-else-if="isSummaryError">
        <div class="keywords-state-card keywords-state-card--error">
          <h2>关键词概览加载失败</h2>
          <p>{{ summaryErrorMessage }}</p>
        </div>
      </template>
      <template v-else>
        <StatCard title="关键词总量" :value="formatNumber(totalKeywords)">
          <template #icon>
            <Search class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="待消费 / 真空词" :value="formatNumber(gapKeywordsTotal)">
          <template #icon>
            <Orbit class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="已消费" :value="formatNumber(consumedKeywordsTotal)">
          <template #icon>
            <Link2 class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="技术集群" :value="formatNumber(clusterCount)">
          <template #icon>
            <Network class="h-5 w-5" />
          </template>
        </StatCard>
      </template>
    </section>

    <section class="keywords-layout">
      <article class="keywords-panel keywords-panel--main">
        <div class="keywords-panel__header">
          <div>
            <span class="keywords-panel__eyebrow">检索与筛选</span>
            <h2 class="keywords-panel__title">关键词池</h2>
          </div>
          <button class="keywords-refresh-button" type="button" @click="handleRefresh">
            <RefreshCcw class="h-4 w-4" />
            刷新
          </button>
        </div>

        <div class="keywords-filters">
          <label class="keywords-field">
            <span class="keywords-field__label">状态</span>
            <el-select
              v-model="draftFilters.status"
              placeholder="全部状态"
              clearable
              class="keywords-field__control"
            >
              <el-option
                v-for="option in statusOptions"
                :key="option.value || 'all-status'"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </label>

          <label class="keywords-field keywords-field--query">
            <span class="keywords-field__label">搜索</span>
            <el-input
              v-model="draftFilters.query"
              class="keywords-field__control"
              placeholder="关键词 / 文章标题 / slug"
              clearable
              @keyup.enter="applyFilters"
            />
          </label>

          <div class="keywords-actions">
            <button class="keywords-action-button keywords-action-button--primary" type="button" @click="applyFilters">
              应用筛选
            </button>
            <button class="keywords-action-button" type="button" @click="resetFilters">
              重置
            </button>
          </div>
        </div>

        <div class="keywords-list-state">
          <el-skeleton v-if="isKeywordsPending" :rows="8" animated />
          <div v-else-if="isKeywordsError" class="keywords-state-card keywords-state-card--error">
            <h3>关键词列表加载失败</h3>
            <p>{{ keywordsErrorMessage }}</p>
          </div>
          <div v-else-if="!keywords.length" class="keywords-state-card">
            <h3>没有匹配的关键词</h3>
            <p>当前筛选条件下没有命中结果，可以调整状态或搜索词后重试。</p>
          </div>
          <template v-else>
            <IndustrialTable :data="keywords">
              <el-table-column min-width="220" label="关键词">
                <template #default="{ row }">
                  <div class="keyword-cell">
                    <span class="keyword-cell__keyword">{{ row.keyword }}</span>
                    <span class="keyword-cell__meta">#{{ row.id }}</span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column width="120" align="center" label="状态">
                <template #default="{ row }">
                  <StatusLabel
                    :status="row.status === 'consumed' ? 'success' : 'warning'"
                    :text="row.status === 'consumed' ? '已消费' : '待消费'"
                  />
                </template>
              </el-table-column>

              <el-table-column width="120" align="center" label="搜索量">
                <template #default="{ row }">
                  {{ formatNumber(row.search_volume) }}
                </template>
              </el-table-column>

              <el-table-column width="110" align="center" label="难度">
                <template #default="{ row }">
                  <StatusLabel
                    :status="difficultyMeta(row.difficulty).status"
                    :text="difficultyMeta(row.difficulty).label"
                  />
                </template>
              </el-table-column>

              <el-table-column width="120" align="center" label="内耗风险">
                <template #default="{ row }">
                  <StatusLabel
                    :status="row.cannibalization_risk ? 'danger' : 'info'"
                    :text="row.cannibalization_risk ? '有风险' : '正常'"
                  />
                </template>
              </el-table-column>

              <el-table-column min-width="220" label="绑定文章">
                <template #default="{ row }">
                  <RouterLink
                    v-if="row.target_article_id"
                    class="keyword-article-link"
                    :to="{ path: '/articles', query: { query: row.target_article_slug || row.target_article_title || row.keyword } }"
                  >
                    {{ row.target_article_title || `文章 #${row.target_article_id}` }}
                  </RouterLink>
                  <span v-else class="keyword-article-placeholder">未绑定文章</span>
                </template>
              </el-table-column>

              <el-table-column width="156" label="创建时间">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
            </IndustrialTable>

            <div class="keywords-pagination">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="pageSize"
                :total="filteredKeywordsTotal"
                layout="total, prev, pager, next"
                background
              />
            </div>
          </template>
        </div>
      </article>

      <aside class="keywords-side-stack">
        <article class="keywords-panel">
          <div class="keywords-panel__header">
            <div>
              <span class="keywords-panel__eyebrow">Gap Queue</span>
              <h2 class="keywords-panel__title">真空词优先队列</h2>
            </div>
            <StatusLabel status="warning" :text="`${gapKeywordsTotal} 条`" />
          </div>

          <el-skeleton v-if="isGapKeywordsPending" :rows="5" animated />
          <div v-else-if="isGapKeywordsError" class="keywords-state-card keywords-state-card--error">
            <h3>真空词队列加载失败</h3>
            <p>{{ gapKeywordsErrorMessage }}</p>
          </div>
          <div v-else-if="!gapKeywords.length" class="keywords-state-card">
            <h3>当前没有待消费关键词</h3>
            <p>关键词池没有积压项，等待下一轮注入或回收。</p>
          </div>
          <div v-else class="gap-keyword-feed">
            <div
              v-for="item in gapKeywords"
              :key="item.id"
              class="gap-keyword-feed__item"
            >
              <div class="gap-keyword-feed__header">
                <span class="gap-keyword-feed__keyword">{{ item.keyword }}</span>
                <StatusLabel
                  :status="difficultyMeta(item.difficulty).status"
                  :text="difficultyMeta(item.difficulty).label"
                />
              </div>
              <div class="gap-keyword-feed__meta">
                <span>搜索量 {{ formatNumber(item.search_volume) }}</span>
                <span>{{ formatDateTime(item.created_at) }}</span>
              </div>
            </div>
          </div>
        </article>

        <article class="keywords-panel">
          <div class="keywords-panel__header">
            <div>
              <span class="keywords-panel__eyebrow">Cluster Distribution</span>
              <h2 class="keywords-panel__title">技术集群分布</h2>
            </div>
            <StatusLabel status="primary" :text="`${clusterCount} 类`" />
          </div>

          <el-skeleton v-if="isClustersPending" :rows="5" animated />
          <div v-else-if="isClustersError" class="keywords-state-card keywords-state-card--error">
            <h3>集群分布加载失败</h3>
            <p>{{ clustersErrorMessage }}</p>
          </div>
          <div v-else-if="!clusters.length" class="keywords-state-card">
            <h3>暂无集群数据</h3>
            <p>还没有可用于聚类的关键词分布信息。</p>
          </div>
          <div v-else class="cluster-list">
            <div
              v-for="cluster in clusters"
              :key="cluster.cluster_name"
              class="cluster-list__item"
            >
              <div class="cluster-list__header">
                <span class="cluster-list__name">{{ cluster.cluster_name }}</span>
                <span class="cluster-list__count">{{ formatNumber(cluster.keywords_total) }}</span>
              </div>
              <div class="cluster-list__bar">
                <span
                  class="cluster-list__fill"
                  :style="{ width: `${clusterBarWidth(cluster.keywords_total)}%` }"
                ></span>
              </div>
              <div class="cluster-list__meta">
                <span>待消费 {{ cluster.pending_keywords }}</span>
                <span>已消费 {{ cluster.consumed_keywords }}</span>
                <span>平均难度 {{ formatScore(cluster.average_difficulty) }}</span>
              </div>
            </div>
          </div>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Link2, Network, Orbit, RefreshCcw, Search } from 'lucide-vue-next'

import IndustrialTable from '../../components/IndustrialTable.vue'
import StatCard from '../../components/StatCard.vue'
import StatusLabel from '../../components/StatusLabel.vue'
import {
  useGapKeywordsQuery,
  useKeywordClustersQuery,
  useKeywordsQuery,
} from '../../composables/useKeywords'

const pageSize = 20

const route = useRoute()
const router = useRouter()

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '待消费', value: 'pending' },
  { label: '已消费', value: 'consumed' },
]

const initialQuery = typeof route.query.query === 'string' ? route.query.query : ''

const draftFilters = reactive({
  status: '',
  query: initialQuery,
})

const appliedFilters = ref({
  status: '',
  query: initialQuery,
})

const currentPage = ref(1)

const listFilters = computed(() => ({
  ...(appliedFilters.value.status ? { status: appliedFilters.value.status } : {}),
  ...(appliedFilters.value.query ? { query: appliedFilters.value.query.trim() } : {}),
  limit: pageSize,
  offset: (currentPage.value - 1) * pageSize,
}))

const summaryFilters = computed(() => ({
  limit: 1,
  offset: 0,
}))

const gapSideFilters = computed(() => ({
  limit: 8,
  offset: 0,
  ...(appliedFilters.value.query ? { query: appliedFilters.value.query.trim() } : {}),
}))

const keywordsQuery = useKeywordsQuery(listFilters)
const keywordsSummaryQuery = useKeywordsQuery(summaryFilters)
const gapKeywordsQuery = useGapKeywordsQuery(gapSideFilters)
const gapKeywordsSummaryQuery = useGapKeywordsQuery(summaryFilters)
const keywordClustersQuery = useKeywordClustersQuery(10)

const keywords = computed(() => keywordsQuery.data.value?.items ?? [])
const filteredKeywordsTotal = computed(() => keywordsQuery.data.value?.total ?? 0)
const totalKeywords = computed(() => keywordsSummaryQuery.data.value?.total ?? 0)
const gapKeywords = computed(() => gapKeywordsQuery.data.value?.items ?? [])
const gapKeywordsTotal = computed(() => gapKeywordsSummaryQuery.data.value?.total ?? 0)
const clusters = computed(() => keywordClustersQuery.data.value?.items ?? [])
const clusterCount = computed(() => clusters.value.length)
const consumedKeywordsTotal = computed(() =>
  Math.max(0, totalKeywords.value - gapKeywordsTotal.value),
)

const maxClusterTotal = computed(() =>
  clusters.value.reduce((max, item) => Math.max(max, item.keywords_total), 0),
)

const isKeywordsPending = computed(() => keywordsQuery.isPending.value)
const isKeywordsError = computed(() => keywordsQuery.isError.value)
const isGapKeywordsPending = computed(() => gapKeywordsQuery.isPending.value)
const isGapKeywordsError = computed(() => gapKeywordsQuery.isError.value)
const isClustersPending = computed(() => keywordClustersQuery.isPending.value)
const isClustersError = computed(() => keywordClustersQuery.isError.value)
const isSummaryPending = computed(() =>
  keywordsSummaryQuery.isPending.value || gapKeywordsSummaryQuery.isPending.value,
)
const isSummaryError = computed(() =>
  keywordsSummaryQuery.isError.value || gapKeywordsSummaryQuery.isError.value,
)

const warningMessages = computed(() =>
  [
    keywordsQuery.data.value?.warning,
    keywordsSummaryQuery.data.value?.warning,
    gapKeywordsQuery.data.value?.warning,
    gapKeywordsSummaryQuery.data.value?.warning,
    keywordClustersQuery.data.value?.warning,
  ].filter((item): item is string => Boolean(item)),
)

const hasWarnings = computed(() => warningMessages.value.length > 0)

const keywordsErrorMessage = computed(() => getErrorMessage(keywordsQuery.error.value))
const gapKeywordsErrorMessage = computed(() => getErrorMessage(gapKeywordsQuery.error.value))
const clustersErrorMessage = computed(() => getErrorMessage(keywordClustersQuery.error.value))
const summaryErrorMessage = computed(() =>
  getErrorMessage(keywordsSummaryQuery.error.value || gapKeywordsSummaryQuery.error.value),
)

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

function applyFilters() {
  currentPage.value = 1
  appliedFilters.value = {
    status: draftFilters.status,
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
  draftFilters.status = ''
  draftFilters.query = ''
  currentPage.value = 1
  appliedFilters.value = {
    status: '',
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
  keywordsQuery.refetch()
  keywordsSummaryQuery.refetch()
  gapKeywordsQuery.refetch()
  gapKeywordsSummaryQuery.refetch()
  keywordClustersQuery.refetch()
}

function difficultyMeta(difficulty: number | null | undefined) {
  const value = difficulty ?? 0

  if (value >= 70) {
    return { status: 'danger' as const, label: `高 ${value}` }
  }

  if (value >= 40) {
    return { status: 'warning' as const, label: `中 ${value}` }
  }

  return { status: 'success' as const, label: `低 ${value}` }
}

function clusterBarWidth(total: number) {
  if (!maxClusterTotal.value) {
    return 0
  }

  return Math.max(10, Math.round((total / maxClusterTotal.value) * 100))
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '--'
  }

  return new Intl.NumberFormat('zh-CN').format(value)
}

function formatScore(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '--'
  }

  return Number(value).toFixed(1)
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

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }

  return '请求失败，请稍后重试。'
}
</script>

<style scoped>
.keywords-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%;
}

.keywords-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 24px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.12), transparent 22%),
    var(--bg-panel);
}

.keywords-hero__main {
  max-width: 720px;
}

.keywords-hero__eyebrow,
.keywords-panel__eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.keywords-hero__title {
  margin: 8px 0 10px;
  font-size: 32px;
  line-height: 1.08;
  font-weight: 700;
  color: var(--text-main);
}

.keywords-hero__description {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: rgba(241, 243, 249, 0.78);
}

.keywords-hero__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  min-width: min(360px, 100%);
}

.keywords-pill {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-height: 88px;
  padding: 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: rgba(7, 10, 19, 0.56);
}

.keywords-pill--warning {
  border-color: rgba(245, 158, 11, 0.18);
}

.keywords-pill--healthy {
  border-color: rgba(34, 197, 94, 0.18);
}

.keywords-pill__label {
  font-size: 12px;
  color: var(--text-muted);
}

.keywords-pill__value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
}

.keywords-alerts {
  display: grid;
  gap: 12px;
}

.keywords-alerts :deep(.el-alert) {
  --el-alert-bg-color: rgba(245, 158, 11, 0.12);
  --el-alert-border-color: rgba(245, 158, 11, 0.18);
  --el-alert-text-color: #f7d089;
}

.keywords-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.keywords-summary__skeleton {
  grid-column: 1 / -1;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
}

.keywords-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.85fr);
  gap: 20px;
}

.keywords-side-stack {
  display: grid;
  gap: 20px;
  align-content: start;
}

.keywords-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
}

.keywords-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.keywords-panel__title {
  margin: 8px 0 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-main);
}

.keywords-refresh-button,
.keywords-action-button {
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

.keywords-action-button--primary {
  background: rgba(37, 99, 235, 0.18);
  border-color: rgba(37, 99, 235, 0.28);
  color: #c9d9ff;
}

.keywords-refresh-button:hover,
.keywords-action-button:hover {
  border-color: var(--border-focus);
  transform: translateY(-1px);
}

.keywords-filters {
  display: grid;
  grid-template-columns: 180px minmax(220px, 1fr) auto;
  gap: 12px;
  align-items: end;
}

.keywords-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.keywords-field__label {
  font-size: 12px;
  color: var(--text-muted);
}

.keywords-field__control {
  width: 100%;
}

.keywords-filters :deep(.el-input__wrapper),
.keywords-filters :deep(.el-select__wrapper) {
  background: rgba(7, 10, 19, 0.72);
  box-shadow: inset 0 0 0 1px var(--border-subtle);
}

.keywords-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.keywords-list-state {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.keywords-pagination {
  display: flex;
  justify-content: flex-end;
}

.keywords-pagination :deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background-color: var(--color-primary);
}

.keywords-pagination :deep(.el-pagination.is-background .btn-next),
.keywords-pagination :deep(.el-pagination.is-background .btn-prev),
.keywords-pagination :deep(.el-pagination.is-background .el-pager li) {
  background-color: var(--bg-panel);
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
}

.keyword-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.keyword-cell__keyword {
  color: var(--text-main);
}

.keyword-cell__meta,
.keyword-article-placeholder {
  color: var(--text-muted);
  font-size: 12px;
}

.keyword-article-link {
  color: #9fc0ff;
  text-decoration: none;
}

.keyword-article-link:hover {
  color: #d6e3ff;
}

.keywords-state-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  min-height: 160px;
  padding: 18px;
  border: 1px dashed rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(7, 10, 19, 0.44);
}

.keywords-state-card--error {
  border-color: rgba(239, 68, 68, 0.22);
  background: rgba(239, 68, 68, 0.06);
}

.keywords-state-card h2,
.keywords-state-card h3 {
  margin: 0;
  color: var(--text-main);
}

.keywords-state-card p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.gap-keyword-feed,
.cluster-list {
  display: grid;
  gap: 12px;
}

.gap-keyword-feed__item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(245, 158, 11, 0.15);
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.04);
}

.gap-keyword-feed__header,
.gap-keyword-feed__meta,
.cluster-list__header,
.cluster-list__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.gap-keyword-feed__keyword,
.cluster-list__name {
  color: var(--text-main);
  font-weight: 600;
}

.gap-keyword-feed__meta,
.cluster-list__count,
.cluster-list__meta {
  color: var(--text-muted);
  font-size: 12px;
}

.cluster-list__item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(37, 99, 235, 0.12);
  border-radius: 8px;
  background: rgba(37, 99, 235, 0.04);
}

.cluster-list__bar {
  width: 100%;
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
}

.cluster-list__fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.45), rgba(37, 99, 235, 0.95));
}

@media (max-width: 1280px) {
  .keywords-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .keywords-layout {
    grid-template-columns: 1fr;
  }

  .keywords-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .keywords-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

@media (max-width: 920px) {
  .keywords-hero {
    flex-direction: column;
  }

  .keywords-hero__meta {
    grid-template-columns: 1fr;
    min-width: 0;
  }
}

@media (max-width: 640px) {
  .keywords-page {
    gap: 18px;
  }

  .keywords-hero,
  .keywords-panel {
    padding: 16px;
  }

  .keywords-summary,
  .keywords-filters {
    grid-template-columns: 1fr;
  }

  .keywords-panel__header,
  .gap-keyword-feed__header,
  .gap-keyword-feed__meta,
  .cluster-list__header,
  .cluster-list__meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
