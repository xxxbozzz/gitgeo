<template>
  <div class="runs-page">
    <header class="runs-hero">
      <div class="runs-hero__main">
        <span class="runs-hero__eyebrow">Runtime Control Center</span>
        <h1 class="runs-hero__title">运行中心</h1>
        <p class="runs-hero__description">
          用统一列表替代日志式排查，聚合查看运行状态、失败信息和步骤时间线。
        </p>
      </div>

      <div class="runs-hero__meta">
        <div class="runs-pill">
          <span class="runs-pill__label">最新运行</span>
          <span class="runs-pill__value">{{ latestRunAtLabel }}</span>
        </div>
        <div class="runs-pill" :class="hasWarnings ? 'runs-pill--warning' : 'runs-pill--healthy'">
          <span class="runs-pill__label">页面状态</span>
          <span class="runs-pill__value">{{ hasWarnings ? '部分降级' : '正常轮询' }}</span>
        </div>
      </div>
    </header>

    <section v-if="hasWarnings" class="runs-alerts">
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

    <section class="runs-summary">
      <el-skeleton
        v-if="isSummaryPending"
        :rows="3"
        animated
        class="runs-summary__skeleton"
      />
      <template v-else-if="isSummaryError">
        <div class="runs-state-card runs-state-card--error">
          <h2>运行概览加载失败</h2>
          <p>{{ summaryErrorMessage }}</p>
        </div>
      </template>
      <template v-else>
        <StatCard title="运行总数" :value="formatNumber(summary.total_runs)">
          <template #icon>
            <Layers3 class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="进行中" :value="formatNumber(summary.running_runs)">
          <template #icon>
            <PlayCircle class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="成功" :value="formatNumber(summary.succeeded_runs)">
          <template #icon>
            <CheckCircle2 class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="失败" :value="formatNumber(summary.failed_runs)">
          <template #icon>
            <CircleX class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="部分成功" :value="formatNumber(summary.partial_runs)">
          <template #icon>
            <AlertTriangle class="h-5 w-5" />
          </template>
        </StatCard>
      </template>
    </section>

    <section class="runs-layout">
      <article class="runs-panel runs-panel--main">
        <div class="runs-panel__header">
          <div>
            <span class="runs-panel__eyebrow">检索与筛选</span>
            <h2 class="runs-panel__title">运行列表</h2>
          </div>
          <button class="runs-refresh-button" type="button" @click="handleRefresh">
            <RefreshCcw class="h-4 w-4" />
            刷新
          </button>
        </div>

        <div class="runs-filters">
          <label class="runs-field">
            <span class="runs-field__label">状态</span>
            <el-select
              v-model="draftFilters.status"
              placeholder="全部状态"
              clearable
              class="runs-field__control"
            >
              <el-option
                v-for="option in statusOptions"
                :key="option.value || 'all-status'"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </label>

          <label class="runs-field">
            <span class="runs-field__label">触发方式</span>
            <el-select
              v-model="draftFilters.trigger_mode"
              placeholder="全部触发方式"
              clearable
              class="runs-field__control"
            >
              <el-option
                v-for="option in triggerModeOptions"
                :key="option.value || 'all-trigger'"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </label>

          <label class="runs-field runs-field--keyword">
            <span class="runs-field__label">关键词</span>
            <el-input
              v-model="draftFilters.keyword"
              class="runs-field__control"
              placeholder="搜索关键词"
              clearable
              @keyup.enter="applyFilters"
            />
          </label>

          <div class="runs-actions">
            <button class="runs-action-button runs-action-button--primary" type="button" @click="applyFilters">
              应用筛选
            </button>
            <button class="runs-action-button" type="button" @click="resetFilters">
              重置
            </button>
          </div>
        </div>

        <div class="runs-list-state">
          <el-skeleton v-if="isRunsPending" :rows="8" animated />
          <div v-else-if="isRunsError" class="runs-state-card runs-state-card--error">
            <h3>运行列表加载失败</h3>
            <p>{{ runsErrorMessage }}</p>
          </div>
          <div v-else-if="!runs.length" class="runs-state-card">
            <h3>没有匹配的运行记录</h3>
            <p>当前筛选条件下没有命中结果，可以调整状态或关键词后重试。</p>
          </div>
          <template v-else>
            <IndustrialTable :data="runs">
              <el-table-column min-width="170" label="运行 ID">
                <template #default="{ row }">
                  <button
                    class="run-link-button"
                    type="button"
                    @click="openRunDetail(row.id)"
                  >
                    {{ row.run_uid }}
                  </button>
                </template>
              </el-table-column>

              <el-table-column width="140" label="触发方式">
                <template #default="{ row }">
                  {{ formatTriggerMode(row.trigger_mode) }}
                </template>
              </el-table-column>

              <el-table-column min-width="180" label="关键词">
                <template #default="{ row }">
                  <div class="run-keyword-cell">
                    <span class="run-keyword-cell__text">{{ row.keyword || '未关联关键词' }}</span>
                    <span v-if="row.article_id" class="run-keyword-cell__meta">文章 #{{ row.article_id }}</span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column width="120" align="center" label="状态">
                <template #default="{ row }">
                  <StatusLabel
                    :status="runStatusMeta(row.status).status"
                    :text="runStatusMeta(row.status).label"
                  />
                </template>
              </el-table-column>

              <el-table-column min-width="160" label="当前步骤">
                <template #default="{ row }">
                  <div class="run-step-cell">
                    <span>{{ formatStepName(row.current_step) }}</span>
                    <span v-if="row.retry_count" class="run-step-cell__meta">
                      重试 {{ row.retry_count }} 次
                    </span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column width="170" label="开始时间">
                <template #default="{ row }">
                  {{ formatDateTime(row.started_at) }}
                </template>
              </el-table-column>

              <el-table-column width="140" label="耗时">
                <template #default="{ row }">
                  {{ formatDuration(row.started_at, row.finished_at) }}
                </template>
              </el-table-column>

              <el-table-column min-width="220" label="失败信息">
                <template #default="{ row }">
                  <span class="run-error-snippet">
                    {{ row.error_message || '无' }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column width="112" fixed="right" label="操作">
                <template #default="{ row }">
                  <button
                    class="runs-table-action"
                    type="button"
                    @click="openRunDetail(row.id)"
                  >
                    查看
                  </button>
                </template>
              </el-table-column>
            </IndustrialTable>

            <div class="runs-pagination">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="pageSize"
                :total="totalRuns"
                layout="total, prev, pager, next"
                background
              />
            </div>
          </template>
        </div>
      </article>

      <aside class="runs-side-stack">
        <article class="runs-panel runs-panel--failures">
          <div class="runs-panel__header">
            <div>
              <span class="runs-panel__eyebrow">近期异常</span>
              <h2 class="runs-panel__title">最近失败 / 部分成功</h2>
            </div>
            <StatusLabel
              :status="recentFailures.length ? 'warning' : 'success'"
              :text="`${recentFailures.length} 条`"
            />
          </div>

          <el-skeleton v-if="isFailuresPending" :rows="5" animated />
          <div v-else-if="isFailuresError" class="runs-state-card runs-state-card--error">
            <h3>最近失败列表加载失败</h3>
            <p>{{ failuresErrorMessage }}</p>
          </div>
          <div v-else-if="!recentFailures.length" class="runs-state-card">
            <h3>近期没有失败记录</h3>
            <p>最近的运行记录里没有失败或部分成功任务。</p>
          </div>
          <div v-else class="failure-feed">
            <button
              v-for="item in recentFailures"
              :key="item.id"
              class="failure-feed__item"
              type="button"
              @click="openRunDetail(item.id)"
            >
              <div class="failure-feed__header">
                <span class="failure-feed__uid">{{ item.run_uid }}</span>
                <StatusLabel
                  :status="runStatusMeta(item.status).status"
                  :text="runStatusMeta(item.status).label"
                />
              </div>
              <p class="failure-feed__keyword">{{ item.keyword || '未关联关键词' }}</p>
              <p class="failure-feed__error">{{ item.error_message || '无错误详情' }}</p>
              <span class="failure-feed__time">{{ formatDateTime(item.started_at) }}</span>
            </button>
          </div>
        </article>

        <article class="runs-panel runs-panel--notes">
          <div class="runs-panel__header">
            <div>
              <span class="runs-panel__eyebrow">后续扩展</span>
              <h2 class="runs-panel__title">预留能力</h2>
            </div>
          </div>

          <ul class="runs-notes">
            <li>运行重试入口已在产品规划中预留，等后端 `POST /api/v1/runs/{run_id}/retry` 后接入。</li>
            <li>当前页面已接统一筛选、分页和详情抽屉，后续可直接增加失败聚合和步骤级重试。</li>
            <li>轮询刷新当前为页面内局部刷新，不会整页 reload。</li>
          </ul>
        </article>
      </aside>
    </section>

    <DetailPanel
      v-model="detailPanelOpen"
      title="运行详情"
      size="720px"
    >
      <div class="run-detail">
        <div v-if="isDetailPending || isStepsPending" class="run-detail__loading">
          <el-skeleton :rows="8" animated />
        </div>

        <div v-else-if="isDetailError" class="runs-state-card runs-state-card--error">
          <h3>运行详情加载失败</h3>
          <p>{{ detailErrorMessage }}</p>
        </div>

        <div v-else-if="!selectedRun" class="runs-state-card">
          <h3>未找到运行记录</h3>
          <p>该运行可能已不存在，或当前接口没有返回详情。</p>
        </div>

        <template v-else>
          <section class="run-detail__summary">
            <div class="run-detail__summary-header">
              <div>
                <span class="run-detail__eyebrow">Run Overview</span>
                <h3 class="run-detail__uid">{{ selectedRun.run_uid }}</h3>
              </div>
              <StatusLabel
                :status="runStatusMeta(selectedRun.status).status"
                :text="runStatusMeta(selectedRun.status).label"
              />
            </div>

            <el-descriptions :column="2" border class="run-detail__descriptions">
              <el-descriptions-item label="运行类型">
                {{ formatRunType(selectedRun.run_type) }}
              </el-descriptions-item>
              <el-descriptions-item label="触发方式">
                {{ formatTriggerMode(selectedRun.trigger_mode) }}
              </el-descriptions-item>
              <el-descriptions-item label="关键词">
                {{ selectedRun.keyword || '未关联关键词' }}
              </el-descriptions-item>
              <el-descriptions-item label="当前步骤">
                {{ formatStepName(selectedRun.current_step) }}
              </el-descriptions-item>
              <el-descriptions-item label="关联文章">
                {{ selectedRun.article_id ? `#${selectedRun.article_id}` : '无' }}
              </el-descriptions-item>
              <el-descriptions-item label="重试次数">
                {{ selectedRun.retry_count }}
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">
                {{ formatDateTime(selectedRun.started_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="结束时间">
                {{ formatDateTime(selectedRun.finished_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="步骤数">
                {{ detail.steps_total }}
              </el-descriptions-item>
              <el-descriptions-item label="失败步骤">
                {{ detail.failed_steps }}
              </el-descriptions-item>
            </el-descriptions>
          </section>

          <section v-if="selectedRun.error_message" class="run-detail__error-panel">
            <div class="run-detail__section-head">
              <h4>失败信息</h4>
            </div>
            <p>{{ selectedRun.error_message }}</p>
          </section>

          <section v-if="selectedRun.detail_json" class="run-detail__json-panel">
            <div class="run-detail__section-head">
              <h4>运行上下文</h4>
            </div>
            <pre>{{ formatJson(selectedRun.detail_json) }}</pre>
          </section>

          <section class="run-detail__steps">
            <div class="run-detail__section-head">
              <h4>步骤时间线</h4>
              <StatusLabel
                :status="runSteps.length ? 'primary' : 'info'"
                :text="`${runSteps.length} 步`"
              />
            </div>

            <div v-if="isStepsError" class="runs-state-card runs-state-card--error">
              <h3>步骤时间线加载失败</h3>
              <p>{{ stepsErrorMessage }}</p>
            </div>
            <div v-else-if="!runSteps.length" class="runs-state-card">
              <h3>暂无步骤记录</h3>
              <p>当前运行还没有写入步骤时间线。</p>
            </div>
            <ol v-else class="run-step-timeline">
              <li
                v-for="step in runSteps"
                :key="step.id"
                class="run-step-timeline__item"
              >
                <div class="run-step-timeline__track">
                  <span
                    class="run-step-timeline__dot"
                    :class="`is-${runStatusMeta(step.status).status}`"
                  ></span>
                </div>
                <div class="run-step-card">
                  <div class="run-step-card__header">
                    <div>
                      <h5>{{ step.step_name }}</h5>
                      <p>{{ step.step_code }}</p>
                    </div>
                    <StatusLabel
                      :status="runStatusMeta(step.status).status"
                      :text="runStatusMeta(step.status).label"
                    />
                  </div>
                  <div class="run-step-card__meta">
                    <span>Attempt {{ step.attempt_no }}</span>
                    <span>{{ formatDateTime(step.started_at) }}</span>
                    <span>{{ formatDuration(step.started_at, step.finished_at) }}</span>
                  </div>
                  <p v-if="step.error_message" class="run-step-card__error">
                    {{ step.error_message }}
                  </p>
                  <pre v-if="step.detail_json" class="run-step-card__json">{{ formatJson(step.detail_json) }}</pre>
                </div>
              </li>
            </ol>
          </section>
        </template>
      </div>
    </DetailPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { AlertTriangle, CheckCircle2, CircleX, Layers3, PlayCircle, RefreshCcw } from 'lucide-vue-next'

import DetailPanel from '../../components/DetailPanel.vue'
import IndustrialTable from '../../components/IndustrialTable.vue'
import StatCard from '../../components/StatCard.vue'
import StatusLabel from '../../components/StatusLabel.vue'
import {
  useRecentRunFailuresQuery,
  useRunDetailQuery,
  useRunsQuery,
  useRunsSummaryQuery,
  useRunStepsQuery,
} from '../../composables/useRuns'

const pageSize = 20
const pollingIntervalMs = 20_000

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '进行中', value: 'running' },
  { label: '成功', value: 'succeeded' },
  { label: '失败', value: 'failed' },
  { label: '部分成功', value: 'partial' },
]

const triggerModeOptions = [
  { label: '全部触发方式', value: '' },
  { label: '关键词自动', value: 'keyword_auto' },
  { label: 'GEO 真空词自动', value: 'geo_gap_auto' },
  { label: '手动', value: 'manual' },
  { label: '自动', value: 'auto' },
]

const draftFilters = reactive({
  status: '',
  trigger_mode: '',
  keyword: '',
})

const appliedFilters = ref({
  status: '',
  trigger_mode: '',
  keyword: '',
})

const currentPage = ref(1)
const selectedRunId = ref<number | null>(null)
const detailPanelOpen = ref(false)

const queryFilters = computed(() => ({
  ...(appliedFilters.value.status ? { status: appliedFilters.value.status } : {}),
  ...(appliedFilters.value.trigger_mode ? { trigger_mode: appliedFilters.value.trigger_mode } : {}),
  ...(appliedFilters.value.keyword ? { keyword: appliedFilters.value.keyword.trim() } : {}),
  limit: pageSize,
  offset: (currentPage.value - 1) * pageSize,
}))

const summaryQuery = useRunsSummaryQuery()
const runsQuery = useRunsQuery(queryFilters)
const recentFailuresQuery = useRecentRunFailuresQuery(6)
const detailQuery = useRunDetailQuery(selectedRunId)
const stepsQuery = useRunStepsQuery(selectedRunId)

const summary = computed(() => summaryQuery.data.value ?? {
  total_runs: 0,
  running_runs: 0,
  succeeded_runs: 0,
  failed_runs: 0,
  partial_runs: 0,
  latest_run_at: null,
  warning: null,
})

const detail = computed(() => detailQuery.data.value ?? {
  run: null,
  steps_total: 0,
  failed_steps: 0,
  warning: null,
})

const runs = computed(() => runsQuery.data.value?.items ?? [])
const totalRuns = computed(() => runsQuery.data.value?.total ?? 0)
const recentFailures = computed(() => recentFailuresQuery.data.value?.items ?? [])
const selectedRun = computed(() => detail.value.run)
const runSteps = computed(() => stepsQuery.data.value?.items ?? [])

const latestRunAtLabel = computed(() => formatDateTime(summary.value.latest_run_at))
const isSummaryPending = computed(() => summaryQuery.isPending.value)
const isSummaryError = computed(() => summaryQuery.isError.value)
const isRunsPending = computed(() => runsQuery.isPending.value)
const isRunsError = computed(() => runsQuery.isError.value)
const isFailuresPending = computed(() => recentFailuresQuery.isPending.value)
const isFailuresError = computed(() => recentFailuresQuery.isError.value)
const isDetailPending = computed(() => detailQuery.isPending.value)
const isDetailError = computed(() => detailQuery.isError.value)
const isStepsPending = computed(() => stepsQuery.isPending.value)
const isStepsError = computed(() => stepsQuery.isError.value)

const warningMessages = computed(() =>
  [
    summaryQuery.data.value?.warning,
    runsQuery.data.value?.warning,
    recentFailuresQuery.data.value?.warning,
  ].filter((item): item is string => Boolean(item)),
)

const hasWarnings = computed(() => warningMessages.value.length > 0)

const summaryErrorMessage = computed(() => getErrorMessage(summaryQuery.error.value))
const runsErrorMessage = computed(() => getErrorMessage(runsQuery.error.value))
const failuresErrorMessage = computed(() => getErrorMessage(recentFailuresQuery.error.value))
const detailErrorMessage = computed(() => getErrorMessage(detailQuery.error.value))
const stepsErrorMessage = computed(() => getErrorMessage(stepsQuery.error.value))

let pollingTimer: number | null = null

watch(detailPanelOpen, (open) => {
  if (!open) {
    return
  }
  detailQuery.refetch()
  stepsQuery.refetch()
})

onMounted(() => {
  pollingTimer = window.setInterval(() => {
    summaryQuery.refetch()
    runsQuery.refetch()
    recentFailuresQuery.refetch()

    if (detailPanelOpen.value && selectedRunId.value) {
      detailQuery.refetch()
      stepsQuery.refetch()
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
    trigger_mode: draftFilters.trigger_mode,
    keyword: draftFilters.keyword,
  }
}

function resetFilters() {
  draftFilters.status = ''
  draftFilters.trigger_mode = ''
  draftFilters.keyword = ''
  currentPage.value = 1
  appliedFilters.value = {
    status: '',
    trigger_mode: '',
    keyword: '',
  }
}

function handleRefresh() {
  summaryQuery.refetch()
  runsQuery.refetch()
  recentFailuresQuery.refetch()

  if (detailPanelOpen.value && selectedRunId.value) {
    detailQuery.refetch()
    stepsQuery.refetch()
  }
}

function openRunDetail(runId: number) {
  selectedRunId.value = runId
  detailPanelOpen.value = true
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

function formatDuration(startedAt: string | null | undefined, finishedAt: string | null | undefined) {
  if (!startedAt) {
    return '--'
  }

  const start = new Date(startedAt).getTime()
  const end = finishedAt ? new Date(finishedAt).getTime() : Date.now()

  if (Number.isNaN(start) || Number.isNaN(end)) {
    return '--'
  }

  const diffSeconds = Math.max(0, Math.floor((end - start) / 1000))

  if (diffSeconds < 60) {
    return `${diffSeconds}s`
  }

  if (diffSeconds < 3600) {
    return `${Math.floor(diffSeconds / 60)}m ${diffSeconds % 60}s`
  }

  return `${Math.floor(diffSeconds / 3600)}h ${Math.floor((diffSeconds % 3600) / 60)}m`
}

function formatRunType(value: string | null | undefined) {
  if (!value) {
    return '未知'
  }

  const map: Record<string, string> = {
    keyword_generation: '关键词生成',
    keyword: '关键词任务',
  }

  return map[value] || value
}

function formatTriggerMode(value: string | null | undefined) {
  if (!value) {
    return '未知'
  }

  const map: Record<string, string> = {
    keyword_auto: '关键词自动',
    geo_gap_auto: 'GEO 真空词自动',
    manual: '手动',
    auto: '自动',
    retry: '重试',
  }

  return map[value] || value
}

function formatStepName(value: string | null | undefined) {
  if (!value) {
    return '未开始'
  }

  const map: Record<string, string> = {
    generate: '生成',
    repair: '返修',
    publish: '发布',
  }

  return map[value] || value
}

function runStatusMeta(status: string | null | undefined) {
  const map: Record<string, { status: 'success' | 'warning' | 'danger' | 'info' | 'primary'; label: string }> = {
    succeeded: { status: 'success', label: '成功' },
    running: { status: 'primary', label: '进行中' },
    failed: { status: 'danger', label: '失败' },
    partial: { status: 'warning', label: '部分成功' },
  }

  return map[status || ''] || { status: 'info', label: status || '未知' }
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
.runs-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%;
}

.runs-hero {
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

.runs-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background-color: var(--color-primary);
}

.runs-hero__main {
  min-width: 0;
  max-width: 720px;
}

.runs-hero__eyebrow,
.runs-panel__eyebrow,
.run-detail__eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

.runs-hero__title {
  margin: 10px 0 12px;
  font-size: 30px;
  line-height: 1.1;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.runs-hero__description {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: rgba(241, 243, 249, 0.78);
}

.runs-hero__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  min-width: 0;
  width: 100%;
  max-width: 360px;
  align-self: start;
}

.runs-pill {
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

.runs-pill--warning {
  border-color: rgba(245, 158, 11, 0.18);
}

.runs-pill--healthy {
  border-color: rgba(34, 197, 94, 0.18);
}

.runs-pill__label {
  font-size: 12px;
  color: var(--text-muted);
}

.runs-pill__value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
}

.runs-alerts {
  display: grid;
  gap: 12px;
}

.runs-alerts :deep(.el-alert) {
  --el-alert-bg-color: rgba(245, 158, 11, 0.1);
  --el-alert-border-color: rgba(245, 158, 11, 0.2);
  --el-alert-text-color: #f7d089;
  border: 1px solid var(--el-alert-border-color);
  border-radius: 8px;
}

.runs-summary {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}

.runs-summary__skeleton {
  grid-column: 1 / -1;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
}

.runs-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.9fr);
  gap: 20px;
}

.runs-side-stack {
  display: grid;
  gap: 20px;
  align-content: start;
}

.runs-panel {
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

.runs-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.runs-panel__title {
  margin: 6px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.runs-refresh-button,
.runs-action-button,
.runs-table-action,
.run-link-button,
.failure-feed__item {
  border: none;
  background: transparent;
  font: inherit;
}

.runs-refresh-button,
.runs-action-button,
.runs-table-action {
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

.runs-refresh-button,
.runs-action-button {
  border: 1px solid var(--border-subtle);
  color: var(--text-main);
  background: rgba(7, 10, 19, 0.5);
}

.runs-action-button--primary,
.runs-table-action {
  background: rgba(37, 99, 235, 0.18);
  border: 1px solid rgba(37, 99, 235, 0.28);
  color: #c9d9ff;
}

.runs-refresh-button:hover,
.runs-action-button:hover,
.runs-table-action:hover {
  border-color: var(--border-focus);
  transform: translateY(-1px);
}

.runs-filters {
  display: grid;
  grid-template-columns: 170px 190px minmax(220px, 1fr) auto;
  gap: 12px;
  align-items: end;
}

.runs-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.runs-field__label {
  font-size: 12px;
  color: var(--text-muted);
}

.runs-field__control {
  width: 100%;
}

.runs-filters :deep(.el-input__wrapper),
.runs-filters :deep(.el-select__wrapper) {
  background: rgba(7, 10, 19, 0.72);
  box-shadow: inset 0 0 0 1px var(--border-subtle);
}

.runs-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.runs-list-state {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.runs-pagination {
  display: flex;
  justify-content: flex-end;
}

.runs-pagination :deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background-color: var(--color-primary);
}

.runs-pagination :deep(.el-pagination.is-background .btn-next),
.runs-pagination :deep(.el-pagination.is-background .btn-prev),
.runs-pagination :deep(.el-pagination.is-background .el-pager li) {
  background-color: var(--bg-panel);
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
}

.run-link-button {
  color: #d8e5ff;
  cursor: pointer;
  text-align: left;
  padding: 0;
}

.run-link-button:hover {
  color: #8db2ff;
}

.run-keyword-cell,
.run-step-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.run-keyword-cell__text {
  color: var(--text-main);
}

.run-keyword-cell__meta,
.run-step-cell__meta {
  font-size: 12px;
  color: var(--text-muted);
}

.run-error-snippet {
  display: -webkit-box;
  overflow: hidden;
  color: var(--text-muted);
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.failure-feed {
  display: grid;
  gap: 12px;
}

.failure-feed__item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(239, 68, 68, 0.16);
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.04);
  cursor: pointer;
  text-align: left;
}

.failure-feed__item:hover {
  border-color: rgba(239, 68, 68, 0.28);
}

.failure-feed__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.failure-feed__uid {
  font-size: 13px;
  color: #e4edff;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.failure-feed__keyword {
  margin: 0;
  color: var(--text-main);
  font-weight: 600;
  font-size: 14px;
}

.failure-feed__error,
.failure-feed__time {
  margin: 0;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.runs-notes {
  margin: 0;
  padding-left: 18px;
  color: var(--text-muted);
  line-height: 1.8;
}

.runs-state-card {
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

.runs-state-card--error {
  border-color: rgba(239, 68, 68, 0.22);
  background: rgba(239, 68, 68, 0.06);
}

.runs-state-card h2,
.runs-state-card h3,
.run-detail__section-head h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
}

.runs-state-card p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  opacity: 0.8;
  line-height: 1.5;
}

.run-detail {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.run-detail__summary,
.run-detail__error-panel,
.run-detail__json-panel,
.run-detail__steps {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: rgba(7, 10, 19, 0.5);
}

.run-detail__summary-header,
.run-detail__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.run-detail__uid {
  margin: 8px 0 0;
  color: var(--text-main);
  font-size: 20px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-weight: 600;
}

.run-detail__descriptions :deep(.el-descriptions__label) {
  width: 108px;
}

.run-detail__descriptions :deep(.el-descriptions__table) {
  --el-descriptions-table-border: var(--border-subtle);
  --el-descriptions-item-bordered-label-background: rgba(255, 255, 255, 0.03);
  --el-fill-color-blank: transparent;
  --el-text-color-primary: var(--text-main);
  --el-text-color-regular: var(--text-muted);
}

.run-detail__error-panel p {
  margin: 0;
  line-height: 1.7;
  color: #f7c1c1;
}

.run-detail__json-panel pre,
.run-step-card__json {
  margin: 0;
  padding: 14px;
  overflow-x: auto;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(0, 0, 0, 0.24);
  color: #d4def7;
  font-size: 12px;
  line-height: 1.6;
}

.run-step-timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 14px;
}

.run-step-timeline__item {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr);
  gap: 12px;
}

.run-step-timeline__track {
  position: relative;
  display: flex;
  justify-content: center;
}

.run-step-timeline__track::after {
  content: '';
  position: absolute;
  top: 14px;
  bottom: -18px;
  width: 1px;
  background: rgba(255, 255, 255, 0.08);
}

.run-step-timeline__item:last-child .run-step-timeline__track::after {
  display: none;
}

.run-step-timeline__dot {
  display: inline-flex;
  width: 12px;
  height: 12px;
  margin-top: 8px;
  border-radius: 999px;
  background: var(--text-muted);
  box-shadow: 0 0 0 2px var(--bg-panel);
}

.run-step-timeline__dot.is-success {
  background: var(--color-success);
  box-shadow: 0 0 0 2px var(--bg-panel), 0 0 8px var(--color-success);
}

.run-step-timeline__dot.is-warning {
  background: var(--color-warning);
  box-shadow: 0 0 0 2px var(--bg-panel), 0 0 8px var(--color-warning);
}

.run-step-timeline__dot.is-danger {
  background: var(--color-danger);
  box-shadow: 0 0 0 2px var(--bg-panel), 0 0 8px var(--color-danger);
}

.run-step-timeline__dot.is-primary {
  background: var(--color-primary);
  box-shadow: 0 0 0 2px var(--bg-panel), 0 0 8px var(--color-primary);
}

.run-step-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: rgba(15, 20, 35, 0.78);
}

.run-step-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.run-step-card__header h5 {
  margin: 0;
  color: var(--text-main);
  font-size: 16px;
}

.run-step-card__header p {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.run-step-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  color: var(--text-muted);
  font-size: 12px;
}

.run-step-card__error {
  margin: 0;
  color: #f6c5c5;
  line-height: 1.7;
}

@media (max-width: 1280px) {
  .runs-summary {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .runs-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 920px) {
  .runs-hero {
    grid-template-columns: 1fr;
  }

  .runs-hero__meta {
    grid-template-columns: 1fr;
    min-width: 0;
  }

  .runs-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .runs-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .runs-page {
    gap: 18px;
  }

  .runs-hero,
  .runs-panel,
  .run-detail__summary,
  .run-detail__error-panel,
  .run-detail__json-panel,
  .run-detail__steps {
    padding: 16px;
  }

  .runs-summary {
    grid-template-columns: 1fr;
  }

  .runs-filters {
    grid-template-columns: 1fr;
  }

  .runs-panel__header,
  .run-detail__summary-header,
  .run-detail__section-head,
  .failure-feed__header,
  .run-step-card__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
