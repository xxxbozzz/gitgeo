<template>
  <div>
    <div class="page-hero">
      <h1 class="page-title">数据总览</h1>
      <p class="page-sub">GEO 引擎实时运行状态 · {{ now }}</p>
    </div>
    <div class="kpi-grid">
      <div v-for="(kpi, i) in kpis" :key="kpi.label" :class="['kpi-card', 'accent-' + kpi.accent]">
        <div class="stat-label">{{ kpi.label }}</div>
        <div class="stat-value">{{ kpi.value }}<span v-if="kpi.suffix" style="font-size:1rem;font-weight:400;opacity:0.6;margin-left:4px">{{ kpi.suffix }}</span></div>
        <div :class="['stat-delta', kpi.trend > 0 ? 'up' : 'down']">{{ kpi.trend > 0 ? '↑' : '↓' }} {{ Math.abs(kpi.trend) }} vs 昨日</div>
      </div>
    </div>
    <n-grid :cols="2" :x-gap="16" style="margin-top:22px">
      <n-gi><n-card title="7 日产出趋势" size="small" :bordered="true"><div ref="chartRef" style="height:240px" /></n-card></n-gi>
      <n-gi><n-card title="待处理关键词" size="small" :bordered="true">
        <n-list v-if="pendingKws.length" :show-divider="false">
          <n-list-item v-for="kw in pendingKws" :key="kw.name" style="padding:8px 0">
            <n-thing :title="kw.name"><template #description><span style="color:var(--text-muted)">搜索量 {{ kw.volume.toLocaleString() }}</span></template></n-thing>
          </n-list-item>
        </n-list>
        <div v-else style="text-align:center;padding:40px;color:var(--text-muted)">暂无待处理关键词</div>
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

const now = new Date().toLocaleString('zh-CN', { month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit' })
const kpis = [
  { label: '文章总数', value: 173, suffix: '篇', trend: 5, accent: 'blue' },
  { label: '质检通过', value: 169, suffix: '篇', trend: 3, accent: 'green' },
  { label: '待处理词', value: 12, suffix: '个', trend: -2, accent: 'amber' },
  { label: '平均质量分', value: 89, suffix: '分', trend: 2, accent: 'blue' },
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
  const c = echarts.init(chartRef.value)
  c.setOption({
    tooltip: { trigger:'axis', backgroundColor:'#1a2235', borderColor:'rgba(255,255,255,0.08)', textStyle:{color:'#e8ecf4',fontSize:12} },
    grid: { left:44, right:16, top:12, bottom:24 },
    xAxis: { type:'category', data:['04-30','05-01','05-02','05-03','05-04','05-05','05-06'],
      axisLine:{lineStyle:{color:'rgba(255,255,255,0.06)'}}, axisLabel:{color:'#7a84a0',fontSize:11} },
    yAxis: { type:'value', minInterval:1,
      splitLine:{lineStyle:{color:'rgba(255,255,255,0.04)'}}, axisLabel:{color:'#7a84a0',fontSize:11} },
    series: [{ data:[3,5,4,5,6,5,7], type:'line', smooth:true, symbol:'circle', symbolSize:5,
      areaStyle:{color:'rgba(96,165,250,0.18)'}, lineStyle:{color:'#60a5fa',width:2},
      itemStyle:{color:'#60a5fa'} }]
  })
  setTimeout(() => c.resize(), 100)
})
</script>
