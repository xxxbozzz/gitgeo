<template>
  <div><div class="page-hero"><h1 class="page-title">素材库</h1><p class="page-sub">管理标题、关键词、图片、作者与知识库</p></div>
    <n-tabs type="line" animated>
      <n-tab-pane name="keywords" tab="关键词"><n-space vertical><n-button type="primary" size="small">添加关键词</n-button>
        <n-data-table :columns="kwCols" :data="kwData" :bordered="false" size="small" /></n-space></n-tab-pane>
      <n-tab-pane name="titles" tab="标题库"><n-button type="primary" size="small" style="margin-bottom:12px">添加标题</n-button>
        <n-data-table :columns="tCols" :data="tData" size="small" /></n-tab-pane>
      <n-tab-pane name="images" tab="图片库"><n-button type="primary" size="small" style="margin-bottom:12px">上传图片</n-button>
        <n-grid :cols="4" :x-gap="12" :y-gap="12"><n-gi v-for="i in 4" :key="i"><n-card size="small"><div style="height:100px;background:var(--n-color-target);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:2rem">🖼</div><div style="font-size:0.78rem;margin-top:6px;text-align:center">workshop-0{{i}}.jpg</div></n-card></n-gi></n-grid></n-tab-pane>
      <n-tab-pane name="authors" tab="作者库"><n-button type="primary" size="small" style="margin-bottom:12px">添加作者</n-button>
        <n-data-table :columns="aCols" :data="aData" size="small" /></n-tab-pane>
      <n-tab-pane name="knowledge" tab="知识库"><n-button type="primary" size="small" style="margin-bottom:12px">上传文档</n-button>
        <n-data-table :columns="kbCols" :data="kbData" size="small" /></n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { NTabs, NTabPane, NButton, NDataTable, NSpace, NCard, NGrid, NGi, NTag } from 'naive-ui'

const kwCols = [{ title:'关键词', key:'kw' },{ title:'搜索量', key:'vol' },{ title:'难度', key:'diff', render:(r:any)=>h(NTag,{type:r.diff>50?'warning':'success',size:'small'},{default:()=>r.diff}) },{ title:'状态', key:'status' }]
const kwData = [{ kw:'ENIG沉金工艺标准', vol:2800, diff:65, status:'已消费' },{ kw:'HDI盲孔最小孔径', vol:1200, diff:45, status:'待处理' },{ kw:'PCB阻抗控制计算', vol:850, diff:30, status:'待处理' }]
const tCols = [{ title:'标题模板', key:'t' },{ title:'分类', key:'c' },{ title:'使用次数', key:'n' }]
const tData = [{ t:'{{keyword}}技术深度解析', c:'技术动态', n:45 },{ t:'{{keyword}}怎么选？', c:'行业资讯', n:23 }]
const aCols = [{ title:'姓名', key:'n' },{ title:'简介', key:'b' }]
const aData = [{ n:'GEO 编辑部', b:'AI 搜索引擎优化内容团队' }]
const kbCols = [{ title:'文档', key:'n' },{ title:'切片数', key:'c' },{ title:'向量化', key:'e', render:(r:any)=>h(NTag,{type:r.e?'success':'warning',size:'small'},{default:()=>r.e?'已完成':'待处理'}) }]
const kbData = [{ n:'行业标准规范合集.pdf', c:48, e:true },{ n:'品牌能力手册_v3.pdf', c:32, e:true }]
</script>
