<template>
  <div class="articles-page">
    <header class="articles-hero">
      <div class="articles-hero__main">
        <span class="articles-hero__eyebrow">Content Asset Center</span>
        <h1 class="articles-hero__title">内容中心</h1>
        <p class="articles-hero__description">
          集中管理文章资产，统一查看正文、关键词、关联运行和返修/回收/手动发布动作。
        </p>
      </div>

      <div class="articles-hero__meta">
        <div class="articles-pill">
          <span class="articles-pill__label">当前结果集</span>
          <span class="articles-pill__value">{{ formatNumber(totalArticles) }}</span>
        </div>
        <div class="articles-pill" :class="hasWarnings ? 'articles-pill--warning' : 'articles-pill--healthy'">
          <span class="articles-pill__label">页面状态</span>
          <span class="articles-pill__value">{{ hasWarnings ? '部分降级' : '正常轮询' }}</span>
        </div>
      </div>
    </header>

    <section v-if="hasWarnings" class="articles-alerts">
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

    <section class="articles-summary">
      <el-skeleton
        v-if="isSummaryPending"
        :rows="3"
        animated
        class="articles-summary__skeleton"
      />
      <template v-else-if="isSummaryError">
        <div class="articles-state-card articles-state-card--error">
          <h2>内容概览加载失败</h2>
          <p>{{ summaryErrorMessage }}</p>
        </div>
      </template>
      <template v-else>
        <StatCard title="文章总量" :value="formatNumber(summary.total_articles)">
          <template #icon>
            <FileText class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="草稿" :value="formatNumber(summary.draft_articles)">
          <template #icon>
            <FilePenLine class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="已通过" :value="formatNumber(summary.approved_articles)">
          <template #icon>
            <BadgeCheck class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="已发布" :value="formatNumber(summary.published_articles)">
          <template #icon>
            <Send class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="平均质量分" :value="formatScore(summary.average_quality_score)">
          <template #icon>
            <BarChart3 class="h-5 w-5" />
          </template>
        </StatCard>
      </template>
    </section>

    <section class="articles-panel">
      <div class="articles-panel__header">
        <div>
          <span class="articles-panel__eyebrow">检索与筛选</span>
          <h2 class="articles-panel__title">文章列表</h2>
        </div>
        <button class="articles-refresh-button" type="button" @click="handleRefresh">
          <RefreshCcw class="h-4 w-4" />
          刷新
        </button>
      </div>

      <div class="articles-filters">
        <label class="articles-field">
          <span class="articles-field__label">状态</span>
          <el-select
            v-model="draftFilters.status"
            placeholder="全部状态"
            clearable
            class="articles-field__control"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value || 'all-status'"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </label>

        <label class="articles-field">
          <span class="articles-field__label">最低分</span>
          <el-input-number
            v-model="draftFilters.min_score"
            class="articles-field__control"
            :min="0"
            :max="100"
            :step="5"
            controls-position="right"
          />
        </label>

        <label class="articles-field articles-field--query">
          <span class="articles-field__label">搜索</span>
          <el-input
            v-model="draftFilters.query"
            class="articles-field__control"
            placeholder="标题 / slug"
            clearable
            @keyup.enter="applyFilters"
          />
        </label>

        <div class="articles-actions">
          <button class="articles-action-button articles-action-button--primary" type="button" @click="applyFilters">
            应用筛选
          </button>
          <button class="articles-action-button" type="button" @click="resetFilters">
            重置
          </button>
        </div>
      </div>

      <div class="articles-list-state">
        <el-skeleton v-if="isListPending" :rows="8" animated />
        <div v-else-if="isListError" class="articles-state-card articles-state-card--error">
          <h3>文章列表加载失败</h3>
          <p>{{ listErrorMessage }}</p>
        </div>
        <div v-else-if="!articles.length" class="articles-state-card">
          <h3>没有匹配的文章</h3>
          <p>当前筛选条件下没有命中结果，可以调整状态、分数或搜索词后重试。</p>
        </div>
        <template v-else>
          <IndustrialTable :data="articles">
            <el-table-column min-width="240" label="标题">
              <template #default="{ row }">
                <div class="article-title-cell">
                  <button
                    class="article-link-button"
                    type="button"
                    @click="openArticleDetail(row.id)"
                  >
                    {{ row.title }}
                  </button>
                  <span class="article-title-cell__slug">{{ row.slug }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column width="100" align="center" label="质量分">
              <template #default="{ row }">
                {{ formatScore(row.quality_score) }}
              </template>
            </el-table-column>

            <el-table-column width="120" align="center" label="状态">
              <template #default="{ row }">
                <StatusLabel
                  :status="articleStatusMeta(row.publish_status).status"
                  :text="articleStatusMeta(row.publish_status).label"
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

            <el-table-column width="120" align="center" label="关联运行">
              <template #default="{ row }">
                <span class="article-run-placeholder">
                  {{ row.publish_status >= 2 ? '已发布链路' : '详情查看' }}
                </span>
              </template>
            </el-table-column>

            <el-table-column width="156" label="更新时间">
              <template #default="{ row }">
                {{ formatDateTime(row.updated_at || row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column width="160" fixed="right" label="操作">
              <template #default="{ row }">
                <div class="article-actions-cell">
                  <button
                    class="articles-table-action"
                    type="button"
                    @click="openArticleDetail(row.id)"
                  >
                    详情
                  </button>
                  <button
                    v-if="row.publish_status < 2"
                    class="articles-table-action articles-table-action--primary"
                    type="button"
                    :disabled="isAnyActionPending"
                    @click="openPublishDialog(row.id, row.title)"
                  >
                    发布
                  </button>
                </div>
              </template>
            </el-table-column>
          </IndustrialTable>

          <div class="articles-pagination">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="totalArticles"
              layout="total, prev, pager, next"
              background
            />
          </div>
        </template>
      </div>
    </section>

    <DetailPanel
      v-model="detailPanelOpen"
      title="文章详情"
      size="920px"
    >
      <div class="article-detail">
        <div v-if="isDetailPending" class="article-detail__loading">
          <el-skeleton :rows="10" animated />
        </div>

        <div v-else-if="isDetailError" class="articles-state-card articles-state-card--error">
          <h3>文章详情加载失败</h3>
          <p>{{ detailErrorMessage }}</p>
        </div>

        <div v-else-if="!selectedArticle" class="articles-state-card">
          <h3>未找到文章</h3>
          <p>该文章可能已不存在，或当前接口没有返回详情。</p>
        </div>

        <template v-else>
          <section class="article-detail__summary">
            <div class="article-detail__summary-header">
              <div>
                <span class="article-detail__eyebrow">Article Overview</span>
                <h3 class="article-detail__title">{{ selectedArticle.title }}</h3>
                <p class="article-detail__slug">{{ selectedArticle.slug }}</p>
              </div>

              <StatusLabel
                :status="articleStatusMeta(selectedArticle.publish_status).status"
                :text="articleStatusMeta(selectedArticle.publish_status).label"
              />
            </div>

            <el-descriptions :column="2" border class="article-detail__descriptions">
              <el-descriptions-item label="文章 ID">
                {{ selectedArticle.id }}
              </el-descriptions-item>
              <el-descriptions-item label="质量分">
                {{ formatScore(selectedArticle.quality_score) }}
              </el-descriptions-item>
              <el-descriptions-item label="主题维度">
                {{ articleTopic(selectedArticle) }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDateTime(selectedArticle.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="内链输出">
                {{ selectedArticle.outgoing_links_count }}
              </el-descriptions-item>
              <el-descriptions-item label="内链输入">
                {{ selectedArticle.incoming_links_count }}
              </el-descriptions-item>
              <el-descriptions-item label="关联运行">
                {{ selectedArticle.related_run_id ? `#${selectedArticle.related_run_id}` : '无' }}
              </el-descriptions-item>
              <el-descriptions-item label="运行状态">
                <StatusLabel
                  :status="runStatusMeta(selectedArticle.related_run_status).status"
                  :text="runStatusMeta(selectedArticle.related_run_status).label"
                />
              </el-descriptions-item>
            </el-descriptions>

            <div class="article-detail__keywords">
              <h4>目标关键词</h4>
              <div v-if="selectedArticle.target_keywords.length" class="article-keyword-list">
                <el-tag
                  v-for="keyword in selectedArticle.target_keywords"
                  :key="keyword"
                  effect="plain"
                  class="article-keyword-list__tag"
                >
                  {{ keyword }}
                </el-tag>
              </div>
              <p v-else class="article-detail__empty-hint">暂无关键词绑定。</p>
            </div>
          </section>

          <section v-if="selectedArticle.meta_json" class="article-detail__meta-panel">
            <div class="article-detail__section-head">
              <h4>元数据</h4>
            </div>
            <pre>{{ formatJson(selectedArticle.meta_json) }}</pre>
          </section>

          <section class="article-detail__content-panel">
            <div class="article-detail__section-head">
              <h4>正文</h4>
            </div>

            <el-tabs v-model="contentTab" class="article-content-tabs">
              <el-tab-pane label="Markdown 预览" name="preview">
                <article class="article-markdown-preview" v-html="articleMarkdownHtml"></article>
              </el-tab-pane>
              <el-tab-pane label="Markdown 源码" name="source">
                <pre class="article-markdown-source">{{ selectedArticle.content_markdown || '暂无正文。' }}</pre>
              </el-tab-pane>
            </el-tabs>
          </section>
        </template>
      </div>

      <template #footer>
        <div class="article-detail__footer">
          <button
            class="article-footer-action"
            type="button"
            :disabled="!selectedArticle || isAnyActionPending"
            @click="selectedArticle && handleRefix(selectedArticle.id)"
          >
            {{ refixMutation.isPending.value ? '返修中...' : '返修' }}
          </button>
          <button
            class="article-footer-action article-footer-action--danger"
            type="button"
            :disabled="!selectedArticle || isAnyActionPending"
            @click="selectedArticle && handleRecycle(selectedArticle.id)"
          >
            {{ recycleMutation.isPending.value ? '回收中...' : '回收' }}
          </button>
          <button
            class="article-footer-action article-footer-action--primary"
            type="button"
            :disabled="!selectedArticle || isAnyActionPending"
            @click="selectedArticle && openPublishDialog(selectedArticle.id, selectedArticle.title)"
          >
            {{ publishMutation.isPending.value ? '发布中...' : '手动发布' }}
          </button>
        </div>
      </template>
    </DetailPanel>

    <el-dialog
      v-model="publishDialogOpen"
      width="520px"
      title="手动发布文章"
      class="article-publish-dialog"
    >
      <div class="article-publish-form">
        <p class="article-publish-form__description">
          当前目标文章：<strong>{{ publishDialogArticleTitle || '未选择文章' }}</strong>
        </p>

        <label class="article-publish-form__field">
          <span class="article-publish-form__label">发布渠道</span>
          <el-checkbox-group v-model="publishForm.channels">
            <el-checkbox label="longform_channel">长文渠道 (Zhihu Adapter)</el-checkbox>
            <el-checkbox label="mobile_channel">移动渠道 (WeChat Adapter)</el-checkbox>
          </el-checkbox-group>
        </label>

        <label class="article-publish-form__field">
          <span class="article-publish-form__label">发布模式</span>
          <el-switch
            v-model="publishForm.go_live"
            active-text="正式发布"
            inactive-text="仅存草稿"
          />
        </label>
      </div>

      <template #footer>
        <div class="article-publish-form__footer">
          <button class="article-footer-action" type="button" @click="publishDialogOpen = false">
            取消
          </button>
          <button
            class="article-footer-action article-footer-action--primary"
            type="button"
            :disabled="!publishDialogArticleId || !publishForm.channels.length || publishMutation.isPending.value"
            @click="handlePublish"
          >
            {{ publishMutation.isPending.value ? '提交中...' : '确认发布' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  BadgeCheck,
  BarChart3,
  FilePenLine,
  FileText,
  RefreshCcw,
  Send,
} from 'lucide-vue-next'

import DetailPanel from '../../components/DetailPanel.vue'
import IndustrialTable from '../../components/IndustrialTable.vue'
import StatCard from '../../components/StatCard.vue'
import StatusLabel from '../../components/StatusLabel.vue'
import {
  useArticleDetailQuery,
  useArticlePublishMutation,
  useArticleRecycleMutation,
  useArticleRefixMutation,
  useArticlesQuery,
  useArticlesSummaryQuery,
} from '../../composables/useArticles'
import type { ArticlePublishRequest, ArticleSummaryItem } from '../../types/articles'
import { renderMarkdownToHtml } from '../../utils/markdown'

const pageSize = 20
const pollingIntervalMs = 20_000

const route = useRoute()
const router = useRouter()

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '草稿', value: 'draft' },
  { label: '已通过', value: 'approved' },
  { label: '已发布', value: 'published' },
]

const initialQuery = typeof route.query.query === 'string' ? route.query.query : ''

const draftFilters = reactive({
  status: '',
  min_score: 0,
  query: initialQuery,
})

const appliedFilters = ref({
  status: '',
  min_score: 0,
  query: initialQuery,
})

const currentPage = ref(1)
const selectedArticleId = ref<number | null>(null)
const detailPanelOpen = ref(false)
const contentTab = ref<'preview' | 'source'>('preview')

const publishDialogOpen = ref(false)
const publishDialogArticleId = ref<number | null>(null)
const publishDialogArticleTitle = ref('')
const publishForm = reactive<ArticlePublishRequest>({
  channels: ['longform_channel'],
  go_live: false,
})

const queryFilters = computed(() => ({
  ...(appliedFilters.value.status ? { status: appliedFilters.value.status } : {}),
  ...(appliedFilters.value.min_score > 0 ? { min_score: appliedFilters.value.min_score } : { min_score: 0 }),
  ...(appliedFilters.value.query ? { query: appliedFilters.value.query.trim() } : {}),
  limit: pageSize,
  offset: (currentPage.value - 1) * pageSize,
}))

const summaryQuery = useArticlesSummaryQuery()
const articlesQuery = useArticlesQuery(queryFilters)
const detailQuery = useArticleDetailQuery(selectedArticleId)
const refixMutation = useArticleRefixMutation()
const recycleMutation = useArticleRecycleMutation()
const publishMutation = useArticlePublishMutation()

const summary = computed(() => summaryQuery.data.value ?? {
  total_articles: 0,
  draft_articles: 0,
  approved_articles: 0,
  published_articles: 0,
  average_quality_score: null,
  warning: null,
})

const articles = computed(() => articlesQuery.data.value?.items ?? [])
const totalArticles = computed(() => articlesQuery.data.value?.total ?? 0)
const selectedArticle = computed(() => detailQuery.data.value?.article ?? null)
const articleMarkdownHtml = computed(() =>
  renderMarkdownToHtml(selectedArticle.value?.content_markdown),
)

const isSummaryPending = computed(() => summaryQuery.isPending.value)
const isSummaryError = computed(() => summaryQuery.isError.value)
const isListPending = computed(() => articlesQuery.isPending.value)
const isListError = computed(() => articlesQuery.isError.value)
const isDetailPending = computed(() => detailQuery.isPending.value)
const isDetailError = computed(() => detailQuery.isError.value)
const isAnyActionPending = computed(
  () =>
    refixMutation.isPending.value
    || recycleMutation.isPending.value
    || publishMutation.isPending.value,
)

const warningMessages = computed(() =>
  [
    summaryQuery.data.value?.warning,
    articlesQuery.data.value?.warning,
    detailQuery.data.value?.warning,
  ].filter((item): item is string => Boolean(item)),
)

const hasWarnings = computed(() => warningMessages.value.length > 0)
const summaryErrorMessage = computed(() => getErrorMessage(summaryQuery.error.value))
const listErrorMessage = computed(() => getErrorMessage(articlesQuery.error.value))
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

  contentTab.value = 'preview'
  detailQuery.refetch()
})

onMounted(() => {
  pollingTimer = window.setInterval(() => {
    summaryQuery.refetch()
    articlesQuery.refetch()

    if (detailPanelOpen.value && selectedArticleId.value) {
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
    status: draftFilters.status,
    min_score: draftFilters.min_score,
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
  draftFilters.min_score = 0
  draftFilters.query = ''
  currentPage.value = 1
  appliedFilters.value = {
    status: '',
    min_score: 0,
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
  summaryQuery.refetch()
  articlesQuery.refetch()

  if (detailPanelOpen.value && selectedArticleId.value) {
    detailQuery.refetch()
  }
}

function openArticleDetail(articleId: number) {
  selectedArticleId.value = articleId
  detailPanelOpen.value = true
}

function openPublishDialog(articleId: number, title: string) {
  publishDialogArticleId.value = articleId
  publishDialogArticleTitle.value = title
  publishForm.channels = ['longform_channel']
  publishForm.go_live = false
  publishDialogOpen.value = true
}

async function handleRefix(articleId: number) {
  try {
    await ElMessageBox.confirm(
      '将调用后端返修链路，可能更新正文，也可能在返修失败后自动回收文章。是否继续？',
      '确认返修',
      {
        confirmButtonText: '确认返修',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    const result = await refixMutation.mutateAsync(articleId)
    ElMessage.success(readMutationMessage(result, '已发起返修。'))

    if (selectedArticleId.value === articleId) {
      detailQuery.refetch()
    }
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }

    ElMessage.error(getErrorMessage(error))
  }
}

async function handleRecycle(articleId: number) {
  try {
    await ElMessageBox.confirm(
      '回收会解绑关键词、删除文章并清理关联内链。该操作不可恢复。是否继续？',
      '确认回收',
      {
        confirmButtonText: '确认回收',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    const result = await recycleMutation.mutateAsync(articleId)
    ElMessage.success(readMutationMessage(result, '已回收文章。'))

    if (selectedArticleId.value === articleId) {
      detailPanelOpen.value = false
      selectedArticleId.value = null
    }

    if (publishDialogArticleId.value === articleId) {
      publishDialogOpen.value = false
      publishDialogArticleId.value = null
      publishDialogArticleTitle.value = ''
    }
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }

    ElMessage.error(getErrorMessage(error))
  }
}

async function handlePublish() {
  if (!publishDialogArticleId.value || !publishForm.channels.length) {
    return
  }

  try {
    const result = await publishMutation.mutateAsync({
      articleId: publishDialogArticleId.value,
      payload: {
        channels: [...publishForm.channels],
        go_live: publishForm.go_live,
      },
    })

    ElMessage.success(readMutationMessage(result, '发布请求已提交。'))
    publishDialogOpen.value = false

    if (selectedArticleId.value === publishDialogArticleId.value) {
      detailQuery.refetch()
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
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

function articleStatusMeta(publishStatus: number | null | undefined) {
  if ((publishStatus ?? 0) >= 2) {
    return { status: 'success' as const, label: '已发布' }
  }

  if (publishStatus === 1) {
    return { status: 'primary' as const, label: '已通过' }
  }

  return { status: 'warning' as const, label: '草稿' }
}

function runStatusMeta(status: string | null | undefined) {
  const map: Record<string, { status: 'success' | 'warning' | 'danger' | 'info' | 'primary'; label: string }> = {
    succeeded: { status: 'success', label: '成功' },
    running: { status: 'primary', label: '进行中' },
    failed: { status: 'danger', label: '失败' },
    partial: { status: 'warning', label: '部分成功' },
  }

  return map[status || ''] || { status: 'info', label: status || '无' }
}

function articleTopic(article: Pick<ArticleSummaryItem, 'dim_subject' | 'dim_action' | 'dim_attribute'>) {
  return [article.dim_subject, article.dim_action, article.dim_attribute]
    .filter(Boolean)
    .join(' / ') || '未补充主题维度'
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

function readMutationMessage(result: Record<string, unknown>, fallback: string) {
  const message = result.message
  return typeof message === 'string' && message ? message : fallback
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }

  return '请求失败，请稍后重试。'
}
</script>

<style scoped>
.articles-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%;
}

.articles-hero {
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

.articles-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background-color: var(--color-primary);
}

.articles-hero__main {
  min-width: 0;
  max-width: 720px;
}

.articles-hero__eyebrow,
.articles-panel__eyebrow,
.article-detail__eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

.articles-hero__title {
  margin: 10px 0 12px;
  font-size: 30px;
  line-height: 1.1;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.articles-hero__description {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: rgba(241, 243, 249, 0.78);
}

.articles-hero__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  min-width: 0;
  width: 100%;
  max-width: 360px;
  align-self: start;
}

.articles-pill {
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

.articles-pill--warning {
  border-color: rgba(245, 158, 11, 0.18);
}

.articles-pill--healthy {
  border-color: rgba(34, 197, 94, 0.18);
}

.articles-pill__label {
  font-size: 12px;
  color: var(--text-muted);
}

.articles-pill__value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
}

.articles-alerts {
  display: grid;
  gap: 12px;
}

.articles-alerts :deep(.el-alert) {
  --el-alert-bg-color: rgba(245, 158, 11, 0.1);
  --el-alert-border-color: rgba(245, 158, 11, 0.2);
  --el-alert-text-color: #f7d089;
  border: 1px solid var(--el-alert-border-color);
  border-radius: 8px;
}

.articles-summary {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}

.articles-summary__skeleton {
  grid-column: 1 / -1;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
}

.articles-panel {
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

.articles-panel__header,
.article-detail__summary-header,
.article-detail__section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.articles-panel__title {
  margin: 6px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.articles-refresh-button,
.articles-action-button,
.articles-table-action,
.article-link-button,
.article-footer-action {
  border: none;
  background: transparent;
  font: inherit;
}

.articles-refresh-button,
.articles-action-button,
.articles-table-action,
.article-footer-action {
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

.articles-refresh-button,
.articles-action-button,
.article-footer-action {
  border: 1px solid var(--border-subtle);
  color: var(--text-main);
  background: rgba(7, 10, 19, 0.5);
}

.articles-action-button--primary,
.articles-table-action--primary,
.article-footer-action--primary {
  background: rgba(37, 99, 235, 0.18);
  border: 1px solid rgba(37, 99, 235, 0.28);
  color: #c9d9ff;
}

.article-footer-action--danger {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #f3bbbb;
}

.articles-refresh-button:hover,
.articles-action-button:hover,
.articles-table-action:hover,
.article-footer-action:hover {
  border-color: var(--border-focus);
  transform: translateY(-1px);
}

.article-footer-action:disabled,
.articles-table-action:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.articles-filters {
  display: grid;
  grid-template-columns: 160px 160px minmax(220px, 1fr) auto;
  gap: 12px;
  align-items: end;
}

.articles-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.articles-field__label {
  font-size: 12px;
  color: var(--text-muted);
}

.articles-field__control {
  width: 100%;
}

.articles-filters :deep(.el-input__wrapper),
.articles-filters :deep(.el-select__wrapper),
.articles-filters :deep(.el-input-number__wrapper) {
  background: rgba(7, 10, 19, 0.72);
  box-shadow: inset 0 0 0 1px var(--border-subtle);
}

.articles-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.articles-list-state {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.articles-pagination {
  display: flex;
  justify-content: flex-end;
}

.articles-pagination :deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background-color: var(--color-primary);
}

.articles-pagination :deep(.el-pagination.is-background .btn-next),
.articles-pagination :deep(.el-pagination.is-background .btn-prev),
.articles-pagination :deep(.el-pagination.is-background .el-pager li) {
  background-color: var(--bg-panel);
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
}

.article-title-cell {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.article-link-button {
  color: #d8e5ff;
  cursor: pointer;
  padding: 0;
  text-align: left;
}

.article-link-button:hover {
  color: #8db2ff;
}

.article-title-cell__slug,
.article-topic,
.article-run-placeholder {
  color: var(--text-muted);
  font-size: 12px;
}

.article-title-cell__slug {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  opacity: 0.8;
}

.article-actions-cell {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.articles-state-card {
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

.articles-state-card--error {
  border-color: rgba(239, 68, 68, 0.22);
  background: rgba(239, 68, 68, 0.06);
}

.articles-state-card h2,
.articles-state-card h3,
.article-detail__keywords h4,
.article-detail__section-head h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
}

.articles-state-card p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  opacity: 0.8;
  line-height: 1.5;
}

.article-detail {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.article-detail__summary,
.article-detail__meta-panel,
.article-detail__content-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: rgba(7, 10, 19, 0.5);
}

.article-detail__title {
  margin: 8px 0 6px;
  color: var(--text-main);
  font-size: 20px;
  font-weight: 600;
}

.article-detail__slug {
  margin: 0;
  color: var(--text-muted);
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  opacity: 0.8;
}

.article-detail__descriptions :deep(.el-descriptions__label) {
  width: 108px;
}

.article-detail__descriptions :deep(.el-descriptions__table) {
  --el-descriptions-table-border: var(--border-subtle);
  --el-descriptions-item-bordered-label-background: rgba(255, 255, 255, 0.03);
  --el-fill-color-blank: transparent;
  --el-text-color-primary: var(--text-main);
  --el-text-color-regular: var(--text-muted);
}

.article-detail__keywords {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.article-keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.article-keyword-list__tag {
  --el-tag-bg-color: rgba(37, 99, 235, 0.08);
  --el-tag-border-color: rgba(37, 99, 235, 0.18);
  --el-tag-text-color: #c9d9ff;
}

.article-detail__empty-hint {
  margin: 0;
  color: var(--text-muted);
}

.article-detail__meta-panel pre,
.article-markdown-source {
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

.article-content-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.article-content-tabs :deep(.el-tabs__item) {
  color: var(--text-muted);
}

.article-content-tabs :deep(.el-tabs__item.is-active) {
  color: #c9d9ff;
}

.article-content-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--color-primary);
}

.article-markdown-preview {
  color: var(--text-main);
  line-height: 1.8;
  word-break: break-word;
}

.article-markdown-preview :deep(h1),
.article-markdown-preview :deep(h2),
.article-markdown-preview :deep(h3),
.article-markdown-preview :deep(h4),
.article-markdown-preview :deep(h5),
.article-markdown-preview :deep(h6) {
  margin: 1.2em 0 0.5em;
  color: var(--text-main);
  line-height: 1.3;
}

.article-markdown-preview :deep(p),
.article-markdown-preview :deep(ul),
.article-markdown-preview :deep(ol),
.article-markdown-preview :deep(blockquote),
.article-markdown-preview :deep(pre) {
  margin: 0 0 1em;
}

.article-markdown-preview :deep(ul),
.article-markdown-preview :deep(ol) {
  padding-left: 1.4em;
}

.article-markdown-preview :deep(blockquote) {
  margin-left: 0;
  padding-left: 1em;
  border-left: 3px solid rgba(37, 99, 235, 0.35);
  color: #d8e0f3;
}

.article-markdown-preview :deep(code) {
  padding: 0.15em 0.4em;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.article-markdown-preview :deep(pre code) {
  display: block;
  padding: 14px;
  overflow-x: auto;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.24);
  line-height: 1.6;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
}

.article-markdown-preview :deep(a) {
  color: #9fc0ff;
  text-decoration: none;
}

.article-markdown-preview :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-subtle);
  margin: 1.2em 0;
}

.article-detail__footer,
.article-publish-form__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.article-publish-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.article-publish-form__description {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.article-publish-form__field {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.article-publish-form__label {
  font-size: 13px;
  color: var(--text-muted);
}

.article-publish-dialog :deep(.el-dialog) {
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
}

.article-publish-dialog :deep(.el-dialog__title) {
  color: var(--text-main);
}

.article-publish-dialog :deep(.el-dialog__body) {
  color: var(--text-main);
}

.article-publish-dialog :deep(.el-checkbox__label),
.article-publish-dialog :deep(.el-switch__label) {
  color: var(--text-main);
}

@media (max-width: 1280px) {
  .articles-summary {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .articles-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .articles-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

@media (max-width: 920px) {
  .articles-hero {
    grid-template-columns: 1fr;
  }

  .articles-hero__meta {
    grid-template-columns: 1fr;
    min-width: 0;
  }
}

@media (max-width: 640px) {
  .articles-page {
    gap: 18px;
  }

  .articles-hero,
  .articles-panel,
  .article-detail__summary,
  .article-detail__meta-panel,
  .article-detail__content-panel {
    padding: 16px;
  }

  .articles-summary,
  .articles-filters {
    grid-template-columns: 1fr;
  }

  .articles-panel__header,
  .article-detail__summary-header,
  .article-detail__section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .article-detail__footer,
  .article-publish-form__footer {
    justify-content: flex-start;
  }
}
</style>
