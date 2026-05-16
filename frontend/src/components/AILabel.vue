<template>
  <el-tooltip :content="tooltip" placement="top">
    <el-tag size="small" type="info" class="ai-label" effect="plain">
      {{ label }}
    </el-tag>
  </el-tooltip>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  label?: string
  tooltip?: string
}>(), {
  label: '🤖 AI生成',
  tooltip: '此内容由DeepSeek AI生成，仅供参考，不构成投资建议'
})
</script>

<script lang="ts">
export default {
  name: 'AILabel'
}
</script>

<style scoped>
.ai-label {
  font-size: 11px;
  opacity: 0.8;
  vertical-align: middle;
}
</style>
