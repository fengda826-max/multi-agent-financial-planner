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
          </el-form-item>
        </el-form>
        <el-divider />
        <el-button link type="primary" @click="fullMode = !fullMode" class="full-mode-toggle">
          {{ fullMode ? '收起完整财务信息 ▲' : '想获得更精准的分析？展开完整财务信息 ▼' }}
        </el-button>
        <div v-show="fullMode" class="optional-fields">
          <el-form :model="optionalFields">
            <el-form-item label="已有存款/投资（元）">
              <el-input-number v-model="optionalFields.total_savings" :min="0" :step="50000" placeholder="已存下的钱+已投资的金额" style="width:100%" />
            </el-form-item>
            <el-form-item label="月度负债（元）">
              <el-input-number v-model="optionalFields.monthly_debt" :min="0" :step="1000" placeholder="房贷/车贷/信用卡月还款" style="width:100%" />
            </el-form-item>
            <el-form-item label="是否配置保险">
              <el-switch v-model="optionalFields.has_insurance" active-text="已配置" inactive-text="未配置" />
            </el-form-item>
          </el-form>
          <p class="optional-note">以上字段为可选项，填写后可获得更精准的财务画像分析，不填则使用系统估算值</p>
        </div>
        <el-button @click="currentStep--">上一步</el-button>
        <el-button type="primary" @click="submitAssessment">提交测评</el-button>
      </div>

      <div v-if="currentStep === 2" class="step-content">
        <el-result icon="success" title="测评完成">
          <template #extra>
            <el-button type="primary" :loading="generating" @click="generateStrategy">
              {{ generating ? '正在启动分析...' : '生成配置方案' }}
            </el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { riskAssessmentAPI, orchestratorAPI } from '../api/client'

const router = useRouter()
const currentStep = ref(0)
const generating = ref(false)
const fullMode = ref(false)
const optionalFields = ref({
  total_savings: null as number | null,
  monthly_debt: null as number | null,
  has_insurance: false,
})
const form = ref({
  age: 30,
  income: 20000,
  expenses: 12000,
  risk_tolerance: 'moderate',
  investment_horizon: '5y'
})

const fullAssessmentData = computed(() => ({
  ...form.value,
  ...(fullMode.value ? {
    total_savings: optionalFields.value.total_savings,
    monthly_debt: optionalFields.value.monthly_debt,
    has_insurance: optionalFields.value.has_insurance,
  } : {}),
}))

const submitAssessment = async () => {
  try {
    await riskAssessmentAPI.submit(fullAssessmentData.value)
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
      risk_assessment: fullAssessmentData.value
    })

    // 立即跳转到结果页，渐进展示
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
