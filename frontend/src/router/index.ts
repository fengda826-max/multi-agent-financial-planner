import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import RiskAssessment from '../views/RiskAssessment.vue'
import StrategyResult from '../views/StrategyResult.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard
    },
    {
      path: '/risk-assessment',
      name: 'RiskAssessment',
      component: RiskAssessment
    },
    {
      path: '/strategy-result',
      name: 'StrategyResult',
      component: StrategyResult
    },
    {
      path: '/',
      redirect: '/login'
    }
  ]
})

export default router
