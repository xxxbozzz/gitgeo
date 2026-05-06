<template>
  <div>
    <div class="page-hero">
      <h1 class="page-title">数据总览</h1>
      <p class="page-sub">GEO 引擎实时运行状态 · {{ now }}</p>
    </div>
    <n-grid :cols="5" :x-gap="16" class="kpi-grid">
      <n-gi v-for="kpi in kpis" :key="kpi.label">
        <n-card :bordered="true" size="small" class="kpi-card">
          <n-statistic :label="kpi.label" :value="kpi.value">
            <template #suffix v-if="kpi.suffix">{{ kpi.suffix }}</template>
          </n-statistic>
          <div :style="{ color: kpi.trend > 0 ? '#22c55e' : '#ef4444', fontSize: '0.78rem', marginTop: '4px' }">
            {{ kpi.trend > 0 ? '↑' : '↓' }} {{ Math.abs(kpi.trend) }} vs 昨日
          </div>
        </n-card>
      </n-gi>
    </n-grid>
    <n-grid :cols="2" :x-gap="16" style="margin-top:20px">
      <n-gi><n-card title="7 日产出趋势" size="small"><div ref="chartRef" style="height:220px" /></n-card></n-gi>
      <n-gi><n-card title="待处理关键词" size="small">
        <n-list>
          <n-list-item v-for="kw in pendingKws" :key="kw.name">
            <n-thing :title="kw.name"><template #description>{{ kw.volume }} 搜索量</template></n-thing>
          </n-list-item>
        </n-list>
      </n-card></n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NGrid, NGi, NCard, NStatistic, NList, NListItem, NThing } from 'naive-ui'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const now = new Date().toLocaleString('zh-CN')
const kpis = [
  { label: '文章总数', value: 173, suffix: '篇', trend: 5 },
  { label: '质检通过', value: 169, suffix: '篇', trend: 3 },
  { label: '待处理关键词', value: 12, suffix: '个', trend: -2 },
  { label: '平均质量分', value: 89, suffix: '分', trend: 2 },
  { label: '内链关系', value: 1242, suffix: '条', trend: 48 },
]
const pendingKws = [
  { name: 'ENIG vs HASL 表面处理对比', volume: 2800 },
  { name: 'Rogers 4003C 板材选型指南', volume: 1200 },
  { name: 'AI 硬件 PCB 设计挑战', volume: 950 },
  { name: '汽车电子 PCB 新材料趋势', volume: 850 },
]
const chartRef = ref<HTMLDivElement>()
onMounted(() => {
  if (!chartRef.value) return
  const chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 10, bottom: 20 },
    xAxis: { type: 'category', data: ['04-30','05-01','05-02','05-03','05-04','05-05','05-06'] },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ data: [3,5,4,5,6,5,7], type: 'line', smooth: true, areaStyle: { color: 'rgba(37,99,235,0.1)' }, lineStyle: { color: '#2563eb' }, itemStyle: { color: '#2563eb' } }]
  })
  setTimeout(() => chart.resize(), 100)
})
</script>

<style scoped>
.page-hero { margin-bottom: 20px }
.page-title { font-size: 1.5rem; font-weight: 700; margin: 0 0 4px }
.page-sub { color: var(--n-text-color-3); font-size: 0.88rem; margin: 0 }
.kpi-grid { margin-top: 8px }
</style>
