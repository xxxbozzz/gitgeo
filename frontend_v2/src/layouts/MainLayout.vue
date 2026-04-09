<template>
  <el-container class="h-screen w-full bg-[var(--bg-dark)] text-[var(--text-main)] overflow-hidden">
    <!-- Desktop Sidebar -->
    <el-aside width="220px" class="bg-[var(--bg-panel)] border-r border-[var(--border-subtle)] flex-col hidden md:flex shrink-0">
      <div class="h-16 flex items-center px-6 cursor-pointer">
        <div class="w-5 h-5 bg-[var(--color-primary)] rounded-sm mr-3 flex items-center justify-center">
          <Monitor class="w-3 h-3 text-white" />
        </div>
        <span class="text-base font-bold tracking-wide">GEO 控制台</span>
      </div>

      <div class="px-6 pb-4">
        <span class="text-[11px] text-[var(--text-muted)]">v5.0 · Generic Edition</span>
      </div>

      <div class="flex-1 overflow-y-auto w-full custom-scrollbar">
        <MenuContent />
      </div>

      <div class="h-14 flex flex-col justify-center px-6 border-t border-[var(--border-subtle)] shrink-0">
        <span class="text-xs text-[var(--text-muted)]">© 2026 GEO Engine</span>
        <a
          :href="openSourceWatermarkUrl"
          target="_blank"
          rel="noreferrer"
          class="text-[11px] text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors"
        >
          {{ openSourceWatermark }}
        </a>
      </div>
    </el-aside>

    <!-- Mobile Drawer Sidebar -->
    <el-drawer
      v-model="mobileMenuOpen"
      direction="ltr"
      size="240px"
      :with-header="false"
      class="geo-mobile-drawer"
    >
      <div class="bg-[var(--bg-panel)] h-full flex flex-col pt-4">
         <div class="h-12 flex items-center px-6 mb-2">
          <div class="w-5 h-5 bg-[var(--color-primary)] rounded-sm mr-3 flex items-center justify-center">
            <Monitor class="w-3 h-3 text-white" />
          </div>
          <span class="text-base font-bold tracking-wide text-[var(--text-main)]">GEO 控制台</span>
        </div>
        <div class="flex-1 overflow-y-auto px-1 custom-scrollbar">
          <MenuContent @navigated="mobileMenuOpen = false" />
        </div>
      </div>
    </el-drawer>

    <!-- Main Content Area -->
    <el-container class="flex-col min-w-0">
      <!-- Mobile Header Fallback -->
      <div class="md:hidden h-14 bg-[var(--bg-panel)] border-b border-[var(--border-subtle)] flex items-center justify-between px-4 shrink-0">
        <div class="flex items-center">
          <div class="w-5 h-5 bg-[var(--color-primary)] rounded-sm mr-2 flex items-center justify-center">
            <Monitor class="w-3 h-3 text-white" />
          </div>
          <span class="text-sm font-bold tracking-wide">GEO 控制台</span>
        </div>
        <button @click="mobileMenuOpen = true" class="text-[var(--text-muted)] hover:text-[var(--text-main)] p-1 rounded transition-colors">
          <Menu class="w-6 h-6" />
        </button>
      </div>

      <el-main class="p-0 bg-[var(--bg-dark)] h-full relative">
        <div
          ref="scrollContainerRef"
          class="absolute inset-0 overflow-y-auto px-4 py-4 md:px-8 md:py-6 custom-scrollbar flex flex-col"
        >
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Monitor, Menu } from 'lucide-vue-next'
import MenuContent from './MenuContent.vue'

const mobileMenuOpen = ref(false)
const scrollContainerRef = ref<HTMLDivElement | null>(null)
const route = useRoute()
const openSourceWatermark = import.meta.env.VITE_OPEN_SOURCE_WATERMARK || 'Open Source Edition · github.com/xxxbozzz'
const openSourceWatermarkUrl = import.meta.env.VITE_OPEN_SOURCE_WATERMARK_URL || 'https://github.com/xxxbozzz'

function resetContentScroll() {
  scrollContainerRef.value?.scrollTo({
    top: 0,
    behavior: 'auto',
  })
}

watch(
  () => route.path,
  async () => {
    await nextTick()
    resetContentScroll()
  },
)

onMounted(() => {
  resetContentScroll()
})
</script>

<style>
/* Global overrides for element-plus drawer to act as sidebar */
.geo-mobile-drawer .el-drawer__body {
  padding: 0 !important;
  background-color: var(--bg-panel) !important;
}
</style>

<style scoped>
/* Custom scrollbar to keep layout clean */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Page Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
