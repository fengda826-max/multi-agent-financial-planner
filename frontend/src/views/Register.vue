<template>
  <div class="register-container">
    <div class="register-bg">
      <div class="bg-gradient-layer"></div>
      <div class="bg-grid-layer"></div>
    </div>
    <div class="register-card-wrapper">
      <div class="register-card">
        <div class="card-header">
          <h2>创建账号</h2>
          <p class="subtitle">开始你的智能理财之旅</p>
        </div>
        <el-form :model="form" :rules="rules" ref="formRef" class="register-form">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" size="large" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱（选填）" size="large" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" size="large" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" class="register-btn" :loading="loading" @click="handleRegister">
              注册
            </el-button>
          </el-form-item>
        </el-form>
        <div class="card-footer">
          <span class="footer-text">已有账号？</span>
          <el-button link class="login-link" @click="$router.push('/login')">立即登录</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { authAPI } from '../api/client'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })

const validateConfirm = (_rule: any, value: string, callback: any) => {
  callback(value !== form.password ? new Error('两次密码不一致') : undefined)
}

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 3, max: 20, message: '3-20位', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '至少6位', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请确认密码', trigger: 'blur' }, { validator: validateConfirm, trigger: 'blur' }]
}

const handleRegister = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authAPI.register({ username: form.username, password: form.password, email: form.email || undefined })
      ElMessage.success('注册成功')
      router.push('/login')
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '注册失败')
    } finally { loading.value = false }
  })
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.register-bg { position: absolute; inset: 0; }
.bg-gradient-layer {
  position: absolute; inset: 0;
  background: linear-gradient(135deg, #0b1e36 0%, #152238 30%, #1a2744 60%, #0F2247 100%);
}
.bg-grid-layer {
  position: absolute; inset: 0;
  background-image: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 70%);
}
.register-card-wrapper { position: relative; z-index: 1; width: 400px; }
.register-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 40px 36px 28px;
  box-shadow: 0 25px 60px rgba(0,0,0,0.3);
}
.card-header { text-align: center; margin-bottom: 28px; }
.card-header h2 {
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 26px; font-weight: 700; color: #f1f5f9; margin: 0 0 4px; letter-spacing: 1px;
}
.subtitle { font-size: 13px; color: rgba(255,255,255,0.35); margin: 0; }
.register-form :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; box-shadow: none; transition: all 0.3s;
}
.register-form :deep(.el-input__wrapper:hover) { border-color: rgba(255,255,255,0.15); }
.register-form :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(200,150,108,0.4);
  box-shadow: 0 0 0 3px rgba(200,150,108,0.08);
}
.register-form :deep(.el-input__inner) { color: #e2e8f0; font-size: 14px; }
.register-form :deep(.el-input__inner::placeholder) { color: rgba(255,255,255,0.25); }
.register-btn {
  width: 100%; height: 44px; border-radius: 12px;
  background: linear-gradient(135deg, #C8956C 0%, #B07D55 100%) !important;
  border: none !important;
  font-size: 15px; font-weight: 600; letter-spacing: 0.5px; transition: all 0.3s;
}
.register-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 25px rgba(200,150,108,0.3); }
.card-footer { text-align: center; margin-top: 6px; }
.footer-text { font-size: 13px; color: rgba(255,255,255,0.3); }
.login-link { font-size: 13px; color: #C8956C !important; font-weight: 500; }
</style>
