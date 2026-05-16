<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <div class="brand-mark">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect width="28" height="28" rx="8" fill="url(#brand-grad)"/>
              <path d="M8 18V12l6-4 6 4v6l-6 3.5L8 18z" fill="white" opacity="0.95"/>
              <circle cx="14" cy="14" r="3" fill="#C8956C"/>
              <defs>
                <linearGradient id="brand-grad" x1="0" y1="0" x2="28" y2="28">
                  <stop offset="0%" stop-color="#1a3a5c"/>
                  <stop offset="100%" stop-color="#0F2247"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span class="app-name">智财</span>
        </div>
        <nav class="header-nav">
          <router-link to="/dashboard" class="nav-item" active-class="nav-active">
            <span class="nav-icon">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="1" y="1" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="10" y="1" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="1" y="10" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="10" y="10" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.4"/></svg>
            </span>
            <span>首页</span>
          </router-link>
          <router-link to="/my-plan" class="nav-item" active-class="nav-active">
            <span class="nav-icon">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="3.5" stroke="currentColor" stroke-width="1.4"/><circle cx="9" cy="6" r="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M9 7.5V3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M12.5 9.5L9 7.5 5.5 9.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
            <span>方案</span>
          </router-link>
          <router-link to="/ai-chat" class="nav-item" active-class="nav-active">
            <span class="nav-icon">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.4"/><circle cx="9" cy="9" r="2" fill="currentColor" opacity="0.3"/><path d="M9 4V6M9 12V14M4 9H6M12 9H14" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            </span>
            <span>AI</span>
          </router-link>
          <router-link to="/market" class="nav-item" active-class="nav-active">
            <span class="nav-icon">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="2" y="12" width="3" height="4" rx="0.5" fill="currentColor" opacity="0.5"/><rect x="7.5" y="6" width="3" height="10" rx="0.5" fill="currentColor" opacity="0.7"/><rect x="13" y="9" width="3" height="7" rx="0.5" fill="currentColor"/></svg>
            </span>
            <span>市场</span>
          </router-link>
          <router-link to="/profile" class="nav-item" active-class="nav-active">
            <span class="nav-icon">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="6" r="2.5" stroke="currentColor" stroke-width="1.4"/><path d="M3 15c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
            </span>
            <span>我的</span>
          </router-link>
        </nav>
        <div class="header-right">
          <el-button link class="logout-btn" @click="handleLogout">退出</el-button>
        </div>
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
  background: #f3f4f6;
}

.app-header {
  background: rgba(11, 30, 54, 0.97);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-mark { display: flex; align-items: center; }

.app-name {
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 0.5px;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.header-nav {
  display: flex;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: 8px;
  text-decoration: none;
  color: rgba(255,255,255,0.55);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  position: relative;
}

.nav-item:hover {
  color: rgba(255,255,255,0.9);
  background: rgba(255,255,255,0.06);
}

.nav-active {
  color: #fff;
  background: rgba(255,255,255,0.1);
}

.nav-active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background: #C8956C;
  border-radius: 1px;
}

.nav-icon {
  display: flex;
  align-items: center;
  color: inherit;
}

.header-right {
  display: flex;
  align-items: center;
}

.logout-btn {
  color: rgba(255,255,255,0.4) !important;
  font-size: 13px;
  transition: color 0.2s;
}

.logout-btn:hover {
  color: rgba(255,255,255,0.8) !important;
}

.app-main {
  max-width: 1280px;
  margin: 0 auto;
  min-height: calc(100vh - 56px);
  padding-top: 4px;
}
</style>
