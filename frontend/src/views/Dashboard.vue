<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>我的理财规划</span>
              <el-button type="primary" @click="$router.push('/risk-assessment')">
                开始测评
              </el-button>
            </div>
          </template>
          <p>欢迎使用智能理财规划系统。点击上方按钮开始风险测评，获取您的专属资产配置方案。</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
