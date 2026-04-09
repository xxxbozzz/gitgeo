<template>
  <div class="dashboard-page">
    <header class="dashboard-hero">
      <div class="dashboard-hero__main">
        <span class="dashboard-hero__eyebrow">GEO System Overview</span>
        <h1 class="dashboard-hero__title">总览</h1>
        <p class="dashboard-hero__description">
          聚合查看近 7 日产出、待处理关键词和内容推进状态，快速判断今天系统是否正常产出。
        </p>
      </div>

      <div class="dashboard-hero__aside">
        <div class="dashboard-pill">
          <span class="dashboard-pill__label">最近产出</span>
          <span class="dashboard-pill__value">{{ latestArticleAtLabel }}</span>
        </div>
        <div class="dashboard-pill" :class="hasWarning ? 'dashboard-pill--warning' : 'dashboard-pill--healthy'">
          <span class="dashboard-pill__label">数据状态</span>
          <span class="dashboard-pill__value">{{ hasWarning ? '部分降级' : '正常' }}</span>
        </div>
      </div>
    </header>

    <section v-if="hasWarning" class="dashboard-alerts">
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

    <section class="dashboard-kpis">
      <el-skeleton
        v-if="isKpisPending"
        :rows="3"
        animated
        class="dashboard-kpis__skeleton"
      />

      <template v-else-if="isKpisError">
        <div class="dashboard-state-card dashboard-state-card--error">
          <h2>KPI 数据加载失败</h2>
          <p>{{ kpisErrorMessage }}</p>
        </div>
      </template>

      <template v-else>
        <StatCard title="文章总量" :value="formatNumber(kpis.articles_total)">
          <template #icon>
            <FileText class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="已通过文章" :value="formatNumber(kpis.passed_articles)">
          <template #icon>
            <BadgeCheck class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="待处理关键词" :value="formatNumber(kpis.pending_keywords)">
          <template #icon>
            <Search class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="平均质量分" :value="formatScore(kpis.average_quality_score)">
          <template #icon>
            <BarChart3 class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="内链总量" :value="formatNumber(kpis.internal_links)">
          <template #icon>
            <Network class="h-5 w-5" />
          </template>
        </StatCard>
      </template>
    </section>

    <section class="dashboard-main-grid">
      <article class="dashboard-panel dashboard-panel--trend">
        <div class="dashboard-panel__header">
          <div>
            <span class="dashboard-panel__eyebrow">近 7 日产出</span>
            <h2 class="dashboard-panel__title">产出趋势</h2>
          </div>
          <StatusLabel
            :status="trendDelta >= 0 ? 'success' : 'warning'"
            :text="trendDeltaLabel"
          />
        </div>

        <el-skeleton v-if="isTrendPending" :rows="6" animated />
        <div v-else-if="isTrendError" class="dashboard-state-card dashboard-state-card--error">
          <h3>趋势数据加载失败</h3>
          <p>{{ trendErrorMessage }}</p>
        </div>
        <div v-else-if="!trendItems.length" class="dashboard-state-card">
          <h3>暂无趋势数据</h3>
          <p>后端还没有返回近 7 日产出记录。</p>
        </div>
        <OverviewTrendChart v-else :points="trendItems" />
      </article>

      <article class="dashboard-panel dashboard-panel--keywords">
        <div class="dashboard-panel__header">
          <div>
            <span class="dashboard-panel__eyebrow">待消费队列</span>
            <h2 class="dashboard-panel__title">待处理关键词</h2>
          </div>
          <RouterLink class="dashboard-panel__link" to="/keywords">
            查看预留模块
          </RouterLink>
        </div>

        <el-skeleton v-if="isBoardPending" :rows="5" animated />
        <div v-else-if="isBoardError" class="dashboard-state-card dashboard-state-card--error">
          <h3>关键词队列加载失败</h3>
          <p>{{ boardErrorMessage }}</p>
        </div>
        <ul v-else-if="pendingKeywords.length" class="keyword-list">
          <li v-for="item in pendingKeywords" :key="item.id" class="keyword-list__item">
            <div class="keyword-list__main">
              <span class="keyword-list__keyword">{{ item.keyword }}</span>
              <span class="keyword-list__meta">
                搜索量 {{ formatNumber(item.search_volume) }}
              </span>
            </div>
            <StatusLabel
              :status="item.difficulty >= 70 ? 'danger' : item.difficulty >= 40 ? 'warning' : 'success'"
              :text="`难度 ${item.difficulty}`"
            />
          </li>
        </ul>
        <div v-else class="dashboard-state-card">
          <h3>暂无待处理关键词</h3>
          <p>关键词池当前没有积压，后续中心页可继续扩展批量操作。</p>
        </div>
      </article>
    </section>

    <section class="dashboard-bottom-grid">
      <article class="dashboard-panel dashboard-panel--latest">
        <div class="dashboard-panel__header">
          <div>
            <span class="dashboard-panel__eyebrow">内容总览</span>
            <h2 class="dashboard-panel__title">最新文章</h2>
          </div>
          <RouterLink class="dashboard-panel__link" to="/articles">
            进入内容中心
          </RouterLink>
        </div>

        <el-skeleton v-if="isLatestArticlesPending" :rows="6" animated />
        <div v-else-if="isLatestArticlesError" class="dashboard-state-card dashboard-state-card--error">
          <h3>最新文章加载失败</h3>
          <p>{{ latestArticlesErrorMessage }}</p>
        </div>
        <IndustrialTable v-else :data="latestArticles" class="dashboard-latest-table">
          <el-table-column min-width="280" label="标题">
            <template #default="{ row }">
              <div class="article-title-cell">
                <RouterLink
                  class="article-title-cell__link"
                  :to="{ path: '/articles', query: { query: row.slug || row.title } }"
                >
                  {{ row.title }}
                </RouterLink>
                <span class="article-title-cell__slug">{{ row.slug }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column width="110" align="center" label="质量分">
            <template #default="{ row }">
              {{ formatScore(row.quality_score) }}
            </template>
          </el-table-column>

          <el-table-column width="120" align="center" label="状态">
            <template #default="{ row }">
              <StatusLabel
                :status="articleStatus(row).status"
                :text="articleStatus(row).label"
              />
            </template>
          </el-table-column>

          <el-table-column min-width="180" label="主题">
            <template #default="{ row }">
              <span class="article-topic">
                {{ articleTopic(row) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column width="160" label="更新时间">
            <template #default="{ row }">
              {{ formatDateTime(row.updated_at || row.created_at) }}
            </template>
          </el-table-column>
        </IndustrialTable>
      </article>

      <div class="dashboard-board-stack">
        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <span class="dashboard-panel__eyebrow">内容推进</span>
              <h2 class="dashboard-panel__title">草稿看板</h2>
            </div>
            <StatusLabel status="warning" :text="`${draftArticles.length} 篇`" />
          </div>

          <el-skeleton v-if="isBoardPending" :rows="4" animated />
          <div v-else-if="draftArticles.length" class="article-board">
            <RouterLink
              v-for="item in draftArticles"
              :key="item.id"
              class="article-board__item"
              :to="{ path: '/articles', query: { query: item.slug || item.title } }"
            >
              <div class="article-board__header">
                <span class="article-board__title">{{ item.title }}</span>
                <StatusLabel status="warning" text="草稿" />
              </div>
              <div class="article-board__footer">
                <span>{{ articleTopic(item) }}</span>
                <span>分数 {{ formatScore(item.quality_score) }}</span>
              </div>
            </RouterLink>
          </div>
          <div v-else class="dashboard-state-card">
            <h3>没有草稿积压</h3>
            <p>草稿队列为空，当前流程没有滞留在初稿阶段的文章。</p>
          </div>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <span class="dashboard-panel__eyebrow">待动作内容</span>
              <h2 class="dashboard-panel__title">待发布看板</h2>
            </div>
            <StatusLabel status="primary" :text="`${readyArticles.length} 篇`" />
          </div>

          <el-skeleton v-if="isBoardPending" :rows="4" animated />
          <div v-else-if="readyArticles.length" class="article-board">
            <RouterLink
              v-for="item in readyArticles"
              :key="item.id"
              class="article-board__item"
              :to="{ path: '/publications', query: { query: item.title } }"
            >
              <div class="article-board__header">
                <span class="article-board__title">{{ item.title }}</span>
                <StatusLabel status="primary" text="待发布" />
              </div>
              <div class="article-board__footer">
                <span>{{ articleTopic(item) }}</span>
                <span>分数 {{ formatScore(item.quality_score) }}</span>
              </div>
            </RouterLink>
          </div>
          <div v-else class="dashboard-state-card">
            <h3>没有待发布文章</h3>
            <p>已通过文章队列为空，说明当前没有排队待发内容。</p>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { BadgeCheck, BarChart3, FileText, Network, Search } from 'lucide-vue-next'

import IndustrialTable from '../../components/IndustrialTable.vue'
import OverviewTrendChart from '../../components/OverviewTrendChart.vue'
import StatCard from '../../components/StatCard.vue'
import StatusLabel from '../../components/StatusLabel.vue'
import { useLatestArticlesQuery, useOverviewBoardQuery, useOverviewKpisQuery, useOverviewTrendQuery } from '../../composables/useOverview'
import type { ArticleSummaryItem } from '../../types/articles'

const kpisQuery = useOverviewKpisQuery()
const trendQuery = useOverviewTrendQuery(7)
const boardQuery = useOverviewBoardQuery(5, 5)
const latestArticlesQuery = useLatestArticlesQuery(8)

const kpis = computed(() => kpisQuery.data.value ?? {
  articles_total: 0,
  passed_articles: 0,
  pending_keywords: 0,
  average_quality_score: null,
  internal_links: 0,
  latest_article_at: null,
  warning: null,
})

const trendItems = computed(() => trendQuery.data.value?.items ?? [])
const pendingKeywords = computed(() => boardQuery.data.value?.pending_keywords ?? [])
const draftArticles = computed(() => boardQuery.data.value?.draft_articles ?? [])
const readyArticles = computed(() => boardQuery.data.value?.ready_articles ?? [])
const latestArticles = computed(() => latestArticlesQuery.data.value?.items ?? [])

const warningMessages = computed(() =>
  [
    kpisQuery.data.value?.warning,
    trendQuery.data.value?.warning,
    boardQuery.data.value?.warning,
    latestArticlesQuery.data.value?.warning,
  ].filter((item): item is string => Boolean(item)),
)

const hasWarning = computed(() => warningMessages.value.length > 0)

const latestArticleAtLabel = computed(() => formatDateTime(kpis.value.latest_article_at))
const isKpisPending = computed(() => kpisQuery.isPending.value)
const isKpisError = computed(() => kpisQuery.isError.value)
const isTrendPending = computed(() => trendQuery.isPending.value)
const isTrendError = computed(() => trendQuery.isError.value)
const isBoardPending = computed(() => boardQuery.isPending.value)
const isBoardError = computed(() => boardQuery.isError.value)
const isLatestArticlesPending = computed(() => latestArticlesQuery.isPending.value)
const isLatestArticlesError = computed(() => latestArticlesQuery.isError.value)

const trendDelta = computed(() => {
  const points = trendItems.value

  if (points.length < 2) {
    return 0
  }

  const firstPoint = points[0]
  const lastPoint = points[points.length - 1]

  if (!firstPoint || !lastPoint) {
    return 0
  }

  return lastPoint.count - firstPoint.count
})

const trendDeltaLabel = computed(() => {
  if (!trendItems.value.length) {
    return '暂无变化'
  }

  const diff = trendDelta.value
  return diff === 0 ? '较首日持平' : `${diff > 0 ? '+' : ''}${diff} 篇`
})

const kpisErrorMessage = computed(() => getErrorMessage(kpisQuery.error.value))
const trendErrorMessage = computed(() => getErrorMessage(trendQuery.error.value))
const boardErrorMessage = computed(() => getErrorMessage(boardQuery.error.value))
const latestArticlesErrorMessage = computed(() => getErrorMessage(latestArticlesQuery.error.value))

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

function articleTopic(article: ArticleSummaryItem) {
  return [article.dim_subject, article.dim_action, article.dim_attribute]
    .filter(Boolean)
    .join(' / ') || '未补充主题维度'
}

function articleStatus(article: ArticleSummaryItem) {
  if (article.publish_status === 2) {
    return {
      status: 'success' as const,
      label: '已发布',
    }
  }

  if ((article.quality_score ?? 0) >= 80) {
    return {
      status: 'primary' as const,
      label: '待发布',
    }
  }

  return {
    status: 'warning' as const,
    label: '草稿',
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
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100%;
}

.dashboard-hero {
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

.dashboard-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background-color: var(--color-primary);
}

.dashboard-hero__main {
  min-width: 0;
  max-width: 720px;
  position: relative;
  z-index: 1;
}

.dashboard-hero__eyebrow,
.dashboard-panel__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

.dashboard-hero__title {
  margin: 10px 0 12px;
  font-size: 30px;
  line-height: 1.1;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.dashboard-hero__description {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(241, 243, 249, 0.7);
}

.dashboard-hero__aside {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  min-width: 0;
  width: 100%;
  max-width: 360px;
  align-self: start;
  position: relative;
  z-index: 1;
}

.dashboard-pill {
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

.dashboard-pill--warning {
  border-color: rgba(245, 158, 11, 0.15);
  box-shadow: inset 0 0 12px rgba(245, 158, 11, 0.05);
}

.dashboard-pill--healthy {
  border-color: rgba(34, 197, 94, 0.15);
  box-shadow: inset 0 0 12px rgba(34, 197, 94, 0.05);
}

.dashboard-pill__label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.dashboard-pill__value {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-main);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.dashboard-alerts {
  display: grid;
  gap: 12px;
}

.dashboard-alerts :deep(.el-alert) {
  --el-alert-bg-color: rgba(245, 158, 11, 0.1);
  --el-alert-border-color: rgba(245, 158, 11, 0.2);
  --el-alert-text-color: #f7d089;
  border: 1px solid var(--el-alert-border-color);
  border-radius: 8px;
}

.dashboard-kpis {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}

.dashboard-kpis__skeleton {
  grid-column: 1 / -1;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
}

.dashboard-main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 1fr);
  gap: 16px;
}

.dashboard-bottom-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 1fr);
  gap: 16px;
}

.dashboard-board-stack {
  display: grid;
  grid-template-rows: 1fr 1fr;
  gap: 16px;
}

.dashboard-panel {
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

.dashboard-panel--trend {
  min-height: 380px;
}

.dashboard-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.dashboard-panel__title {
  margin: 6px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.dashboard-panel__link {
  font-size: 13px;
  color: var(--color-primary);
  text-decoration: none;
  white-space: nowrap;
  font-weight: 500;
}

.dashboard-panel__link:hover {
  text-decoration: underline;
}

.dashboard-state-card {
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

.dashboard-state-card--error {
  border-color: rgba(239, 68, 68, 0.22);
  background: rgba(239, 68, 68, 0.06);
}

.dashboard-state-card h2,
.dashboard-state-card h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
}

.dashboard-state-card p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  opacity: 0.8;
  line-height: 1.5;
}

.keyword-list,
.article-board {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.keyword-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.keyword-list__item,
.article-board__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: var(--bg-dark);
  text-decoration: none;
  transition: all 0.2s ease;
}

.keyword-list__item:hover,
.article-board__item:hover {
  border-color: var(--border-focus);
  background: var(--bg-panel-hover);
  transform: translateX(2px);
}

.article-board__item {
  flex-direction: column;
  align-items: stretch;
}

.keyword-list__main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.keyword-list__keyword,
.article-board__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
  word-break: break-word;
  line-height: 1.4;
}

.keyword-list__meta,
.article-board__footer {
  font-size: 12px;
  color: var(--text-muted);
}

.article-board__header,
.article-board__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-latest-table {
  min-height: 0;
}

.dashboard-latest-table :deep(.el-table__body-wrapper) {
  min-height: 240px;
}

.article-title-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.article-title-cell__link {
  color: var(--text-main);
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
}

.article-title-cell__link:hover {
  text-decoration: underline;
}

.article-title-cell__slug,
.article-topic {
  font-size: 12px;
  color: var(--text-muted);
  word-break: break-word;
}

@media (max-width: 1280px) {
  .dashboard-kpis {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-main-grid,
  .dashboard-bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .dashboard-hero {
    grid-template-columns: 1fr;
    padding: 24px;
  }

  .dashboard-hero__aside {
    grid-template-columns: 1fr;
    min-width: 0;
  }

  .dashboard-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .dashboard-page {
    gap: 16px;
  }

  .dashboard-hero,
  .dashboard-panel {
    padding: 16px;
  }

  .dashboard-hero__title {
    font-size: 24px;
  }

  .dashboard-kpis {
    grid-template-columns: 1fr;
  }

  .keyword-list__item,
  .article-board__header,
  .article-board__footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
