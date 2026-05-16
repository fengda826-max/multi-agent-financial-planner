<template>
  <div class="workbench">
    <div class="workbench-header">
      <span class="workbench-title">Agent 工作台</span>
      <span class="workbench-timer" v-if="totalElapsed">累计 {{ totalElapsed }}s</span>
    </div>

    <div v-for="agent in agents" :key="agent.key" class="agent-card" :class="{ active: agent.active, done: agent.done }">
      <div class="agent-header" @click="agent.expanded = !agent.expanded">
        <span class="agent-name">{{ agent.icon }} {{ agent.label }}</span>
        <span class="agent-status">
          <template v-if="agent.done">已完成 · {{ agent.elapsed }}s</template>
          <template v-else-if="agent.active">执行中...</template>
          <template v-else>等待中</template>
        </span>
        <span class="expand-icon">{{ agent.expanded ? '▼' : '▶' }}</span>
      </div>
      <div v-show="agent.expanded" class="agent-steps">
        <div v-for="(step, i) in agent.steps" :key="i" class="step-item" :class="{ done: i < agent.currentIndex }">
          <span class="step-check">{{ i < agent.currentIndex ? '✓' : agent.active ? '○' : '—' }}</span>
          <span class="step-label">{{ step.label }}</span>
        </div>
        <div v-if="agent.lastStepDetail && agent.active" class="step-detail">
          <pre>{{ agent.lastStepDetail }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface AgentStep {
  step: string
  label: string
  detail: string
  formula?: string
  rule?: string
  source?: string
}

const props = defineProps<{
  agentSteps: Record<string, AgentStep[]>
  currentStep: string
}>()

const agents = ref([
  { key: 'profile', icon: '🧑', label: '用户画像分析', active: false, done: false, elapsed: 0, expanded: true, steps: [] as AgentStep[], currentIndex: 0, lastStepDetail: '' },
  { key: 'market', icon: '📈', label: '市场研判', active: false, done: false, elapsed: 0, expanded: false, steps: [] as AgentStep[], currentIndex: 0, lastStepDetail: '' },
  { key: 'strategy', icon: '🎯', label: '配置方案生成', active: false, done: false, elapsed: 0, expanded: false, steps: [] as AgentStep[], currentIndex: 0, lastStepDetail: '' },
  { key: 'coaching', icon: '💡', label: '督导建议', active: false, done: false, elapsed: 0, expanded: false, steps: [] as AgentStep[], currentIndex: 0, lastStepDetail: '' },
])

const totalElapsed = computed(() => {
  return agents.value.filter(a => a.done).reduce((s, a) => s + a.elapsed, 0)
})

const stepAgentMap: Record<string, string> = {
  'analyzing_profile': 'profile', 'profile_complete': 'profile',
  'analyzing_market': 'market', 'market_complete': 'market',
  'generating_strategy': 'strategy', 'strategy_complete': 'strategy',
  'generating_coaching': 'coaching', 'coaching_complete': 'coaching',
}

watch(() => props.agentSteps, (newSteps) => {
  if (!newSteps) return
  for (const [key, steps] of Object.entries(newSteps)) {
    const agent = agents.value.find(a => a.key === key)
    if (agent && Array.isArray(steps) && steps.length > 0) {
      agent.steps = steps
      agent.currentIndex = steps.length
      const last = steps[steps.length - 1]
      if (last) agent.lastStepDetail = last.detail || ''
    }
  }
}, { deep: true })

watch(() => props.currentStep, (step) => {
  const agentKey = stepAgentMap[step]
  if (!agentKey) return
  agents.value.forEach(a => {
    if (a.key === agentKey) {
      a.active = !step.endsWith('_complete')
      a.done = step.endsWith('_complete')
      if (a.active && !a.expanded) a.expanded = true
    }
  })
})
</script>

<style scoped>
.workbench { margin-bottom: 20px; }
.workbench-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.workbench-title { font-size: 15px; font-weight: 600; color: #1e293b; }
.workbench-timer { font-size: 13px; color: #64748b; font-family: monospace; }

.agent-card {
  background: #fff;
  border: 1px solid #e8ecf1;
  border-radius: 10px;
  margin-bottom: 6px;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.agent-card.active { border-color: #3b82f6; box-shadow: 0 0 0 1px rgba(59,130,246,0.15); }
.agent-card.done { border-color: #e8ecf1; opacity: 0.85; }

.agent-header {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; cursor: pointer;
  font-size: 13px; user-select: none;
}
.agent-header:hover { background: #f8fafc; }
.agent-name { flex: 1; font-weight: 500; color: #1e293b; }
.agent-status { font-size: 11px; color: #64748b; font-family: monospace; }
.agent-card.active .agent-status { color: #3b82f6; }
.agent-card.done .agent-status { color: #10b981; }
.expand-icon { font-size: 9px; color: #94a3b8; width: 14px; text-align: center; }

.agent-steps { padding: 0 14px 10px; }
.step-item { display: flex; align-items: center; gap: 6px; padding: 3px 0; font-size: 12px; color: #94a3b8; }
.step-item.done { color: #10b981; }
.step-check { width: 14px; text-align: center; font-size: 10px; flex-shrink: 0; }
.step-detail { margin-top: 6px; padding: 8px 12px; background: #f8fafc; border-radius: 6px; border: 1px solid #f1f5f9; }
.step-detail pre { margin: 0; font-size: 11px; line-height: 1.5; color: #475569; white-space: pre-wrap; font-family: 'SF Mono', 'Consolas', monospace; }
</style>
