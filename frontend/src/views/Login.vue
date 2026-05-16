<template>
  <div class="login-container">
    <div class="login-bg">
      <div class="bg-gradient-layer"></div>
      <div class="bg-grid-layer"></div>
    </div>
    <div class="login-card-wrapper">
      <div class="login-card">
        <div class="card-header">
          <div class="brand-mark">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <rect width="36" height="36" rx="10" fill="url(#login-grad)"/>
              <path d="M10 23V15l8-5.5 8 5.5v8l-8 5L10 23z" fill="white" opacity="0.9"/>
              <circle cx="18" cy="18" r="4" fill="#C8956C"/>
              <defs>
                <linearGradient id="login-grad" x1="0" y1="0" x2="36" y2="36">
                  <stop offset="0%" stop-color="#1a3a5c"/>
                  <stop offset="100%" stop-color="#0F2247"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h2>智财</h2>
          <p class="subtitle">智能理财规划系统</p>
        </div>
        <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
          <el-form-item>
            <el-input
              v-model="form.username"
              placeholder="用户名"
              size="large"
              :prefix-icon="UserFilled"
            />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        <div class="card-footer">
          <span class="footer-text">还没有账号？</span>
          <el-button link type="primary" class="register-link" @click="$router.push('/register')">
            立即注册
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '../api/client'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const UserFilled = 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="5" r="3" stroke="#94a3b8" stroke-width="1.3"/><path d="M2 14c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="#94a3b8" stroke-width="1.3" stroke-linecap="round"/></svg>')
const Lock = 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="3.5" y="7" width="9" height="7" rx="1.3" stroke="#94a3b8" stroke-width="1.3"/><path d="M5.5 7V4.5a2.5 2.5 0 015 0V7" stroke="#94a3b8" stroke-width="1.3" stroke-linecap="round"/></svg>')

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await authAPI.login(form.value)
    localStorage.setItem('token', result.access_token)
    localStorage.setItem('user_id', result.user_id)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
}

.bg-gradient-layer {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0b1e36 0%, #152238 30%, #1a2744 60%, #0F2247 100%);
}

.bg-grid-layer {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 70%);
}

.login-card-wrapper {
  position: relative;
  z-index: 1;
  width: 400px;
}

.login-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 44px 36px 32px;
  box-shadow: 0 25px 60px rgba(0,0,0,0.3);
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.brand-mark { display: flex; justify-content: center; margin-bottom: 16px; }

.card-header h2 {
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 28px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0 0 4px 0;
  letter-spacing: 1px;
}

.subtitle {
  font-size: 13px;
  color: rgba(255,255,255,0.35);
  margin: 0;
  letter-spacing: 1px;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  box-shadow: none;
  transition: all 0.3s;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(255,255,255,0.15);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(200, 150, 108, 0.4);
  box-shadow: 0 0 0 3px rgba(200, 150, 108, 0.08);
}

.login-form :deep(.el-input__inner) {
  color: #e2e8f0;
  font-size: 14px;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(255,255,255,0.25);
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #C8956C 0%, #B07D55 100%) !important;
  border: none !important;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
  transition: all 0.3s;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 25px rgba(200, 150, 108, 0.3);
}

.card-footer {
  text-align: center;
  margin-top: 8px;
}

.footer-text {
  font-size: 13px;
  color: rgba(255,255,255,0.3);
}

.register-link {
  font-size: 13px;
  color: #C8956C !important;
  font-weight: 500;
}
</style>
