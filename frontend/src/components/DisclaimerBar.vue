<template>
  <div class="disclaimer-bar">
    <el-alert
      :title="title"
      type="warning"
      :closable="false"
      show-icon
    >
      <template #default>
        <p>{{ message }}</p>
      </template>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  message?: string
}>()
</script>

<script lang="ts">
export default {
  name: 'DisclaimerBar'
}
</script>

<style scoped>
.disclaimer-bar {
  margin-top: 24px;
  margin-bottom: 8px;
}

.disclaimer-bar p {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #92400e;
  line-height: 1.6;
}
</style>
