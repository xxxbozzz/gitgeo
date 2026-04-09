import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig({
  base: '/console/',
  plugins: [
    vue(),
    Components({
      dts: 'src/components.d.ts',
      resolvers: [ElementPlusResolver({ importStyle: 'css' })],
    }),
    tailwindcss(),
  ],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return
          }

          if (
            id.includes('/node_modules/vue/') ||
            id.includes('vue-router') ||
            id.includes('pinia') ||
            id.includes('@tanstack/vue-query')
          ) {
            return 'vue-core'
          }

          if (id.includes('echarts') || id.includes('zrender')) {
            return 'echarts'
          }

          if (id.includes('lucide-vue-next')) {
            return 'lucide'
          }

          if (id.includes('axios')) {
            return 'network'
          }
        },
      },
    },
  },
})
