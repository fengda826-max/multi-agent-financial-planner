<template>
  <div class="result-container">
    <el-card v-if="loading" class="loading-card">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在生成您的专属配置方案...</p>
    </el-card>

    <template v-else-if="strategy">
      <h2>您的专属资产配置方案</h2>

      <el-row :gutter="20">
        <el-col :span="6" v-for="(bucket, key) in strategy.four_buckets" :key="key">
          <el-card class="bucket-card">
            <h3>{{ bucketNames[key] }}</h3>
            <div class="allocation">{{ (bucket.allocation * 100).toFixed(0) }}%</div>
            <p class="reason">{{ bucket.reason }}</p>
            <div class="products">
              <el-tag v-for="product in bucket.products" :key="product" size="small">
                {{ product }}
              </el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="stress-test-card">
        <h3>压力测试</h3>
        <el-table :data="stressTestData">
          <el-table-column prop="scenario" label="情景" />
          <el-table-column prop="loss" label="预期损失">
            <template #default="{ row }">
              <span :class="{ 'negative': row.loss < 0 }">{{ (row.loss * 100).toFixed(1) }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="recovery_time" label="恢复时间" />
        </el-table>
      </el-card>

      <el-card v-if="coachingMessage" class="coaching-card">
        <h3>督导建议</h3>
        <p>{{ coachingMessage }}</p>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { orchestratorAPI } from '../api/client'

const route = useRoute()
const loading = ref(true)
const strategy = ref<any>(null)
const coachingMessage = ref('')

const bucketNames: Record<string, string> = {
  living_money: '活钱',
  stable_money: '稳健',
  growth_money: '长期',
  protection_money: '保障'
}

const stressTestData = ref<any[]>([])

onMounted(async () => {
  const userId = route.query.userId as string
  if (!userId) return

  try {
    const result = await orchestratorAPI.getStatus(userId)
    strategy.value = result.strategy
    coachingMessage.value = result.coaching_history?.[0]?.message || ''

    if (result.strategy?.stress_test) {
      stressTestData.value = Object.entries(result.strategy.stress_test).map(([scenario, data]: [string, any]) => ({
        scenario,
        ...data
      }))
    }
  } catch (error) {
    console.error('Failed to load strategy:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.result-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 20px;
}

.loading-card {
  text-align: center;
  padding: 60px;
}

.bucket-card {
  text-align: center;
  margin-bottom: 20px;
}

.allocation {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin: 10px 0;
}

.reason {
  color: #666;
  font-size: 14px;
}

.products {
  margin-top: 10px;
}

.stress-test-card {
  margin-top: 20px;
}

.coaching-card {
  margin-top: 20px;
  background: #f0f9ff;
}

.negative {
  color: #f56c6c;
}
</style>
