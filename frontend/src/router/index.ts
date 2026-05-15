import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../views/Layout.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import RiskAssessment from '../views/RiskAssessment.vue'
import StrategyResult from '../views/StrategyResult.vue'
import MyPlan from '../views/MyPlan.vue'
import AIChat from '../views/AIChat.vue'
import Market from '../views/Market.vue'
import Profile from '../views/Profile.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: Register,
      meta: { guest: true }
    },
    {
      path: '/',
      component: Layout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: Dashboard,
          meta: { auth: true }
        },
        {
          path: 'my-plan',
          name: 'MyPlan',
          component: MyPlan,
          meta: { auth: true }
        },
        {
          path: 'risk-assessment',
          name: 'RiskAssessment',
          component: RiskAssessment,
          meta: { auth: true }
        },
        {
          path: 'strategy-result',
          name: 'StrategyResult',
          component: StrategyResult,
          meta: { auth: true }
        },
        {
          path: 'ai-chat',
          name: 'AIChat',
          component: AIChat,
          meta: { auth: true }
        },
        {
          path: 'market',
          name: 'Market',
          component: Market,
          meta: { auth: true }
        },
        {
          path: 'profile',
          name: 'Profile',
          component: Profile,
          meta: { auth: true }
        }
      ]
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.auth && !token) {
    return next('/login')
  }

  if (to.meta.guest && token) {
    return next('/dashboard')
  }

  next()
})

export default router
