<template>
  <div class="capabilities-page">
    <header class="capabilities-hero">
      <div class="capabilities-hero__main">
        <span class="capabilities-hero__eyebrow">Capability Memory Center</span>
        <h1 class="capabilities-hero__title">能力库中心</h1>
        <p class="capabilities-hero__description">
          统一查看能力项、证据来源和最近引用文章，先把治理读面和停用动作补齐。
        </p>
      </div>

      <div class="capabilities-hero__meta">
        <div class="capabilities-pill">
          <span class="capabilities-pill__label">轮询频率</span>
          <span class="capabilities-pill__value">30s / 次</span>
        </div>
        <div class="capabilities-pill" :class="hasWarnings ? 'capabilities-pill--warning' : 'capabilities-pill--healthy'">
          <span class="capabilities-pill__label">数据状态</span>
          <span class="capabilities-pill__value">{{ hasWarnings ? '部分降级' : '正常' }}</span>
        </div>
      </div>
    </header>

    <section v-if="hasWarnings" class="capabilities-alerts">
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

    <section class="capabilities-summary">
      <el-skeleton
        v-if="isSummaryPending"
        :rows="3"
        animated
        class="capabilities-summary__skeleton"
      />
      <template v-else-if="isSummaryError">
        <div class="capabilities-state-card capabilities-state-card--error">
          <h2>能力库概览加载失败</h2>
          <p>{{ summaryErrorMessage }}</p>
        </div>
      </template>
      <template v-else>
        <StatCard title="能力项总量" :value="formatNumber(totalCapabilities)">
          <template #icon>
            <Wrench class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="启用中" :value="formatNumber(activeTotal)">
          <template #icon>
            <ShieldCheck class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="已停用" :value="formatNumber(inactiveTotal)">
          <template #icon>
            <ShieldOff class="h-5 w-5" />
          </template>
        </StatCard>
        <StatCard title="能力分组" :value="formatNumber(groupsTotal)">
          <template #icon>
            <Blocks class="h-5 w-5" />
          </template>
        </StatCard>
      </template>
    </section>

    <section class="capabilities-layout">
      <article class="capabilities-panel capabilities-panel--main">
        <div class="capabilities-panel__header">
          <div>
            <span class="capabilities-panel__eyebrow">检索与筛选</span>
            <h2 class="capabilities-panel__title">能力项列表</h2>
          </div>
          <button class="capabilities-refresh-button" type="button" @click="handleRefresh">
            <RefreshCcw class="h-4 w-4" />
            刷新
          </button>
        </div>

        <div class="capabilities-filters">
          <label class="capabilities-field">
            <span class="capabilities-field__label">状态</span>
            <el-select
              v-model="draftFilters.active"
              placeholder="全部状态"
              clearable
              class="capabilities-field__control"
            >
              <el-option
                v-for="option in activeOptions"
                :key="option.key"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </label>

          <label class="capabilities-field">
            <span class="capabilities-field__label">能力分组</span>
            <el-select
              v-model="draftFilters.group_code"
              placeholder="全部分组"
              clearable
              filterable
              class="capabilities-field__control"
            >
              <el-option
                v-for="option in groupOptions"
                :key="option.value || 'all-groups'"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </label>

          <label class="capabilities-field capabilities-field--query">
            <span class="capabilities-field__label">搜索</span>
            <el-input
              v-model="draftFilters.query"
              class="capabilities-field__control"
              placeholder="能力名 / 编码 / public claim"
              clearable
              @keyup.enter="applyFilters"
            />
          </label>

          <div class="capabilities-actions">
            <button class="capabilities-action-button capabilities-action-button--primary" type="button" @click="applyFilters">
              应用筛选
            </button>
            <button class="capabilities-action-button" type="button" @click="resetFilters">
              重置
            </button>
          </div>
        </div>

        <div class="capabilities-list-state">
          <el-skeleton v-if="isCapabilitiesPending" :rows="8" animated />
          <div v-else-if="isCapabilitiesError" class="capabilities-state-card capabilities-state-card--error">
            <h3>能力列表加载失败</h3>
            <p>{{ capabilitiesErrorMessage }}</p>
          </div>
          <div v-else-if="!capabilities.length" class="capabilities-state-card">
            <h3>没有匹配的能力项</h3>
            <p>当前筛选条件下没有命中结果，可以调整状态、分组或搜索词后重试。</p>
          </div>
          <template v-else>
            <IndustrialTable :data="capabilities">
              <el-table-column min-width="220" label="能力项">
                <template #default="{ row }">
                  <div class="capability-cell">
                    <button
                      class="capability-link-button"
                      type="button"
                      @click="openCapabilityDetail(row.id)"
                    >
                      {{ row.capability_name }}
                    </button>
                    <span class="capability-cell__meta">{{ row.capability_code }}</span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column width="150" label="能力分组">
                <template #default="{ row }">
                  {{ row.group_name }}
                </template>
              </el-table-column>

              <el-table-column width="110" align="center" label="状态">
                <template #default="{ row }">
                  <StatusLabel
                    :status="row.is_active ? 'success' : 'info'"
                    :text="row.is_active ? '启用中' : '已停用'"
                  />
                </template>
              </el-table-column>

              <el-table-column width="110" align="center" label="口径">
                <template #default="{ row }">
                  <StatusLabel
                    :status="claimLevelMeta(row.claim_level).status"
                    :text="claimLevelMeta(row.claim_level).label"
                  />
                </template>
              </el-table-column>

              <el-table-column width="108" align="center" label="置信度">
                <template #default="{ row }">
                  {{ formatPercent(row.confidence_score) }}
                </template>
              </el-table-column>

              <el-table-column width="96" align="center" label="来源数">
                <template #default="{ row }">
                  {{ formatNumber(row.source_count) }}
                </template>
              </el-table-column>

              <el-table-column min-width="280" label="对外口径">
                <template #default="{ row }">
                  <p class="capability-claim">{{ row.public_claim || '暂无 public claim' }}</p>
                </template>
              </el-table-column>

              <el-table-column width="156" label="更新时间">
                <template #default="{ row }">
                  {{ formatDateTime(row.updated_at) }}
                </template>
              </el-table-column>

              <el-table-column width="110" fixed="right" label="操作">
                <template #default="{ row }">
                  <button
                    class="capability-row-action"
                    type="button"
                    :disabled="!row.is_active || disableMutation.isPending.value"
                    @click="handleDisableCapability(row.id, row.capability_name)"
                  >
                    停用
                  </button>
                </template>
              </el-table-column>
            </IndustrialTable>

            <div class="capabilities-pagination">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="pageSize"
                :total="filteredCapabilitiesTotal"
                layout="total, prev, pager, next"
                background
              />
            </div>
          </template>
        </div>
      </article>

      <aside class="capabilities-side-stack">
        <article class="capabilities-panel">
          <div class="capabilities-panel__header">
            <div>
              <span class="capabilities-panel__eyebrow">Group Distribution</span>
              <h2 class="capabilities-panel__title">分组热度</h2>
            </div>
            <StatusLabel status="primary" :text="`${groupOptions.length - 1} 组`" />
          </div>

          <div v-if="!groupDistribution.length" class="capabilities-state-card">
            <h3>暂无分组统计</h3>
            <p>当前列表没有可用于统计的能力分组。</p>
          </div>
          <div v-else class="capability-group-feed">
            <div
              v-for="group in groupDistribution"
              :key="group.group_code"
              class="capability-group-feed__item"
            >
              <div class="capability-group-feed__header">
                <span class="capability-group-feed__name">{{ group.group_name }}</span>
                <span class="capability-group-feed__count">{{ formatNumber(group.total) }}</span>
              </div>
              <div class="capability-group-feed__bar">
                <span
                  class="capability-group-feed__fill"
                  :style="{ width: `${group.maxPercent}%` }"
                ></span>
              </div>
              <div class="capability-group-feed__meta">
                <span>启用 {{ group.active }}</span>
                <span>停用 {{ group.inactive }}</span>
              </div>
            </div>
          </div>
        </article>

        <article class="capabilities-panel">
          <div class="capabilities-panel__header">
            <div>
              <span class="capabilities-panel__eyebrow">Capability Policy</span>
              <h2 class="capabilities-panel__title">治理规则</h2>
            </div>
          </div>

          <ul class="capabilities-notes">
            <li>默认展示当前启用的能力画像。</li>
            <li>停用动作只改 `is_active`，不删除历史来源。</li>
            <li>详情抽屉显示 public claim、适用条件和最近引用文章。</li>
            <li>来源列表按 `priority_weight` 排序，优先展示高可信来源。</li>
          </ul>
        </article>
      </aside>
    </section>

    <DetailPanel
      v-model="detailOpen"
      :title="detailPanelTitle"
      size="760px"
    >
      <div v-if="isDetailPending || isSourcesPending" class="capability-detail-state">
        <el-skeleton :rows="10" animated />
      </div>

      <div v-else-if="isDetailError" class="capabilities-state-card capabilities-state-card--error">
        <h3>能力详情加载失败</h3>
        <p>{{ detailErrorMessage }}</p>
      </div>

      <div v-else-if="!selectedCapability" class="capabilities-state-card">
        <h3>没有可展示的能力项</h3>
        <p>当前能力项不存在或已被移除。</p>
      </div>

      <template v-else>
        <section class="capability-detail-section">
          <div class="capability-detail-grid">
            <div class="capability-detail-card">
              <span class="capability-detail-card__label">能力编码</span>
              <pre class="capability-detail-card__value">{{ selectedCapability.capability_code }}</pre>
            </div>
            <div class="capability-detail-card">
              <span class="capability-detail-card__label">能力分组</span>
              <div class="capability-detail-card__value">{{ selectedCapability.group_name }}</div>
            </div>
            <div class="capability-detail-card">
              <span class="capability-detail-card__label">口径级别</span>
              <StatusLabel
                :status="claimLevelMeta(selectedCapability.claim_level).status"
                :text="claimLevelMeta(selectedCapability.claim_level).label"
              />
            </div>
            <div class="capability-detail-card">
              <span class="capability-detail-card__label">状态</span>
              <StatusLabel
                :status="selectedCapability.is_active ? 'success' : 'info'"
                :text="selectedCapability.is_active ? '启用中' : '已停用'"
              />
            </div>
          </div>
        </section>

        <section class="capability-detail-section">
          <div class="capability-detail-block">
            <span class="capability-detail-block__label">public claim</span>
            <p class="capability-detail-block__body">{{ selectedCapability.public_claim || '暂无 public claim。' }}</p>
          </div>

          <div class="capability-detail-stack">
            <div class="capability-detail-block">
              <span class="capability-detail-block__label">保守口径</span>
              <p class="capability-detail-block__body">{{ selectedCapability.conservative_value_text || '暂无' }}</p>
            </div>
            <div class="capability-detail-block">
              <span class="capability-detail-block__label">进阶口径</span>
              <p class="capability-detail-block__body">{{ selectedCapability.advanced_value_text || '暂无' }}</p>
            </div>
          </div>

          <div class="capability-detail-stack">
            <div class="capability-detail-block">
              <span class="capability-detail-block__label">适用条件</span>
              <p class="capability-detail-block__body">{{ selectedCapability.conditions_text || '暂无限制说明。' }}</p>
            </div>
            <div class="capability-detail-block">
              <span class="capability-detail-block__label">应用标签</span>
              <div class="capability-detail-tags">
                <span
                  v-for="tag in selectedCapability.application_tags"
                  :key="tag"
                  class="capability-detail-tag"
                >
                  {{ tag }}
                </span>
                <span v-if="!selectedCapability.application_tags.length" class="capability-detail-tag capability-detail-tag--muted">
                  暂无标签
                </span>
              </div>
            </div>
          </div>
        </section>

        <section class="capability-detail-section">
          <div class="capability-detail-section__header">
            <div>
              <span class="capability-detail-section__eyebrow">Evidence Sources</span>
              <h3 class="capability-detail-section__title">来源列表</h3>
            </div>
            <StatusLabel status="primary" :text="`${capabilitySources.length} 条`" />
          </div>

          <div v-if="isSourcesError" class="capabilities-state-card capabilities-state-card--error">
            <h3>来源列表加载失败</h3>
            <p>{{ sourcesErrorMessage }}</p>
          </div>
          <div v-else-if="!capabilitySources.length" class="capabilities-state-card">
            <h3>暂无来源</h3>
            <p>当前能力项还没有挂接可展示来源。</p>
          </div>
          <div v-else class="capability-source-list">
            <a
              v-for="source in capabilitySources"
              :key="source.id"
              :href="source.source_url"
              target="_blank"
              rel="noreferrer"
              class="capability-source-list__item"
            >
              <div class="capability-source-list__header">
                <span class="capability-source-list__vendor">{{ source.source_vendor }}</span>
                <StatusLabel status="info" :text="`#${source.priority_weight}`" />
              </div>
              <div class="capability-source-list__title">{{ source.source_title }}</div>
              <div class="capability-source-list__meta">
                <span>{{ source.source_type }}</span>
                <span>可靠度 {{ formatPercent(source.reliability_score) }}</span>
                <span>{{ source.observed_on || '未标注日期' }}</span>
              </div>
            </a>
          </div>
        </section>

        <section class="capability-detail-section">
          <div class="capability-detail-section__header">
            <div>
              <span class="capability-detail-section__eyebrow">Recent Articles</span>
              <h3 class="capability-detail-section__title">最近命中文章</h3>
            </div>
          </div>

          <div v-if="!selectedCapability.recent_articles.length" class="capabilities-state-card">
            <h3>暂无引用文章</h3>
            <p>当前没有命中该能力项的近期文章。</p>
          </div>
          <div v-else class="capability-article-list">
            <RouterLink
              v-for="article in selectedCapability.recent_articles"
              :key="article.id"
              class="capability-article-list__item"
              :to="{ path: '/articles', query: { query: article.slug } }"
            >
              <div class="capability-article-list__header">
                <span class="capability-article-list__title">{{ article.title }}</span>
                <StatusLabel
                  :status="article.publish_status >= 2 ? 'success' : article.publish_status >= 1 ? 'primary' : 'warning'"
                  :text="article.publish_status >= 2 ? '已发布' : article.publish_status >= 1 ? '已通过' : '草稿'"
                />
              </div>
              <div class="capability-article-list__meta">
                <span>{{ article.slug }}</span>
                <span>质量分 {{ formatNumber(article.quality_score) }}</span>
                <span>{{ formatDateTime(article.updated_at) }}</span>
              </div>
            </RouterLink>
          </div>
        </section>
      </template>
    </DetailPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Blocks, RefreshCcw, ShieldCheck, ShieldOff, Wrench } from 'lucide-vue-next'

import DetailPanel from '../../components/DetailPanel.vue'
import IndustrialTable from '../../components/IndustrialTable.vue'
import StatCard from '../../components/StatCard.vue'
import StatusLabel from '../../components/StatusLabel.vue'
import {
  useCapabilitiesQuery,
  useCapabilityDetailQuery,
  useCapabilitySourcesQuery,
  useDisableCapabilityMutation,
} from '../../composables/useCapabilities'

const pageSize = 20

const activeOptions = [
  { key: 'all', label: '全部状态', value: 'all' },
  { key: 'active', label: '启用中', value: 'active' },
  { key: 'inactive', label: '已停用', value: 'inactive' },
]

const draftFilters = reactive<{
  active: 'all' | 'active' | 'inactive'
  group_code: string
  query: string
}>({
  active: 'all',
  group_code: '',
  query: '',
})

const appliedFilters = ref({
  active: 'all' as 'all' | 'active' | 'inactive',
  group_code: '',
  query: '',
})

const currentPage = ref(1)
const selectedCapabilityId = ref<number | null>(null)
const detailOpen = ref(false)

const listFilters = computed(() => ({
  ...(appliedFilters.value.active === 'active'
    ? { active: true }
    : appliedFilters.value.active === 'inactive'
      ? { active: false }
      : {}),
  ...(appliedFilters.value.group_code ? { group_code: appliedFilters.value.group_code } : {}),
  ...(appliedFilters.value.query ? { query: appliedFilters.value.query.trim() } : {}),
  limit: pageSize,
  offset: (currentPage.value - 1) * pageSize,
}))

const summaryFilters = computed(() => ({
  limit: 1,
  offset: 0,
}))

const capabilitiesQuery = useCapabilitiesQuery(listFilters)
const capabilitiesSummaryQuery = useCapabilitiesQuery(summaryFilters)
const capabilityDetailQuery = useCapabilityDetailQuery(selectedCapabilityId)
const capabilitySourcesQuery = useCapabilitySourcesQuery(selectedCapabilityId)
const disableMutation = useDisableCapabilityMutation()

const capabilities = computed(() => capabilitiesQuery.data.value?.items ?? [])
const filteredCapabilitiesTotal = computed(() => capabilitiesQuery.data.value?.total ?? 0)
const totalCapabilities = computed(() => capabilitiesSummaryQuery.data.value?.total ?? 0)
const activeTotal = computed(() => capabilitiesSummaryQuery.data.value?.active_total ?? 0)
const inactiveTotal = computed(() => capabilitiesSummaryQuery.data.value?.inactive_total ?? 0)
const groupsTotal = computed(() => capabilitiesSummaryQuery.data.value?.groups_total ?? 0)
const selectedCapability = computed(() => capabilityDetailQuery.data.value?.capability ?? null)
const capabilitySources = computed(() => capabilitySourcesQuery.data.value?.items ?? [])

const isCapabilitiesPending = computed(() => capabilitiesQuery.isPending.value)
const isCapabilitiesError = computed(() => capabilitiesQuery.isError.value)
const isSummaryPending = computed(() => capabilitiesSummaryQuery.isPending.value)
const isSummaryError = computed(() => capabilitiesSummaryQuery.isError.value)
const isDetailPending = computed(() => capabilityDetailQuery.isPending.value)
const isDetailError = computed(() => capabilityDetailQuery.isError.value)
const isSourcesPending = computed(() => capabilitySourcesQuery.isPending.value)
const isSourcesError = computed(() => capabilitySourcesQuery.isError.value)

const warningMessages = computed(() =>
  [
    capabilitiesQuery.data.value?.warning,
    capabilitiesSummaryQuery.data.value?.warning,
    capabilityDetailQuery.data.value?.warning,
    capabilitySourcesQuery.data.value?.warning,
  ].filter((item): item is string => Boolean(item)),
)

const hasWarnings = computed(() => warningMessages.value.length > 0)
const capabilitiesErrorMessage = computed(() => getErrorMessage(capabilitiesQuery.error.value))
const summaryErrorMessage = computed(() => getErrorMessage(capabilitiesSummaryQuery.error.value))
const detailErrorMessage = computed(() => getErrorMessage(capabilityDetailQuery.error.value))
const sourcesErrorMessage = computed(() => getErrorMessage(capabilitySourcesQuery.error.value))

const groupDistribution = computed(() => {
  const totals = new Map<string, { group_code: string; group_name: string; total: number; active: number; inactive: number }>()

  for (const item of capabilities.value) {
    const current = totals.get(item.group_code) ?? {
      group_code: item.group_code,
      group_name: item.group_name,
      total: 0,
      active: 0,
      inactive: 0,
    }
    current.total += 1
    if (item.is_active) {
      current.active += 1
    } else {
      current.inactive += 1
    }
    totals.set(item.group_code, current)
  }

  const items = Array.from(totals.values()).sort((a, b) => b.total - a.total)
  const maxTotal = items[0]?.total ?? 1
  return items.map((item) => ({
    ...item,
    maxPercent: Math.max(12, Math.round((item.total / maxTotal) * 100)),
  }))
})

const groupOptions = computed(() => {
  const map = new Map<string, string>()
  for (const item of capabilities.value) {
    map.set(item.group_code, item.group_name)
  }

  return [
    { label: '全部分组', value: '' },
    ...Array.from(map.entries())
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label, 'zh-CN')),
  ]
})

const detailPanelTitle = computed(() =>
  selectedCapability.value ? `${selectedCapability.value.capability_name} · 能力详情` : '能力详情',
)

function applyFilters() {
  currentPage.value = 1
  appliedFilters.value = {
    active: draftFilters.active,
    group_code: draftFilters.group_code,
    query: draftFilters.query,
  }
}

function resetFilters() {
  draftFilters.active = 'all'
  draftFilters.group_code = ''
  draftFilters.query = ''
  currentPage.value = 1
  appliedFilters.value = {
    active: 'all',
    group_code: '',
    query: '',
  }
}

function handleRefresh() {
  capabilitiesQuery.refetch()
  capabilitiesSummaryQuery.refetch()
  if (selectedCapabilityId.value) {
    capabilityDetailQuery.refetch()
    capabilitySourcesQuery.refetch()
  }
}

function openCapabilityDetail(specId: number) {
  selectedCapabilityId.value = specId
  detailOpen.value = true
}

async function handleDisableCapability(specId: number, capabilityName: string) {
  try {
    await ElMessageBox.confirm(
      `停用后该能力项将不再参与命中和上下文注入，但历史来源仍会保留。确认停用「${capabilityName}」吗？`,
      '停用能力项',
      {
        confirmButtonText: '确认停用',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    const result = await disableMutation.mutateAsync(specId)
    ElMessage.success(readMutationMessage(result, '能力项已停用。'))
    handleRefresh()
  } catch (error) {
    if (isCancelError(error)) {
      return
    }
    ElMessage.error(getErrorMessage(error))
  }
}

function claimLevelMeta(level: string | null | undefined) {
  const normalized = (level || 'public_safe').toLowerCase()

  if (normalized === 'experimental') {
    return { status: 'danger' as const, label: '实验口径' }
  }

  if (normalized === 'advanced_project') {
    return { status: 'warning' as const, label: '项目进阶' }
  }

  return { status: 'success' as const, label: '公开安全' }
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '--'
  }

  return new Intl.NumberFormat('zh-CN').format(value)
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '--'
  }

  return `${Math.round(Number(value) * 100)}%`
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

function readMutationMessage(result: Record<string, unknown>, fallback: string) {
  return typeof result.message === 'string' && result.message ? result.message : fallback
}

function isCancelError(error: unknown) {
  return Boolean(error) && typeof error === 'string' && error === 'cancel'
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }

  if (typeof error === 'string') {
    return error
  }

  return '请求失败，请稍后重试。'
}
</script>

<style scoped>
.capabilities-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%;
}

.capabilities-hero,
.capabilities-panel {
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, transparent 100%),
    var(--bg-panel);
}

.capabilities-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 32px;
}

.capabilities-hero__main,
.capabilities-hero__meta {
  display: flex;
  flex-direction: column;
}

.capabilities-hero__meta {
  gap: 12px;
  min-width: 200px;
}

.capabilities-hero__eyebrow,
.capabilities-panel__eyebrow,
.capability-detail-section__eyebrow {
  font-size: 11px;
  line-height: 1;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.capabilities-hero__title {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 700;
  color: var(--text-main);
}

.capabilities-hero__description {
  max-width: 720px;
  margin-top: 10px;
  color: var(--text-muted);
  line-height: 1.7;
}

.capabilities-pill {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.capabilities-pill--healthy {
  border-color: rgba(34, 197, 94, 0.22);
}

.capabilities-pill--warning {
  border-color: rgba(245, 158, 11, 0.22);
}

.capabilities-pill__label,
.capabilities-field__label,
.capability-detail-card__label,
.capability-detail-block__label {
  font-size: 12px;
  color: var(--text-muted);
}

.capabilities-pill__value,
.capability-detail-card__value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  color: var(--text-main);
  font-weight: 700;
}

.capabilities-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.capabilities-summary__skeleton,
.capabilities-state-card {
  grid-column: 1 / -1;
}

.capabilities-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 0.9fr);
  gap: 20px;
  min-height: 0;
}

.capabilities-panel {
  padding: 20px 22px;
}

.capabilities-panel--main {
  min-width: 0;
}

.capabilities-side-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.capabilities-panel__header,
.capability-detail-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.capabilities-panel__title,
.capability-detail-section__title {
  margin-top: 8px;
  font-size: 20px;
  color: var(--text-main);
}

.capabilities-refresh-button,
.capabilities-action-button,
.capability-row-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-main);
  padding: 10px 14px;
  transition: border-color 0.2s ease, background-color 0.2s ease, opacity 0.2s ease;
}

.capabilities-refresh-button:hover,
.capabilities-action-button:hover,
.capability-row-action:hover {
  border-color: rgba(37, 99, 235, 0.4);
  background: rgba(37, 99, 235, 0.08);
}

.capabilities-action-button--primary {
  border-color: rgba(37, 99, 235, 0.36);
  background: rgba(37, 99, 235, 0.12);
}

.capability-row-action:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.capabilities-filters {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 220px)) minmax(0, 1fr) auto;
  gap: 14px;
  margin-bottom: 18px;
}

.capabilities-field,
.capabilities-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capabilities-actions {
  flex-direction: row;
  align-items: flex-end;
}

.capability-cell,
.capability-group-feed__header,
.capability-source-list__header,
.capability-article-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.capability-link-button {
  color: var(--text-main);
  font-weight: 600;
  text-align: left;
}

.capability-link-button:hover {
  color: var(--color-primary);
}

.capability-cell__meta,
.capability-article-list__meta,
.capability-source-list__meta,
.capability-group-feed__meta {
  font-size: 12px;
  color: var(--text-muted);
}

.capability-cell__meta,
.capability-detail-card__value,
.capability-detail-block__body,
.capability-source-list__title {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.capability-claim {
  color: var(--text-muted);
  line-height: 1.6;
}

.capabilities-pagination {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.capabilities-state-card {
  padding: 20px;
  border-radius: 8px;
  border: 1px dashed rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.02);
}

.capabilities-state-card--error {
  border-color: rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.08);
}

.capability-group-feed,
.capability-source-list,
.capability-article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.capability-group-feed__item,
.capability-source-list__item,
.capability-article-list__item,
.capability-detail-card,
.capability-detail-block {
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
}

.capability-group-feed__name,
.capability-source-list__vendor,
.capability-article-list__title {
  color: var(--text-main);
  font-weight: 600;
}

.capability-group-feed__bar {
  height: 8px;
  margin-top: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.capability-group-feed__fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.9), rgba(96, 165, 250, 0.85));
}

.capabilities-notes {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 18px;
  color: var(--text-muted);
  line-height: 1.7;
}

.capability-detail-state {
  padding: 6px 0;
}

.capability-detail-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.capability-detail-section + .capability-detail-section {
  margin-top: 24px;
}

.capability-detail-grid,
.capability-detail-stack {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.capability-detail-block__body {
  margin-top: 10px;
  color: var(--text-main);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.capability-detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.capability-detail-tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(37, 99, 235, 0.12);
  color: var(--text-main);
  font-size: 12px;
}

.capability-detail-tag--muted {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
}

@media (max-width: 1280px) {
  .capabilities-summary,
  .capabilities-layout,
  .capabilities-filters,
  .capability-detail-grid,
  .capability-detail-stack {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .capabilities-hero,
  .capabilities-layout,
  .capabilities-summary,
  .capabilities-filters,
  .capability-detail-grid,
  .capability-detail-stack {
    grid-template-columns: minmax(0, 1fr);
  }

  .capabilities-hero {
    padding: 24px 20px;
  }

  .capabilities-hero__meta {
    min-width: 0;
  }

  .capabilities-actions {
    flex-wrap: wrap;
  }
}
</style>
