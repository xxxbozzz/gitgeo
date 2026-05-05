<template>
  <div class="geo-page">
    <div class="hero">
      <h1>素材库</h1>
      <p>管理标题库、关键词库、图片库、作者信息和知识库文档</p>
    </div>

    <!-- Tabs for sub-categories -->
    <el-tabs v-model="activeTab" class="mt-6">
      <el-tab-pane label="关键词" name="keywords">
        <KeywordsPanel />
      </el-tab-pane>
      <el-tab-pane label="标题库" name="titles">
        <TitlesPanel />
      </el-tab-pane>
      <el-tab-pane label="图片库" name="images">
        <ImagesPanel />
      </el-tab-pane>
      <el-tab-pane label="作者库" name="authors">
        <AuthorsPanel />
      </el-tab-pane>
      <el-tab-pane label="知识库" name="knowledge">
        <KnowledgePanel />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import KeywordsPanel from './KeywordsPanel.vue'
import TitlesPanel from './TitlesPanel.vue'
import ImagesPanel from './ImagesPanel.vue'
import AuthorsPanel from './AuthorsPanel.vue'
import KnowledgePanel from './KnowledgePanel.vue'

const activeTab = ref('keywords')
</script>
