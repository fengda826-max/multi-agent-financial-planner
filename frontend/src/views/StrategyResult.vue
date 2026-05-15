<template>
  <div class="result-container">
    <el-card v-if="loading" class="loading-card">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在生成您的专属配置方案...</p>
      <p class="loading-hint">AI Agent 正在分析您的数据，预计需要 60-90 秒</p>
    </el-card>

    <template v-else-if="strategy">
      <h2>您的专属资产配置方案</h2>

      <!-- 环形饼图 + 四笔钱卡片 -->
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
                <div class="bucket-amount">约 ¥{{ formatAmount(bucket.allocation, profileData?.investable_assets) }}</div>
                <div class="products">
                  <el-tag
                    v-for="product in bucket.products"
                    :key="product"
                    size="small"
                    class="product-tag"
                  >
                    {{ product }}
                  </el-tag>
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

      <!-- 压力测试 -->
      <el-card class="stress-test-card">
        <template #header>
          <span>📊 压力测试</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="12">
            <div ref="stressChartRef" class="stress-chart"></div>
          </el-col>
          <el-col :span="12">
            <div class="stress-detail" v-for="(data, scenario) in strategy.stress_test" :key="scenario">
              <div class="stress-scenario">
                <span class="scenario-name">{{ scenarioNames[scenario] || scenario }}</span>
                <span class="scenario-loss" :class="{ negative: data.loss < 0 }">
                  {{ (data.loss * 100).toFixed(1) }}%
                </span>
                <span class="scenario-recovery">恢复时间：{{ data.recovery_time }}</span>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 再平衡规则 -->
      <el-card class="rebalance-card" v-if="strategy.rebalance_triggers">
        <template #header>
          <span>⚖️ 再平衡规则</span>
        </template>
        <div class="rebalance-info">
          <el-tag type="warning" size="large">偏离阈值：{{ (strategy.rebalance_triggers.drift_threshold * 100).toFixed(0) }}%</el-tag>
          <el-tag type="info" size="large">检查频率：{{ frequencyLabel }}</el-tag>
        </div>
      </el-card>

      <!-- 督导建议 -->
      <el-card v-if="coachingMessage" class="coaching-card">
        <template #header>
          <span>💡 督导建议</span>
        </template>
        <p>{{ coachingMessage }}</p>
      </el-card>

      <div class="action-buttons">
        <el-button type="primary" size="large" @click="$router.push('/risk-assessment')">
          🔄 重新测评
        </el-button>
        <el-button size="large" disabled>
          📤 分享方案（即将上线）
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { orchestratorAPI, riskAssessmentAPI } from '../api/client'

const route = useRoute()
const loading = ref(true)
const strategy = ref<any>(null)
const coachingMessage = ref('')
const profileData = ref<any>(null)
const pieChartRef = ref<HTMLElement | null>(null)
const stressChartRef = ref<HTMLElement | null>(null)
let pieChart: echarts.ECharts | null = null
let stressChart: echarts.ECharts | null = null

const bucketNames: Record<string, string> = {
  living_money: '活钱',
  stable_money: '稳健',
  growth_money: '长期',
  protection_money: '保障'
}

const bucketIcons: Record<string, string> = {
  living_money: '💰',
  stable_money: '🏦',
  growth_money: '📈',
  protection_money: '🛡️'
}

const scenarioNames: Record<string, string> = {
  scenario_2015_crash: '2015年股灾',
  scenario_covid: '2020年疫情冲击'
}

const frequencyLabel = ref('每季度')

function formatAmount(allocation: number, totalAssets: number | undefined): string {
  const amount = allocation * (totalAssets || 0)
  if (amount >= 10000) return (amount / 10000).toFixed(1) + '万'
  return amount.toFixed(0)
}

function renderPieChart() {
  if (!pieChartRef.value || !strategy.value?.four_buckets) return
  pieChart = echarts.init(pieChartRef.value)

  const buckets = strategy.value.four_buckets
  const colors = ['#10B981', '#6366F1', '#F59E0B', '#EF4444']

  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const keys = Object.keys(buckets)
        const key = keys[params.dataIndex]
        const bucket = buckets[key]
        const amount = profileData.value?.investable_assets
          ? formatAmount(bucket.allocation, profileData.value.investable_assets)
          : '-'
        return `${params.name}<br/>占比：${params.value}%<br/>约：¥${amount}`
      }
    },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 4 },
      label: {
        show: true,
        formatter: '{b}\n{d}%',
        fontSize: 13
      },
      emphasis: {
        label: { fontSize: 20, fontWeight: 'bold' },
        scaleSize: 10
      },
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
  stressChart = echarts.init(stressChartRef.value)

  const stressData: any[] = []
  const names: string[] = []
  for (const [scenario, data] of Object.entries(strategy.value.stress_test)) {
    names.push(scenarioNames[scenario] || scenario)
    stressData.push({
      name: scenarioNames[scenario] || scenario,
      value: Math.abs((data as any).loss * 100)
    })
  }

  stressChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const d = params[0]
        const originalKey = Object.keys(strategy.value.stress_test)[d.dataIndex]
        const recovery = strategy.value.stress_test[originalKey]?.recovery_time || '-'
        return `${d.name}<br/>最大回撤：${d.value}%<br/>恢复时间：${recovery}`
      }
    },
    xAxis: {
      type: 'category',
      data: names
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value}%' }
    },
    series: [{
      type: 'bar',
      data: stressData.map(d => d.value),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#ef4444' },
          { offset: 1, color: '#fca5a5' }
        ]),
        borderRadius: [6, 6, 0, 0]
      },
      barWidth: '50%'
    }]
  })
}

onMounted(async () => {
  const userId = route.query.userId as string
  if (!userId) return

  try {
    const [result, profileResult] = await Promise.all([
      orchestratorAPI.getStatus(userId),
      riskAssessmentAPI.getMyProfile().catch(() => null)
    ])

    strategy.value = result.strategy
    coachingMessage.value = result.coaching_history?.[0]?.message || ''

    if (profileResult?.profile) {
      profileData.value = profileResult.profile
    }

    if (result.strategy?.rebalance_triggers?.review_frequency) {
      const freq = result.strategy.rebalance_triggers.review_frequency
      frequencyLabel.value = freq === 'quarterly' ? '每季度' : freq === 'monthly' ? '每月' : freq
    }
  } catch (error) {
    console.error('Failed to load strategy:', error)
  } finally {
    loading.value = false
  }

  await nextTick()
  renderPieChart()
  renderStressChart()
})
</script>

<style scoped>
.result-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

.result-container h2 {
  color: #1e293b;
  margin-bottom: 20px;
}

.loading-card {
  text-align: center;
  padding: 80px 20px;
}

.loading-card p {
  font-size: 16px;
  color: #64748b;
  margin-top: 16px;
}

.loading-hint {
  font-size: 13px !important;
  color: #94a3b8 !important;
}

.chart-card {
  height: 360px;
  margin-bottom: 20px;
}

.pie-chart {
  width: 100%;
  height: 320px;
}

.bucket-card {
  margin-bottom: 12px;
  border-left: 4px solid #e5e7eb;
}

.bucket-living_money { border-left-color: #10B981; }
.bucket-stable_money { border-left-color: #6366F1; }
.bucket-growth_money { border-left-color: #F59E0B; }
.bucket-protection_money { border-left-color: #EF4444; }

.bucket-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.bucket-icon { font-size: 18px; }
.bucket-name { font-size: 16px; font-weight: 600; color: #1e293b; }

.allocation {
  font-size: 28px;
  font-weight: bold;
  color: #3b82f6;
  margin: 6px 0 2px 0;
}

.bucket-amount {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.products {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.product-tag {
  margin-bottom: 2px;
}

.reason {
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
}

.stress-test-card {
  margin-top: 20px;
}

.stress-chart {
  width: 100%;
  height: 200px;
}

.stress-detail {
  padding: 16px 0;
}

.stress-scenario {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 12px;
}

.scenario-name {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.scenario-loss {
  font-size: 28px;
  font-weight: bold;
}

.scenario-loss.negative { color: #ef4444; }

.scenario-recovery {
  font-size: 14px;
  color: #64748b;
}

.rebalance-card {
  margin-top: 20px;
}

.rebalance-info {
  display: flex;
  gap: 16px;
}

.coaching-card {
  margin-top: 20px;
  background: #f0f9ff;
  border-color: #bae6fd;
}

.coaching-card p {
  font-size: 15px;
  line-height: 1.8;
  color: #0c4a6e;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 30px;
}
</style>
