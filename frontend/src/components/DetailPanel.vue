<template>
  <div class="detail-panel">
    <div class="panel-header">
      <span class="panel-title">分析详情</span>
      <el-button link class="panel-close" @click="$emit('close')">✕ 收起</el-button>
    </div>

    <div class="panel-body" v-if="activeItem">
      <div class="detail-section" v-for="(section, i) in activeItem.content" :key="i">
        <div class="section-title">{{ section.title }}</div>
        <div class="section-text"><pre>{{ section.text }}</pre></div>
      </div>

      <div class="panel-footer">
        <el-tag :type="credibilityType" size="small" effect="plain">
          {{ credibilityLabel }}
        </el-tag>
        <span class="credibility-note">{{ activeItem.source }}</span>
      </div>
    </div>

    <div class="panel-empty" v-else>
      <p>👈 点击左侧指标查看详细数据来源和计算过程</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DetailSection {
  title: string
  text: string
}

interface DetailItem {
  label: string
  credibility: 'high' | 'medium' | 'low'
  source: string
  content: DetailSection[]
}

const props = defineProps<{
  activeItem: DetailItem | null
}>()

defineEmits<{ close: [] }>()

const credibilityLabel = computed(() => {
  const map = { high: '🟢 直接计算值', medium: '🟡 基于输入推算', low: '🔵 AI模型生成' }
  return map[props.activeItem?.credibility || 'medium']
})

const credibilityType = computed(() => {
  const map = { high: 'success', medium: 'warning', low: 'info' }
  return map[props.activeItem?.credibility || 'medium']
})
</script>

<script lang="ts">
export default { name: 'DetailPanel' }
</script>

<style scoped>
.detail-panel {
  background: #fff;
  border: 1px solid #e8ecf1;
  border-radius: 14px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 18px; border-bottom: 1px solid #f1f5f9;
}
.panel-title { font-size: 14px; font-weight: 600; color: #1e293b; }
.panel-close { font-size: 12px; color: #94a3b8; }

.panel-body { flex: 1; overflow-y: auto; padding: 16px 18px; }
.detail-section { margin-bottom: 14px; }
.section-title { font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 8px; }
.section-text pre { margin: 0; font-size: 13px; line-height: 1.7; color: #334155; white-space: pre-wrap; font-family: 'SF Mono', 'Consolas', monospace; background: #f8fafc; padding: 10px 14px; border-radius: 8px; }

.panel-footer { padding: 10px 18px; border-top: 1px solid #f1f5f9; display: flex; align-items: center; gap: 8px; }
.credibility-note { font-size: 12px; color: #94a3b8; }

.panel-empty { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px; text-align: center; }
.panel-empty p { font-size: 14px; color: #94a3b8; }

@media (max-width: 768px) {
  .detail-panel { position: fixed; bottom: 0; left: 0; right: 0; max-height: 55vh; z-index: 50; border-radius: 16px 16px 0 0; box-shadow: 0 -8px 30px rgba(0,0,0,0.1); }
}
</style>
