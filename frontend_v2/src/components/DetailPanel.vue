<template>
  <el-drawer
    v-model="visible"
    :size="size"
    :with-header="false"
    append-to-body
    class="geo-detail-panel"
  >
    <div class="h-full flex flex-col bg-[var(--bg-panel)]">
      <!-- Header -->
      <div class="h-16 border-b border-[var(--border-subtle)] px-6 flex items-center justify-between shrink-0">
        <h2 class="text-lg font-bold text-[var(--text-main)]">{{ title }}</h2>
        <div class="flex items-center gap-3">
          <slot name="header-actions"></slot>
          <button @click="visible = false" class="text-[var(--text-muted)] hover:text-[#f1f3f9] transition-colors p-1 rounded-full hover:bg-[rgba(255,255,255,0.05)]">
            <X class="w-5 h-5" />
          </button>
        </div>
      </div>
      
      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6 custom-scrollbar text-[var(--text-main)]">
        <slot></slot>
      </div>
      
      <!-- Footer -->
      <div v-if="$slots.footer" class="p-6 border-t border-[var(--border-subtle)] shrink-0 bg-[#0c101a]">
        <slot name="footer"></slot>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: boolean
  title: string
  size?: string | number
}>()

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})
</script>

<style>
.geo-detail-panel .el-drawer__body {
  padding: 0 !important;
  background-color: transparent !important;
}
</style>
