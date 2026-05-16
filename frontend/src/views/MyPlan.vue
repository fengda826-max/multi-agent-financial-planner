<template>
  <div class="plan-container">
    <!-- 空状态 -->
    <el-card v-if="!strategy" class="empty-card">
      <div class="empty-state">
        <div class="empty-icon">📊</div>
        <h2>暂无配置方案</h2>
        <p>完成风险测评后，AI 将为您生成专属的"四笔钱"资产配置方案</p>
        <el-button type="primary" size="large" @click="$router.push('/risk-assessment')">
          开始测评
        </el-button>
      </div>
    </el-card>

    <template v-else>
      <div class="plan-header">
        <div>
          <h2>我的配置方案</h2>
          <p class="plan-meta">
            <el-tag type="info">{{ lifecycleLabel }}</el-tag>
            <el-tag :type="riskTagType">{{ riskLabel }}</el-tag>
          </p>
        </div>
        <div class="plan-actions">
          <el-button @click="$router.push('/risk-assessment')">🔄 重新测评</el-button>
          <el-button type="primary" @click="handleRebalance" :loading="rebalancing">⚖️ 检查再平衡</el-button>
        </div>
      </div>

      <!-- 环形饼图 -->
      <el-card class="chart-card">
        <div ref="pieChartRef" class="pie-chart"></div>
      </el-card>

      <!-- 四笔钱详情 -->
      <el-row :gutter="16" class="buckets-row">
        <el-col :span="6" v-for="(bucket, key) in strategy.four_buckets" :key="key">
          <el-card class="bucket-detail-card" :class="`bucket-${key}`">
            <div class="bucket-title">
              <span class="bucket-emoji">{{ bucketIcons[key] }}</span>
              <span>{{ bucketNames[key] }}</span>
            </div>
            <div class="bucket-percent">{{ (bucket.allocation * 100).toFixed(0) }}%</div>
            <div class="bucket-amount">约 ¥{{ formatAmount(bucket.allocation, investableAssets) }}</div>
            <div class="product-list">
              <div class="products-label">示例产品</div>
            <el-tag v-for="p in bucket.products" :key="p" size="small" class="product-tag" effect="plain">
                {{ p }}
              </el-tag>
            </div>
            <el-divider />
            <div class="bucket-reason">
              <span class="reason-label">💡 配置理由</span>
              <p>{{ bucket.reason }}</p>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 压力测试 + 再平衡 -->
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card class="detail-card">
            <template #header>📊 压力测试</template>
            <div ref="stressChartRef" class="stress-chart"></div>
            <div class="stress-list" v-for="(data, scenario) in strategy.stress_test" :key="scenario">
              <div class="stress-item">
                <span>{{ scenarioNames[scenario] || scenario }}</span>
                <span class="loss" :class="{ negative: data.loss < 0 }">{{ (data.loss * 100).toFixed(1) }}%</span>
                <span class="recovery">恢复 {{ data.recovery_time }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="detail-card" v-if="strategy.rebalance_triggers">
            <template #header>⚖️ 再平衡规则</template>
            <div class="rebalance-detail">
              <div class="rb-item">
                <span class="rb-label">偏离阈值</span>
                <span class="rb-value">{{ (strategy.rebalance_triggers.drift_threshold * 100).toFixed(0) }}%</span>
              </div>
              <div class="rb-item">
                <span class="rb-label">检查频率</span>
                <span class="rb-value">{{ frequencyLabel }}</span>
              </div>
              <div class="rb-hint">
                当实际持仓偏离目标超过阈值时，建议重新平衡以控制风险。
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <DisclaimerBar
      v-if="strategy"
      message="本方案由DeepSeek AI生成，产品列表为示例，不代表购买推荐。投资有风险，决策需谨慎。"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { orchestratorAPI, riskAssessmentAPI } from '../api/client'
import DisclaimerBar from '../components/DisclaimerBar.vue'

const strategy = ref<any>(null)
const investableAssets = ref(0)
const rebalancing = ref(false)
const pieChartRef = ref<HTMLElement | null>(null)
const stressChartRef = ref<HTMLElement | null>(null)

const bucketNames: Record<string, string> = {
  living_money: '活钱', stable_money: '稳健', growth_money: '长期', protection_money: '保障'
}

const bucketIcons: Record<string, string> = {
  living_money: '💰', stable_money: '🏦', growth_money: '📈', protection_money: '🛡️'
}

const scenarioNames: Record<string, string> = {
  scenario_2015_crash: '2015年股灾', scenario_covid: '2020年疫情冲击'
}

const riskLabel = computed(() => {
  const map: Record<string, string> = { conservative: '保守型', moderate: '稳健型', aggressive: '进取型', low: '保守型', medium: '稳健型', high: '进取型' }
  return map[profileData.value?.risk_capacity] || '-'
})

const riskTagType = computed(() => {
  const map: Record<string, string> = { low: 'success', conservative: 'success', medium: '', moderate: '', high: 'warning', aggressive: 'warning' }
  return map[profileData.value?.risk_capacity] || 'info'
})

const lifecycleLabel = computed(() => {
  const map: Record<string, string> = { accumulation: '积累期', consolidation: '巩固期', distribution: '分配期' }
  return map[profileData.value?.lifecycle_stage] || ''
})

const frequencyLabel = computed(() => {
  const freq = strategy.value?.rebalance_triggers?.review_frequency
  return freq === 'quarterly' ? '每季度' : freq === 'monthly' ? '每月' : freq || '-'
})

const profileData = ref<any>({})

function formatAmount(allocation: number, total: number): string {
  const amount = allocation * total
  if (amount >= 10000) return (amount / 10000).toFixed(1) + '万'
  return amount.toFixed(0)
}

function renderPieChart() {
  if (!pieChartRef.value || !strategy.value?.four_buckets) return
  const chart = echarts.init(pieChartRef.value)
  const buckets = strategy.value.four_buckets
  const colors = ['#10B981', '#6366F1', '#F59E0B', '#EF4444']

  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '50%'],
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
  const chart = echarts.init(stressChartRef.value)
  const data: { name: string; value: number }[] = []
  Object.entries(strategy.value.stress_test).forEach(([scenario, val]: [string, any]) => {
    data.push({ name: scenarioNames[scenario] || scenario, value: Math.abs(val.loss * 100) })
  })

  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'category', data: data.map(d => d.name) },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [{
      type: 'bar',
      data: data.map(d => d.value),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#ef4444' }, { offset: 1, color: '#fca5a5' }
        ]),
        borderRadius: [6, 6, 0, 0]
      },
      barWidth: '50%'
    }]
  })
}

async function handleRebalance() {
  rebalancing.value = true
  try {
    const userId = localStorage.getItem('user_id')
    if (!userId) return
    await orchestratorAPI.replan({
      user_id: userId,
      trigger: 'manual_rebalance',
      trigger_detail: '用户手动触发再平衡检查',
      replan_from: 'strategy'
    })
    ElMessage.success('再平衡完成，方案已更新')
    window.location.reload()
  } catch {
    ElMessage.error('再平衡失败，请重试')
  } finally {
    rebalancing.value = false
  }
}

onMounted(async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  try {
    const [statusData, profileDataApi] = await Promise.all([
      orchestratorAPI.getStatus(userId),
      riskAssessmentAPI.getMyProfile().catch(() => null)
    ])

    if (statusData.strategy) {
      strategy.value = statusData.strategy
    }

    if (profileDataApi) {
      profileData.value = profileDataApi.profile
      investableAssets.value = profileDataApi.profile.investable_assets || 0
    }
  } catch {
    // 无方案数据
  }

  await nextTick()
  renderPieChart()
  renderStressChart()
})
</script>

<style scoped>
.plan-container {
  padding: 20px;
}

.empty-card {
  margin-top: 80px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon { font-size: 64px; margin-bottom: 20px; }
.empty-state h2 { color: #1e293b; margin-bottom: 12px; }
.empty-state p { color: #64748b; margin-bottom: 30px; font-size: 16px; }

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.plan-header h2 {
  color: #1e293b;
  margin: 0 0 8px 0;
}

.plan-meta {
  display: flex;
  gap: 8px;
  margin: 0;
}

.plan-actions {
  display: flex;
  gap: 8px;
}

.chart-card {
  margin-bottom: 20px;
  text-align: center;
}

.pie-chart {
  width: 100%;
  height: 320px;
}

.buckets-row {
  margin-bottom: 20px;
}

.bucket-detail-card {
  border-top: 3px solid #e5e7eb;
  height: 100%;
}

.bucket-living_money { border-top-color: #10B981; }
.bucket-stable_money { border-top-color: #6366F1; }
.bucket-growth_money { border-top-color: #F59E0B; }
.bucket-protection_money { border-top-color: #EF4444; }

.bucket-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.bucket-emoji { font-size: 20px; }

.bucket-percent {
  font-size: 32px;
  font-weight: bold;
  color: #3b82f6;
  margin: 8px 0 4px;
}

.bucket-amount {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 12px;
}

.product-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.product-tag {
  margin-bottom: 2px;
}

.bucket-reason p {
  color: #475569;
  font-size: 13px;
  line-height: 1.5;
  margin: 4px 0 0 0;
}

.reason-label {
  font-size: 13px;
  color: #94a3b8;
}

.detail-card {
  height: 100%;
}

.stress-chart {
  width: 100%;
  height: 180px;
}

.stress-list {
  margin-top: 12px;
}

.stress-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 14px;
}

.loss {
  font-weight: bold;
}

.loss.negative { color: #ef4444; }

.recovery {
  color: #64748b;
  font-size: 13px;
}

.rebalance-detail {
  padding: 8px 0;
}

.rb-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.rb-label { color: #64748b; font-size: 15px; }
.rb-value { font-size: 20px; font-weight: bold; color: #1e293b; }

.rb-hint {
  margin-top: 16px;
  padding: 12px;
  background: #fffbeb;
  border-radius: 8px;
  color: #92400e;
  font-size: 14px;
  line-height: 1.6;
}

.products-label {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 6px;
}
</style>
