<template>
  <el-card class="analysis-card" :class="[`trust-${credibility}`, { selected }]" @click="$emit('cardClick')">
    <template #header>
      <div class="card-header">
        <span class="card-title">{{ title }}</span>
        <div class="header-right">
          <el-tag :type="credibilityTag" size="small" class="credibility-tag">
            {{ credibilityLabel }}
          </el-tag>
          <el-button v-if="detailSections.length > 0" link type="primary" @click="expanded = !expanded">
            {{ expanded ? '收起详情 ▲' : '查看方法 ▼' }}
          </el-button>
        </div>
      </div>
    </template>

    <!-- 概览：始终可见 -->
    <slot name="summary" />

    <!-- 详情：可展开 -->
    <el-collapse-transition>
      <div v-show="expanded" class="detail-panel">
        <el-divider />
        <div v-for="(section, i) in detailSections" :key="i" class="detail-section">
          <div class="detail-title">{{ section.title }}</div>
          <div class="detail-content">{{ section.content }}</div>
        </div>
      </div>
    </el-collapse-transition>

    <!-- 简版：仅一段提示 -->
    <div v-if="!detailSections.length && note" class="card-note">{{ note }}</div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(defineProps<{
  title: string
  credibility: 'high' | 'medium' | 'low'
  detailSections?: Array<{ title: string; content: string }>
  note?: string
  selected?: boolean
}>(), {
  detailSections: () => [],
  note: '',
  selected: false,
})

defineEmits<{ cardClick: [] }>()

const expanded = ref(false)

const credibilityLabel = computed(() => {
  return { high: '🟢 计算值', medium: '🟡 推算值', low: '🔵 AI生成' }[props.credibility]
})

const credibilityTag = computed(() => {
  return { high: 'success', medium: 'warning', low: 'info' }[props.credibility]
})
</script>

<script lang="ts">
export default { name: 'AnalysisCard' }
</script>

<style scoped>
.analysis-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.analysis-card:hover { border-color: #94a3b8; }
.analysis-card.selected { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }

.trust-high { border-left: 3px solid #10b981; }
.trust-medium { border-left: 3px solid #f59e0b; }
.trust-low { border-left: 3px solid #3b82f6; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.card-title { font-size: 16px; font-weight: 600; }

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.credibility-tag { font-size: 11px; }

.detail-panel { margin-top: 8px; }

.detail-section { margin-bottom: 12px; }

.detail-title {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 4px;
}

.detail-content {
  font-size: 13px;
  color: #475569;
  line-height: 1.7;
  white-space: pre-wrap;
}

.card-note {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}
</style>
