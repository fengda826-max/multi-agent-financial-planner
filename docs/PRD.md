# PRD：多 Agent 智能理财规划系统

> **更新日期：** 2026-05-16  
> **版本：** v1.1 — 根据实际实现状态更新

## 一、产品概述

### 1.1 产品定位
面向 25-45 岁有理财需求的个人用户，通过 AI Agent 协作提供个性化的"四笔钱"资产配置方案，并持续追踪、提醒、对话，帮助用户实现财务健康。

### 1.2 核心价值
- **即时生成**：5 个输入 → 完整资产配置方案
- **渐进披露**：生成过程中逐步展示画像→市场→策略→督导，不干等
- **专业背书**：基于 LangGraph 多 Agent 协作，LLM + 规则引擎双重保障
- **持续陪伴**：不是一次性报告，而是长期理财伴侣
- **真实数据**：AKShare 实时金融数据（沪深300、创业板指、国债、CPI）

### 1.3 技术架构
```
用户浏览器 → Vue 3 前端 (Vite :3000)
  → API Gateway (FastAPI :8000)
    → Orchestrator (LangGraph :8010)
      → Profile Agent (:8001)    用户画像分析 (12字段)
      → Market Agent (:8002)     市场研判 (AKShare实时数据)
      → Strategy Agent (:8003)   配置方案生成 (适当性约束)
      → Coaching Agent (:8004)   陪伴督导 (对话记忆)
    ← DeepSeek v4-pro
  → PostgreSQL + Redis + RabbitMQ
```

---

## 二、后端能力盘点

### 2.1 实现状态总览

| 功能 | 状态 | 说明 |
|------|------|------|
| 注册/登录 | ✅ | JWT + bcrypt，Register.vue |
| 风险测评 | ✅ | 4维度打分算法，3步向导 |
| 策略生成 | ✅ | 4 Agent 异步后台执行 |
| 渐进式披露 | ✅ | 画像→市场→策略→督导逐步展示 |
| 四笔钱可视化 | ✅ | ECharts 环形饼图 + 柱状图 |
| AI 对话助手 | ✅ | 对话记忆(6条历史)、市场上下文 |
| 再规划 | ✅ | MyPlan 页 [检查再平衡] 按钮 |
| 测评历史 | ✅ | GET /risk-assessment/history |
| DB 持久化 | ✅ | Portfolio/Strategy/MarketAnalysis |
| 市场实时数据 | ✅ | AKShare 4源，10s超时/源 |
| 10 个前端页面 | ✅ | Layout/Login/Register/Dashboard/MyPlan/AIChat/Market/Profile/RiskAssessment/StrategyResult |
| 路由鉴权 | ✅ | router.beforeEach |
| 监控告警 | 🔲 | MarketMonitor + UserMonitor 容器未启动 |
| MCP Server | ⚠️ | 已实现但未被调用（Agent 直接调 AKShare） |
| 主动提醒 | 🔲 | PRD P2 |

### 2.2 每个 Agent 返回的数据（当前实际字段）

**Profile Agent → 用户画像**（12字段）
```
lifecycle_stage:          "accumulation" | "consolidation" | "distribution"
lifecycle_explanation:    为什么处于这个阶段
risk_capacity:            "low" | "medium" | "high"
risk_explanation:         风险承受能力判断依据
investment_style:         投资风格（如"稳健偏成长型"）
financial_health_score:   0-100 财务健康评分
financial_health_comment: 评分简要说明
strengths:                [财务优势列表]
weaknesses:               [需关注方面列表]
profile_summary:          一句话画像总结
investable_assets:        可投资资产金额
monthly_surplus:          月结余
```

**Market Agent → 市场研判**
```
market_overview: {
  equity:    { expected_return, volatility, recommendation },
  bond:      { expected_return, volatility, recommendation },
  commodity: { expected_return, volatility, recommendation }
}
risk_factors:          [string, ...]
overall_recommendation: string

数据来源: AKShare 实时数据（沪深300/创业板指/10年国债/CPI）
         失败时回退硬编码默认值
```

**Strategy Agent → 配置方案**
```
four_buckets: {
  living_money:     { allocation, products: [...], reason },
  stable_money:     { allocation, products: [...], reason },
  growth_money:     { allocation, products: [...], reason },
  protection_money: { allocation, products: [...], reason }
}
rebalance_triggers: { drift_threshold, review_frequency }
stress_test: {
  scenario_2015_crash: { loss, recovery_time },
  scenario_covid:      { loss, recovery_time }
}
```

**Coaching Agent → 督导建议**
```
message:            督导回复文本
action:             "none" | "followup" | "replan"
replan_trigger:     建议重规划的原因（可选）
对话记忆:           最近6条对话历史注入 LLM prompt
```

### 2.3 风险测评打分算法

| 维度 | 分值 |
|------|------|
| 年龄: <30(30分), <40(25分), <50(20分), >=50(10分) | |
| 收入: >3万(25分), >1.5万(20分), >8千(15分), 其他(10分) | |
| 风险偏好: 进取(30分), 稳健(20分), 保守(10分) | |
| 投资期限: 10年+(30分), 5年(25分), 3年(15分), 1年(5分) | |
| **总分 <50→保守, <75→稳健, >=75→进取** | |

### 2.4 适当性约束

| 风险等级 | 权益上限 | 允许产品 |
|----------|---------|---------|
| conservative/low | 20% | 货币基金、债券基金、银行理财、国债 |
| moderate/medium | 60% | 混合基金、指数基金、债券基金 |
| aggressive/high | 90% | 股票、股票基金、期货、期权 |

LLM 生成的方案由规则引擎二次校验：growth_money 超出上限时自动截断，多余部分转入 stable_money。

---

## 三、用户旅程

### 3.1 首次用户完整路径

```
注册 → 登录 → 首页(空状态引导)
  → 风险测评(3步向导，默认值可快速提交)
  → 点击"生成配置方案" → 立即跳转结果页
  → 渐进式披露：
      5秒   🧑 用户画像分析（生命周期、财务健康分、优劣势）
      15秒  📈 市场研判（3类资产预期收益、波动率、风险因素）
      30秒  📊 四笔钱方案（环形饼图、4张卡片、压力测试）
      80秒  💡 督导建议（个性化解读 + AI 对话入口）
  → 探索其他页面（AI 助手、我的方案、市场观察）
```

### 3.2 回访用户路径

```
登录 → 首页仪表盘（健康分 + 4指标 + 资产配置饼图）
  → 我的方案（查看详情 / 检查再平衡）
  → AI 助手（提问市场或方案相关问题）
  → 市场观察（查看最新研判数据）
  → 个人中心（重新测评 / 查看历史）
```

---

## 四、功能列表

符号说明：✅ 已完成 | ⚠️ 部分完成 | 🔲 未开始

### P0 - MVP

| ID | 功能 | 状态 |
|----|------|------|
| F01 | 注册页面 (Register.vue) | ✅ |
| F02 | 首页仪表盘（健康分+指标+饼图+快捷入口） | ✅ |
| F03 | 四笔钱可视化（ECharts 环形饼图） | ✅ |
| F04 | 压力测试图表（ECharts 柱状图） | ✅ |
| F05 | 路由鉴权（router.beforeEach） | ✅ |

### P1 - 核心体验

| ID | 功能 | 状态 |
|----|------|------|
| F06 | 方案详情页（MyPlan.vue，可展开产品+理由） | ✅ |
| F07 | 再平衡功能（/replan API + 前端按钮） | ✅ |
| F08 | 市场数据页（Market.vue，展示研判+风险因素） | ✅ |
| F09 | AI 对话助手（AIChat.vue，对话记忆+快捷问题） | ✅ |
| F10 | 测评历史（GET /risk-assessment/history） | ✅ |
| F11 | 渐进式披露（StrategyResult 逐步展示4阶段） | ✅ |
| F12 | 用户画像丰富化（12字段，含财务健康分） | ✅ |
| F13 | 对话记忆（Coaching Agent 保留6条历史） | ✅ |
| F14 | 市场实时数据（AKShare 4源，10s超时/源） | ✅ |
| F15 | DB 策略持久化（Portfolio/Strategy/MarketAnalysis） | ✅ |

### P2 - 持续追踪

| ID | 功能 | 状态 |
|----|------|------|
| F16 | 主动提醒（组合偏离/市场异常/到期提醒） | 🔲 |
| F17 | 持仓追踪（虚拟持仓管理） | 🔲 |
| F18 | 收益模拟（历史回测） | 🔲 |
| F19 | 报告分享/导出 | 🔲 |
| F20 | WebSocket 实时推送 | 🔲 |

---

## 五、前端页面设计规格

### 5.1 页面导航结构

```
顶部导航栏（Layout.vue）
├── 🏠 首页      /dashboard
├── 📊 我的方案  /my-plan
├── 💬 AI助手   /ai-chat
├── 📈 市场观察  /market
└── 👤 我的      /profile
```

### 5.2 各页面实际实现

#### 首页仪表盘 (/dashboard)

**有数据状态：**
- 👋 你好 + 用户名 + 上次更新时间
- 理财健康分（90 分，圆形显示）
- 4 个指标卡片：总资产、月结余、风险等级、配置状态+下次检查日
- 资产配置分布（ECharts 环形饼图）
- 快捷操作：查看完整方案 / 重新测评 / 咨询AI助手

**空状态**（新用户）：
- 引导文案 + [立即测评] 按钮

#### 我的方案 (/my-plan)

- 顶部：风险等级标签 + 生命周期标签
- 环形饼图
- 4 张颜色区分的详情卡片（活钱/稳健/长期/保障），含产品标签 + 配置理由（折叠）
- 压力测试柱状图 + 列表
- 再平衡规则卡片（偏离阈值、检查频率）
- [检查再平衡] + [重新测评] 按钮

#### 策略结果页 (/strategy-result) — 渐进式披露

**生成中（分4阶段逐步出现）：**
- 步骤进度条（1-2-3-4 带圆点）
- 阶段1：🧑 用户画像分析卡片（生命周期解释、投资风格、财务健康分、优势/劣势标签、画像总结）
- 阶段2：📈 市场研判卡片（3类资产：权益/债券/商品，预期收益+波动率+建议，风险因素标签，整体建议）
- 阶段3：📊 四笔钱环形饼图 + 4张卡片 + 压力测试表格 + 再平衡规则
- 阶段4：💡 督导建议

**完成后：** [查看完整方案] + [咨询AI助手] 按钮

#### AI 理财助手 (/ai-chat)

- 聊天界面：AI消息(左) + 用户消息(右)，打字动画
- 无策略时：引导文案 + [开始测评] 按钮
- 有策略时：5 个快捷问题 + 自由输入
- 对话上下文：自动包含市场数据和策略方案
- 消息包含 action 标签（replan 时显示按钮）

#### 市场观察 (/market)

- 3 张资产卡片：权益/债券/商品（预期收益 + 波动率 + 建议）
- AI 市场研判（overall_recommendation）
- 风险因素标签列表
- 空状态：先生成配置方案

#### 个人中心 (/profile)

- 用户信息（用户名、注册时间、邮箱）
- 风险等级 + 评分 + 测评时间 + 生命周期
- 可投资资产 + 月结余
- 配置方案状态
- [重新测评] + [查看方案] + [退出登录]

---

## 六、设计系统（已采用）

### 配色
```
主色(Trust Blue):    #3B82F6
活钱(Liquid Green):  #10B981
稳健(Stable Blue):   #6366F1
长期(Growth Gold):   #F59E0B
保障(Protect Red):   #EF4444
背景(Light Gray):    #F8FAFC
卡片白:              #FFFFFF
文字(Dark):          #1E293B
次要文字(Gray):      #64748B
```

### 组件规范
- 卡片圆角 12px，阴影 0 1px 3px rgba(0,0,0,0.08)
- 按钮圆角 8px
- 涨：红色 #EF4444 | 跌：绿色 #10B981（国内习惯）
- 资产金额：24-36px Bold | 正文字号：14-16px

---

## 七、路由设计（已实现）

```typescript
const routes = [
  { path: '/',                redirect: '/dashboard' },
  { path: '/login',           component: Login,          meta: { guest: true } },
  { path: '/register',        component: Register,       meta: { guest: true } },
  { path: '/dashboard',       component: Dashboard,      meta: { auth: true } },
  { path: '/my-plan',         component: MyPlan,         meta: { auth: true } },
  { path: '/ai-chat',         component: AIChat,         meta: { auth: true } },
  { path: '/market',          component: Market,         meta: { auth: true } },
  { path: '/profile',         component: Profile,        meta: { auth: true } },
  { path: '/risk-assessment', component: RiskAssessment, meta: { auth: true } },
  { path: '/strategy-result', component: StrategyResult, meta: { auth: true } },
]

// Auth guard: token? → 放行 : → /login
// Guest guard: token? → /dashboard : → 放行
```

---

## 八、后端改动（全部完成）

### P0 改动 ✅

| 改动 | 实现 |
|------|------|
| GET /api/users/me 扩展 | 返回 username, email, created_at |
| Strategy/Portfolio 持久化 | Portfolio + Strategy + MarketAnalysis 三表写入 |
| /replan 修复 | 完整重执行，从内存+DB加载状态 |

### P1 改动 ✅

| 改动 | 实现 |
|------|------|
| Market Agent 实时数据 | AKShare 异步并发获取4源，10s超时/源 |
| 对话历史持久化 | Coaching Agent conversation_history 参数，6条历史 |
| 测评历史 API | GET /api/risk-assessment/history |
| /chat 端点 | POST /orchestrator/chat 代理到 Coaching Agent |
| Profile Agent 丰富化 | 12字段输出（含财务健康分、优劣势等） |
| Market Agent 超时修复 | asyncio.to_thread + 120s orchestrator timeout |
| DB FK 修复 | strategy_id 在 flush 后赋值 |
| lifecyclestage 同步 | 策略保存时回写 user_profiles |

---

## 九、实施进度

### Phase 1：MVP ✅ 全部完成
- [x] F01 注册页面
- [x] F02 首页仪表盘
- [x] F03 ECharts 环形饼图
- [x] F04 压力测试柱状图
- [x] F05 路由鉴权

### Phase 2：核心体验 ✅ 全部完成
- [x] F06 MyPlan 方案详情页
- [x] F07 再平衡功能
- [x] F08 Market 市场数据页
- [x] F09 AIChat AI对话
- [x] F10 测评历史 API
- [x] F11-F15 渐进披露/画像丰富/对话记忆/实时数据/DB持久化

### Phase 3：持续追踪 🔲
- [ ] F16 主动提醒
- [ ] F17 持仓追踪
- [ ] F18 收益模拟
- [ ] F19 报告分享

### Phase 4：架构完善 🔲
- [ ] F20 WebSocket 实时推送
- [ ] 审计日志写入
- [ ] MCP Server 集成
- [ ] Monitor 容器启用
