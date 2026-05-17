<template>
  <div class="dashboard-container">
    <!-- 空状态：未开始测评 -->
    <el-card v-if="!hasPlan" class="empty-card">
      <div class="empty-state">
        <div class="empty-icon">📊</div>
        <h2>开始您的专属理财规划</h2>
        <p>完成风险测评，AI 将为您生成个性化的"四笔钱"资产配置方案</p>
        <el-button type="primary" size="large" @click="$router.push('/risk-assessment')">
          立即测评
        </el-button>
      </div>
    </el-card>

    <!-- 有数据状态 -->
    <template v-else>
      <!-- 问候 + 健康分 -->
      <div class="greeting-row">
        <div>
          <h2>👋 你好，{{ userName }}</h2>
          <p class="update-time">上次更新：{{ lastUpdateTime }}</p>
        </div>
        <div class="health-score">
          <el-popover placement="bottom" :width="280" trigger="hover" :show-after="300">
            <template #reference>
              <div class="score-circle clickable">
                <span class="score-num">{{ healthScore }}</span>
                <span class="score-label">理财健康分 🟡</span>
              </div>
            </template>
            <div v-if="healthBreakdown.savings" class="breakdown">
              <div class="bd-item" v-for="item in [
                { key: 'savings', icon: '💰' },
                { key: 'emergency', icon: '🏦' },
                { key: 'investment', icon: '📈' },
                { key: 'protection', icon: '🛡️' }
              ]" :key="item.key">
                <span class="bd-icon">{{ item.icon }}</span>
                <span class="bd-label">{{ healthBreakdown[item.key]?.label }}</span>
                <span class="bd-score">{{ healthBreakdown[item.key]?.score }}分</span>
                <span class="bd-detail">{{ healthBreakdown[item.key]?.detail }}</span>
              </div>
              <el-divider style="margin: 8px 0" />
              <div class="bd-note">🟡 推算值 — 基于用户输入和公式计算</div>
            </div>
            <div v-else class="breakdown">
              <p class="bd-note">暂未生成健康分详情。完成风险测评后生成。</p>
            </div>
          </el-popover>
        </div>
      </div>

      <!-- 4个指标卡片 -->
      <el-row :gutter="16" class="metrics-row">
        <el-col :span="6">
          <el-card class="metric-card" shadow="hover">
            <div class="metric-label">总资产</div>
            <div class="metric-value">¥{{ formatMoney(profile.investable_assets) }}</div>
            <div class="metric-desc">估算可投资资产</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card" shadow="hover">
            <div class="metric-label">月结余</div>
            <div class="metric-value">¥{{ formatMoney(profile.monthly_surplus) }}</div>
            <div class="metric-desc">月收入 - 月支出</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card" shadow="hover">
            <div class="metric-label">风险等级</div>
            <div class="metric-value risk-tag" :class="riskClass">
              {{ riskLabel }}
            </div>
            <div class="metric-desc">
              评分：{{ profile.latest_assessment?.score || '-' }} 分
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card" shadow="hover">
            <div class="metric-label">配置状态</div>
            <div class="metric-value status-active">运行中</div>
            <div class="metric-desc">下次检查：{{ nextReviewDate }}</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 资产配置 + 快捷入口 -->
      <el-row :gutter="16" class="content-row">
        <el-col :span="16">
          <el-card class="chart-card">
            <template #header>
              <span>资产配置分布</span>
            </template>
            <div ref="chartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="quick-actions-card">
            <template #header>
              <span>快捷操作</span>
            </template>
            <div class="quick-actions">
              <el-button type="primary" size="large" @click="goToPlan">
                📊 查看完整方案
              </el-button>
              <el-button size="large" @click="$router.push('/risk-assessment')">
                🔄 重新测评
              </el-button>
              <el-button size="large" @click="$router.push('/ai-chat')">
                💬 咨询AI助手
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <DisclaimerBar
      v-if="hasPlan"
      message="本页面数据基于AI分析和用户自报信息生成。资产金额为估算值。投资有风险，内容仅供参考。"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { userAPI, riskAssessmentAPI, orchestratorAPI } from '../api/client'
import DisclaimerBar from '../components/DisclaimerBar.vue'

const router = useRouter()

const userName = ref('')
const hasPlan = ref(false)
const profile = ref<any>({
  investable_assets: 0,
  monthly_surplus: 0,
  risk_capacity: 'medium',
  lifecycle_stage: '',
  latest_assessment: null
})
const strategy = ref<any>(null)
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const healthBreakdown = ref<Record<string, { score: number; label: string; detail: string }>>({})

const healthScore = computed(() => {
  const bd = healthBreakdown.value
  if (bd?.savings) {
    return bd.savings.score + bd.emergency.score + bd.investment.score + bd.protection.score
  }
  if (!profile.value.investable_assets) return 75
  const score = profile.value.latest_assessment?.score || 70
  return Math.min(Math.max(score, 50), 98)
})

const riskLabel = computed(() => {
  const map: Record<string, string> = { low: '保守型', medium: '稳健型', high: '进取型', conservative: '保守型', moderate: '稳健型', aggressive: '进取型' }
  return map[profile.value.risk_capacity] || '未测评'
})

const riskClass = computed(() => {
  const mapping: Record<string, string> = { low: 'risk-low', conservative: 'risk-low', medium: 'risk-medium', moderate: 'risk-medium', high: 'risk-high', aggressive: 'risk-high' }
  return mapping[profile.value.risk_capacity] || ''
})

const lastUpdateTime = computed(() => {
  if (!profile.value.latest_assessment?.assessed_at) return '未测评'
  const d = new Date(profile.value.latest_assessment.assessed_at)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

const nextReviewDate = computed(() => {
  if (!profile.value.latest_assessment?.assessed_at) return '请先生成方案'
  const d = new Date(profile.value.latest_assessment.assessed_at)
  d.setMonth(d.getMonth() + 3)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

function formatMoney(val: number | undefined | null): string {
  if (!val) return '0'
  if (val >= 10000) return (val / 10000).toFixed(1) + '万'
  return val.toLocaleString()
}

function goToPlan() {
  const userId = localStorage.getItem('user_id')
  if (userId) {
    router.push('/my-plan')
  }
}

function renderChart() {
  if (!chartRef.value || !strategy.value?.four_buckets) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const buckets = strategy.value.four_buckets
  const names: Record<string, string> = {
    living_money: '活钱',
    stable_money: '稳健',
    growth_money: '长期',
    protection_money: '保障'
  }
  const colors = ['#10B981', '#6366F1', '#F59E0B', '#EF4444']

  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const bucket = buckets[Object.keys(buckets)[params.dataIndex]]
        const products = bucket?.products?.join('、') || ''
        return `${params.name}: ${params.value}%<br/>推荐：${products}`
      }
    },
    legend: { bottom: 10 },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: {
        show: true,
        position: 'outside',
        formatter: '{b}\n{d}%'
      },
      emphasis: {
        label: { fontSize: 18, fontWeight: 'bold' }
      },
      data: Object.entries(buckets).map(([key, val]: [string, any], i) => ({
        value: Math.round(val.allocation * 100),
        name: names[key] || key,
        itemStyle: { color: colors[i] }
      }))
    }]
  })
}

onMounted(async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  try {
    const [userData, profileData] = await Promise.all([
      userAPI.getMe(),
      riskAssessmentAPI.getMyProfile()
    ])

    userName.value = userData.username

    if (profileData.has_assessment) {
      hasPlan.value = true
      profile.value = {
        ...profileData.profile,
        latest_assessment: profileData.latest_assessment
      }
    }

    // 尝试获取策略数据
    try {
      const statusData = await orchestratorAPI.getStatus(userId)
      if (statusData.strategy) {
        strategy.value = statusData.strategy
        hasPlan.value = true
      }
      if (statusData.user_profile?.health_score_breakdown) {
        healthBreakdown.value = statusData.user_profile.health_score_breakdown
      }
    } catch {
      // 无策略数据，使用空状态
    }
  } catch {
    // 加载失败
  }

  await nextTick()
  if (strategy.value?.four_buckets) {
    renderChart()
  }
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

.empty-card {
  margin-top: 80px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h2 {
  color: #1e293b;
  margin-bottom: 12px;
}

.empty-state p {
  color: #64748b;
  margin-bottom: 30px;
  font-size: 16px;
}

.greeting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.greeting-row h2 {
  color: #1e293b;
  margin: 0 0 4px 0;
}

.update-time {
  color: #94a3b8;
  font-size: 14px;
  margin: 0;
}

.health-score {
  text-align: center;
}

.score-circle {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(145deg, #1a3a5c, #0F2247);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 0 4px 24px rgba(15,34,71,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
}
.score-circle::before {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(200,150,108,0.4), transparent 60%);
  z-index: -1;
}
.score-num { font-family: 'Georgia', serif; font-size: 28px; font-weight: 700; color: #C8956C; line-height: 1.1; }
.score-label { font-size: 11px; color: rgba(255,255,255,0.5); letter-spacing: 0.5px; }

.score-circle.clickable { cursor: pointer; transition: transform 0.2s; }
.score-circle.clickable:hover { transform: scale(1.05); }

.breakdown { padding: 4px 0; }
.bd-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 13px; }
.bd-icon { font-size: 16px; }
.bd-label { color: #64748b; width: 50px; }
.bd-score { font-weight: 600; color: #1e293b; width: 36px; }
.bd-detail { color: #94a3b8; font-size: 12px; }
.bd-note { font-size: 12px; color: #94a3b8; text-align: center; }

.score-num {
  font-size: 28px;
  font-weight: bold;
  line-height: 1;
}

.score-label {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 4px;
}

.metrics-row {
  margin-bottom: 16px;
}

.metric-card {
  text-align: center;
}

.metric-label {
  color: #64748b;
  font-size: 14px;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 22px;
  font-weight: bold;
  color: #1e293b;
  margin-bottom: 4px;
}

.metric-desc {
  font-size: 12px;
  color: #94a3b8;
}

.risk-tag {
  display: inline;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 16px !important;
}

.risk-low { background: #d1fae5; color: #059669; }
.risk-medium { background: #dbeafe; color: #2563eb; }
.risk-high { background: #fef3c7; color: #d97706; }

.status-active {
  color: #10b981 !important;
}

.content-row {
  margin-bottom: 16px;
}

.chart-card {
  height: 380px;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.quick-actions-card {
  height: 380px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 0;
}

.quick-actions .el-button {
  width: 100%;
  justify-content: flex-start;
  height: 48px;
  font-size: 15px;
}
</style>
