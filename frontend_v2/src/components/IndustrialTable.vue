<template>
  <div class="geo-industrial-table w-full">
    <el-table
      v-bind="$attrs"
      :data="data"
      class="w-full"
      header-row-class-name="geo-table-header"
      row-class-name="geo-table-row"
    >
      <slot></slot>
      <template #empty>
        <div class="py-12 flex flex-col items-center justify-center text-[var(--text-muted)]">
          <slot name="empty">暂无数据</slot>
        </div>
      </template>
    </el-table>
    <div v-if="pagination" class="mt-4 flex justify-end">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        background
        @current-change="$emit('page-change', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  data: any[]
  pagination?: boolean
  total?: number
  defaultPageSize?: number
}>()

const emit = defineEmits(['page-change'])
const currentPage = ref(1)
const pageSize = ref(props.defaultPageSize || 10)

watch(currentPage, (val) => {
  emit('page-change', val)
})
</script>

<style>
.geo-industrial-table .el-table {
  background-color: transparent !important;
  --el-table-border-color: var(--border-subtle);
  --el-table-header-bg-color: rgba(0, 0, 0, 0.2);
  --el-table-header-text-color: var(--text-muted);
  --el-table-text-color: var(--text-main);
  --el-table-row-hover-bg-color: var(--bg-panel-hover);
  --el-table-tr-bg-color: transparent;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
}

.geo-industrial-table .el-table th.el-table__cell.is-leaf {
  border-bottom: 1px solid var(--border-subtle);
  font-weight: 500;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 10px 0;
}

.geo-industrial-table .el-table td.el-table__cell {
  border-bottom: 1px solid var(--border-subtle);
  padding: 12px 0;
  font-size: 13px;
  transition: background-color 0.2s;
}

.geo-industrial-table .el-table__inner-wrapper::before {
  display: none;
}

/* Pagination Overrides */
.geo-industrial-table .el-pagination.is-background .el-pager li:not(.is-disabled).is-active {
  background-color: var(--color-primary);
  color: var(--text-main);
  border: none;
}
.geo-industrial-table .el-pagination.is-background .btn-next, 
.geo-industrial-table .el-pagination.is-background .btn-prev, 
.geo-industrial-table .el-pagination.is-background .el-pager li {
  background-color: var(--bg-panel);
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
}
.geo-industrial-table .el-pagination.is-background .el-pager li:hover {
  color: var(--text-main);
  border-color: var(--border-focus);
}
</style>
