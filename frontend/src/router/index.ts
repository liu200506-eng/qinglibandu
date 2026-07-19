import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/layout/MainLayout.vue'

const LearningFlowView = () => import('@/views/LearningFlowView.vue')
const ProfileView = () => import('@/views/ProfileView.vue')
const PlanningView = () => import('@/views/PlanningView.vue')
const ResourceView = () => import('@/views/ResourceView.vue')
const TutoringView = () => import('@/views/TutoringView.vue')
const FeedbackView = () => import('@/views/FeedbackView.vue')
const WorkflowView = () => import('@/views/WorkflowView.vue')
const RAGView = () => import('@/views/RAGView.vue')
const LoginView = () => import('@/views/LoginView.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: Layout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'learning-flow', component: LearningFlowView },
        { path: 'profile', name: 'profile', component: ProfileView },
        { path: 'planning', name: 'planning', component: PlanningView },
        { path: 'resources', name: 'resources', component: ResourceView },
        { path: 'tutoring', name: 'tutoring', component: TutoringView },
        { path: 'feedback', name: 'feedback', component: FeedbackView },
        { path: 'workflow', name: 'workflow', component: WorkflowView },
        { path: 'knowledge', name: 'knowledge', component: RAGView }
      ]
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)

  if (requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
