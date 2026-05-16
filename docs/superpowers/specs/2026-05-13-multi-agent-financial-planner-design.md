# 多 Agent 协作智能理财规划系统 - 设计文档（v1.1）

> **更新日期：** 2026-05-15  
> **更新说明：** 根据项目实际实现状态更新。新增 ✅ 标记表示已实现，🔲 标记表示待实现。

---

## 1. 项目概述

### 1.1 背景与目标

普通用户面对基金、股票、保险等海量金融产品无从下手，传统理财顾问费用高昂，市面上理财 App 多为单点推荐，缺乏全局资产配置视角。

本系统旨在通过多个专业化 Agent 协作，为用户提供个性化、可解释、动态调优的全生命周期理财规划服务。

### 1.2 核心价值

- **全局视角**：基于"四笔钱"（活钱、稳健、长期、保障）的资产配置框架
- **多 Agent 协作**：专业分工，LLM 推理 + 规则引擎双重保障
- **适当性匹配**：风险等级自动约束权益配置上限 ✅
- **持续陪伴**：AI 对话助手，市场异动检测，用户偏离提醒

### 1.3 项目定位

个人学习/作品集项目，部署在单机 Docker Compose 环境。

---

## 2. 系统架构（C4 模型）

### 2.1 系统上下文图（Level 1）

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户（浏览器）                            │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      多Agent理财规划系统                          │
│                                                                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│   │ 用户画像  │  │ 市场研判  │  │ 策略生成  │  │ 陪伴督导  │       │
│   │   Agent  │  │   Agent  │  │   Agent  │  │   Agent  │       │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
         ↑              ↑              ↑              ↑
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │  用户   │    │ DeepSeek │    │ AKShare  │    │ 事件    │
    │ (前端)  │    │  v4-pro  │    │ 金融数据  │    │ 监控    │
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 2.2 容器图（Level 2）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            用户（浏览器）                                 │
└─────────────────────────────────────────────────────────────────────────┘
                              │ HTTP (Vite dev / Nginx production)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       API Gateway（FastAPI :8000）                       │
│  JWT 认证 | 路由代理 | CORS | Orchestrator 代理                          │
│  /api/auth/* | /api/users/* | /api/risk-assessment/* | /api/orchestrator/*│
└─────────────────────────────────────────────────────────────────────────┘
                              │ HTTP (Docker内部网络)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Orchestrator（FastAPI :8010）                         │
│                                                                          │
│  POST /start      — 启动LangGraph状态图，运行完整4节点流程               │
│  POST /replan     — 重新生成策略（完整重执行）                            │
│  GET /status/{id} — 查询流程状态（内存 → DB回退）                        │
│  POST /chat       — AI对话（代理到Coaching Agent）                       │
│                                                                          │
│  状态图: profile → market → strategy → coaching → END                   │
│  持久化: PostgreSQL (portfolios/strategies/market_analyses)  ✅          │
└─────────────────────────────────────────────────────────────────────────┘
        │               │               │               │
        ▼               ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐
│ 用户画像    │  │ 市场研判    │  │ 策略生成    │  │ 陪伴督导            │
│ Agent      │  │ Agent      │  │ Agent      │  │ Agent              │
│ :8001      │  │ :8002      │  │ :8003      │  │ :8004              │
│            │  │            │  │            │  │                    │
│ POST       │  │ POST       │  │ POST       │  │ POST /interact     │
│ /analyze   │  │ /analyze   │  │ /generate  │  │ POST /event/*      │
└────────────┘  └─────┬──────┘  └─────┬──────┘  │ RabbitMQ Consumer  │
                      │               │         └─────────┬──────────┘
                      │               │                   │
                      ▼               │                   │
              ┌──────────────┐        │                   │
              │  AKShare     │        │                   │
              │  直接调用     │        │                   │
              │  (非MCP)     │        │                   │
              └──────────────┘        │                   │
                                      │                   │
┌─────────────────────────────────────┼───────────────────┼─────────────┐
│                          RabbitMQ   │                   │             │
│  ┌──────────────────────────────────┴───────────────────┘             │
│  │ market.anomaly.* | user.deviation.*                                │
│  └────────────────────────────────────────────────────────────────────│
└───────────────────────────────────────────────────────────────────────┘
      ▲                                           ▲
      │                                           │
┌─────────────────────┐                 ┌─────────────────────┐
│   Market Monitor    │                 │    User Monitor     │
│   🔲 容器未启动      │                 │   🔲 容器未启动      │
│   读取 Redis 缓存    │                 │  查询 DB Portfolios  │
│   发布到 RabbitMQ   │                 │  发布到 RabbitMQ    │
└─────────────────────┘                 └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  PostgreSQL                          │        Redis                      │
│  ✅ 9张表，实际写入4张                 │  🔲 缓存设计完成但未使用           │
│  users/user_profiles/                │                                  │
│  risk_assessments/portfolios/        │                                  │
│  strategies/market_analyses ✅       │                                  │
│  audit_logs/compliance_records/      │                                  │
│  langgraph_checkpoints 🔲            │                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  LLM: DeepSeek v4-pro (via langchain-openai, OpenAI-compatible API)     │
│  Model: deepseek-v4-pro | Base: https://api.deepseek.com/v1             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 组件清单

| # | 组件 | 端口 | 状态 | 职责 |
|---|------|------|------|------|
| 1 | 前端 Vue 3 SPA | :3000 | ✅ Vite dev | 10个页面，ECharts可视化 |
| 2 | API Gateway | :8000 | ✅ | 认证、代理、风险测评API |
| 3 | Orchestrator | :8010 | ✅ | LangGraph编排、/chat、DB持久化 |
| 4 | Profile Agent | :8001 | ✅ | 画像分析（LLM + fallback） |
| 5 | Market Agent | :8002 | ✅ | 市场研判（AKShare优先 → mock回退） |
| 6 | Strategy Agent | :8003 | ✅ | 四笔钱生成 + 适当性约束引擎 |
| 7 | Coaching Agent | :8004 | ✅ | AI对话 + RabbitMQ消费者 |
| 8 | Market Monitor | - | 🔲 容器未启动 | 市场异动检测 |
| 9 | User Monitor | - | 🔲 容器未启动 | 用户偏离检测 |
| 10 | MCP Server | stdio | 🔲 容器未启动 | AKShare MCP工具 (4个) |
| 11 | PostgreSQL | :5432 | ✅ | 数据存储 |
| 12 | Redis | :6379 | ✅ | 缓存（已配置，未使用） |
| 13 | RabbitMQ | :5672 | ✅ | 事件总线（Coaching Agent 已消费） |

---

## 3. Agent 详细设计

### 3.1 Orchestrator（状态图编排）

**职责：**
- 持有 LangGraph 状态图定义，管理全局流程状态
- 为每个用户执行完整规划流程
- 根据条件分支决定消息路由
- 策略结果持久化到 DB（Portfolio/Strategy/MarketAnalysis 三表）
- AI 对话代理到 Coaching Agent（支持 conversation_history）

**接口：**

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/start` | 启动完整规划流程 |
| POST | `/replan` | 重新生成策略（完整重执行） |
| GET | `/status/{user_id}` | 查询状态（内存 → DB 回退） |
| POST | `/chat` | AI 对话（代理到 Coaching Agent） |

**状态图定义（实际实现）：**

```python
# orchestrator/graph.py
workflow = StateGraph(FinancialPlanningState)

workflow.add_node("profile", call_profile_agent)
workflow.add_node("market", call_market_agent)
workflow.add_node("strategy", call_strategy_agent)
workflow.add_node("coaching", call_coaching_agent)

workflow.set_entry_point("profile")

# 条件1: profile → market（正常）/ coaching（需要追问）
workflow.add_conditional_edges("profile", route_after_profile, {
    "coaching": "coaching",
    "market": "market"
})

# market → strategy（固定）
workflow.add_edge("market", "strategy")

# 条件2: strategy → coaching（固定）
workflow.add_conditional_edges("strategy", route_after_strategy, {
    "coaching": "coaching"
})

workflow.add_edge("coaching", END)
```

**实际路由行为：**
- `route_after_profile`: 检查 `needs_followup`。由于 Orchestrator 自动注入 `investable_assets`，此值始终为 `false`，总是路由到 `market`。
- `route_after_strategy`: 始终返回 `"coaching"`。
- 实际路径：`profile → market → strategy → coaching → END`

**状态持久化：**
- ✅ 策略结果（four_buckets/rebalance_triggers/stress_test）→ Portfolio + Strategy 表
- ✅ 市场分析（market_overview/risk_factors）→ MarketAnalysis 表
- ✅ /status 端点优先查内存，不存在时从 DB 加载
- 🔲 LangGraph 本身的 checkpoint 机制未启用（langgraph_checkpoints 表未写入）

**Replan 机制（实际行为）：**
- 接收 `replan_from` 参数但不修改 LangGraph 图入口
- 始终从 `profile` 节点开始完整重执行
- 🔲 节点级重执行未实现（LangGraph 限制）
- 🔲 防抖机制未实现

**并发管理：**
- ✅ 每个用户独立状态（内存 dict + DB 回退）
- 🔲 重规划锁未实现
- 🔲 进程重启后 LangGraph 实例从 checkpoint 恢复（checkpoint 未启用）

### 3.2 用户画像 Agent

**职责：**
- LLM 深度分析用户财务数据
- 输出 12 字段丰富画像：lifecycle_stage + explanation, risk_capacity + explanation, investment_style, financial_health_score, strengths, weaknesses, profile_summary 等

**接口（实际）：**

```
POST /analyze
Request:  { "user_id": "uuid", "risk_assessment": {...} }
Response: {
  "profile": {
    "lifecycle_stage": "accumulation",
    "lifecycle_explanation": "您处于财富积累期...",
    "risk_capacity": "medium",
    "risk_explanation": "基于稳健偏好...",
    "investment_style": "稳健偏成长型",
    "financial_health_score": 85,
    "financial_health_comment": "财务状况良好",
    "strengths": ["月结余8000元", "储蓄率40%"],
    "weaknesses": ["建议增加保障配置"],
    "profile_summary": "30岁积累期，财务基础扎实",
    "investable_assets": 72000,
    "monthly_surplus": 8000
  },
  "needs_followup": false,
  "followup_questions": []
}
```

**内部逻辑：**
- ✅ LLM 调用 (DeepSeek v4-pro, temperature=0.3)
- ✅ Fallback 逻辑：LLM 解析失败时使用 `_default_analysis`（基于年龄+风险偏好）
- ✅ needs_followup：如果提供 investable_assets 则强制 false
- ✅ 结果持久化到 user_profiles 表（API Gateway 风险测评时写入）

### 3.3 市场研判 Agent

**职责：**
- 采集市场数据 + LLM 分析
- 输出预期收益、波动率、风险因素、整体建议

**接口：**

```
POST /analyze
Request:  { "analysis_type": "full", "focus_areas": ["equity","bond","commodity"], "time_horizon": "1y" }
Response: {
  "market_overview": {
    "equity": { "expected_return": 0.08, "volatility": 0.20, "recommendation": "适度配置" },
    "bond": { "expected_return": 0.035, "volatility": 0.05, "recommendation": "标配" },
    "commodity": { "expected_return": 0.05, "volatility": 0.15, "recommendation": "低配观察" }
  },
  "risk_factors": ["利率风险", "地缘政治风险"],
  "overall_recommendation": "均衡配置，股债6:4"
}
```

**数据获取（实际实现）：**
- ✅ 优先尝试 AKShare 获取真实数据（沪深300/创业板指/国债收益率/CPI）
- ✅ AKShare 不可用时回退硬编码默认值
- 🔲 MCP Server 未被调用（Market Agent 直接 import akshare，绕过 MCP）

### 3.4 策略生成 Agent

**职责：**
- LLM 生成四笔钱配置方案
- 适当性规则引擎二次校验
- 输出压力测试 + 再平衡触发器

**接口：**

```
POST /generate
Request:  { "user_id": "uuid", "profile": {...}, "market_analysis": {...} }
Response: {
  "four_buckets": {
    "living_money":     { "allocation": 0.10, "products": [...], "reason": "..." },
    "stable_money":     { "allocation": 0.30, "products": [...], "reason": "..." },
    "growth_money":     { "allocation": 0.50, "products": [...], "reason": "..." },
    "protection_money": { "allocation": 0.10, "products": [...], "reason": "..." }
  },
  "rebalance_triggers": { "drift_threshold": 0.05, "review_frequency": "quarterly" },
  "stress_test": {
    "scenario_2015_crash": { "loss": -0.15, "recovery_time": "8m" },
    "scenario_covid":      { "loss": -0.12, "recovery_time": "4m" }
  }
}
```

**适当性规则引擎（实际实现）：**

| 风险等级 | 权益上限 | 允许产品 |
|----------|---------|---------|
| conservative/low | 20% | 货币基金、债券基金、银行理财、国债 |
| moderate/medium | 60% | 混合基金、指数基金、债券基金 |
| aggressive/high | 90% | 股票、股票基金、期货、期权 |

规则逻辑：LLM 生成方案后，如果 growth_money.allocation > max_equity_allocation，则强制截断，超出部分转入 stable_money。

**Fallback 逻辑（按风险等级预设）：**

| 风险 | 活钱 | 稳健 | 长期 | 保障 |
|------|------|------|------|------|
| low | 15% | 50% | 25% | 10% |
| medium | 10% | 30% | 50% | 10% |
| high | 5% | 20% | 65% | 10% |

### 3.5 陪伴督导 Agent

**职责：**
- AI 对话（支持 conversation_history 上下文）
- 市场异动安抚 + 用户偏离提醒
- RabbitMQ 事件消费

**双重触发机制（实际实现）：**

1. **HTTP 同步调用**（/interact）：
```
POST /interact
{ "user_id": "...", "context": "...", "strategy": {...}, "user_message": "...", "conversation_history": [...] }
→ { "message": "督导回复", "action": "none/followup/replan" }
```

2. **RabbitMQ 异步事件触发** ✅：
```
exchange: market_events (topic)  → queue: coaching.market  (routing: market.anomaly.*)
exchange: user_events (topic)    → queue: coaching.user    (routing: user.deviation.*)
```

**对话记忆** ✅：
- Orchestrator /chat 端点接收 conversation_history
- Coaching Agent 将最近 6 条对话注入 LLM prompt
- 系统提示词包含"记住之前的对话内容"

**Actions：**
- `none`：普通回复
- `followup`：想追问更多信息
- `replan`：建议重规划（前端显示"需要调整方案？"按钮）

---

## 4. 数据模型

### 4.1 数据库表（实际状态）

| 表名 | 字段 | 写入状态 |
|------|------|----------|
| `users` | id, username, email, phone, password_hash, created_at, updated_at | ✅ 注册时写入 |
| `user_profiles` | id, user_id, lifecycle_stage, risk_capacity, investable_assets, monthly_surplus, kyc_level | ✅ 测评时写入 |
| `risk_assessments` | id, user_id, answers (JSONB), score, risk_level, assessed_at | ✅ 测评时写入 |
| `portfolios` | id, user_id, strategy_id, four_buckets (JSONB), total_assets, status | ✅ 策略生成后写入 |
| `strategies` | id, portfolio_id, market_analysis_id, rebalance_triggers (JSONB), stress_test_results (JSONB) | ✅ 策略生成后写入 |
| `market_analyses` | id, analysis_type, market_overview (JSONB), correlation_matrix (JSONB), risk_factors (JSONB) | ✅ 策略生成后写入 |
| `audit_logs` | id, user_id, action, actor, detail (JSONB), ip_address | 🔲 从未写入 |
| `compliance_records` | id, user_id, record_type, content (JSONB), signed_at | 🔲 从未写入 |
| `langgraph_checkpoints` | id, thread_id, checkpoint (JSONB), metadata (JSONB) | 🔲 从未写入 |

### 4.2 Redis 缓存（设计完成，未使用）

```
🔲 session:{user_id} → JWT token
🔲 market:index:{symbol} → 指数数据 (TTL 5min)
🔲 market:macro:{indicator} → 宏观指标 (TTL 1h)
🔲 llm:cache:{hash} → LLM 响应 (TTL 24h)
🔲 ratelimit:mcp:{source} → 限流计数
```

---

## 5. 关键流程

### 5.1 新用户首次理财规划（实际流程）

```
用户                      API Gateway        Orchestrator        4个Agent
 │                           │                    │                   │
 │  POST /register           │                    │                   │
 │ ─────────────────────────→│ → DB users         │                   │
 │                           │                    │                   │
 │  POST /login              │                    │                   │
 │ ─────────────────────────→│ → JWT token        │                   │
 │                           │                    │                   │
 │  POST /risk-assessment    │                    │                   │
 │ ─────────────────────────→│ → DB risk_assessments + user_profiles │
 │                           │                    │                   │
 │  POST /orchestrator/start │                    │                   │
 │ ─────────────────────────→│ ──────────────────→│                   │
 │                           │                    │ → Profile Agent   │
 │                           │                    │ → Market Agent    │
 │                           │                    │ → Strategy Agent  │
 │                           │                    │ → Coaching Agent  │
 │                           │                    │                   │
 │                           │                    │ → DB Portfolio    │
 │                           │                    │ → DB Strategy     │
 │                           │                    │ → DB MarketAnalysis│
 │                           │                    │                   │
 │  返回完整策略方案          │                    │                   │
 │ ←─────────────────────────│←───────────────────│                   │
 │                           │                    │                   │
 │  跳转 /strategy-result    │                    │                   │
 │  GET /orchestrator/status │                    │                   │
 │ ─────────────────────────→│ ──────────────────→│ (从DB加载)        │
```

### 5.2 渐进式披露流程（策略生成）

```
用户点击"生成配置方案"
  → /start 返回立即 (异步后台执行)
  → 跳转 StrategyResult 页面
  → 轮询 /status 每2秒:
      step=analyzing_profile     → 🔵 步骤1活跃
      step=profile_complete      → 🟢 步骤1完成, 🧑 用户画像卡片出现
      step=market_complete       → 🟢 步骤2完成, 📈 市场研判卡片出现
      step=strategy_complete     → 🟢 步骤3完成, 📊 四笔钱+饼图+压力测试出现
      step=coaching_complete     → 🟢 步骤4完成, 💡 督导建议出现
  → 全部完成, 显示 [查看完整方案] + [咨询AI助手] 按钮
```

**实现要点：**
- graph 节点通过 `_update_progress()` 将中间结果写入 `user_states`
- 前端 `setInterval(pollStatus, 2000)` 每2秒拉取最新状态
- 每个 section 有独立的 `v-if` 条件，数据就绪即刻展示
- 步骤进度条显示 1-2-3-4 圆点，已完成变绿

### 5.3 用户回访流程

```
登录 → 首页仪表盘 (健康分+指标+饼图)
          ↓
    ┌─────┼─────┐
    ↓     ↓     ↓
  方案   AI   市场
  详情   对话   观察
```

---

## 6. 前端架构

### 6.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.4+ | Composition API |
| TypeScript | 2.0+ (vue-tsc) | 类型安全 |
| Vite | 5.0+ | 开发服务器 + 构建 |
| Element Plus | 2.5+ | UI 组件库 |
| ECharts | 6.0+ | 数据可视化 |
| Axios | 1.6+ | HTTP 客户端 |
| Vue Router | 4.3+ | 前端路由 |

### 6.2 页面清单（10个页面）

| 页面 | 路由 | 状态 |
|------|------|------|
| Layout | 父级布局 | ✅ 顶部导航栏 (5项+退出) |
| Login | /login | ✅ |
| Register | /register | ✅ |
| Dashboard | /dashboard | ✅ 健康分 + 4指标 + 饼图 |
| MyPlan | /my-plan | ✅ 方案详情 + 再平衡 |
| AIChat | /ai-chat | ✅ 对话 + 快捷问题 |
| Market | /market | ✅ 资产卡片 + 研判 |
| Profile | /profile | ✅ 用户信息 + 风险历史 |
| RiskAssessment | /risk-assessment | ✅ 3步向导 |
| StrategyResult | /strategy-result | ✅ 环形图 + 卡片 + 柱状图 |

### 6.3 导航结构

```
顶部导航栏（Layout.vue）
├── 🏠 首页      /dashboard
├── 📊 我的方案  /my-plan
├── 💬 AI助手   /ai-chat
├── 📈 市场观察  /market
└── 👤 我的      /profile
```

### 6.4 路由鉴权

```typescript
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.auth && !token) return next('/login')      // 未登录 → 登录页
  if (to.meta.guest && token) return next('/dashboard')   // 已登录 → 首页
  next()
})
```

---

## 7. 异常场景处理

### 7.1 Orchestrator 状态持久化 ✅

**问题：** 进程重启时内存中的状态丢失。

**实际方案：**
- ✅ 策略/市场分析结果持久化到 PostgreSQL
- ✅ /status 端点先查内存，不存在时从 DB 加载
- 🔲 LangGraph checkpoint 机制未启用

### 7.2 LLM 调用超时与降级 ✅

**实际方案：**
- ✅ 每个 Agent 有 `_default_analysis` / `_default_strategy` 等 fallback 方法
- ✅ LLM JSON 解析失败时使用 fallback
- ✅ Market Agent AKShare 不可用时回退硬编码默认值
- 🔲 模型切换（DeepSeek → MiMo）未实现（MiMo 未配置）

### 7.3 API 超时 ✅

- ✅ Orchestrator /start 超时 180s（4个 Agent 调用约 70-80s）
- ✅ 前端 axios timeout 同步调整

### 7.4 前端加载状态 ✅

- ✅ Dashboard 空状态引导
- ✅ MyPlan 空状态引导
- ✅ Market 空状态引导
- ✅ StrategyResult 加载动画

---

## 8. 部署架构

### 8.1 Docker Compose 实际服务列表

```yaml
services:
  # 基础设施
  postgres:    # PostgreSQL 16 (端口 5432)   ✅ 运行中
  redis:       # Redis 7 (端口 6379)         ✅ 运行中
  rabbitmq:    # RabbitMQ 3.12 (端口 5672)   ✅ 运行中

  # 核心服务
  api-gateway:     # FastAPI :8000  ✅ 运行中
  orchestrator:    # FastAPI :8010  ✅ 运行中

  # Agents (4个)
  agent-profile:   # FastAPI :8001  ✅ 运行中
  agent-market:    # FastAPI :8002  ✅ 运行中
  agent-strategy:  # FastAPI :8003  ✅ 运行中
  agent-coaching:  # FastAPI :8004  ✅ 运行中

  # 监控 (定义但未启动)
  monitor-market:  # Python 定时任务  🔲 未运行
  monitor-user:    # Python 定时任务  🔲 未运行

  # MCP
  mcp-server:      # Python MCP stdio 🔲 未运行

  # 前端（开发用 Vite dev，此处为生产构建）
  frontend:        # Nginx :3000 → :80  🔲 未运行

volumes:
  pgdata:
```

**当前运行方式：**
- 后端：`docker compose up -d postgres redis rabbitmq api-gateway orchestrator agent-*`
- 前端：`cd frontend && npm run dev`（Vite dev server :3000）

### 8.2 网络拓扑（实际）

```
外部访问 → localhost:3000 (Vite dev 前端)
         → localhost:8000 (API Gateway)

内部 Docker 网络：
  api-gateway → orchestrator:8010 (HTTP)
  orchestrator → agent-profile:8001 (HTTP)
  orchestrator → agent-market:8002 (HTTP)
  orchestrator → agent-strategy:8003 (HTTP)
  orchestrator → agent-coaching:8004 (HTTP)
  agent-coaching → rabbitmq:5672 (AMQP)
  所有服务 → postgres:5432 (TCP)
  所有服务 → redis:6379 (TCP)
```

---

## 9. 合规性设计

### 9.1 适当性匹配 ✅

- ✅ 风险测评 → 打分（4维度）→ 风险等级
- ✅ 策略生成 → 适当性规则引擎校验
- ✅ 权益配置上限自动截断
- 🔲 适当性匹配记录未写入 compliance_records 表

### 9.2 审计日志 🔲

- 🔲 表结构就绪，写入代码未添加
- 应记录：登录、测评、策略生成、重规划、Agent 调用

### 9.3 KYC 流程 🔲

- 🔲 UserProfile 有 kyc_level 字段但从未使用
- 当前无 KYC 验证流程

---

## 10. 与原始设计的差异汇总

| 设计文档（原） | 实际实现 | 原因 |
|---------------|---------|------|
| WebSocket 推送方案结果 | HTTP 轮询（页面加载时请求） | 未实现，复杂度高 |
| MCP Client 在 Agent 中 | Market Agent 直接 import akshare | MCP stdio 协议集成不便 |
| LangGraph Checkpoint 持久化 | 策略结果持久化但 checkpoint 未启用 | 策略结果比检查点更实用 |
| 审计日志实时写入 | 从未写入 | 未实现 |
| 限流 | 未实现 | 开发环境不需要 |
| LLM 模型 deepseek-chat | deepseek-v4-pro | API 实际支持的模型 |
| 节点级 Replan | 完整重执行 | LangGraph ainvoke 限制 |
| needs_followup 动态分支 | 始终为 false | Orchestrator 自动注入数据 |
| 5个前端页面 | 10个 | 增加了注册、测评、策略结果等 |
| 9个后端服务 | 12个定义 / 9个运行 | 加了 monitors 和 mcp-server |

---

## 附录 A：设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 架构风格 | 微服务 + 消息队列 | 作品集展示多技能点 |
| Agent 协作 | LangGraph 状态图 + 条件分支 | 天然支持条件路由 |
| 编排方式 | Orchestrator 模式 | 集中管理流程状态 |
| 消息队列 | RabbitMQ | 持久化、ack、死信队列 |
| 数据源 | AKShare 直接调用 | 避免 MCP stdio 集成复杂性 |
| LLM 接入 | langchain-openai (OpenAI 兼容) | DeepSeek 支持 OpenAI 接口 |
| 数据库 | PostgreSQL + JSONB | 灵活存储 Agent 输出 |
| 缓存 | Redis（已配置） | 后续启用 |
| 前端图表 | ECharts | 国产、文档丰富、交互好 |
| 超时策略 | 180s Orchestrator / 60s Agent | 覆盖 DeepSeek API 响应时间 |
