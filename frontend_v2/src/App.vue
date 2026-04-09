<template>
  <el-config-provider :size="'default'" :z-index="3000">
    <router-view></router-view>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ElConfigProvider } from 'element-plus'
</script>
