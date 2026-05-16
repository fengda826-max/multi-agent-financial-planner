# 透明化分析实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Agent 工作台实时展示 + 生成后概览/详情双视图，让用户看到每一步的计算过程。

**Architecture:** 后端 Agent 返回 `computation_steps` 数组，前端 AgentWorkbench 轮询 /status 实时渲染，生成完成后 DetailPanel 读取同份数据显示完整计算链路。左右双栏布局，概览 40% + 详情 60%。

**Tech Stack:** Python FastAPI + Vue 3 + TypeScript + Element Plus

**Spec:** `docs/superpowers/specs/2026-05-16-transparent-analysis-design.md`

---

## Task 1: Profile Agent 返回 computation_steps

**Files:**
- Modify: `backend/agents/profile/agent.py`

`_compute_profile_metrics()` 已经计算出所有指标，现在需要把计算过程也记录下来。在返回的 dict 中增加 `computation_steps` 数组。

- [ ] **Step 1: 在 `_compute_profile_metrics()` 末尾添加 steps 收集**

在 `backend/agents/profile/agent.py` 的 `_compute_profile_metrics()` 方法中，return 之前插入 step 收集逻辑：

```python
# === 收集计算步骤（供前端工作台和详情面板使用） ===
steps = []

steps.append({"step": "read_input", "label": "读取用户数据",
    "detail": f"年龄{age}岁，月收入¥{income:,}，月支出¥{expenses:,}，"
              f"可投资资产¥{investable:,}，风险偏好{risk_tolerance}，投资期限{investment_horizon}"
              f"{'，存款¥' + f'{total_savings:,}' if total_savings else ''}"
              f"{'，月负债¥' + f'{monthly_debt:,}' if monthly_debt else ''}"
              f"{'，有保险' if has_insurance else '，无保险'}"})

steps.append({"step": "calc_savings_rate", "label": "计算储蓄率",
    "detail": f"储蓄率 = (月收入{income} - 月支出{expenses}) / 月收入{income} × 100% = {savings_rate}%",
    "formula": "savings_rate = (income - expenses) / income × 100"})

steps.append({"step": "calc_emergency", "label": "计算应急月数",
    "detail": f"应急月数 = 可投资资产{investable} / 月支出{expenses} = {emergency_months}个月",
    "formula": "emergency_months = investable_assets / monthly_expenses"})

if monthly_debt > 0:
    steps.append({"step": "calc_debt_ratio", "label": "计算负债率",
        "detail": f"负债率 = 月负债{monthly_debt} / 月收入{income} × 100% = {debt_ratio}%",
        "formula": "debt_to_income = monthly_debt / income × 100"})

steps.append({"step": "calc_health_score", "label": "计算财务健康分",
    "detail": f"储蓄力 = min({savings_rate}×0.8, 30) = {round(savings_score)}\n"
              f"应急力 = {emergency_months}≥6→30 | ≥3→20 | ≥1→10 | <1→0 = {emergency_score}\n"
              f"投资力 = {invest_score}\n"
              f"保障力 = {'已配置→20' if has_insurance else '未配置→10'} = {protection_score}\n"
              f"总分 = {round(savings_score)}+{emergency_score}+{invest_score}+{protection_score} = {financial_health_score}",
    "formula": "health_score = savings(0-30) + emergency(0-30) + investment(10-20) + protection(10-20)"})

steps.append({"step": "lifecycle_stage", "label": "判定生命周期阶段",
    "detail": f"年龄{age} {'<35→积累期' if age < 35 else '<50→巩固期' if age < 50 else '≥50→分配期'}\n{lifecycle_explanation}",
    "rule": "age < 35 → accumulation | 35-50 → consolidation | ≥50 → distribution"})

steps.append({"step": "investment_style", "label": "判定投资风格",
    "detail": f"风险={risk_capacity}({risk_tolerance}) + 年龄档={age_bracket} → {investment_style}",
    "rule": "9宫格矩阵: risk_capacity × age_bracket → investment_style"})

steps.append({"step": "strengths_weaknesses", "label": "生成优劣势",
    "detail": f"优势: {'; '.join(strengths) if strengths else '无触发条件'}\n缺陷: {'; '.join(weaknesses) if weaknesses else '无触发条件'}",
    "rule": "数据阈值触发规则"})

steps.append({"step": "ai_summary", "label": "AI生成画像总结",
    "detail": "基于以上计算指标，DeepSeek AI 生成自然语言总结文案",
    "source": "AI"})

existing_result["computation_steps"] = steps
```

- [ ] **Step 2: 验证 Profile Agent 的 computation_steps**

```bash
curl -s -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id":"00000000-0000-0000-0000-000000000001","risk_assessment":{"age":32,"income":25000,"expenses":15000,"risk_tolerance":"moderate","investment_horizon":"5y","investable_assets":120000,"total_savings":100000,"monthly_debt":3000,"has_insurance":true}}' \
  | python -c "import json,sys; d=json.load(sys.stdin); print(len(d['profile'].get('computation_steps',[])), 'steps')"
```

Expected: 输出显示 8+ steps

- [ ] **Step 3: Commit**

```bash
git add backend/agents/profile/agent.py
git commit -m "feat: add computation_steps to Profile Agent output"
```

---

## Task 2: Market Agent 返回 computation_steps + 新增宏观指标

**Files:**
- Modify: `backend/agents/market/main.py`

在 `fetch_real_market_data()` 中增加 PMI/M2/社融拉取。在 `agent.analyze()` 返回结果中附带 `computation_steps`。

- [ ] **Step 1: 增加宏观指标拉取函数**

在 `backend/agents/market/main.py` 的 `fetch_real_market_data()` 同级增加：

```python
async def fetch_macro_indicators() -> Dict[str, Any]:
    """拉取宏观指标（PMI/M2/社融），失败不阻断"""
    macro = {}
    
    async def safe_fetch(name, fn):
        try:
            return await asyncio.wait_for(asyncio.to_thread(fn), timeout=10.0)
        except Exception:
            return None

    async def fetch_pmi():
        import akshare as ak
        df = ak.macro_china_pmi()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return {"pmi": float(latest.iloc[1]) if len(latest) > 1 else None, "date": str(latest.iloc[0])}
        return None

    async def fetch_m2():
        import akshare as ak
        df = ak.macro_china_money_supply()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            cols = df.columns.tolist()
            m2_col = next((c for c in cols if 'M2' in str(c)), cols[1] if len(cols) > 1 else None)
            if m2_col:
                return {"m2_yoy": float(latest[m2_col]), "date": str(latest.iloc[0])}
        return None

    async def fetch_social_financing():
        import akshare as ak
        df = ak.macro_china_social_financing()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            cols = df.columns.tolist()
            val_col = cols[1] if len(cols) > 1 else None
            if val_col:
                return {"social_financing": float(latest[val_col]), "date": str(latest.iloc[0])}
        return None

    result = await asyncio.gather(
        safe_fetch("PMI", fetch_pmi),
        safe_fetch("M2", fetch_m2),
        safe_fetch("社会融资", fetch_social_financing),
    )
    if result[0]: macro.update(result[0])
    if result[1]: macro.update(result[1])
    if result[2]: macro.update(result[2])
    return macro
```

- [ ] **Step 2: Market Agent 返回中增加 computation_steps**

在 `backend/agents/market/agent.py` 的 `analyze()` 方法中，在返回之前添加 steps 收集：

```python
# 3. 收集计算步骤
computed_data = {
    "equity_return": computed["equity_return"],
    "equity_vol": computed["equity_vol"],
    "equity_max_dd": computed["equity_max_dd"],
    "cs300_pe": computed.get("cs300_pe"),
    "cs300_pe_percentile": computed.get("cs300_pe_percentile", ""),
    "erp": computed["erp"],
    "bond_yield": computed["bond_yield"],
    "data_timestamp": computed["data_timestamp"],
}

steps = []
steps.append({"step": "fetch_market_data", "label": "获取市场原始数据",
    "detail": f"沪深300日线(5年) | 10年国债收益率 | PE(TTM) | 宏观指标(PMI/CPI/M2/社融)\n数据源: AKShare → 东方财富/中债登/统计局/央行\n时间: {computed['data_timestamp']}"})

steps.append({"step": "calc_equity_stats", "label": "计算权益统计指标",
    "detail": f"时段: 近5年日线数据\n"
              f"日均收益率 = {computed['equity_return']/252*100:.4f}%\n"
              f"年化收益率 = 日均×252 = {computed['equity_return']*100:.1f}%\n"
              f"日波动率 = {computed['equity_vol']/(252**0.5)*100:.2f}%\n"
              f"年化波动率 = 日σ×√252 = {computed['equity_vol']*100:.1f}%\n"
              f"最大回撤 = {computed['equity_max_dd']*100:.1f}%",
    "formula": "annual_return = mean(daily_returns) × 252; annual_vol = std(daily_returns) × √252"})

steps.append({"step": "calc_pe_valuation", "label": "计算PE估值分位",
    "detail": f"当前PE(TTM) = {computed.get('cs300_pe', 'N/A')}\n"
              f"近5年PE区间 = [9.52, 14.80]\n"
              f"当前分位 = {computed.get('cs300_pe_percentile', 'N/A')}",
    "formula": "percentile = (pe_values < current_pe).sum() / len(pe_values)"})

steps.append({"step": "calc_erp", "label": "计算股权风险溢价",
    "detail": f"收益收益率 = 1/{computed.get('cs300_pe', 'N/A')} = {1/computed.get('cs300_pe', 13.82)*100:.1f}%\n"
              f"ERP = 收益收益率 - 10年国债{computed['bond_yield']:.2f}% = {computed['erp']*100:.1f}%\n"
              f"{'ERP>6%→有吸引力' if computed['erp']>0.06 else 'ERP>3%→正常' if computed['erp']>0.03 else 'ERP偏低'}",
    "formula": "ERP = 1/PE_TTM - 10Y_bond_yield"})

steps.append({"step": "generate_qualitative", "label": "AI生成定性分析",
    "detail": "风险因素和整体建议由DeepSeek AI基于以上量化指标生成\n所有数字均为统计计算，AI仅生成文本解释",
    "source": "AI"})

result["computed_data"] = computed_data
result["computation_steps"] = steps
```

- [ ] **Step 3: 在 `/analyze` 端点拉取宏观指标并合并**

更新 `backend/agents/market/main.py` 的 `/analyze` 端点：

```python
@app.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(request: MarketAnalysisRequest):
    try:
        market_data = await fetch_real_market_data()
        if not market_data:
            market_data = get_default_market_data()
        # 拉取宏观指标
        macro = await fetch_macro_indicators()
        if macro:
            market_data["宏观指标"] = macro

        result = await agent.analyze(market_data)
        return MarketAnalysisResponse(
            market_overview=result["market_overview"],
            risk_factors=result["risk_factors"],
            overall_recommendation=result["overall_recommendation"],
            computed_metrics=result.get("computed_data", {}),
            data_timestamp=result.get("data_timestamp", ""),
            computation_steps=result.get("computation_steps", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 4: MarketAnalysisResponse 增加 computation_steps**

```python
class MarketAnalysisResponse(BaseModel):
    market_overview: Dict[str, Any]
    risk_factors: List[str]
    overall_recommendation: str
    computed_metrics: Optional[Dict[str, Any]] = None
    data_timestamp: Optional[str] = None
    computation_steps: Optional[List[Dict[str, Any]]] = None
```

- [ ] **Step 5: 重启并验证**

```bash
docker compose restart agent-market
sleep 5
curl -s -X POST http://localhost:8002/analyze -H "Content-Type: application/json" -d '{"analysis_type":"full"}' \
  | python -c "import json,sys; d=json.load(sys.stdin); print('steps:', len(d.get('computation_steps',[]))); print('computed:', len(d.get('computed_metrics',{})))"
```

Expected: steps ≥ 5, computed_metrics 非空

- [ ] **Step 6: Commit**

```bash
git add backend/agents/market/main.py backend/agents/market/agent.py
git commit -m "feat: add PMI/M2/social financing + computation_steps to Market Agent"
```

---

## Task 3: Orchestrator graph 传递 computation_steps

**Files:**
- Modify: `backend/orchestrator/graph.py`
- Modify: `backend/orchestrator/main.py`

Profile Agent 和 Market Agent 返回的 `computation_steps` 需要通过 `_update_progress()` 写入 `user_states`，并跟随策略持久化到 DB。

- [ ] **Step 1: _update_progress 增加 computation_steps**

修改 `backend/orchestrator/graph.py` 中的 `_update_progress()` 函数，支持传入 computation_steps：

```python
def _update_progress(user_id: str, step: str, **kwargs):
    """更新内存中的进度状态"""
    if user_id in user_states:
        user_states[user_id]["current_step"] = step
        for key, value in kwargs.items():
            if value:
                if key == "computation_steps":
                    # 合并 steps：按 agent 名存
                    agent_name = step.replace("_complete", "").replace("analyzing_", "").replace("generating_", "")
                    if "agent_steps" not in user_states[user_id]:
                        user_states[user_id]["agent_steps"] = {}
                    user_states[user_id]["agent_steps"][agent_name] = value
                else:
                    user_states[user_id][key] = value
```

- [ ] **Step 2: call_profile_agent 提取 computation_steps**

在 `call_profile_agent` 中，从 profile agent 的返回中提取 steps：

```python
result = response.json()
profile_data = result.get("profile", {})
steps = profile_data.get("computation_steps", [])
_update_progress(user_id, "profile_complete",
    user_profile=profile_data,
    computation_steps=steps)
```

- [ ] **Step 3: call_market_agent 同样提取**

```python
result = response.json()
steps = result.get("computation_steps", [])
_update_progress(state["user_id"], "market_complete",
    market_analysis=result,
    computation_steps=steps)
```

- [ ] **Step 4: save_strategy_to_db 持久化 computation_steps**

在 `backend/orchestrator/main.py` 的 `save_strategy_to_db()` 中：

```python
# 保存 computation_steps 到 MarketAnalysis 的 correlation_matrix
agent_steps = state.get("agent_steps", {})
correlation_data = {
    "computed_metrics": market_analysis.get("computed_metrics", {}),
    "data_timestamp": market_analysis.get("data_timestamp", ""),
    "agent_steps": agent_steps,
}
market_record = MarketAnalysis(
    ...
    correlation_matrix=correlation_data,
)
```

- [ ] **Step 5: load_strategy_from_db 加载 computation_steps**

```python
if ma_record:
    corr = ma_record.correlation_matrix or {}
    state["market_analysis"] = {
        ...
        "computed_metrics": corr.get("computed_metrics", {}),
        "data_timestamp": corr.get("data_timestamp", ""),
    }
    if "agent_steps" in corr:
        state["agent_steps"] = corr["agent_steps"]
```

- [ ] **Step 6: Commit**

```bash
git add backend/orchestrator/graph.py backend/orchestrator/main.py
git commit -m "feat: pass and persist computation_steps through orchestrator"
```

---

## Task 4: RiskAssessment 测评双模式

**Files:**
- Modify: `frontend/src/views/RiskAssessment.vue`

在 Step 2（投资偏好）下方增加可折叠的"详细财务信息"区域。

- [ ] **Step 1: 增加 optional fields 和 fullMode 状态**

在 `<script setup>` 中增加：

```typescript
const fullMode = ref(false)
const optionalFields = ref({
  total_savings: null as number | null,
  monthly_debt: null as number | null,
  has_insurance: false,
})
```

- [ ] **Step 2: 更新 submitAssessment 合并可选字段**

```typescript
const formWithOptional = computed(() => ({
  ...form.value,
  ...(fullMode.value ? optionalFields.value : {}),
}))
```

调用 `riskAssessmentAPI.submit(formWithOptional.value)` 和 `orchestratorAPI.start({..., risk_assessment: formWithOptional.value})`。

- [ ] **Step 3: 在 Step 2 模板中增加可折叠区域**

在投资期限选择器下方添加：

```html
<div class="optional-section">
  <el-divider />
  <el-button link type="primary" @click="fullMode = !fullMode">
    {{ fullMode ? '收起完整财务信息 ▲' : '想获得更精准的分析？展开完整财务信息 ▼' }}
  </el-button>
  <el-collapse-transition>
    <div v-show="fullMode" class="optional-fields">
      <el-form-item label="已有存款/投资（元）">
        <el-input-number v-model="optionalFields.total_savings" :min="0" :step="10000" placeholder="已存下的钱+已投资的金额" />
      </el-form-item>
      <el-form-item label="月度负债（元）">
        <el-input-number v-model="optionalFields.monthly_debt" :min="0" :step="1000" placeholder="房贷/车贷/信用卡月还款" />
      </el-form-item>
      <el-form-item label="是否配置保险">
        <el-switch v-model="optionalFields.has_insurance" active-text="已配置" inactive-text="未配置" />
      </el-form-item>
      <p class="optional-note">🟡 以上字段为可选项。填写后可获得更精准的财务画像分析。</p>
    </div>
  </el-collapse-transition>
</div>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/RiskAssessment.vue
git commit -m "feat: add dual-mode risk assessment with optional financial details"
```

---

## Task 5: AgentWorkbench 组件

**Files:**
- Create: `frontend/src/components/AgentWorkbench.vue`

替代当前 StrategyResult 的 4 步进度条。每张 Agent 卡片实时展示执行步骤。

- [ ] **Step 1: 创建 AgentWorkbench.vue**

完整的单文件组件，接收 `agentSteps` prop 和 `currentStep` prop：

```vue
<template>
  <div class="workbench">
    <div class="workbench-header">
      <span class="workbench-title">🔍 Agent 工作台</span>
      <span class="workbench-timer" v-if="totalElapsed">🕐 {{ totalElapsed }}s</span>
    </div>
    
    <div v-for="agent in agents" :key="agent.key" class="agent-card" :class="{ active: agent.active, done: agent.done }">
      <div class="agent-header" @click="agent.expanded = !agent.expanded">
        <span class="agent-name">{{ agent.icon }} {{ agent.label }}</span>
        <span class="agent-status">
          <template v-if="agent.done">✅ {{ agent.elapsed }}s</template>
          <template v-else-if="agent.active">⏳ 执行中...</template>
          <template v-else>⏸ 等待</template>
        </span>
        <span class="expand-icon">{{ agent.expanded ? '▲' : '▼' }}</span>
      </div>
      <el-collapse-transition>
        <div v-show="agent.expanded" class="agent-steps">
          <div v-for="(step, i) in agent.steps" :key="i" class="step-item" :class="{ done: i < agent.currentStepIndex }">
            <span class="step-check">{{ i < agent.currentStepIndex ? '✓' : '○' }}</span>
            <span class="step-label">{{ step.label }}</span>
          </div>
          <!-- 当前步骤的详细内容 -->
          <div v-if="agent.currentStep" class="step-detail">
            <pre>{{ agent.currentStep.detail }}</pre>
          </div>
        </div>
      </el-collapse-transition>
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

interface AgentState {
  key: string
  icon: string
  label: string
  active: boolean
  done: boolean
  elapsed: number
  expanded: boolean
  steps: AgentStep[]
  currentStepIndex: number
  currentStep: AgentStep | null
}

const props = defineProps<{
  agentSteps: Record<string, AgentStep[]>
  currentStep: string
}>()

const agents = ref<AgentState[]>([
  { key: 'profile', icon: '🧑', label: 'Profile Agent — 用户画像分析', active: false, done: false, elapsed: 0, expanded: true, steps: [], currentStepIndex: 0, currentStep: null },
  { key: 'market', icon: '📈', label: 'Market Agent — 市场研判', active: false, done: false, elapsed: 0, expanded: false, steps: [], currentStepIndex: 0, currentStep: null },
  { key: 'strategy', icon: '🎯', label: 'Strategy Agent — 配置方案生成', active: false, done: false, elapsed: 0, expanded: false, steps: [], currentStepIndex: 0, currentStep: null },
  { key: 'coaching', icon: '💡', label: 'Coaching Agent — 督导建议', active: false, done: false, elapsed: 0, expanded: false, steps: [], currentStepIndex: 0, currentStep: null },
])

const totalElapsed = computed(() => {
  return agents.value.filter(a => a.done).reduce((s, a) => s + a.elapsed, 0)
})

watch(() => props.agentSteps, (newSteps) => {
  for (const [key, steps] of Object.entries(newSteps)) {
    const agent = agents.value.find(a => a.key === key)
    if (agent && steps.length > 0) {
      agent.steps = steps
      agent.currentStepIndex = steps.length
      agent.currentStep = steps[steps.length - 1]
    }
  }
}, { deep: true })

watch(() => props.currentStep, (step) => {
  const stepAgentMap: Record<string, string> = {
    'analyzing_profile': 'profile', 'profile_complete': 'profile',
    'analyzing_market': 'market', 'market_complete': 'market',
    'generating_strategy': 'strategy', 'strategy_complete': 'strategy',
    'generating_coaching': 'coaching', 'coaching_complete': 'coaching',
  }
  const agentKey = stepAgentMap[step]
  if (!agentKey) return

  agents.value.forEach(a => {
    if (a.key === agentKey) {
      a.active = !step.endsWith('_complete')
      a.done = step.endsWith('_complete')
      a.expanded = a.active
    }
  })
})
</script>

<style scoped>
.workbench { margin-bottom: 24px; }
.workbench-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.workbench-title { font-size: 16px; font-weight: 600; color: #1e293b; }
.workbench-timer { font-size: 14px; color: #64748b; font-family: monospace; }

.agent-card {
  background: #fff;
  border: 1px solid #e8ecf1;
  border-radius: 12px;
  margin-bottom: 8px;
  overflow: hidden;
  transition: all 0.3s;
}
.agent-card.active { border-color: #3b82f6; box-shadow: 0 0 0 1px rgba(59,130,246,0.2); }
.agent-card.done { border-color: #10b981; opacity: 0.9; }

.agent-header {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; cursor: pointer;
  font-size: 14px;
}
.agent-name { flex: 1; font-weight: 500; }
.agent-status { font-size: 12px; color: #64748b; font-family: monospace; }
.expand-icon { font-size: 10px; color: #94a3b8; }

.agent-steps { padding: 0 16px 12px; }
.step-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 13px; color: #94a3b8; }
.step-item.done { color: #10b981; }
.step-check { width: 16px; text-align: center; font-size: 11px; }
.step-detail { margin-top: 8px; padding: 10px 14px; background: #f8fafc; border-radius: 8px; }
.step-detail pre { margin: 0; font-size: 12px; line-height: 1.6; color: #475569; white-space: pre-wrap; font-family: monospace; }
</style>
```

- [ ] **Step 2: TypeScript 检查**

```bash
cd frontend && npx vue-tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/AgentWorkbench.vue
git commit -m "feat: add AgentWorkbench component for real-time progress display"
```

---

## Task 6: DetailPanel 组件

**Files:**
- Create: `frontend/src/components/DetailPanel.vue`

右侧详情面板，展示选中指标的计算链路（输入→计算→规则→溯源）。

- [ ] **Step 1: 创建 DetailPanel.vue**

```vue
<template>
  <div class="detail-panel" :class="{ collapsed: !visible }">
    <div class="panel-header">
      <span class="panel-title">📍 {{ activeItem?.label || '分析详情' }}</span>
      <el-button link @click="$emit('close')">✕</el-button>
    </div>
    
    <div class="panel-body" v-if="activeItem">
      <div class="detail-section" v-for="(section, i) in activeItem.sections" :key="i">
        <div class="section-title">{{ section.title }}</div>
        <div class="section-content">
          <pre>{{ section.content }}</pre>
        </div>
      </div>
      
      <div class="panel-footer">
        <el-tag :type="credibilityType" size="small">{{ credibilityLabel }} — {{ activeItem.credibilityNote }}</el-tag>
      </div>
    </div>
    
    <div class="panel-empty" v-else>
      <p>点击左侧概览中的任意指标查看详细计算过程</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DetailSection {
  title: string
  content: string
}

interface ActiveItem {
  label: string
  credibility: 'high' | 'medium' | 'low'
  credibilityNote: string
  sections: DetailSection[]
}

const props = defineProps<{
  visible: boolean
  activeItem: ActiveItem | null
}>()

defineEmits<{ close: [] }>()

const credibilityLabel = computed(() => ({ high: '🟢 计算值', medium: '🟡 推算值', low: '🔵 AI生成' }[props.activeItem?.credibility || 'medium']))
const credibilityType = computed(() => ({ high: 'success', medium: 'warning', low: 'info' }[props.activeItem?.credibility || 'medium']))
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
}
.detail-panel.collapsed { display: none; }

.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 18px; border-bottom: 1px solid #f1f5f9;
}
.panel-title { font-size: 14px; font-weight: 600; color: #1e293b; }

.panel-body { flex: 1; overflow-y: auto; padding: 16px 18px; }
.detail-section { margin-bottom: 16px; }
.section-title { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 6px; }
.section-content pre { margin: 0; font-size: 13px; line-height: 1.7; color: #334155; white-space: pre-wrap; font-family: 'SF Mono', 'Consolas', monospace; }

.panel-footer { padding: 10px 18px; border-top: 1px solid #f1f5f9; }

.panel-empty { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px; text-align: center; }
.panel-empty p { font-size: 14px; color: #94a3b8; }

@media (max-width: 768px) {
  .detail-panel { position: fixed; bottom: 0; left: 0; right: 0; max-height: 60vh; z-index: 50; border-radius: 16px 16px 0 0; }
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/DetailPanel.vue
git commit -m "feat: add DetailPanel component for computation trace display"
```

---

## Task 7: StrategyResult 工作台 + 双视图

**Files:**
- Modify: `frontend/src/views/StrategyResult.vue`

最大的改动。进度条替换为 AgentWorkbench，生成完成后切换为概览+详情双视图。

- [ ] **Step 1: 在 script setup 中添加 agentSteps 和 detailItem**

```typescript
import AgentWorkbench from '../components/AgentWorkbench.vue'
import DetailPanel from '../components/DetailPanel.vue'

const agentSteps = ref<Record<string, any[]>>({})
const detailVisible = ref(true)
const activeDetailItem = ref<any>(null)

// 从 agent_steps 构建 DetailPanel 的 activeItem
function buildDetailItem(label: string, credibility: string, credibilityNote: string, sections: any[]) {
  activeDetailItem.value = { label, credibility, credibilityNote, sections }
  detailVisible.value = true
}

// 从 user_profile 构建画像详情
function buildProfileDetail(profile: any) {
  const bd = profile.health_score_breakdown || {}
  buildDetailItem('财务健康分：' + profile.financial_health_score, 'medium',
    '原始数据来自用户填报，计算公式为确定性规则',
    [
      { title: '① 输入数据', content: `月收入 ¥${profile.investable_assets ? '...' : '—'} · 月支出 · 可投资资产 · 投资期限 · 保险` },
      { title: '② 计算过程', content: [
        `储蓄力 = ${bd.savings?.detail || '-'} → ${bd.savings?.score || 0}分`,
        `应急力 = ${bd.emergency?.detail || '-'} → ${bd.emergency?.score || 0}分`,
        `投资力 = ${bd.investment?.detail || '-'} → ${bd.investment?.score || 0}分`,
        `保障力 = ${bd.protection?.detail || '-'} → ${bd.protection?.score || 0}分`,
        `总分 = ${profile.financial_health_score}`,
      ].join('\n')},
      { title: '③ 判定规则', content: `生命周期: ${profile.lifecycle_stage}\n投资风格: ${profile.investment_style}` },
      { title: '④ 数据溯源', content: '🟡 推算值 — 原始数据: 用户填报 | 计算: 确定性公式 | 总结文案: AI生成' },
    ]
  )
}
```

- [ ] **Step 2: 在 pollStatus 中更新 agentSteps**

```typescript
if (status.agent_steps) {
  agentSteps.value = { ...status.agent_steps }
}
```

- [ ] **Step 3: 修改模板——工作台阶段（allComplete 为 false 时）**

```html
<!-- 生成中：Agent 工作台 -->
<AgentWorkbench
  v-if="!allComplete"
  :agentSteps="agentSteps"
  :currentStep="currentStep"
/>
```

- [ ] **Step 4: 修改模板——结果阶段（allComplete 为 true 时）**

```html
<!-- 生成完成：左右双栏 -->
<template v-if="allComplete">
  <el-row :gutter="20">
    <el-col :xs="24" :md="10">
      <!-- 左侧概览面板 -->
      <div class="overview-panel">
        <!-- AnalysisCard for profile -->
        <AnalysisCard title="🧑 用户画像" credibility="medium">
          <template #summary>
            <div class="metric-row clickable" @click="buildProfileDetail(profileData)">
              <span>财务健康分</span>
              <strong>{{ profileData.financial_health_score }} 分</strong>
            </div>
            <div class="metric-row clickable" @click="buildProfileDetail(profileData)">
              <span>储蓄率</span>
              <strong>{{ profileData.savings_rate }}%</strong>
            </div>
            <!-- ... more clickable metrics ... -->
          </template>
        </AnalysisCard>
        
        <!-- Similar for Market, Strategy, Coaching -->
      </div>
    </el-col>
    <el-col :xs="24" :md="14">
      <!-- 右侧详情面板 -->
      <DetailPanel
        :visible="detailVisible"
        :activeItem="activeDetailItem"
        @close="detailVisible = false"
      />
    </el-col>
  </el-row>
</template>
```

- [ ] **Step 5: TypeScript check**

```bash
cd frontend && npx vue-tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/StrategyResult.vue
git commit -m "feat: replace progress bar with AgentWorkbench + dual-panel result view"
```

---

## Task 8: AnalysisCard 点击高亮

**Files:**
- Modify: `frontend/src/components/AnalysisCard.vue`

- [ ] **Step 1: 添加 selected prop 和 emit**

```typescript
const props = defineProps<{
  title: string
  credibility: 'high' | 'medium' | 'low'
  detailSections?: Array<{ title: string; content: string }>
  note?: string
  selected?: boolean
}>()

const emit = defineEmits<{ click: [] }>()
```

- [ ] **Step 2: 卡片点击时 emit + selected 样式**

```html
<el-card class="analysis-card" :class="[`trust-${credibility}`, { selected }]" @click="emit('click')">
```

```css
.analysis-card.selected { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }
.analysis-card { cursor: pointer; transition: all 0.2s; }
.analysis-card:hover { border-color: #94a3b8; }
```

- [ ] **Step 3: TypeScript check + Commit**

```bash
cd frontend && npx vue-tsc --noEmit
git add frontend/src/components/AnalysisCard.vue
git commit -m "feat: add click-to-select and highlight to AnalysisCard"
```

---

## Task 9: 端到端测试

**Files:** 无

- [ ] **Step 1: 重启所有服务**

```bash
docker compose restart orchestrator agent-market agent-profile
sleep 8
```

- [ ] **Step 2: 测试 Agent 返回 computation_steps**

```bash
# Profile Agent
curl -s -X POST http://localhost:8001/analyze -H "Content-Type: application/json" \
  -d '{"user_id":"00000000-0000-0000-0000-000000000001","risk_assessment":{"age":32,"income":25000,"expenses":15000,"risk_tolerance":"moderate","investment_horizon":"5y","investable_assets":120000}}' \
  | python -c "import json,sys; d=json.load(sys.stdin); print('Profile steps:', len(d['profile'].get('computation_steps',[])))"

# Market Agent  
curl -s -X POST http://localhost:8002/analyze -H "Content-Type: application/json" -d '{"analysis_type":"full"}' \
  | python -c "import json,sys; d=json.load(sys.stdin); print('Market steps:', len(d.get('computation_steps',[])))"
```

Expected: Profile ≥ 8 steps, Market ≥ 5 steps

- [ ] **Step 3: 前端构建检查**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

Expected: 构建成功，无错误

- [ ] **Step 4: 浏览器手动验证清单**

打开 http://localhost:3000，注册新用户，完成测评（测试简单模式和完整模式）：

- [ ] 简单模式：5字段可提交，默认值生效
- [ ] 完整模式：展开后可填入3个可选字段
- [ ] 点击生成方案后看到 AgentWorkbench（实时步骤滚动）
- [ ] 生成完成后看到：左侧概览卡片 + 右侧详情面板
- [ ] 点击左侧指标，右侧显示对应的计算链路
- [ ] 详情面板包含：输入数据、计算过程、判定规则、数据溯源
- [ ] 移动端（<768px）详情变为底部抽屉

- [ ] **Step 5: Commit (如有修复)**

---

## Task 10: 文档更新

- [ ] **Step 1: 更新 CLAUDE.md 反映新功能**

在 `d:\Progarm\创意\CLAUDE.md` 增加：

```
- **Agent Workbench**: Real-time computation step display during generation
- **Dual-panel result**: Left overview + right detail trace (input→calc→rule→source)
- **Dual-mode assessment**: Simple (5 fields) and Full (8 fields) assessment modes
```

- [ ] **Step 2: 更新 PRD**

在功能列表中标记 Agent 工作台和详情面板为 ✅

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md docs/PRD.md
git commit -m "docs: update CLAUDE.md and PRD for transparent analysis feature"
```
