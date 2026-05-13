# 多 Agent 协作智能理财规划系统 - 设计文档

## 1. 项目概述

### 1.1 背景与目标

普通用户面对基金、股票、保险等海量金融产品无从下手，传统理财顾问费用高昂，市面上理财 App 多为单点推荐，缺乏全局资产配置视角。

本系统旨在通过多个专业化 Agent 协作，为用户提供个性化、可解释、动态调优的全生命周期理财规划服务。

### 1.2 核心价值

- **全局视角**：基于"四笔钱"（活钱、稳健、长期、保障）的资产配置框架
- **多 Agent 协作**：专业分工，长链推理，条件分支动态路由
- **合规留痕**：KYC 模拟、适当性匹配、审计日志
- **实时督导**：市场异动检测、用户偏离纠偏、心理按摩

### 1.3 项目定位

个人学习/作品集项目，部署在单机 Docker Compose 环境，架构设计向生产级靠拢。

---

## 2. 系统架构（C4 模型）

### 2.1 系统上下文图（Level 1）

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户（浏览器）                            │
└─────────────────────────────────────────────────────────────────┘
                              │
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
    │  用户   │    │  LLM    │    │ 金融    │    │ 事件    │
    │ (前端)  │    │ 多模型  │    │ 数据源  │    │ 监控    │
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**外部实体说明：**

| 实体 | 交互方式 | 说明 |
|------|---------|------|
| 用户 | HTTP/WebSocket → API Gateway | 前端调用统一入口 |
| LLM 提供方 | HTTP API → LangChain | DeepSeek、MiMo 等，配置切换 |
| 金融数据源 | MCP 协议 | AKShare、Tushare、Wind，适配器模式 |
| 事件监控 | RabbitMQ 事件 | Market Monitor、User Monitor |

### 2.2 容器图（Level 2）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            用户（浏览器）                                 │
└─────────────────────────────────────────────────────────────────────────┘
                              │ HTTP / WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       API Gateway（FastAPI）                             │
│  JWT 认证 | 请求路由 | WebSocket 管理 | 限流 | 日志                       │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                Orchestrator（长驻进程，多用户并发）                        │
│                                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                                 │
│  │ 用户A    │  │ 用户B    │  │ 用户C    │  ... LangGraph 状态图实例        │
│  │ 状态图   │  │ 状态图   │  │ 状态图   │                                 │
│  └─────────┘  └─────────┘  └─────────┘                                 │
│                                                                          │
│  支持：并发执行 | 暂停/恢复 | 条件分支 | 重规划（回退到指定节点）            │
│  状态持久化 → PostgreSQL langgraph_checkpoints                           │
└─────────────────────────────────────────────────────────────────────────┘
        │               │               │               │
        ▼               ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐
│ 用户画像    │  │ 市场研判    │  │ 策略生成    │  │ 陪伴督导            │
│ Agent      │  │ Agent      │  │ Agent      │  │ Agent              │
│ HTTP 接口  │  │ HTTP 接口  │  │ HTTP 接口  │  │ HTTP 接口           │
│ MCP Client │  │ MCP Client │  │            │  │ RabbitMQ Consumer  │
└─────┬──────┘  └─────┬──────┘  └────────────┘  │                    │
      │               │                          │ 重规划请求          │
      ▼               ▼                          └─────────┬──────────┘
┌─────────────────────────────┐                             │
│      MCP Server             │                             │
│  限流器 | 请求队列 | 缓存    │                             │
│  AKShare | Tushare | Wind   │                             │
└─────────────────────────────┘                             │
                                                            │
┌───────────────────────────────────────────────────────────┼─────────────┐
│                      RabbitMQ                              │             │
│  ┌──────────────────┬──────────────────┬──────────────────┘             │
│  │ market.anomaly.* │ user.deviation.* │ strategy.alert.*              │
│  └──────────────────┴──────────────────┴──────────────────              │
└─────────────────────────────────────────────────────────────────────────┘
      ▲                                           ▲
      │                                           │
┌─────────────────────┐                 ┌─────────────────────┐
│   Market Monitor    │                 │    User Monitor     │
│  定时检查市场异动    │                 │  偏离检测 + 活跃度   │
│  读取 Redis 缓存/PG │                 │  监听交易事件/扫描PG │
└─────────────────────┘                 └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  PostgreSQL                          │        Redis                      │
│  users | profiles | portfolios       │  会话缓存 | 市场数据缓存           │
│  strategies | audit_logs             │  LLM 响应缓存 | 限流计数器         │
│  compliance_records                  │                                  │
│  langgraph_checkpoints               │                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  LLM 抽象层（LangChain）                                                │
│  ChatDeepSeek | ChatMiMo | ChatOpenAI                                  │
│  配置驱动，per-Agent 可指定不同模型                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 组件清单

| # | 组件 | 类型 | 职责 |
|---|------|------|------|
| 1 | 前端 | Vue 3 SPA | 用户交互界面（对话、看板、测评） |
| 2 | API Gateway | FastAPI | 认证、路由、WebSocket、限流 |
| 3 | Orchestrator | 长驻进程 | LangGraph 状态图编排、并发管理 |
| 4 | 用户画像 Agent | FastAPI | 构建用户数字画像、KYC |
| 5 | 市场研判 Agent | FastAPI | 多源数据分析、风险矩阵 |
| 6 | 策略生成 Agent | FastAPI | 四笔钱配置、压力测试 |
| 7 | 陪伴督导 Agent | FastAPI + MQ | 用户交互、纠偏、心理按摩 |
| 8 | Market Monitor | 定时任务 | 检测市场异动，发布事件 |
| 9 | User Monitor | FastAPI | 检测用户偏离，发布事件 |
| 10 | MCP Server | MCP 协议服务 | 数据源适配、限流、缓存 |

---

## 3. Agent 详细设计

### 3.1 Orchestrator（状态图编排）

**职责：**
- 持有 LangGraph 状态图定义，管理全局流程状态
- 为每个用户创建独立的状态图实例
- 根据条件分支逻辑决定消息路由
- 处理 Agent 间的上下文传递和重规划

**接口：**
Orchestrator 作为 FastAPI 服务暴露 HTTP 接口，API Gateway 通过 HTTP 调用：
- `POST /orchestrator/start` — 启动新的状态图实例
- `POST /orchestrator/resume` — 恢复暂停的状态图实例
- `POST /orchestrator/replan` — 触发重规划
- `GET /orchestrator/status/{user_id}` — 查询当前流程状态

**状态图定义：**

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated

class FinancialPlanningState(TypedDict):
    user_id: str
    user_profile: dict          # 用户画像数据
    market_analysis: dict       # 市场分析结果
    strategy: dict              # 生成的配置方案
    coaching_history: list      # 督导对话历史
    current_step: str           # 当前步骤
    needs_followup: bool        # 是否需要追问
    replan_trigger: str | None  # 重规划触发原因

# 状态图构建
workflow = StateGraph(FinancialPlanningState)

# 添加节点
workflow.add_node("profile", call_profile_agent)
workflow.add_node("market", call_market_agent)
workflow.add_node("strategy", call_strategy_agent)
workflow.add_node("coaching", call_coaching_agent)

# 条件分支
workflow.add_conditional_edges(
    "profile",
    route_after_profile,
    {
        "needs_followup": "coaching",
        "ready": "market"
    }
)

workflow.add_conditional_edges(
    "strategy",
    route_after_strategy,
    {
        "needs_explanation": "coaching",
        "complete": END
    }
)

# 并行执行（画像和市场可以并行）
workflow.add_edge("profile", "market")  # 或并行
workflow.add_edge("market", "strategy")
```

**并发管理：**
- 每个用户有独立的 LangGraph Runnable 实例
- 实例 ID = user_id
- 状态持久化到 PostgreSQL（langgraph_checkpoints 表）
- 进程重启后可从 checkpoint 恢复

**重规划机制：**

```
POST /orchestrator/replan
{
  "user_id": "xxx",
  "trigger": "market_anomaly",
  "trigger_detail": "沪深300单日跌幅-3.5%",
  "replan_from": "market_analysis",
  "context": { ... }
}
```

Orchestrator 收到重规划请求时：
1. 检查该用户是否有进行中的流程
2. 如果有，取消当前流程，从指定节点重新开始
3. 如果没有，创建新流程从指定节点开始
4. 使用防抖机制，短时间内多次重规划只执行最后一次

### 3.2 用户画像 Agent

**职责：**
- 动态分析用户的收入、支出、风险偏好、所处生命周期阶段
- 构建可更新的数字画像
- KYC 流程模拟
- 适当性匹配留痕

**接口：**

```
POST /agent/profile/analyze
Request:
{
  "user_id": "xxx",
  "risk_assessment": {
    "age": 30,
    "income": 20000,
    "expenses": 12000,
    "risk_tolerance": "moderate",
    "investment_horizon": "5y"
  }
}

Response:
{
  "profile": {
    "lifecycle_stage": "accumulation",
    "risk_capacity": "medium",
    "investable_assets": 500000,
    "monthly_surplus": 8000,
    "kyc_level": "standard"
  },
  "needs_followup": false,
  "followup_questions": []
}
```

**内部逻辑：**
- LangChain 调用 LLM 分析用户输入
- MCP Client 调用数据源获取市场基准数据
- 输出结构化画像，持久化到 PostgreSQL

### 3.3 市场研判 Agent

**职责：**
- 采集宏观指标、行业轮动、基金评级等多源异构数据
- 输出主要资产的预期收益与风险矩阵
- 计算资产相关性

**接口：**

```
POST /agent/market/analyze
Request:
{
  "analysis_type": "full",
  "focus_areas": ["equity", "bond", "commodity"],
  "time_horizon": "1y"
}

Response:
{
  "market_overview": {
    "equity": {"expected_return": 0.08, "volatility": 0.20},
    "bond": {"expected_return": 0.035, "volatility": 0.05},
    "commodity": {"expected_return": 0.05, "volatility": 0.15}
  },
  "correlation_matrix": [[1.0, -0.2, 0.1], ...],
  "risk_factors": ["利率上行风险", "地缘政治风险"],
  "recommendation": "适度增配债券"
}
```

**MCP 工具调用：**
- `get_index_data(symbol, period)` — 获取指数数据
- `get_fund_rating(fund_id)` — 获取基金评级
- `get_macro_indicator(indicator)` — 获取宏观指标
- `get_bond_yield curve` — 获取债券收益率曲线

### 3.4 策略生成 Agent

**职责：**
- 基于现代投资组合理论（MPT）
- 结合用户画像与市场输入
- 生成"四笔钱"配置方案
- 附带调仓逻辑与压力测试

**接口：**

```
POST /agent/strategy/generate
Request:
{
  "user_id": "xxx",
  "profile": { ... },
  "market_analysis": { ... }
}

Response:
{
  "four_buckets": {
    "living_money": {
      "allocation": 0.10,
      "products": ["货币基金", "活期存款"],
      "reason": "保持3-6个月生活费流动性"
    },
    "stable_money": {
      "allocation": 0.30,
      "products": ["债券基金", "银行理财"],
      "reason": "稳健增值，波动可控"
    },
    "growth_money": {
      "allocation": 0.50,
      "products": ["沪深300ETF", "偏股混合基金"],
      "reason": "长期增值，承受短期波动"
    },
    "protection_money": {
      "allocation": 0.10,
      "products": ["重疾险", "意外险"],
      "reason": "风险兜底，防止因病返贫"
    }
  },
  "rebalance_triggers": {
    "drift_threshold": 0.05,
    "review_frequency": "quarterly"
  },
  "stress_test": {
    "scenario_2015_crash": {"loss": -0.15, "recovery_time": "8m"},
    "scenario_covid": {"loss": -0.12, "recovery_time": "4m"}
  }
}
```

**适当性匹配规则引擎：**
- 根据用户风险等级过滤产品
- 记录匹配过程到 compliance_records 表
- 生成模拟监管报告

### 3.5 陪伴督导 Agent

**职责：**
- 实时监测市场异动与用户行为偏离
- 主动进行追问、纠偏与心理按摩
- 保障计划执行率

**双重触发机制：**

1. **Orchestrator 同步调用**（主流程中）：
```
POST /agent/coaching/interact
{
  "user_id": "xxx",
  "context": "strategy_explanation",
  "strategy": { ... }
}
```

2. **RabbitMQ 异步事件触发**：
```
Queue: coaching.events
Message:
{
  "event_type": "market.anomaly.index_drop",
  "user_id": "xxx",
  "detail": {"index": "沪深300", "change": -0.035},
  "timestamp": "2026-05-13T10:30:00Z"
}
```

**督导策略：**
- 市场下跌时：安抚情绪，强调长期配置逻辑
- 用户偏离时：温和提醒，解释偏离风险
- 长期不活跃时：主动问候，了解近况

**重规划请求：**
当督导判断需要重规划时，HTTP 通知 Orchestrator：
```
POST /orchestrator/replan
{
  "user_id": "xxx",
  "trigger": "user_concern",
  "trigger_detail": "用户对当前配置不满，希望更保守",
  "replan_from": "strategy"
}
```

---

## 4. 数据模型

### 4.1 PostgreSQL 表结构

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户画像表
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    lifecycle_stage VARCHAR(50),  -- accumulation, consolidation, distribution
    risk_capacity VARCHAR(20),    -- low, medium, high
    investable_assets DECIMAL(15,2),
    monthly_surplus DECIMAL(15,2),
    kyc_level VARCHAR(20),        -- basic, standard, enhanced
    kyc_verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 风险测评表
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    answers JSONB NOT NULL,
    score INTEGER,
    risk_level VARCHAR(20),       -- conservative, moderate, aggressive
    assessed_at TIMESTAMP DEFAULT NOW()
);

-- 资产配置方案表
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    strategy_id UUID,
    four_buckets JSONB NOT NULL,
    total_assets DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'active',  -- active, archived, rebalancing
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 策略详情表
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    market_analysis_id UUID,
    rebalance_triggers JSONB,
    stress_test_results JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 市场分析记录表
CREATE TABLE market_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_type VARCHAR(50),
    market_overview JSONB,
    correlation_matrix JSONB,
    risk_factors JSONB,
    analyzed_at TIMESTAMP DEFAULT NOW()
);

-- 审计日志表（轻量级，用于合规留痕）
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(50),            -- user, system, agent
    detail JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 合规记录表
CREATE TABLE compliance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    record_type VARCHAR(50),      -- kyc, suitability, risk_disclosure
    content JSONB NOT NULL,
    signed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- LangGraph 状态检查点表（高频读写，建议单独表空间）
CREATE TABLE langgraph_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id VARCHAR(100) NOT NULL,  -- user_id 作为 thread_id
    checkpoint JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_checkpoints_thread ON langgraph_checkpoints(thread_id, created_at DESC);
```

### 4.2 Redis 缓存结构

```
# 会话缓存
session:{user_id} → JSON (JWT token, last_active, current_step)

# 市场数据缓存
market:index:{symbol} → JSON (最新指数数据，TTL 5分钟)
market:macro:{indicator} → JSON (宏观指标，TTL 1小时)

# LLM 响应缓存
llm:cache:{hash(prompt)} → JSON (LLM 响应，TTL 24小时)

# 限流计数器
ratelimit:mcp:{source} → Integer (每秒请求数)
```

---

## 5. 关键流程

### 5.1 新用户首次理财规划

```
用户                    API Gateway          Orchestrator         画像Agent        市场Agent        策略Agent        督导Agent
 │                         │                    │                   │               │               │               │
 │  POST /risk-assessment  │                    │                   │               │               │               │
 │ ───────────────────────→│                    │                   │               │               │               │
 │                         │  创建状态图实例      │                   │               │               │               │
 │                         │ ──────────────────→│                   │               │               │               │
 │                         │                    │                   │               │               │               │
 │                         │                    │  HTTP /analyze     │               │               │               │
 │                         │                    │ ──────────────────→│               │               │               │
 │                         │                    │                   │               │               │               │
 │                         │                    │  返回画像           │               │               │               │
 │                         │                    │ ←──────────────────│               │               │               │
 │                         │                    │                   │               │               │               │
 │                         │                    │  HTTP /analyze     │               │               │               │
 │                         │                    │ ───────────────────────────────────→│               │               │
 │                         │                    │                   │               │               │               │
 │                         │                    │  返回市场分析       │               │               │               │
 │                         │                    │ ←───────────────────────────────────│               │               │
 │                         │                    │                   │               │               │               │
 │                         │                    │  HTTP /generate    │               │               │               │
 │                         │                    │ ──────────────────────────────────────────────────→│               │
 │                         │                    │                   │               │               │               │
 │                         │                    │  返回配置方案       │               │               │               │
 │                         │                    │ ←──────────────────────────────────────────────────│               │
 │                         │                    │                   │               │               │               │
 │                         │                    │  条件：需解释方案   │               │               │               │
 │                         │                    │  HTTP /interact    │               │               │               │
 │                         │                    │ ─────────────────────────────────────────────────────────────────→│
 │                         │                    │                   │               │               │               │
 │                         │                    │  返回督导内容       │               │               │               │
 │                         │                    │ ←─────────────────────────────────────────────────────────────────│
 │                         │                    │                   │               │               │               │
 │  WebSocket 推送方案     │                    │                   │               │               │               │
 │ ←──────────────────────│←───────────────────│                   │               │               │               │
 │                         │                    │                   │               │               │               │
```

### 5.2 市场异动触发重规划

```
Market Monitor          RabbitMQ           督导Agent          Orchestrator         市场Agent        策略Agent
    │                      │                   │                   │                   │               │
    │  检测到沪深300跌3.5%  │                   │                   │                   │               │
    │  发布事件             │                   │                   │                   │               │
    │ ────────────────────→│                   │                   │                   │               │
    │                      │  消费事件          │                   │                   │               │
    │                      │ ─────────────────→│                   │                   │               │
    │                      │                   │                   │                   │               │
    │                      │                   │  生成安抚内容       │                   │               │
    │                      │                   │  WebSocket 推送    │                   │               │
    │                      │                   │ ─────────────────→│ (推送给用户)        │               │
    │                      │                   │                   │                   │               │
    │                      │                   │  判断需重规划       │                   │               │
    │                      │                   │  HTTP /replan      │                   │               │
    │                      │                   │ ─────────────────→│                   │               │
    │                      │                   │                   │                   │               │
    │                      │                   │                   │  取消当前流程       │               │
    │                      │                   │                   │  从市场分析重跑     │               │
    │                      │                   │                   │ ─────────────────→│               │
    │                      │                   │                   │                   │               │
    │                      │                   │                   │  返回新分析         │               │
    │                      │                   │                   │ ←─────────────────│               │
    │                      │                   │                   │                   │               │
    │                      │                   │                   │  生成新策略         │               │
    │                      │                   │                   │ ──────────────────────────────────→│
    │                      │                   │                   │                   │               │
    │                      │                   │                   │  返回新方案         │               │
    │                      │                   │                   │ ←──────────────────────────────────│
    │                      │                   │                   │                   │               │
```

---

## 6. 异常场景处理

### 6.1 Orchestrator 状态图持久化与恢复

**问题：** 内存中同时住着大量状态图实例，进程重启时未完成的状态图会丢失。

**解决方案：**
- LangGraph 支持 Checkpoint 机制，每次状态变更时持久化到 PostgreSQL
- 进程重启后，从 checkpoint 恢复状态图实例
- 序列化要求：状态图中的数据必须可 JSON 序列化
- 定期清理过期 checkpoint（保留最近 7 天）

### 6.2 Checkpoint 与审计日志 IO 隔离

**问题：** langgraph_checkpoints 高频读写可能阻塞 audit_logs 写入。

**解决方案：**
- 分离表空间：checkpoints 和 audit_logs 使用不同的 PostgreSQL 表空间
- 或使用不同的数据库实例（学习项目可简化为同一实例，但逻辑分离）
- 审计日志使用异步写入（通过消息队列缓冲）

### 6.3 Monitor 组件不需要 MCP Client

**问题：** Market Monitor 和 User Monitor 不应直接调用外部 API。

**解决方案：**
- Market Monitor 读取 Redis 缓存或 PostgreSQL 历史数据
- User Monitor 监听交易事件（通过 RabbitMQ）或扫描 PostgreSQL
- 两个 Monitor 都不需要 MCP Client，减少网络开销和凭证泄露面

### 6.4 重规划并发冲突

**问题：** 短时间内市场波动极大时，同一用户可能收到多条重规划指令。

**解决方案：**
- Orchestrator 维护每个用户的重规划锁
- 如果已有重规划进行中，新请求排队等待
- 使用防抖机制：30 秒内的多次重规划只执行最后一次
- 重规划请求携带优先级，高优先级可中断低优先级

### 6.5 LLM 调用超时与降级

**问题：** LLM API 可能超时或不可用。

**解决方案：**
- 设置超时时间（30 秒）
- 超时后降级到缓存的响应或默认模板
- 支持模型切换（DeepSeek 超时后切 MiMo）
- 记录超时事件到审计日志

---

## 7. 技术栈

| 层级 | 技术 | 版本 | 理由 |
|------|------|------|------|
| 前端 | Vue 3 + TypeScript + Vite | 3.4+ | 组合式 API，类型安全 |
| UI 组件 | Element Plus / Ant Design Vue | - | 企业级组件库 |
| 后端框架 | FastAPI | 0.110+ | 异步、自动文档、类型校验 |
| Agent 框架 | LangGraph | 0.2+ | 状态图编排、条件分支、checkpoint |
| LLM 编排 | LangChain | 0.2+ | 多模型抽象、工具调用 |
| MCP 实现 | mcp (Python) | 1.0+ | 标准化工具协议 |
| 消息队列 | RabbitMQ | 3.12+ | 持久化、ack、死信队列 |
| 数据库 | PostgreSQL | 16+ | JSONB 支持、可靠性 |
| 缓存 | Redis | 7+ | 高性能、会话管理 |
| 向量数据库 | Chroma | 0.4+ | 轻量级起步，后续集成（Phase 2） |
| 容器化 | Docker + Docker Compose | - | 单机部署 |
| LLM 接入 | LangChain ChatModel | - | DeepSeek、MiMo、OpenAI 兼容 |

---

## 8. 部署架构

### 8.1 Docker Compose 服务列表

```yaml
services:
  # 前端
  frontend:
    build: ./frontend
    ports: ["3000:80"]

  # API Gateway
  api-gateway:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis, rabbitmq]

  # Orchestrator
  orchestrator:
    build: ./backend/orchestrator
    depends_on: [postgres, redis, rabbitmq]

  # Agents
  agent-profile:
    build: ./backend/agents/profile
    depends_on: [postgres, mcp-server]

  agent-market:
    build: ./backend/agents/market
    depends_on: [postgres, mcp-server]

  agent-strategy:
    build: ./backend/agents/strategy
    depends_on: [postgres]

  agent-coaching:
    build: ./backend/agents/coaching
    depends_on: [postgres, rabbitmq]

  # Monitors
  monitor-market:
    build: ./backend/monitors/market
    depends_on: [redis, rabbitmq]

  monitor-user:
    build: ./backend/monitors/user
    depends_on: [postgres, rabbitmq]

  # MCP Server
  mcp-server:
    build: ./backend/mcp
    ports: ["8001:8001"]

  # 基础设施
  postgres:
    image: postgres:16
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine

  rabbitmq:
    image: rabbitmq:3.12-management
    ports: ["5672:5672", "15672:15672"]

volumes:
  pgdata:
```

### 8.2 网络拓扑

```
外部访问 → localhost:3000 (前端)
         → localhost:8000 (API Gateway)
         → localhost:15672 (RabbitMQ 管理界面)

内部网络：
  api-gateway → orchestrator (HTTP)
  orchestrator → agent-* (HTTP)
  agent-* → mcp-server (SSE)
  agent-coaching → rabbitmq (AMQP)
  monitor-* → rabbitmq (AMQP)
  所有服务 → postgres (TCP 5432)
  所有服务 → redis (TCP 6379)
```

---

## 9. 合规性设计

### 9.1 KYC 流程模拟

1. 用户注册时收集基本信息（年龄、职业、收入）
2. 风险测评问卷（10-15 题）
3. 根据答案计算风险等级
4. 记录到 compliance_records 表
5. 策略生成时校验适当性匹配

### 9.2 适当性匹配规则

```python
SUITABILITY_RULES = {
    "conservative": {
        "allowed_products": ["货币基金", "债券基金", "银行理财", "国债"],
        "max_equity_allocation": 0.20
    },
    "moderate": {
        "allowed_products": ["混合基金", "指数基金", "债券基金"],
        "max_equity_allocation": 0.60
    },
    "aggressive": {
        "allowed_products": ["股票", "股票基金", "期货", "期权"],
        "max_equity_allocation": 0.90
    }
}
```

### 9.3 审计日志

所有关键操作记录到 audit_logs 表：
- 用户注册/登录
- 风险测评完成
- 策略生成
- 策略变更
- 重规划触发
- Agent 调用记录

---

## 10. 后续演进方向

1. **MCP Server 多实例**：根据数据源频率限制调整，支持水平扩展
2. **向量数据库集成**：引入 Chroma/Milvus，RAG 增强市场知识库检索
3. **前端实时图表**：WebSocket 推送市场数据，ECharts 可视化
4. **移动端适配**：响应式设计或 React Native
5. **分布式追踪**：引入 OpenTelemetry，实现跨服务调用链追踪

---

## 附录 A：设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 架构风格 | 微服务 + 消息队列 | 作品集展示多技能点，架构向生产级靠拢 |
| Agent 协作 | 条件分支 | 动态路由，支持重规划 |
| 编排方式 | Orchestrator + LangGraph | 状态图天然支持条件分支和 checkpoint |
| 消息队列 | RabbitMQ | 持久化、ack、死信队列 |
| 数据源协议 | MCP | 标准化工具调用，支持多源扩展 |
| LLM 接入 | LangChain 抽象层 | 多模型切换，per-Agent 配置 |
| 数据库 | PostgreSQL | JSONB 支持、可靠性 |
| 缓存 | Redis | 高性能、会话管理 |

## 附录 B：开放问题

1. **LLM 模型选择策略**：不同 Agent 使用不同模型的具体配置规则
2. **数据源优先级**：多个数据源返回不一致时的仲裁逻辑
3. **用户数据脱敏**：敏感字段（收入、资产）的加密存储方案
4. **压力测试数据**：历史极端行情数据的来源和模拟方式
