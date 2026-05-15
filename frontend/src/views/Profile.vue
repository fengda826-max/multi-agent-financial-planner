<template>
  <div class="profile-container">
    <h2>👤 我的</h2>

    <!-- 个人信息卡片 -->
    <el-card class="info-card">
      <div class="user-info" v-if="userData">
        <div class="avatar">👤</div>
        <div class="user-details">
          <div class="user-name">{{ userData.username }}</div>
          <div class="user-meta">注册时间：{{ formatDate(userData.created_at) }}</div>
          <div class="user-meta" v-if="userData.email">邮箱：{{ userData.email }}</div>
        </div>
      </div>
    </el-card>

    <!-- 风险等级 -->
    <el-card class="section-card">
      <template #header>
        <span>📋 风险测评</span>
      </template>
      <template v-if="profileData?.has_assessment">
        <div class="info-row">
          <span class="info-label">风险等级</span>
          <el-tag :type="riskTagType">{{ riskLabel }}</el-tag>
        </div>
        <div class="info-row">
          <span class="info-label">测评评分</span>
          <span class="info-value">{{ profileData.latest_assessment?.score }} 分</span>
        </div>
        <div class="info-row">
          <span class="info-label">测评时间</span>
          <span class="info-value">{{ formatDate(profileData.latest_assessment?.assessed_at) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">生命周期</span>
          <span class="info-value">{{ lifecycleLabel }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">可投资资产</span>
          <span class="info-value">¥{{ formatMoney(profileData.profile?.investable_assets) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">月结余</span>
          <span class="info-value">¥{{ formatMoney(profileData.profile?.monthly_surplus) }}</span>
        </div>
      </template>
      <template v-else>
        <div class="no-data">尚未完成风险测评</div>
      </template>
      <div class="section-action">
        <el-button type="primary" @click="$router.push('/risk-assessment')">🔄 重新测评</el-button>
      </div>
    </el-card>

    <!-- 历史方案 -->
    <el-card class="section-card">
      <template #header>
        <span>📜 配置方案</span>
      </template>
      <template v-if="hasStrategy">
        <div class="info-row">
          <span class="info-label">方案状态</span>
          <el-tag type="success">运行中</el-tag>
        </div>
        <div class="info-row">
          <span class="info-label">生成时间</span>
          <span class="info-value">{{ profileData.latest_assessment?.assessed_at ? formatDate(profileData.latest_assessment.assessed_at) : '-' }}</span>
        </div>
      </template>
      <template v-else>
        <div class="no-data">暂无方案记录</div>
      </template>
      <div class="section-action">
        <el-button @click="$router.push('/my-plan')">📊 查看方案</el-button>
      </div>
    </el-card>

    <!-- 退出登录 -->
    <el-card class="section-card">
      <el-button type="danger" @click="handleLogout" style="width:100%">退出登录</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userAPI, riskAssessmentAPI, orchestratorAPI } from '../api/client'

const router = useRouter()
const userData = ref<any>(null)
const profileData = ref<any>(null)
const hasStrategy = ref(false)

const riskLabel = computed(() => {
  const map: Record<string, string> = { conservative: '保守型', low: '保守型', moderate: '稳健型', medium: '稳健型', aggressive: '进取型', high: '进取型' }
  return map[profileData.value?.profile?.risk_capacity] || map[profileData.value?.latest_assessment?.risk_level] || '-'
})

const riskTagType = computed(() => {
  const level = profileData.value?.latest_assessment?.risk_level || profileData.value?.profile?.risk_capacity
  if (level === 'aggressive' || level === 'high') return 'warning'
  if (level === 'moderate' || level === 'medium') return ''
  return 'success'
})

const lifecycleLabel = computed(() => {
  const map: Record<string, string> = { accumulation: '积累期', consolidation: '巩固期', distribution: '分配期' }
  return map[profileData.value?.profile?.lifecycle_stage] || '-'
})

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function formatMoney(val: number | undefined | null): string {
  if (!val) return '0'
  if (val >= 10000) return (val / 10000).toFixed(1) + '万'
  return val.toLocaleString()
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user_id')
  router.push('/login')
}

onMounted(async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  try {
    const [user, profile] = await Promise.all([
      userAPI.getMe(),
      riskAssessmentAPI.getMyProfile()
    ])
    userData.value = user
    profileData.value = profile

    // Check for strategy
    try {
      const status = await orchestratorAPI.getStatus(userId)
      hasStrategy.value = !!status.strategy
    } catch { /* no strategy */ }
  } catch { /* ignore */ }
})
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-container h2 {
  color: #1e293b;
  margin-bottom: 20px;
}

.info-card {
  margin-bottom: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.user-meta {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 2px;
}

.section-card {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 15px;
  color: #64748b;
}

.info-value {
  font-size: 15px;
  color: #1e293b;
  font-weight: 500;
}

.no-data {
  text-align: center;
  padding: 30px;
  color: #94a3b8;
  font-size: 15px;
}

.section-action {
  padding-top: 12px;
  text-align: center;
}
</style>
