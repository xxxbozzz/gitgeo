<template>
  <div ref="containerRef" class="knowledge-graph-canvas"></div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import { TooltipComponent } from 'echarts/components'

import type { KnowledgeGraphLink, KnowledgeGraphNode } from '../types/graph'

echarts.use([GraphChart, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  nodes: KnowledgeGraphNode[]
  links: KnowledgeGraphLink[]
}>()

const containerRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const categories = [
  { name: '主题' },
  { name: '文章' },
  { name: '关键词' },
  { name: '能力分组' },
  { name: '能力项' },
]

const categoryIndex = computed<Record<KnowledgeGraphNode['category'], number>>(() => ({
  subject: 0,
  article: 1,
  keyword: 2,
  group: 3,
  capability: 4,
}))

function ensureChart() {
  if (!containerRef.value) {
    return null
  }

  if (!chart) {
    chart = echarts.init(containerRef.value)
  }

  return chart
}

function renderChart() {
  const instance = ensureChart()
  if (!instance) {
    return
  }

  instance.setOption({
    backgroundColor: 'transparent',
    animationDuration: 400,
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 20, 35, 0.96)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: {
        color: '#f1f3f9',
      },
      formatter: (params: { data?: { name?: string; meta?: string } }) => {
        const name = params.data?.name || '未命名节点'
        const meta = params.data?.meta ? `<br/>${params.data.meta}` : ''
        return `${name}${meta}`
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        label: {
          show: true,
          color: '#f1f3f9',
          fontSize: 12,
        },
        force: {
          repulsion: 240,
          edgeLength: [60, 120],
          gravity: 0.08,
        },
        lineStyle: {
          color: 'rgba(148, 163, 184, 0.35)',
          width: 1.2,
          curveness: 0.06,
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 2,
            color: 'rgba(37, 99, 235, 0.8)',
          },
        },
        categories,
        data: props.nodes.map((node) => ({
          id: node.id,
          name: node.name,
          value: node.value,
          meta: node.meta,
          category: categoryIndex.value[node.category],
          symbolSize: Math.max(22, Math.min(50, 18 + node.value * 2)),
          itemStyle: {
            color: node.category === 'subject'
              ? '#2563eb'
              : node.category === 'article'
                ? '#38bdf8'
                : node.category === 'keyword'
                  ? '#f59e0b'
                  : node.category === 'group'
                    ? '#14b8a6'
                    : '#22c55e',
            borderColor: 'rgba(255,255,255,0.16)',
            borderWidth: 1,
          },
        })),
        links: props.links.map((link) => ({
          source: link.source,
          target: link.target,
          value: link.label,
        })),
      },
    ],
  })
}

function handleResize() {
  chart?.resize()
}

watch(
  () => [props.nodes, props.links],
  () => {
    renderChart()
  },
  { deep: true },
)

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.knowledge-graph-canvas {
  width: 100%;
  min-height: 480px;
}
</style>
