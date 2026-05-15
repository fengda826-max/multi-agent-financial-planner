<template>
  <div class="market-container">
    <h2>📈 市场观察</h2>

    <el-card v-if="!hasData" class="empty-card">
      <div class="empty-state">
        <div class="empty-icon">📈</div>
        <p>请先生成配置方案，市场研判数据将一并展示</p>
        <el-button type="primary" @click="$router.push('/risk-assessment')">开始测评</el-button>
      </div>
    </el-card>

    <template v-else>
      <!-- 关键指标 -->
      <el-row :gutter="16" class="metrics-row">
        <el-col :span="6" v-for="asset in assetCards" :key="asset.name">
          <el-card class="asset-card" shadow="hover">
            <div class="asset-name">{{ asset.name }}</div>
            <div class="asset-return">
              <span class="return-value">{{ (asset.expectedReturn * 100).toFixed(1) }}%</span>
              <span class="return-label">预期收益</span>
            </div>
            <div class="asset-vol">波动率 {{ (asset.volatility * 100).toFixed(1) }}%</div>
            <div class="asset-rec">{{ asset.recommendation }}</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- AI 研判 -->
      <el-card class="analysis-card">
        <template #header>
          <span>📝 AI 市场研判</span>
        </template>
        <div class="recommendation">
          <strong>整体建议：</strong>{{ overallRecommendation }}
        </div>
      </el-card>

      <!-- 风险因素 -->
      <el-card class="risk-card" v-if="riskFactors.length > 0">
        <template #header>
          <span>⚠️ 需关注的风险因素</span>
        </template>
        <div class="risk-list">
          <div v-for="(risk, i) in riskFactors" :key="i" class="risk-item">
            <span class="risk-num">{{ i + 1 }}</span>
            <span>{{ risk }}</span>
          </div>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { orchestratorAPI } from '../api/client'

const hasData = ref(false)
const marketData = ref<any>({})
const riskFactors = ref<string[]>([])
const overallRecommendation = ref('')

const assetCards = computed(() => {
  const overview = marketData.value?.market_overview || {}
  return Object.entries(overview).map(([key, val]: [string, any]) => ({
    name: { equity: '权益', bond: '债券', commodity: '商品' }[key] || key,
    expectedReturn: val.expected_return || 0,
    volatility: val.volatility || 0,
    recommendation: val.recommendation || ''
  }))
})

onMounted(async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  try {
    const result = await orchestratorAPI.getStatus(userId)
    if (result.market_analysis?.market_overview) {
      marketData.value = result.market_analysis
      riskFactors.value = result.market_analysis.risk_factors || []
      overallRecommendation.value = result.market_analysis.overall_recommendation || ''
      hasData.value = true
    }
  } catch {
    // 无数据
  }
})
</script>

<style scoped>
.market-container {
  padding: 20px;
}

.market-container h2 {
  color: #1e293b;
  margin-bottom: 20px;
}

.empty-card {
  margin-top: 80px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon { font-size: 64px; margin-bottom: 16px; }
.empty-state p { color: #64748b; font-size: 16px; margin-bottom: 24px; }

.metrics-row { margin-bottom: 16px; }

.asset-card {
  text-align: center;
}

.asset-name {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
  font-weight: 500;
}

.asset-return {
  margin-bottom: 6px;
}

.return-value {
  font-size: 28px;
  font-weight: bold;
  color: #f59e0b;
}

.return-label {
  font-size: 12px;
  color: #94a3b8;
  margin-left: 4px;
}

.asset-vol {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.asset-rec {
  font-size: 13px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 6px 12px;
  border-radius: 6px;
}

.analysis-card {
  margin-bottom: 16px;
}

.recommendation {
  font-size: 15px;
  line-height: 1.8;
  color: #1e293b;
}

.risk-card {
  margin-bottom: 16px;
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #fffbeb;
  border-radius: 8px;
  font-size: 14px;
  color: #92400e;
}

.risk-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fef3c7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}
</style>
