import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const darkMode = ref(false)
  const sidebarCollapsed = ref(false)

  function toggleDark() { darkMode.value = !darkMode.value }
  function toggleSidebar() { sidebarCollapsed.value = !sidebarCollapsed.value }

  return { darkMode, sidebarCollapsed, toggleDark, toggleSidebar }
})
