<template>
  <span :class="['geo-status-label', statusClass]">
    <span class="geo-status-label__dot" :class="dotClass"></span>
    <span class="geo-status-label__text"><slot>{{ text }}</slot></span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  text?: string
}>()

const statusClass = computed(() => {
  const map: Record<string, string> = {
    success: 'bg-[rgba(34,197,94,0.1)] border-[rgba(34,197,94,0.2)] text-[var(--color-success)]',
    warning: 'bg-[rgba(245,158,11,0.1)] border-[rgba(245,158,11,0.2)] text-[var(--color-warning)]',
    danger:  'bg-[rgba(239,68,68,0.1)] border-[rgba(239,68,68,0.2)] text-[var(--color-danger)]',
    info:    'bg-[rgba(139,146,168,0.1)] border-[rgba(139,146,168,0.2)] text-[var(--text-muted)]',
    primary: 'bg-[rgba(37,99,235,0.1)] border-[rgba(37,99,235,0.2)] text-[var(--color-primary)]'
  }
  return map[props.status] || map.info
})

const dotClass = computed(() => {
  const map: Record<string, string> = {
    success: 'bg-[var(--color-success)] shadow-[0_0_6px_var(--color-success)]',
    warning: 'bg-[var(--color-warning)] shadow-[0_0_6px_var(--color-warning)]',
    danger:  'bg-[var(--color-danger)] shadow-[0_0_6px_var(--color-danger)]',
    info:    'bg-[var(--text-muted)] shadow-[0_0_6px_var(--text-muted)]',
    primary: 'bg-[var(--color-primary)] shadow-[0_0_6px_var(--color-primary)]'
  }
  return map[props.status] || map.info
})
</script>

<style scoped>
.geo-status-label {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  border: 1px solid transparent;
  white-space: nowrap;
}

.geo-status-label__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  flex-shrink: 0;
}
</style>
