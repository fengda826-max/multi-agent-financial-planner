# PRD：多 Agent 智能理财规划系统

## 一、产品概述

### 1.1 产品定位
面向 25-45 岁有理财需求的个人用户，通过 AI Agent 协作提供个性化的"四笔钱"资产配置方案，并持续追踪、提醒、对话，帮助用户实现财务健康。

### 1.2 核心价值
- **即时生成**：5 个输入 → 完整资产配置方案（5 分钟）
- **专业背书**：基于 LangGraph 多 Agent 协作，每种 Agent 各司其职
- **持续陪伴**：不是一次性报告，而是长期理财伴侣

### 1.3 技术架构
```
用户浏览器 → Vue 3 前端 (Vite)
  → API Gateway (FastAPI :8000)
    → Orchestrator (LangGraph :8010)
      → Profile Agent (:8001)    用户画像分析
      → Market Agent (:8002)     市场研判
      → Strategy Agent (:8003)   配置方案生成
      → Coaching Agent (:8004)   陪伴督导
    ← DeepSeek API
  → PostgreSQL + Redis + RabbitMQ
```

---

## 二、后端能力盘点

### 2.1 当前端到端可用

| 功能 | 后端 | 前端 | 可用？ |
|------|------|------|--------|
| 注册 | POST /api/auth/register | 死链接(无/register路由) | ❌ 后端有，前端缺 |
| 登录 | POST /api/auth/login | 完整 | ✅ |
| 风险测评 | POST /api/risk-assessment/ | 3步向导，完整 | ✅ |
| 策略生成 | POST /api/orchestrator/start | 单按钮调用 | ✅ |
| 结果查看 | GET /api/orchestrator/status/{id} | 4卡片+表格 | ✅ |
| 再规划 | POST /api/orchestrator/replan | API封装了但从未调用 | ❌ 死代码 |
| 调查问卷 | needs_followup/followup_questions | 不存在 | ❌ 无UI |
| 市场数据 | 硬编码mock数据 | 不存在独立页面 | ❌ 无展示 |
| 监控告警 | MarketMonitor + UserMonitor | 不存在 | ❌ 无UI |
| MCP工具 | 4个AKShare工具 | 不适用(后端对后端) | ❌ 未集成 |

### 2.2 每个 Agent 返回的数据（前端可用字段）

**Profile Agent → 用户画像**
```
lifecycle_stage: "accumulation" | "consolidation" | "distribution"
risk_capacity:   "low" | "medium" | "high"
needs_followup:  boolean (目前始终为false)
followup_questions: [string, ...]
```

**Market Agent → 市场研判**
```
market_overview: {
  equity:    { expected_return, volatility, recommendation },
  bond:      { expected_return, volatility, recommendation },
  commodity: { expected_return, volatility, recommendation }
}
risk_factors: [string, ...]
overall_recommendation: string
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
message: string (温暖专业的理财建议)
action: "none" | "followup" | "replan"
replan_trigger: string (如果建议重规划，说明原因)
```

### 2.3 风险测评打分算法（后端已实现）

| 维度 | 分值 |
|------|------|
| 年龄: <30(30分), <40(25分), <50(20分), >=50(10分) | |
| 收入: >3万(25分), >1.5万(20分), >8千(15分), 其他(10分) | |
| 风险偏好: 进取(30分), 稳健(20分), 保守(10分) | |
| 投资期限: 10年+(30分), 5年(25分), 3年(15分), 1年(5分) | |
| **总分 <50→保守, <75→稳健, >=75→进取** | |

### 2.4 适当性约束（Strategy Agent 已实现）

| 风险等级 | 权益上限 | 允许产品 |
|----------|---------|---------|
| 保守 | 20% | 货币基金、债券基金、银行理财、国债 |
| 稳健 | 60% | 混合基金、指数基金、债券基金 |
| 进取 | 90% | 股票、股票基金、期货、期权 |

---

## 三、用户旅程

### 3.1 首次用户完整路径

```
注册 → 登录 → 首页(空状态引导) → 风险测评(3步5题)
  → 生成方案(等待约1分钟) → 查看方案(4笔钱+压力测试+AI解读)
  → 探索AI助手(问问题) → 设置通知偏好
```

### 3.2 回访用户路径

```
登录 → 首页仪表盘(资产总览+市场快讯+今日提醒)
  → 检查偏离 → 对话AI → (可选)重新测评/再平衡
```

---

## 四、功能列表

### P0 - MVP（最小可用产品，完善当前体验）

| ID | 功能 | 描述 | 后端依赖 | 工作量 |
|----|------|------|----------|--------|
| F01 | 注册页面 | 补齐 /register 路由和Register.vue页面 | POST /auth/register | 小 |
| F02 | 首页仪表盘 | 用真实数据替换空壳：理财健康分、资产概览、快捷入口 | GET /status/{id} | 中 |
| F03 | 四笔钱可视化 | 环形/玫瑰饼图展示配置比例，替代纯文字卡片 | 无(纯前端) | 小 |
| F04 | 压力测试图表 | 柱状图展示损失/恢复，替代Plain表格 | 无(纯前端) | 小 |
| F05 | 路由鉴权 | router.beforeEach 检查登录状态 | 无(纯前端) | 小 |

### P1 - 核心体验（让产品"好用"）

| ID | 功能 | 描述 | 后端依赖 | 工作量 |
|----|------|------|----------|--------|
| F06 | 方案详情页 | 可展开每笔钱的产品列表、理由、金额计算 | 无(已有数据) | 中 |
| F07 | 再平衡功能 | "偏离预警" → 点击触发 /replan | POST /replan | 中 |
| F08 | 市场数据页 | 展示Market Agent的研判结果+指数行情 | GET /status + 市场数据 | 中 |
| F09 | 对话AI助手 | 类似ChatGPT的对话界面，调用Coaching Agent | POST /interact | 大 |
| F10 | 测评历史 | 展示历史RiskAssessment记录 | 需要新API | 小 |

### P2 - 持续追踪（让用户"离不开"）

| ID | 功能 | 描述 | 后端依赖 | 工作量 |
|----|------|------|----------|--------|
| F11 | 主动提醒 | 首页显示"组合偏离""市场异常""到期提醒" | 需要新API | 中 |
| F12 | 持仓追踪 | 虚拟持仓管理，追踪实际vs目标偏离 | 需要新模型+API | 大 |
| F13 | 收益模拟 | 基于历史数据的收益区间展示 | 需要新API | 中 |
| F14 | 报告分享/导出 | 分享截图或导出PDF | 无(纯前端) | 小 |

---

## 五、前端页面设计规格

### 5.1 页面导航结构

```
顶部/左侧导航（5项）：
├── 🏠 首页      /dashboard
├── 📊 我的方案  /my-plan
├── 💬 AI助手   /ai-chat
├── 📈 市场      /market
└── 👤 我的      /profile
```

### 5.2 各页面规格

#### 首页仪表盘 (/dashboard)

**顶部——问候+健康分**
- "你好，{用户名}"
- 理财健康分（基于风险等级+方案合适度，计算75-95分）
- 上次更新时间

**中部——4个关键指标卡片**
- 总资产 = investable_assets（来自UserProfile）
- 本月结余 = monthly_surplus（来自UserProfile）
- 配置方案状态（active/"待生成"）
- 下次检查日期 = 上次生成+3个月

**中下部——资产配置环形图**
- ECharts 环形饼图，四笔钱四种颜色
- 点击某一块跳转到方案详情

**底部——快捷入口**
- [开始测评] [查看方案] [咨询AI]

**空状态**（新用户未测评）
- 大图 + "开始您的第一次理财规划"
- [立即测评] 按钮

---

#### 我的方案 (/my-plan)

**顶部——方案信息**
- 生成时间、风险等级标签、生命周期阶段标签

**主体——四笔钱详情**
- 4张横向卡片，每张不同颜色
- 显示：名称、百分比、估计金额、产品标签（el-tag）、理由（折叠/展开）
- 环形饼图（与首页相同）

**压力测试区域**
- ECharts 横向柱状图，2个场景对比
- X轴：损失百分比（负值向左），Y轴：场景名
- 标注恢复时间

**再平衡规则**
- 偏离阈值：5%
- 审核频率：每季度
- 下次审核日期

**操作按钮**
- [检查偏离] → 对比目标vs实际 → 触发提醒
- [重新生成] → 走 /replan API

**空状态**（无方案）
- 引导文字 + [开始测评] 按钮

---

#### AI 理财助手 (/ai-chat)

**聊天界面**
- 消息列表：AI消息在左，用户消息在右
- AI消息含头像（机器人图标）
- 支持Markdown渲染（粗体、列表、分段）
- 消息下方显示 action 标签（如果action=replan时显示"需要调整方案？"按钮）

**输入区域**
- 文本输入框 + 发送按钮
- 底部快捷问题按钮（3-4个建议问题）
- 建议问题示例：
  - "为什么我的长期仓位占50%？"
  - "现在市场适合投资吗？"  
  - "帮我解释一下压力测试"
  - "我需要调整方案吗？"

**Coaching Agent 当前能力**
- POST /interact 接受 user_message 参数
- 返回 message(文本) + action(none/followup/replan)
- 可作为普通聊天使用

**空状态**
- AI 打招呼消息
- 显示建议问题按钮

---

#### 市场观察 (/market)

**顶部——关键指标卡片行**
- 沪深300：价格 + 涨跌幅
- 创业板指：价格 + 涨跌幅
- 10年国债：收益率
- CPI：最新值

**中部——AI 市场研判**
- 从 Market Agent 获取的完整分析
- 三种资产（权益/债券/商品）的预期收益、波动率、建议
- 风险因素列表（可用 tag 展示）

**底部——整体建议**
- Market Agent 的 overall_recommendation

**数据来源问题**
- 当前 Market Agent 用硬编码 mock 数据
- 展示的是策略生成时的历史研判
- 可添加 [刷新研判] 按钮调用 Market Agent 重新分析

**空状态**
- 如果用户从未生成方案，显示"请先生成配置方案，市场研判将一并展示"

---

#### 个人中心 (/profile)

**个人信息**
- 用户名、注册时间

**风险等级**
- 当前等级 + 评分
- 测评时间
- [重新测评] 按钮

**历史记录**
- 测评历史列表
- 方案生成历史列表
- （当前无持久化，需要后端保存）

**通知设置**
- 偏离预警开关
- 市场异常提醒开关

**账号操作**
- 退出登录

---

## 六、原型设计

### 6.1 设计系统

**配色**
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

**数字展示规范**
- 资产金额（>10万）：36px Bold
- 资产金额（<10万）：24px Bold
- 百分比：24px Bold
- 标签文字：14px
- 正文：16px
- 卡片圆角：12px
- 按钮圆角：8px

**涨跌颜色（国内习惯）**
- 涨/正收益：红色 #EF4444
- 跌/负收益：绿色 #10B981（国内：红涨绿跌）

**卡片阴影**
- 默认：0 1px 3px rgba(0,0,0,0.08)
- Hover：0 4px 12px rgba(0,0,0,0.12)

---

### 6.2 关键页面线框

#### 首页仪表盘
```
┌──────────────────────────────────────────┐
│ 🏠 首页  📊方案  💬AI  📈市场  👤我     │ ← 顶部导航
├──────────────────────────────────────────┤
│                                          │
│  👋 你好，小明                            │
│  ┌──────────────────────────────────┐    │
│  │ 理财健康指数  85分 良好 ↑        │    │
│  └──────────────────────────────────┘    │
│                                          │
│  ┌──────────┐ ┌──────────┐              │
│  │ 总资产    │ │ 本月结余  │              │
│  │ ¥128,500 │ │ ¥8,000   │              │
│  └──────────┘ └──────────┘              │
│  ┌──────────┐ ┌──────────┐              │
│  │ 配置状态  │ │ 下次检查  │              │
│  │ 运行中 ✅ │ │ 2026-08-13│              │
│  └──────────┘ └──────────┘              │
│                                          │
│  ┌── 资产配置 ──────────────────────┐    │
│  │        [环形饼图]                 │    │
│  │  💰活钱10%  🏦稳健30%            │    │
│  │  📈长期50%  🛡保障10%            │    │
│  └────────────────────────────────┘    │
│                                          │
│  📈 市场快讯                             │
│  · 沪深300 上周 +1.2%                   │
│  · 10年国债收益率降至 2.55%             │
│                                          │
│  💡 今日提醒                             │
│  · 距上次更新已87天，建议检查风险测评    │
│                                          │
└──────────────────────────────────────────┘
```

#### 我的方案
```
┌──────────────────────────────────────────┐
│ ← 返回    我的配置方案    🔄 重新生成    │
├──────────────────────────────────────────┤
│  生成于 2026-05-13 · 稳健型 · 积累期     │
│                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ 💰   │ │ 🏦   │ │ 📈   │ │ 🛡   │   │
│  │ 活钱 │ │ 稳健 │ │ 长期 │ │ 保障 │   │
│  │ 10%  │ │ 30%  │ │ 50%  │ │ 10%  │   │
│  │¥1.3万│ │¥3.9万│ │¥6.4万│ │¥1.3万│   │
│  │      │ │      │ │      │ │      │   │
│  │[详情]│ │[详情]│ │[详情]│ │[详情]│   │
│  └──────┘ └──────┘ └──────┘ └──────┘   │
│                                          │
│  📊 压力测试                             │
│  ┌──────────────────────────────────┐    │
│  │ 2015股灾  ████████  -15%  8月恢复 │    │
│  │ 2020疫情  ██████    -12%  4月恢复 │    │
│  └──────────────────────────────────┘    │
│                                          │
│  ⚖️ 再平衡规则                           │
│  偏离阈值5% · 每季度审核 · 下次8月13日  │
│                                          │
│  [立即检查偏离]  [分享方案]              │
└──────────────────────────────────────────┘
```

#### AI 助手
```
┌──────────────────────────────────────────┐
│ 💬 AI 理财助手                            │
├──────────────────────────────────────────┤
│                                          │
│  🤖 您好！我是您的专属理财顾问...        │
│                                          │
│  [为什么长期占50%] [现在适合买基金吗]    │
│  [我的风险等级合理吗] [如何调整方案]     │
│                                          │
│  ────────────────────────────────────    │
│                                          │
│                  👤 长期仓位会不会太高?   │
│                                          │
│  🤖 基于您的年龄(30岁)和风险偏好(稳健    │
│     型)，50%的长期配置是合理的...         │
│                                          │
│  ────────────────────────────────────    │
│  ┌──────────────────────────────┐        │
│  │ 输入问题...              📎  │        │
│  └──────────────────────────────┘        │
└──────────────────────────────────────────┘
```

---

## 七、路由设计

```typescript
// router/index.ts
const routes = [
  { path: '/',           redirect: '/dashboard' },
  { path: '/login',      component: Login,     meta: { guest: true } },
  { path: '/register',   component: Register,  meta: { guest: true } },
  { path: '/dashboard',  component: Dashboard, meta: { auth: true } },
  { path: '/my-plan',    component: MyPlan,    meta: { auth: true } },
  { path: '/ai-chat',    component: AIChat,    meta: { auth: true } },
  { path: '/market',     component: Market,    meta: { auth: true } },
  { path: '/profile',    component: Profile,   meta: { auth: true } },
  { path: '/risk-assessment', component: RiskAssessment, meta: { auth: true } },
  { path: '/strategy-result', component: StrategyResult, meta: { auth: true } },
]

// Navigation Guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.auth && !token) return next('/login')
  if (to.meta.guest && token) return next('/dashboard')
  next()
})
```

---

## 八、所需后端改动

### 8.1 MVP 阶段（P0）必须的后端改动

| 改动 | 原因 | 文件 |
|------|------|------|
| GET /api/users/me 扩展 | Dashboard需要用户名、注册时间等基本信息 | routers/user.py |
| GET /api/orchestrator/plan/{userId} | 前端需要最新的方案数据（已有status但字段不够友好） | orchestrator/main.py |
| POST /api/orchestrator/replan 修复 | 当前replan_from不生效，LangGraph总是从profile开始 | orchestrator/main.py |
| Strategy/Portfolio 持久化 | 当前仅内存存储，重启丢失；首页需要历史数据 | orchestrator/main.py |

### 8.2 P1 阶段需要的后端改动

| 改动 | 原因 |
|------|------|
| Market Agent 实时数据 | 用 MCP/AKShare 替代 mock 数据 |
| 对话历史持久化 | Coaching 对话需要存储到 DB |
| 测评历史 API | GET /api/risk-assessment/history |

---

## 九、实施计划

### Phase 1：MVP（2-3天）
- [ ] F01 注册页面
- [ ] F05 路由鉴权
- [ ] F02 首页仪表盘（真实数据+空状态）
- [ ] F03 四笔钱可视化（ECharts 环形图）
- [ ] F04 压力测试图表（柱状图）

### Phase 2：核心体验（3-5天）
- [ ] F06 方案详情页（展开/折叠）
- [ ] F07 再平衡功能
- [ ] F08 市场数据页
- [ ] F09 对话AI助手

### Phase 3：持续追踪（5-7天）
- [ ] F11 主动提醒
- [ ] F10 测评历史
- [ ] F14 报告分享

### Phase 4：完善（按需）
- [ ] F12 持仓追踪
- [ ] F13 收益模拟
