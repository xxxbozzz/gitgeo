import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'), // To be implemented in Phase 2
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/index.vue'),
      },
      {
        path: 'runs',
        name: 'Runs',
        component: () => import('../views/runs/index.vue'),
      },
      {
        path: 'articles',
        name: 'Articles',
        component: () => import('../views/articles/index.vue'),
      },
      {
        path: 'publications',
        name: 'Publications',
        component: () => import('../views/publications/index.vue'),
      },
      {
        path: 'system',
        name: 'System',
        component: () => import('../views/system/index.vue'),
      },
      // Management pages
      {
        path: 'materials',
        name: 'Materials',
        component: () => import('../views/materials/index.vue'),
      },
      {
        path: 'prompts',
        name: 'Prompts',
        component: () => import('../views/prompts/index.vue'),
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('../views/models/index.vue'),
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('../views/tasks/index.vue'),
      },
      // Content operations
      {
        path: 'keywords',
        name: 'Keywords',
        component: () => import('../views/keywords/index.vue'),
      },
      {
        path: 'capabilities',
        name: 'Capabilities',
        component: () => import('../views/capabilities/index.vue'),
      },
      {
        path: 'graph',
        name: 'Graph',
        component: () => import('../views/graph/index.vue'),
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
