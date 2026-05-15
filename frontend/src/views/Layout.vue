<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-left">
        <span class="logo">🏦</span>
        <span class="app-name">智能理财规划</span>
      </div>
      <nav class="header-nav">
        <router-link to="/dashboard" class="nav-item" active-class="nav-active">
          <span class="nav-icon">🏠</span>
          <span>首页</span>
        </router-link>
        <router-link to="/my-plan" class="nav-item" active-class="nav-active">
          <span class="nav-icon">📊</span>
          <span>我的方案</span>
        </router-link>
        <router-link to="/ai-chat" class="nav-item" active-class="nav-active">
          <span class="nav-icon">💬</span>
          <span>AI助手</span>
        </router-link>
        <router-link to="/market" class="nav-item" active-class="nav-active">
          <span class="nav-icon">📈</span>
          <span>市场观察</span>
        </router-link>
        <router-link to="/profile" class="nav-item" active-class="nav-active">
          <span class="nav-icon">👤</span>
          <span>我的</span>
        </router-link>
      </nav>
      <div class="header-right">
        <el-button link type="danger" @click="handleLogout">退出</el-button>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user_id')
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: #f5f7fa;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 24px;
  height: 60px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo { font-size: 24px; }

.app-name {
  font-size: 17px;
  font-weight: 600;
  color: #1e293b;
}

.header-nav {
  display: flex;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: #64748b;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.nav-active {
  background: #eff6ff;
  color: #3b82f6;
  font-weight: 500;
}

.nav-icon { font-size: 16px; }

.header-right {
  display: flex;
  align-items: center;
}

.app-main {
  max-width: 1280px;
  margin: 0 auto;
  min-height: calc(100vh - 60px);
}
</style>
