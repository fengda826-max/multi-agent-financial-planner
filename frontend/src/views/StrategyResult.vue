<template>
  <div class="result-container">
    <h2>您的专属资产配置方案</h2>

    <!-- 进度指示器 -->
    <div class="progress-bar" v-if="!allComplete">
      <div class="progress-steps">
        <div class="step" :class="{ active: stepIndex >= 0, done: stepIndex > 0 }">
          <span class="step-dot">1</span>
          <span class="step-label">用户画像</span>
        </div>
        <div class="step-line" :class="{ done: stepIndex > 0 }"></div>
        <div class="step" :class="{ active: stepIndex >= 1, done: stepIndex > 1 }">
          <span class="step-dot">2</span>
          <span class="step-label">市场研判</span>
        </div>
        <div class="step-line" :class="{ done: stepIndex > 1 }"></div>
        <div class="step" :class="{ active: stepIndex >= 2, done: stepIndex > 2 }">
          <span class="step-dot">3</span>
          <span class="step-label">配置方案</span>
        </div>
        <div class="step-line" :class="{ done: stepIndex > 2 }"></div>
        <div class="step" :class="{ active: stepIndex >= 3, done: stepIndex > 3 }">
          <span class="step-dot">4</span>
          <span class="step-label">督导建议</span>
        </div>
      </div>
    </div>

    <!-- 1. 用户画像（profile 完成后展示） -->
    <el-card v-if="profileData" class="section-card profile-card">
      <template #header>
        <div class="section-header">
          <span>🧑 用户画像分析</span>
          <el-tag :type="riskTagType">{{ profileData.risk_capacity_label || profileData.risk_capacity }}</el-tag>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="profile-metrics">
            <div class="profile-item">
              <span class="p-label">生命周期</span>
              <span class="p-value">{{ lifecycleLabel }}</span>
              <p class="p-desc">{{ profileData.lifecycle_explanation || '' }}</p>
            </div>
            <div class="profile-item">
              <span class="p-label">投资风格</span>
              <span class="p-value">{{ profileData.investment_style || '' }}</span>
            </div>
            <div class="profile-item">
              <span class="p-label">风险承受</span>
              <span class="p-value">{{ profileData.risk_explanation || '' }}</span>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="profile-score">
            <div class="health-circle">
              <span class="health-num">{{ profileData.financial_health_score || '-' }}</span>
              <span class="health-unit">分</span>
            </div>
            <div class="health-label">财务健康指数</div>
            <p class="health-comment">{{ profileData.financial_health_comment || '' }}</p>
          </div>
          <div v-if="profileData.strengths?.length" class="profile-tags">
            <span class="tag-label">✅ 优势</span>
            <el-tag v-for="s in profileData.strengths" :key="s" size="small" type="success" effect="plain">{{ s }}</el-tag>
          </div>
          <div v-if="profileData.weaknesses?.length" class="profile-tags">
            <span class="tag-label">⚠️ 需关注</span>
            <el-tag v-for="w in profileData.weaknesses" :key="w" size="small" type="warning" effect="plain">{{ w }}</el-tag>
          </div>
        </el-col>
      </el-row>
      <div v-if="profileData.profile_summary" class="profile-summary">
        💡 {{ profileData.profile_summary }}
      </div>
    </el-card>

    <!-- 2. 市场研判（market 完成后展示） -->
    <el-card v-if="marketData" class="section-card market-card">
      <template #header>
        <span>📈 市场研判</span>
      </template>
      <el-row :gutter="16">
        <el-col :span="8" v-for="(info, asset) in marketData.market_overview" :key="asset">
          <div class="asset-item">
            <div class="asset-name">{{ assetNames[asset] || asset }}</div>
            <div class="asset-return">
              预期收益 <strong>{{ (info.expected_return * 100).toFixed(1) }}%</strong>
            </div>
            <div class="asset-vol">波动率 {{ (info.volatility * 100).toFixed(1) }}%</div>
            <div class="asset-rec">{{ info.recommendation }}</div>
          </div>
        </el-col>
      </el-row>
      <div v-if="marketData.risk_factors?.length" class="risk-factors">
        <span class="risk-label">风险因素：</span>
        <el-tag v-for="(r, i) in marketData.risk_factors" :key="i" size="small" type="danger" effect="plain">{{ r }}</el-tag>
      </div>
      <div v-if="marketData.overall_recommendation" class="overall-rec">
        📝 {{ marketData.overall_recommendation }}
      </div>
    </el-card>

    <!-- 3. 策略方案（strategy 完成后展示） -->
    <template v-if="strategy">
      <!-- 环形饼图 -->
      <el-row :gutter="20">
        <el-col :span="10">
          <el-card class="chart-card">
            <div ref="pieChartRef" class="pie-chart"></div>
          </el-card>
        </el-col>
        <el-col :span="14">
          <el-row :gutter="12">
            <el-col :span="12" v-for="(bucket, key) in strategy.four_buckets" :key="key">
              <el-card class="bucket-card" :class="`bucket-${key}`">
                <div class="bucket-header">
                  <span class="bucket-icon">{{ bucketIcons[key] }}</span>
                  <span class="bucket-name">{{ bucketNames[key] }}</span>
                </div>
                <div class="allocation">{{ (bucket.allocation * 100).toFixed(0) }}%</div>
                <div class="bucket-amount">约 ¥{{ formatAmount(bucket.allocation, investableAssets) }}</div>
                <div class="products">
                  <el-tag v-for="p in bucket.products" :key="p" size="small" class="product-tag">{{ p }}</el-tag>
                </div>
                <el-collapse>
                  <el-collapse-item title="配置理由">
                    <p class="reason">{{ bucket.reason }}</p>
                  </el-collapse-item>
                </el-collapse>
              </el-card>
            </el-col>
          </el-row>
        </el-col>
      </el-row>

      <!-- 压力测试 + 再平衡 -->
      <el-row :gutter="20" class="bottom-row">
        <el-col :span="12">
          <el-card class="stress-test-card">
            <template #header><span>📊 压力测试</span></template>
            <div ref="stressChartRef" class="stress-chart"></div>
            <div class="stress-detail" v-for="(data, scenario) in strategy.stress_test" :key="scenario">
              <div class="stress-item">
                <span>{{ scenarioNames[scenario] || scenario }}</span>
                <span class="loss" :class="{ negative: data.loss < 0 }">{{ (data.loss * 100).toFixed(1) }}%</span>
                <span class="recovery">恢复 {{ data.recovery_time }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card v-if="strategy.rebalance_triggers" class="rebalance-card">
            <template #header><span>⚖️ 再平衡规则</span></template>
            <div class="rebalance-info">
              <el-tag type="warning" size="large">偏离阈值 {{ (strategy.rebalance_triggers.drift_threshold * 100).toFixed(0) }}%</el-tag>
              <el-tag type="info" size="large">{{ frequencyLabel }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 4. 督导建议（coaching 完成后展示） -->
    <el-card v-if="coachingMessage" class="coaching-card">
      <template #header><span>💡 督导建议</span></template>
      <p>{{ coachingMessage }}</p>
    </el-card>

    <!-- 操作按钮 -->
    <div v-if="allComplete" class="action-buttons">
      <el-button type="primary" size="large" @click="$router.push('/my-plan')">📊 查看完整方案</el-button>
      <el-button size="large" @click="$router.push('/ai-chat')">💬 咨询AI助手</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { orchestratorAPI, riskAssessmentAPI } from '../api/client'

const route = useRoute()

// State
const loading = ref(true)
const allComplete = ref(false)
const profileData = ref<any>(null)
const marketData = ref<any>(null)
const strategy = ref<any>(null)
const coachingMessage = ref('')
const investableAssets = ref(0)
const pieChartRef = ref<HTMLElement | null>(null)
const stressChartRef = ref<HTMLElement | null>(null)
let pieChart: echarts.ECharts | null = null
let stressChart: echarts.ECharts | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null

// Constants
const bucketNames: Record<string, string> = {
  living_money: '活钱', stable_money: '稳健', growth_money: '长期', protection_money: '保障'
}
const bucketIcons: Record<string, string> = {
  living_money: '💰', stable_money: '🏦', growth_money: '📈', protection_money: '🛡️'
}
const scenarioNames: Record<string, string> = {
  scenario_2015_crash: '2015年股灾', scenario_covid: '2020年疫情冲击'
}
const assetNames: Record<string, string> = {
  equity: '权益', bond: '债券', commodity: '商品'
}

const stepIndex = computed(() => {
  if (!currentStep.value) return -1
  if (allComplete.value) return 4
  if (strategy.value) return 3
  if (marketData.value) return 2
  if (profileData.value) return 1
  return 0
})

const currentStep = ref('')

const lifecycleLabel = computed(() => {
  const map: Record<string, string> = { accumulation: '积累期', consolidation: '巩固期', distribution: '分配期' }
  return map[profileData.value?.lifecycle_stage] || profileData.value?.lifecycle_stage || ''
})

const riskTagType = computed(() => {
  const cap = profileData.value?.risk_capacity
  if (cap === 'high' || cap === '进取型') return 'warning'
  if (cap === 'medium' || cap === '稳健型') return ''
  return 'success'
})

const frequencyLabel = computed(() => {
  const freq = strategy.value?.rebalance_triggers?.review_frequency
  return freq === 'quarterly' ? '每季度' : freq === 'monthly' ? '每月' : freq || ''
})

function formatAmount(allocation: number, total: number): string {
  const amt = allocation * total
  if (amt >= 10000) return (amt / 10000).toFixed(1) + '万'
  return amt.toFixed(0)
}

function renderPieChart() {
  if (!pieChartRef.value || !strategy.value?.four_buckets) return
  if (!pieChart) pieChart = echarts.init(pieChartRef.value)
  const buckets = strategy.value.four_buckets
  const colors = ['#10B981', '#6366F1', '#F59E0B', '#EF4444']
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: ['50%', '75%'], center: ['50%', '50%'],
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 4 },
      label: { formatter: '{b}\n{d}%', fontSize: 13 },
      emphasis: { label: { fontSize: 18, fontWeight: 'bold' } },
      data: Object.entries(buckets).map(([key, val]: [string, any], i) => ({
        value: Math.round(val.allocation * 100),
        name: bucketNames[key] || key,
        itemStyle: { color: colors[i] }
      }))
    }]
  })
}

function renderStressChart() {
  if (!stressChartRef.value || !strategy.value?.stress_test) return
  if (!stressChart) stressChart = echarts.init(stressChartRef.value)
  const data: { name: string; value: number }[] = []
  Object.entries(strategy.value.stress_test).forEach(([s, v]: [string, any]) => {
    data.push({ name: scenarioNames[s] || s, value: Math.abs(v.loss * 100) })
  })
  stressChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'category', data: data.map(d => d.name) },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [{
      type: 'bar', data: data.map(d => d.value), barWidth: '50%',
      itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#ef4444' }, { offset: 1, color: '#fca5a5' }]), borderRadius: [6, 6, 0, 0] }
    }]
  })
}

async function pollStatus() {
  const userId = route.query.userId as string
  if (!userId) return

  try {
    const status = await orchestratorAPI.getStatus(userId)
    const step = status.current_step
    if (step !== currentStep.value) {
      currentStep.value = step
    }

    // Progressive disclosure: show each section as it becomes available
    if (status.user_profile && Object.keys(status.user_profile).length > 0 && !profileData.value) {
      const p = status.user_profile
      const rcMap: Record<string, string> = { low: '保守型', medium: '稳健型', high: '进取型' }
      profileData.value = {
        ...p,
        risk_capacity_label: rcMap[p.risk_capacity] || p.risk_capacity
      }
    }

    if (status.market_analysis && !marketData.value) {
      marketData.value = status.market_analysis
    }

    if (status.strategy?.four_buckets && !strategy.value) {
      strategy.value = status.strategy
      investableAssets.value = status.user_profile?.investable_assets || 0
      await nextTick()
      renderPieChart()
      renderStressChart()
      loading.value = false
    }

    if (status.coaching_history?.length && !coachingMessage.value) {
      coachingMessage.value = status.coaching_history[0]?.message || ''
    }

    // Stop polling when everything is complete
    if (step === 'coaching_complete' && status.strategy?.four_buckets) {
      allComplete.value = true
      loading.value = false
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }
  } catch {
    // Status not ready yet, keep polling
  }
}

onMounted(async () => {
  const userId = route.query.userId as string
  if (!userId) return

  // Also try to get investable assets from profile
  try {
    const profile = await riskAssessmentAPI.getMyProfile()
    if (profile?.profile?.investable_assets) {
      investableAssets.value = profile.profile.investable_assets
    }
  } catch { /* ignore */ }

  // Start polling
  await pollStatus()
  if (!allComplete.value) {
    pollTimer = setInterval(pollStatus, 2000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (pieChart) pieChart.dispose()
  if (stressChart) stressChart.dispose()
})
</script>

<style scoped>
.result-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

.result-container h2 { color: #1e293b; margin-bottom: 20px; }

/* Progress Bar */
.progress-bar { margin-bottom: 24px; }

.progress-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #cbd5e1;
}

.step.active { color: #3b82f6; }
.step.done { color: #10b981; }

.step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8;
}

.step.active .step-dot { background: #3b82f6; color: #fff; }
.step.done .step-dot { background: #10b981; color: #fff; }
.step-label { font-size: 13px; white-space: nowrap; }

.step-line {
  width: 60px;
  height: 2px;
  background: #e2e8f0;
  margin: 0 4px 20px 4px;
}
.step-line.done { background: #10b981; }

/* Section Cards */
.section-card { margin-bottom: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; }

/* Profile */
.profile-metrics { display: flex; flex-direction: column; gap: 12px; }
.profile-item { }
.p-label { font-size: 12px; color: #94a3b8; }
.p-value { font-size: 16px; font-weight: 600; color: #1e293b; }
.p-desc { font-size: 13px; color: #64748b; margin: 4px 0 0 0; }

.profile-score { text-align: center; margin-bottom: 16px; }
.health-circle {
  width: 90px; height: 90px; border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  display: inline-flex; flex-direction: column;
  align-items: center; justify-content: center; color: #fff;
}
.health-num { font-size: 28px; font-weight: bold; line-height: 1; }
.health-unit { font-size: 12px; }
.health-label { font-size: 14px; color: #64748b; margin: 8px 0 4px; }
.health-comment { font-size: 13px; color: #94a3b8; }

.profile-tags { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; margin-top: 8px; }
.tag-label { font-size: 13px; color: #64748b; margin-right: 4px; }

.profile-summary {
  margin-top: 16px; padding: 12px 16px; background: #f0f9ff;
  border-radius: 8px; font-size: 14px; color: #0c4a6e; line-height: 1.6;
}

/* Market */
.asset-item {
  text-align: center; padding: 16px; background: #f8fafc;
  border-radius: 10px; height: 100%;
}
.asset-name { font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }
.asset-return { font-size: 14px; color: #64748b; margin-bottom: 4px; }
.asset-return strong { color: #f59e0b; font-size: 18px; }
.asset-vol { font-size: 13px; color: #94a3b8; margin-bottom: 8px; }
.asset-rec { font-size: 13px; color: #3b82f6; }

.risk-factors { margin-top: 16px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.risk-label { font-size: 13px; color: #64748b; }
.overall-rec { margin-top: 12px; padding: 12px; background: #fffbeb; border-radius: 8px; font-size: 14px; color: #92400e; }

/* Strategy (bucket cards, charts - same as before) */
.chart-card { height: 360px; }
.pie-chart { width: 100%; height: 320px; }
.bucket-card { margin-bottom: 12px; border-left: 4px solid #e5e7eb; }
.bucket-living_money { border-left-color: #10B981; }
.bucket-stable_money { border-left-color: #6366F1; }
.bucket-growth_money { border-left-color: #F59E0B; }
.bucket-protection_money { border-left-color: #EF4444; }
.bucket-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.bucket-icon { font-size: 18px; }
.bucket-name { font-size: 16px; font-weight: 600; color: #1e293b; }
.allocation { font-size: 28px; font-weight: bold; color: #3b82f6; margin: 6px 0 2px; }
.bucket-amount { font-size: 13px; color: #64748b; margin-bottom: 8px; }
.products { display: flex; flex-wrap: wrap; gap: 4px; }
.product-tag { margin-bottom: 2px; }
.reason { color: #475569; font-size: 14px; line-height: 1.6; }

.bottom-row { margin-top: 20px; }
.stress-test-card { }
.stress-chart { width: 100%; height: 180px; }
.stress-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
.loss { font-weight: bold; }
.loss.negative { color: #ef4444; }
.recovery { color: #64748b; font-size: 13px; }

.rebalance-card { height: 100%; }
.rebalance-info { display: flex; gap: 12px; align-items: center; padding: 20px 0; }

.coaching-card { margin-top: 20px; background: #f0f9ff; border-color: #bae6fd; }
.coaching-card p { font-size: 15px; line-height: 1.8; color: #0c4a6e; }

.action-buttons { display: flex; gap: 12px; justify-content: center; margin-top: 30px; }
</style>
