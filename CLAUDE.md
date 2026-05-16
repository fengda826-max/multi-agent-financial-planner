# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick commands

```bash
# Start all backend services
docker compose up -d postgres redis rabbitmq api-gateway orchestrator agent-profile agent-market agent-strategy agent-coaching

# Start frontend dev server
cd frontend && npm run dev                    # → localhost:3000

# TypeScript check
cd frontend && npx vue-tsc --noEmit

# Restart a service after code change
docker compose restart orchestrator           # uvicorn --reload usually auto-detects, but restart if not

# Database
docker exec fp-postgres psql -U financial_planner -d financial_planner -c "\dt"
docker exec fp-postgres psql -U financial_planner -d financial_planner -c "SELECT id, username FROM users;"

# Test APIs
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/auth/register -H "Content-Type: application/json" -d '{"username":"t","password":"123456"}'
curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"t","password":"123456"}'
curl -s http://localhost:8010/status/<user_id>

# Git
git push origin feature/multi-agent-financial-planner
```

## Architecture

12 Docker services orchestrated via docker-compose.yml. All backend code in `backend/`, mounted as volume so uvicorn --reload picks up changes.

### Service dependency chain

```
postgres + redis + rabbitmq (infrastructure)
  → api-gateway (:8000)         — JWT auth, CORS, routes /api/*, proxies /api/orchestrator/* → orchestrator
  → orchestrator (:8010)        — LangGraph state machine, /start /status /replan /chat
    → agent-profile (:8001)     — LLM: 12-field user profile (lifecycle, health score, strengths, etc.)
    → agent-market (:8002)      — AKShare real data (async, 10s timeout/source) + LLM: expected returns, volatility, risk factors
    → agent-strategy (:8003)    — LLM: four_buckets allocation + suitability rules engine
    → agent-coaching (:8004)    — LLM (temp=0.7): chat advisor with 6-message conversation memory + RabbitMQ consumer
```

### LangGraph flow (orchestrator/graph.py)

```
profile → [conditional] → market → strategy → [conditional] → coaching → END
```

- `route_after_profile`: checks `needs_followup` → market (normal) or coaching (followup). In practice, always routes to market because orchestrator auto-injects `investable_assets`.
- `route_after_strategy`: always routes to coaching.
- Each node calls its agent via HTTP and returns partial state dict. Graph composes final state.
- **Progressive disclosure**: `_update_progress()` writes intermediate results to `user_states` after each node. Frontend polls `/status` every 2s, shows sections as they become available: profile → market → strategy → coaching.

### State & persistence (orchestrator/state.py + main.py)

- `FinancialPlanningState` TypedDict with `user_id, risk_assessment, user_profile, market_analysis, strategy, coaching_history (operator.add), current_step, needs_followup, replan_trigger, error`
- `user_states` dict (in-memory) shared between graph nodes and API endpoints. Graph nodes report progress via `_update_progress()`.
- On `/start`: graph runs as background task (`asyncio.create_task`), frontend polls `/status` for progress.
- On `/status`: checks memory first, falls back to `load_strategy_from_db()` which reads Portfolio→Strategy→MarketAnalysis FK chain.
- `save_strategy_to_db()` writes Portfolio, Strategy, MarketAnalysis on completion.

### Data sources

- **User data**: PostgreSQL (users, user_profiles, risk_assessments tables). Written during register + risk assessment.
- **Market data**: AKShare direct calls (not via MCP server). 4 sources: 沪深300, 创业板指, 10年国债, CPI. Falls back to hardcoded defaults if AKShare fails.
- **AI**: DeepSeek v4-pro via `langchain-openai` (OpenAI-compatible API at `https://api.deepseek.com/v1`).

### Suitability rules (agents/strategy/agent.py)

Applied **after** LLM generates strategy:

| Risk level | Max equity | Allowed products |
|------------|-----------|------------------|
| conservative/low | 20% | 货币基金, 债券基金, 银行理财, 国债 |
| moderate/medium | 60% | 混合基金, 指数基金, 债券基金 |
| aggressive/high | 90% | 股票, 股票基金, 期货, 期权 |

If growth_money.allocation exceeds cap, excess is moved to stable_money.

### Risk scoring (api_gateway/routers/risk_assessment.py)

4 dimensions: age (<30:30, <40:25, <50:20, ≥50:10), income (>30k:25, >15k:20, >8k:15, else:10), risk_tolerance (aggressive:30, moderate:20, conservative:10), horizon (10y+:30, 5y:25, 3y:15, 1y:5). Score <50→conservative, <75→moderate, ≥75→aggressive.

### Frontend routes (10 pages)

| Route | Page | Purpose |
|-------|------|---------|
| /login, /register | Login, Register | Auth (guest-only) |
| / | Layout → /dashboard | Top nav shell (auth-required children) |
| /dashboard | Dashboard | Health score + 4 metrics + ECharts ring chart |
| /my-plan | MyPlan | Full strategy detail + rebalance button |
| /ai-chat | AIChat | Conversational coaching with history |
| /market | Market | Real-time indicators + AI market analysis |
| /profile | Profile | User info + risk level + plan history |
| /risk-assessment | RiskAssessment | 3-step wizard |
| /strategy-result | StrategyResult | Progressive disclosure: profile→market→strategy→coaching |

Auth guard: `router.beforeEach` checks `localStorage.token`. API interceptor adds `Authorization: Bearer` header and handles 401 → redirect to /login.

## Key files

```
backend/orchestrator/graph.py          # LangGraph state machine (nodes + edges)
backend/orchestrator/main.py           # /start /status /replan /chat endpoints + DB persistence
backend/orchestrator/state.py          # FinancialPlanningState TypedDict + user_states dict
backend/agents/strategy/agent.py       # Suitability rules + _default_strategy fallback
backend/agents/market/main.py          # fetch_real_market_data() — AKShare integration
backend/agents/coaching/agent.py       # generate_response() — conversation history support
backend/api_gateway/main.py            # API Gateway + orchestrator proxy
backend/api_gateway/routers/risk_assessment.py  # Scoring algorithm + /history endpoint
backend/api_gateway/middleware/auth.py # JWT + bcrypt
frontend/src/api/client.ts            # Axios instance + typed API methods
frontend/src/router/index.ts          # Routes with auth guard
frontend/src/views/Layout.vue         # Top nav bar (shared by all auth pages)
```

## Key design deviations

- **MCP Server unused**: Market Agent calls AKShare directly, not through MCP stdio server.
- **Replan always full**: `replan_from` parameter accepted but LangGraph always starts from entry point.
- **needs_followup always false**: Orchestrator calculates `investable_assets` before calling Profile Agent, so followup branch never triggers.
- **WebSocket not implemented**: Frontend uses HTTP polling/on-demand fetch instead.
- **Audit logs not written**: `audit_logs` table exists but no code writes to it.
- **Monitors not running**: `monitor-market` and `monitor-user` defined in docker-compose but containers not started.
