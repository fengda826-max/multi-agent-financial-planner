import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import RiskAssessment from '../views/RiskAssessment.vue'
import StrategyResult from '../views/StrategyResult.vue'

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
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard,
      meta: { auth: true }
    },
    {
      path: '/risk-assessment',
      name: 'RiskAssessment',
      component: RiskAssessment,
      meta: { auth: true }
    },
    {
      path: '/strategy-result',
      name: 'StrategyResult',
      component: StrategyResult,
      meta: { auth: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
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
