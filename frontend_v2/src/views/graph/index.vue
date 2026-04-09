<template>
  <div class="graph-page">
    <header class="graph-hero">
      <div class="graph-hero__main">
        <span class="graph-hero__eyebrow">Knowledge Graph Explorer</span>
        <h1 class="graph-hero__title">知识图谱</h1>
        <p class="graph-hero__description">
          用轻量关系视图把文章主题、关键词池和能力库串起来，先提供可浏览、可排查的读版图谱。
        </p>
      </div>

      <div class="graph-hero__meta">
        <div class="graph-pill">
          <span class="graph-pill__label">图谱节点</span>
          <span class="graph-pill__value">{{ formatNumber(nodes.length) }}</span>
        </div>
        <div class="graph-pill">
          <span class="graph-pill__label">图谱边</span>
          <span class="graph-pill__value">{{ formatNumber(links.length) }}</span>
        </div>
      </div>
    </header>

    <section v-if="hasWarnings" class="graph-alerts">
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

    <section class="graph-summary">
      <StatCard title="主题节点" :value="formatNumber(subjectNodesTotal)">
        <template #icon>
          <Orbit class="h-5 w-5" />
        </template>
      </StatCard>
      <StatCard title="文章节点" :value="formatNumber(articleNodesTotal)">
        <template #icon>
          <FileText class="h-5 w-5" />
        </template>
      </StatCard>
      <StatCard title="关键词节点" :value="formatNumber(keywordNodesTotal)">
        <template #icon>
          <Hash class="h-5 w-5" />
        </template>
      </StatCard>
      <StatCard title="能力项节点" :value="formatNumber(capabilityNodesTotal)">
        <template #icon>
          <Wrench class="h-5 w-5" />
        </template>
      </StatCard>
    </section>

    <section class="graph-layout">
      <article class="graph-panel graph-panel--canvas">
        <div class="graph-panel__header">
          <div>
            <span class="graph-panel__eyebrow">Live Relationship Map</span>
            <h2 class="graph-panel__title">关系网络</h2>
          </div>
        </div>

        <div v-if="isGraphPending" class="graph-state-card">
          <el-skeleton :rows="12" animated />
        </div>
        <div v-else-if="isGraphError" class="graph-state-card graph-state-card--error">
          <h3>图谱数据加载失败</h3>
          <p>{{ graphErrorMessage }}</p>
        </div>
        <div v-else-if="!nodes.length" class="graph-state-card">
          <h3>暂无可视化数据</h3>
          <p>当前文章、关键词或能力库数据不足，暂时无法生成关系图。</p>
        </div>
        <KnowledgeGraphCanvas v-else :nodes="nodes" :links="links" />
      </article>

      <aside class="graph-side-stack">
        <article class="graph-panel">
          <div class="graph-panel__header">
            <div>
              <span class="graph-panel__eyebrow">Link Samples</span>
              <h2 class="graph-panel__title">关系样本</h2>
            </div>
          </div>

          <div v-if="!relationshipSamples.length" class="graph-state-card">
            <h3>暂无关系样本</h3>
            <p>等图谱节点生成后，这里会展示关键关系链。</p>
          </div>
          <div v-else class="graph-feed">
            <div
              v-for="sample in relationshipSamples"
              :key="sample.id"
              class="graph-feed__item"
            >
              <div class="graph-feed__header">
                <StatusLabel :status="sample.status" :text="sample.type" />
              </div>
              <div class="graph-feed__body">{{ sample.text }}</div>
            </div>
          </div>
        </article>

        <article class="graph-panel">
          <div class="graph-panel__header">
            <div>
              <span class="graph-panel__eyebrow">Legend</span>
              <h2 class="graph-panel__title">节点说明</h2>
            </div>
          </div>

          <div class="graph-legend">
            <div class="graph-legend__item"><span class="graph-legend__dot graph-legend__dot--subject"></span>主题</div>
            <div class="graph-legend__item"><span class="graph-legend__dot graph-legend__dot--article"></span>文章</div>
            <div class="graph-legend__item"><span class="graph-legend__dot graph-legend__dot--keyword"></span>关键词</div>
            <div class="graph-legend__item"><span class="graph-legend__dot graph-legend__dot--group"></span>能力分组</div>
            <div class="graph-legend__item"><span class="graph-legend__dot graph-legend__dot--capability"></span>能力项</div>
          </div>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { FileText, Hash, Orbit, Wrench } from 'lucide-vue-next'

import KnowledgeGraphCanvas from '../../components/KnowledgeGraphCanvas.vue'
import StatCard from '../../components/StatCard.vue'
import StatusLabel from '../../components/StatusLabel.vue'
import { useArticlesQuery } from '../../composables/useArticles'
import { useCapabilitiesQuery } from '../../composables/useCapabilities'
import { useKeywordsQuery } from '../../composables/useKeywords'
import type { KnowledgeGraphLink, KnowledgeGraphNode } from '../../types/graph'

const articlesQuery = useArticlesQuery({
  min_score: 0,
  limit: 12,
  offset: 0,
})
const keywordsQuery = useKeywordsQuery({
  limit: 24,
  offset: 0,
})
const capabilitiesQuery = useCapabilitiesQuery({
  active: true,
  limit: 20,
  offset: 0,
})

const articles = computed(() => articlesQuery.data.value?.items ?? [])
const keywords = computed(() => keywordsQuery.data.value?.items ?? [])
const capabilities = computed(() => capabilitiesQuery.data.value?.items ?? [])

const nodes = computed<KnowledgeGraphNode[]>(() => {
  const bucket = new Map<string, KnowledgeGraphNode>()

  for (const article of articles.value) {
    const subject = normalizeText(article.dim_subject)
    if (subject) {
      bucket.set(`subject:${subject}`, {
        id: `subject:${subject}`,
        name: article.dim_subject as string,
        category: 'subject',
        value: 3,
        meta: '文章主题',
      })
    }

    bucket.set(`article:${article.id}`, {
      id: `article:${article.id}`,
      name: article.title,
      category: 'article',
      value: Math.max(2, Math.round((article.quality_score || 0) / 20)),
      meta: article.slug,
    })
  }

  for (const keyword of keywords.value) {
    bucket.set(`keyword:${keyword.id}`, {
      id: `keyword:${keyword.id}`,
      name: keyword.keyword,
      category: 'keyword',
      value: Math.max(2, Math.round((keyword.difficulty || 0) / 20)),
      meta: keyword.status === 'consumed' ? '已消费关键词' : '待消费关键词',
    })
  }

  for (const capability of capabilities.value) {
    bucket.set(`group:${capability.group_code}`, {
      id: `group:${capability.group_code}`,
      name: capability.group_name,
      category: 'group',
      value: 4,
      meta: '能力分组',
    })
    bucket.set(`capability:${capability.id}`, {
      id: `capability:${capability.id}`,
      name: capability.capability_name,
      category: 'capability',
      value: Math.max(2, Math.round(capability.confidence_score * 5)),
      meta: capability.capability_code,
    })
  }

  return Array.from(bucket.values())
})

const links = computed<KnowledgeGraphLink[]>(() => {
  const bucket = new Map<string, KnowledgeGraphLink>()
  const subjectIds = new Set(nodes.value.filter((item) => item.category === 'subject').map((item) => item.id))

  for (const article of articles.value) {
    const articleId = `article:${article.id}`
    const subject = normalizeText(article.dim_subject)
    if (subject) {
      const subjectId = `subject:${subject}`
      if (subjectIds.has(subjectId)) {
        bucket.set(`${articleId}->${subjectId}`, {
          source: articleId,
          target: subjectId,
          label: '主题归属',
        })
      }
    }
  }

  for (const keyword of keywords.value) {
    if (keyword.target_article_id) {
      const articleId = `article:${keyword.target_article_id}`
      bucket.set(`keyword:${keyword.id}->${articleId}`, {
        source: `keyword:${keyword.id}`,
        target: articleId,
        label: '已绑定',
      })
    }
  }

  for (const capability of capabilities.value) {
    const groupId = `group:${capability.group_code}`
    bucket.set(`capability:${capability.id}->${groupId}`, {
      source: `capability:${capability.id}`,
      target: groupId,
      label: '能力归组',
    })

    const relatedSubject = articles.value.find((article) =>
      isTextRelated(article.dim_subject, capability.group_name) ||
      isTextRelated(article.dim_subject, capability.capability_name),
    )
    if (relatedSubject?.dim_subject) {
      const subjectId = `subject:${normalizeText(relatedSubject.dim_subject)}`
      if (subjectIds.has(subjectId)) {
        bucket.set(`${groupId}->${subjectId}`, {
          source: groupId,
          target: subjectId,
          label: '主题关联',
        })
      }
    }
  }

  return Array.from(bucket.values())
})

const subjectNodesTotal = computed(() => nodes.value.filter((item) => item.category === 'subject').length)
const articleNodesTotal = computed(() => nodes.value.filter((item) => item.category === 'article').length)
const keywordNodesTotal = computed(() => nodes.value.filter((item) => item.category === 'keyword').length)
const capabilityNodesTotal = computed(() => nodes.value.filter((item) => item.category === 'capability').length)

const isGraphPending = computed(() =>
  articlesQuery.isPending.value || keywordsQuery.isPending.value || capabilitiesQuery.isPending.value,
)
const isGraphError = computed(() =>
  articlesQuery.isError.value || keywordsQuery.isError.value || capabilitiesQuery.isError.value,
)
const graphErrorMessage = computed(() =>
  getErrorMessage(
    articlesQuery.error.value || keywordsQuery.error.value || capabilitiesQuery.error.value,
  ),
)
const warningMessages = computed(() =>
  [
    articlesQuery.data.value?.warning,
    keywordsQuery.data.value?.warning,
    capabilitiesQuery.data.value?.warning,
  ].filter((item): item is string => Boolean(item)),
)
const hasWarnings = computed(() => warningMessages.value.length > 0)

const relationshipSamples = computed(() => {
  const samples: Array<{ id: string; type: string; text: string; status: 'primary' | 'warning' | 'success' }> = []

  for (const link of links.value.slice(0, 8)) {
    const source = nodes.value.find((node) => node.id === link.source)
    const target = nodes.value.find((node) => node.id === link.target)
    if (!source || !target) {
      continue
    }

    samples.push({
      id: `${link.source}-${link.target}`,
      type: link.label || '关系',
      text: `${source.name} -> ${target.name}`,
      status: link.label === '已绑定' ? 'success' : link.label === '主题关联' ? 'warning' : 'primary',
    })
  }

  return samples
})

function normalizeText(value: string | null | undefined) {
  return String(value || '').trim().toLowerCase()
}

function isTextRelated(left: string | null | undefined, right: string | null | undefined) {
  const normalizedLeft = normalizeText(left)
  const normalizedRight = normalizeText(right)

  if (!normalizedLeft || !normalizedRight) {
    return false
  }

  return normalizedLeft.includes(normalizedRight) || normalizedRight.includes(normalizedLeft)
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '--'
  }
  return new Intl.NumberFormat('zh-CN').format(value)
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }
  return '请求失败，请稍后重试。'
}
</script>

<style scoped>
.graph-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%;
}

.graph-hero,
.graph-panel {
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, transparent 100%),
    var(--bg-panel);
}

.graph-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 32px;
}

.graph-hero__meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 180px;
}

.graph-hero__eyebrow,
.graph-panel__eyebrow {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.graph-hero__title {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 700;
  color: var(--text-main);
}

.graph-hero__description {
  max-width: 720px;
  margin-top: 10px;
  color: var(--text-muted);
  line-height: 1.7;
}

.graph-pill {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.graph-pill__label {
  font-size: 12px;
  color: var(--text-muted);
}

.graph-pill__value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  color: var(--text-main);
  font-weight: 700;
}

.graph-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.graph-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.75fr) minmax(300px, 0.95fr);
  gap: 20px;
}

.graph-panel {
  padding: 20px 22px;
}

.graph-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.graph-panel__title {
  margin-top: 8px;
  font-size: 20px;
  color: var(--text-main);
}

.graph-panel--canvas {
  min-width: 0;
}

.graph-side-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.graph-state-card {
  padding: 20px;
  border-radius: 8px;
  border: 1px dashed rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.02);
}

.graph-state-card--error {
  border-color: rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.08);
}

.graph-feed {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.graph-feed__item {
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
}

.graph-feed__body {
  margin-top: 10px;
  color: var(--text-main);
  line-height: 1.6;
}

.graph-legend {
  display: grid;
  gap: 12px;
}

.graph-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text-main);
}

.graph-legend__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
}

.graph-legend__dot--subject { color: #2563eb; background: #2563eb; }
.graph-legend__dot--article { color: #38bdf8; background: #38bdf8; }
.graph-legend__dot--keyword { color: #f59e0b; background: #f59e0b; }
.graph-legend__dot--group { color: #14b8a6; background: #14b8a6; }
.graph-legend__dot--capability { color: #22c55e; background: #22c55e; }

@media (max-width: 1280px) {
  .graph-summary,
  .graph-layout {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .graph-hero,
  .graph-summary,
  .graph-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .graph-hero {
    flex-direction: column;
    padding: 24px 20px;
  }

  .graph-hero__meta {
    min-width: 0;
  }
}
</style>
