<template>
  <div class="assessment-container">
    <el-card>
      <h2>风险承受能力测评</h2>
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="基本信息" />
        <el-step title="投资偏好" />
        <el-step title="测评结果" />
      </el-steps>

      <div v-if="currentStep === 0" class="step-content">
        <el-form :model="form">
          <el-form-item label="年龄">
            <el-input-number v-model="form.age" :min="18" :max="80" />
          </el-form-item>
          <el-form-item label="月收入（元）">
            <el-input-number v-model="form.income" :min="0" :step="1000" />
          </el-form-item>
          <el-form-item label="月支出（元）">
            <el-input-number v-model="form.expenses" :min="0" :step="1000" />
          </el-form-item>
        </el-form>
        <el-button type="primary" @click="currentStep++">下一步</el-button>
      </div>

      <div v-if="currentStep === 1" class="step-content">
        <el-form :model="form">
          <el-form-item label="风险偏好">
            <el-radio-group v-model="form.risk_tolerance">
              <el-radio label="conservative">保守型</el-radio>
              <el-radio label="moderate">稳健型</el-radio>
              <el-radio label="aggressive">进取型</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="投资期限">
            <el-select v-model="form.investment_horizon">
              <el-option label="1年以内" value="1y" />
              <el-option label="1-3年" value="3y" />
              <el-option label="3-5年" value="5y" />
              <el-option label="5年以上" value="10y+" />
            </el-select>
          </el-form-item>
        </el-form>
        <el-button @click="currentStep--">上一步</el-button>
        <el-button type="primary" @click="submitAssessment">提交测评</el-button>
      </div>

      <div v-if="currentStep === 2" class="step-content">
        <el-result icon="success" title="测评完成">
          <template #extra>
            <el-button type="primary" :loading="generating" @click="generateStrategy">
              {{ generating ? generatingProgress : '生成配置方案' }}
            </el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { riskAssessmentAPI, orchestratorAPI } from '../api/client'

const router = useRouter()
const currentStep = ref(0)
const generating = ref(false)
const generatingProgress = ref('正在启动分析...')
const form = ref({
  age: 30,
  income: 20000,
  expenses: 12000,
  risk_tolerance: 'moderate',
  investment_horizon: '5y'
})

const submitAssessment = async () => {
  try {
    await riskAssessmentAPI.submit(form.value)
    currentStep.value = 2
    ElMessage.success('测评提交成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交失败')
  }
}

const generateStrategy = async () => {
  try {
    const userId = localStorage.getItem('user_id')
    if (!userId) {
      ElMessage.error('请先登录')
      return
    }

    generating.value = true

    // 启动后台生成
    await orchestratorAPI.start({
      user_id: userId,
      risk_assessment: form.value
    })

    // 轮询进度
    const progressLabels: Record<string, string> = {
      started: '正在启动分析...',
      analyzing_profile: '正在分析您的财务画像...',
      analyzing_market: '正在分析市场行情...',
      generating_strategy: '正在生成配置方案...',
      generating_coaching: '正在生成督导建议...',
      coaching_complete: '即将完成...'
    }
    let lastStep = ''
    for (let i = 0; i < 90; i++) {
      await new Promise(r => setTimeout(r, 1500))
      try {
        const status = await orchestratorAPI.getStatus(userId)
        const step = status.current_step
        if (step !== lastStep) {
          const label = progressLabels[step] || step
          lastStep = step
          // Update the button text with current progress
          generatingProgress.value = label
        }
        if (step === 'coaching_complete' && status.strategy?.four_buckets) {
          break
        }
      } catch {
        // 状态尚未就绪，继续轮询
      }
    }

    router.push({
      path: '/strategy-result',
      query: { userId }
    })
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成方案失败')
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.assessment-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
}

.step-content {
  margin-top: 30px;
}
</style>
