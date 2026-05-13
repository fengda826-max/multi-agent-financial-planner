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
            <el-button type="primary" @click="generateStrategy">
              生成配置方案
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

    const result = await orchestratorAPI.start({
      user_id: userId,
      risk_assessment: form.value
    })

    router.push({
      path: '/strategy-result',
      query: { userId }
    })
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成方案失败')
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
