<template>
  <div class="result-container">
    <h2>您的专属资产配置方案</h2>

    <!-- Agent 工作台（生成中） -->
    <AgentWorkbench
      v-if="!allComplete"
      :agentSteps="agentSteps"
      :currentStep="currentStep"
    />

    <!-- 结果阶段（生成完成）：左右双栏 -->
    <el-row v-if="allComplete" :gutter="20">
      <!-- 左侧：概览 -->
      <el-col :xs="24" :md="10">
        <div class="overview-panel">
          <!-- 1. 用户画像 -->
    <AnalysisCard
      v-if="profileData"
      title="🧑 用户画像分析"
      credibility="medium"
      :detailSections="profileDetailSections"
      @cardClick="buildDetailItem('用户画像分析', 'medium', '原始数据来自用户填报，计算公式为确定性规则，总结文案由AI生成', [
        {title:'① 输入数据', text: '年龄、收入、支出、风险偏好、投资期限 → 来自用户填报\n存款、负债、保险 → 来自用户填报或系统估算'},
        {title:'② 计算方法', text: profileDetailSections[0]?.content || '基于储蓄率、应急月数、投资期限、保险配置4维度加权评分'},
        {title:'③ 数据溯源', text: '🟡 推算值 — 原始输入: 用户填报 | 评分: 确定性公式 | 总结: AI文案'}
      ])"
    >
      <template #summary>
        <div class="section-header">
          <el-tag :type="riskTagType">{{ profileData.risk_capacity_label || profileData.risk_capacity }}</el-tag>
        </div>
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
      </template>
    </AnalysisCard>

    <!-- 2. 市场研判 -->
    <AnalysisCard
      v-if="marketData"
      title="📈 市场研判"
      credibility="high"
      :detailSections="marketDetailSections"
    >
      <template #summary>
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
      <div class="data-source-note">
        市场原始数据来自 AKShare 公开金融数据接口（沪深300、创业板指、国债收益率、CPI），AI 据此生成研判。数据可能存在延迟，仅供参考。
      </div>
      </template>
    </AnalysisCard>

    <!-- 3. 策略方案 -->
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
                  <span class="products-label">示例产品：</span>
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

    <!-- 4. 督导建议 -->
    <AnalysisCard
      v-if="coachingMessage"
      title="💡 督导建议"
      credibility="low"
    >
      <template #summary>
        <p>{{ coachingMessage }}</p>
      </template>
    </AnalysisCard>

        </div>
      </el-col>
      <!-- 右侧：详情面板 -->
      <el-col :xs="24" :md="14" class="detail-col">
        <DetailPanel
          :activeItem="activeDetailItem"
          @close="activeDetailItem = null"
        />
      </el-col>
    </el-row>

    <!-- 操作按钮 -->
    <div v-if="allComplete" class="action-buttons">
      <el-button type="primary" size="large" @click="$router.push('/ai-chat')">💬 咨询AI助手</el-button>
    </div>

    <DisclaimerBar
      title="免责声明"
      message="本方案由 DeepSeek AI 基于您提供的财务数据和当前市场信息生成，仅供理财教育和参考，不构成专业投资建议。产品列表为示例，不代表具体购买推荐。投资有风险，决策需谨慎。市场数据来源：AKShare 公开金融数据接口。"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { orchestratorAPI, riskAssessmentAPI } from '../api/client'
import DisclaimerBar from '../components/DisclaimerBar.vue'
import AnalysisCard from '../components/AnalysisCard.vue'
import AgentWorkbench from '../components/AgentWorkbench.vue'
import DetailPanel from '../components/DetailPanel.vue'

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

const agentSteps = ref<Record<string, any[]>>({})
const activeDetailItem = ref<any>(null)

function buildDetailItem(label: string, credibility: string, source: string, content: Array<{ title: string; text: string }>) {
  activeDetailItem.value = { label, credibility, source, content }
}

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

const profileDetailSections = computed(() => {
  const bd = profileData.value?.health_score_breakdown
  if (!bd) return []
  return [{
    title: '📊 健康分计算方法',
    content: `财务健康评分由4个维度组成（满分100）：
• 储蓄力（0-30分）：储蓄率越高得分越高 — 当前${bd.savings?.detail || '-'}，得分${bd.savings?.score || 0}
• 应急力（0-30分）：应急储备覆盖月数越多得分越高 — 当前${bd.emergency?.detail || '-'}，得分${bd.emergency?.score || 0}
• 投资力（10-20分）：投资期限越长越适合权益配置 — 当前${bd.investment?.detail || '-'}，得分${bd.investment?.score || 0}
• 保障力（10-20分）：已配置保险则得分更高 — 当前${bd.protection?.detail || '-'}，得分${bd.protection?.score || 0}

评分由确定性公式计算，不含AI主观判断。`
  }, {
    title: '📡 数据来源',
    content: '生命周期阶段根据年龄规则判定（<35积累期，35-50巩固期，>50分配期）。投资风格根据风险偏好+年龄组合映射。优劣势基于储蓄率、应急月数、负债率、保险配置等真实指标触发规则生成。画像总结由AI基于以上数据撰写。'
  }]
})

const marketDetailSections = computed(() => {
  const cm = marketData.value?.computed_metrics
  if (!cm) return [{
    title: '📡 数据来源',
    content: '市场原始数据来自AKShare公开金融数据接口（东方财富、中国债券信息网、国家统计局）。预期收益率和波动率由近5年日线数据统计计算（年化收益=日均收益×252，年化波动率=日收益标准差×√252）。AI仅生成风险因素和定性建议。'
  }]
  return [{
    title: '📊 计算方法',
    content: `权益（沪深300）：基于近5年日线数据统计
• 年化收益 = 日均收益率 × 252 = ${(cm.equity_return * 100).toFixed(1)}%
• 年化波动率 = 日收益率标准差 × √252 = ${(cm.equity_vol * 100).toFixed(1)}%
• 最大回撤 = 区间内最高点到最低点的跌幅 = ${(cm.equity_max_dd * 100).toFixed(1)}%
• PE(TTM) = ${cm.cs300_pe || '暂缺'}（${cm.cs300_pe_percentile || '分位数据暂缺'}）
• 股权风险溢价 = 1/PE - 10年国债收益率 = ${(cm.erp * 100).toFixed(1)}%

债券：预期收益 = 当前10年国债收益率 = ${(cm.bond_yield || 0).toFixed(2)}%，波动率通常2-5%

⚠️ 历史收益不代表未来表现。统计基于过去数据，不包含对未来预测。`
  }, {
    title: '📡 数据来源',
    content: `• 沪深300行情/PE → AKShare (东方财富) | 更新时间：${marketData.value?.data_timestamp || '策略生成时'}
• 10年国债收益率 → AKShare (中国债券信息网)
• CPI → AKShare (国家统计局)
• 风险因素和定性建议 → DeepSeek AI（基于计算好的量化指标生成）`
  }]
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

    // Agent workbench steps
    if (status.agent_steps) {
      agentSteps.value = { ...status.agent_steps }
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

.data-source-note {
  margin-top: 12px;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.5;
}

.products-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}
</style>
