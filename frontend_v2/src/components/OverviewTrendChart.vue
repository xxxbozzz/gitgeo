<template>
  <div ref="chartRef" class="overview-trend-chart"></div>
</template>

<script setup lang="ts">
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { use, init, graphic, type ECharts } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { OverviewTrendPoint } from '../types/overview'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  points: OverviewTrendPoint[]
}>()

const chartRef = ref<HTMLElement | null>(null)

let chart: ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const normalizedPoints = computed(() =>
  props.points.map((item) => ({
    label: item.day || '--',
    value: item.count,
  })),
)

function renderChart() {
  if (!chartRef.value) {
    return
  }

  if (!chart) {
    chart = init(chartRef.value)
  }

  chart.setOption({
    animationDuration: 350,
    grid: {
      top: 20,
      right: 8,
      bottom: 18,
      left: 8,
      containLabel: true,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0f1423',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: {
        color: '#f1f3f9',
      },
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: normalizedPoints.value.map((item) => item.label),
      axisLine: {
        lineStyle: {
          color: 'rgba(255,255,255,0.08)',
        },
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        color: '#8b92a8',
      },
    },
    yAxis: {
      type: 'value',
      splitNumber: 4,
      axisLabel: {
        color: '#8b92a8',
      },
      axisLine: {
        show: false,
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255,255,255,0.06)',
        },
      },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: normalizedPoints.value.map((item) => item.value),
        lineStyle: {
          color: '#2563eb',
          width: 3,
        },
        itemStyle: {
          color: '#2563eb',
          borderColor: '#0f1423',
          borderWidth: 2,
        },
        areaStyle: {
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37,99,235,0.28)' },
            { offset: 1, color: 'rgba(37,99,235,0.02)' },
          ]),
        },
      },
    ],
  })
}

onMounted(() => {
  renderChart()

  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      chart?.resize()
    })
    resizeObserver.observe(chartRef.value)
  }
})

watch(
  normalizedPoints,
  () => {
    renderChart()
  },
  { deep: true },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.overview-trend-chart {
  width: 100%;
  min-height: 280px;
  height: 100%;
}
</style>
