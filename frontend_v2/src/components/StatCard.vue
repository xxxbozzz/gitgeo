<template>
  <div class="geo-stat-card">
    <div class="geo-stat-card__header">
      <span class="geo-stat-card__title">{{ title }}</span>
      <div v-if="$slots.icon" class="geo-stat-card__icon">
        <slot name="icon"></slot>
      </div>
    </div>
    <div class="geo-stat-card__body">
      <span class="geo-stat-card__value">{{ value }}</span>
      <span v-if="unit" class="geo-stat-card__unit">{{ unit }}</span>
    </div>
    <div v-if="trend !== undefined" class="geo-stat-card__footer" :class="trend >= 0 ? 'is-up' : 'is-down'">
      <span class="geo-stat-card__trend-icon">{{ trend >= 0 ? '▲' : '▼' }}</span>
      <span class="geo-stat-card__trend-value">{{ Math.abs(trend) }}%</span>
      <span class="geo-stat-card__trend-label">{{ trendLabel || '较上期' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  unit?: string
  trend?: number
  trendLabel?: string
}>()
</script>

<style scoped>
.geo-stat-card {
  background-color: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.geo-stat-card:hover {
  border-color: var(--border-focus);
  background-color: var(--bg-panel-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.geo-stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background-color: var(--color-primary);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.geo-stat-card:hover::before {
  opacity: 1;
}

.geo-stat-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.geo-stat-card__title {
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.geo-stat-card__icon {
  color: var(--text-muted);
  opacity: 0.6;
  transition: all 0.2s ease;
}

.geo-stat-card:hover .geo-stat-card__icon {
  color: var(--color-primary);
  opacity: 1;
}

.geo-stat-card__body {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.geo-stat-card__value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-main);
  /* Use system monospace or sans-serif for numbers */
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  letter-spacing: -0.02em;
}

.geo-stat-card__unit {
  color: var(--text-muted);
  font-size: 13px;
}

.geo-stat-card__footer {
  margin-top: 14px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.geo-stat-card__footer.is-up {
  color: var(--color-success);
}

.geo-stat-card__footer.is-down {
  color: var(--color-danger);
}

.geo-stat-card__trend-icon {
  font-size: 10px;
}

.geo-stat-card__trend-value {
  font-weight: 600;
}

.geo-stat-card__trend-label {
  color: var(--text-muted);
  font-weight: normal;
  margin-left: 4px;
}
</style>
