<template>
  <div><div class="page-hero"><h1 class="page-title">任务调度</h1><p class="page-sub">创建定时任务 · 配置生成节奏与发布策略</p></div>
    <n-space style="margin-bottom:16px"><n-button type="primary" size="small">新建任务</n-button></n-space>
    <n-data-table :columns="cols" :data="data" size="small" :bordered="false" />
  </div>
</template>
<script setup lang="ts">
import { h } from 'vue'
import { NDataTable, NButton, NTag, NSpace } from 'naive-ui'
const cols = [
  { title:'任务', key:'name' },{ title:'调度', key:'schedule' },{ title:'日产量', key:'limit' },
  { title:'状态', key:'status', render:(r:any)=>h(NTag,{type:r.status==='运行中'?'success':'warning',size:'small'},{default:()=>r.status}) },
  { title:'上次运行', key:'last' },
  { title:'操作', key:'action', render:()=>h(NSpace,{size:'small'},()=>[h(NButton,{size:'tiny',quaternary:true},()=>'暂停'),h(NButton,{size:'tiny',quaternary:true},()=>'编辑')]) },
]
const data = [
  { name:'关键词消费生产', schedule:'持续运行', limit:'3篇/天', status:'运行中', last:'05-06 10:30' },
  { name:'低分文章修复', schedule:'每小时', limit:'—', status:'运行中', last:'05-06 10:00' },
  { name:'AI 平台探测', schedule:'每天 20:00', limit:'10次', status:'已暂停', last:'—' },
  { name:'官网 HTML 导出', schedule:'每天 06:00', limit:'5篇/天', status:'运行中', last:'05-06 06:00' },
]
</script>
