import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'
import { queryClient } from './app/queryClient'

// Global styles
import 'element-plus/theme-chalk/dark/css-vars.css' // Element Plus Dark Theme
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import './style.css' // Tailwind & Global CSS Tokens

import router from './router'
import App from './App.vue'

const app = createApp(App)

app.use(createPinia())
app.use(VueQueryPlugin, { queryClient })
app.use(router)

// Set element plus dark mode explicitly to html tag
document.documentElement.classList.add('dark')

app.mount('#app')
