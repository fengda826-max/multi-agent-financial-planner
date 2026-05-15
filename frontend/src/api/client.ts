import axios from 'axios'
import type {
  UserResponse,
  LoginResponse,
  RiskProfileResponse,
  OrchestratorStatusResponse,
} from './types'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient

export const authAPI = {
  register: (data: { username: string; password: string; email?: string }) =>
    apiClient.post('/auth/register', data) as Promise<UserResponse>,
  login: (data: { username: string; password: string }) =>
    apiClient.post('/auth/login', data) as Promise<LoginResponse>,
}

export const userAPI = {
  getMe: () => apiClient.get('/users/me') as Promise<UserResponse>,
}

export const riskAssessmentAPI = {
  submit: (data: { age: number; income: number; expenses: number; risk_tolerance: string; investment_horizon: string }) =>
    apiClient.post('/risk-assessment/', data),
  getMyProfile: () => apiClient.get('/risk-assessment/my-profile') as Promise<RiskProfileResponse>,
}

export const orchestratorAPI = {
  start: (data: { user_id: string; risk_assessment: any }) =>
    apiClient.post('/orchestrator/start', data, { timeout: 180000 }),
  getStatus: (userId: string) =>
    apiClient.get(`/orchestrator/status/${userId}`) as Promise<OrchestratorStatusResponse>,
  replan: (data: { user_id: string; trigger: string; trigger_detail: string; replan_from: string }) =>
    apiClient.post('/orchestrator/replan', data, { timeout: 180000 }),
}
