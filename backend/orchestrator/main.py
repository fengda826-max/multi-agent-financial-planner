import os
import json
import uuid as uuid_lib
import asyncio
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from orchestrator.graph import graph
from orchestrator.state import FinancialPlanningState, user_states
from shared.database import async_session
from shared.models.portfolio import Portfolio, Strategy, MarketAnalysis
from shared.models.profile import UserProfile

app = FastAPI(title="Orchestrator")


class StartRequest(BaseModel):
    user_id: str
    risk_assessment: Dict[str, Any]


class ReplanRequest(BaseModel):
    user_id: str
    trigger: str
    trigger_detail: str
    replan_from: str
    context: Optional[Dict[str, Any]] = None


class OrchestratorResponse(BaseModel):
    user_id: str
    current_step: str
    user_profile: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    coaching_history: Optional[list] = None
    error: Optional[str] = None


async def save_strategy_to_db(user_id: str, state: FinancialPlanningState):
    """将策略结果持久化到数据库"""
    try:
        async with async_session() as db:
            # 保存市场分析
            market_analysis = state.get("market_analysis", {})
            market_record = None
            if market_analysis and "market_overview" in market_analysis:
                market_record = MarketAnalysis(
                    analysis_type="full",
                    market_overview=market_analysis.get("market_overview", {}),
                    risk_factors=market_analysis.get("risk_factors", []),
                    correlation_matrix={
                        "computed_metrics": market_analysis.get("computed_metrics", {}),
                        "data_timestamp": market_analysis.get("data_timestamp", ""),
                        "agent_steps": state.get("agent_steps", {}),
                    }
                )
                db.add(market_record)
                await db.flush()

            # 保存策略
            strategy_data = state.get("strategy", {})
            four_buckets = strategy_data.get("four_buckets", {})

            # 获取并更新用户画像
            result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == uuid_lib.UUID(user_id))
            )
            profile = result.scalar_one_or_none()
            total_assets = float(profile.investable_assets) if profile and profile.investable_assets else 0

            # 同步Profile Agent返回的lifecycle_stage到DB
            user_profile_data = state.get("user_profile", {})
            if profile and user_profile_data.get("lifecycle_stage"):
                profile.lifecycle_stage = user_profile_data["lifecycle_stage"]
            elif profile and not profile.lifecycle_stage:
                # Fallback: 根据年龄推断
                risk_assessment = state.get("risk_assessment", {})
                age = risk_assessment.get("age", 30)
                profile.lifecycle_stage = "accumulation" if age < 35 else ("consolidation" if age < 50 else "distribution")

            # 创建Portfolio
            portfolio = Portfolio(
                user_id=uuid_lib.UUID(user_id),
                four_buckets=four_buckets if four_buckets else {},
                total_assets=total_assets,
                status="active"
            )
            db.add(portfolio)
            await db.flush()

            # 创建Strategy记录
            strategy_record = Strategy(
                portfolio_id=portfolio.id,
                market_analysis_id=market_record.id if market_record else None,
                rebalance_triggers=strategy_data.get("rebalance_triggers", {}),
                stress_test_results=strategy_data.get("stress_test", {})
            )
            db.add(strategy_record)
            await db.flush()  # 先flush让strategy获得ID
            portfolio.strategy_id = strategy_record.id

            await db.commit()
    except Exception as e:
        print(f"Failed to persist strategy to DB: {e}")


async def load_strategy_from_db(user_id: str) -> Optional[Dict[str, Any]]:
    """从数据库加载最新的策略数据"""
    try:
        async with async_session() as db:
            # 查询最新的活跃portfolio
            result = await db.execute(
                select(Portfolio)
                .where(Portfolio.user_id == uuid_lib.UUID(user_id))
                .where(Portfolio.status == "active")
                .order_by(Portfolio.created_at.desc())
                .limit(1)
            )
            portfolio = result.scalar_one_or_none()
            if not portfolio:
                return None

            state = {
                "current_step": "coaching_complete",
                "strategy": {"four_buckets": portfolio.four_buckets or {}, "rebalance_triggers": {}, "stress_test": {}},
                "market_analysis": {},
                "user_profile": {},
                "coaching_history": [],
            }

            # 加载策略详情
            if portfolio.strategy_id:
                strat_result = await db.execute(
                    select(Strategy).where(Strategy.id == portfolio.strategy_id)
                )
                strategy_record = strat_result.scalar_one_or_none()
                if strategy_record:
                    state["strategy"]["rebalance_triggers"] = strategy_record.rebalance_triggers or {}
                    state["strategy"]["stress_test"] = strategy_record.stress_test_results or {}

                    # 加载市场分析
                    if strategy_record.market_analysis_id:
                        ma_result = await db.execute(
                            select(MarketAnalysis).where(MarketAnalysis.id == strategy_record.market_analysis_id)
                        )
                        ma_record = ma_result.scalar_one_or_none()
                        if ma_record:
                            corr = ma_record.correlation_matrix or {}
                            state["market_analysis"] = {
                                "market_overview": ma_record.market_overview or {},
                                "risk_factors": ma_record.risk_factors or [],
                                "computed_metrics": corr.get("computed_metrics", {}),
                                "data_timestamp": corr.get("data_timestamp", ""),
                            }
                            if "agent_steps" in corr:
                                state["agent_steps"] = corr["agent_steps"]

            # 加载用户画像
            profile_result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == uuid_lib.UUID(user_id))
            )
            profile = profile_result.scalar_one_or_none()
            if profile:
                state["user_profile"] = {
                    "lifecycle_stage": profile.lifecycle_stage,
                    "risk_capacity": profile.risk_capacity,
                    "investable_assets": float(profile.investable_assets) if profile.investable_assets else 0,
                    "monthly_surplus": float(profile.monthly_surplus) if profile.monthly_surplus else 0,
                }

            return state
    except Exception as e:
        print(f"Failed to load strategy from DB: {e}")
        return None


@app.post("/start", response_model=OrchestratorResponse)
async def start_planning(request: StartRequest):
    """启动理财规划流程（异步后台执行，前端轮询 /status 获取进度）"""
    user_id = str(request.user_id)

    initial_state: FinancialPlanningState = {
        "user_id": user_id,
        "risk_assessment": request.risk_assessment,
        "user_profile": {},
        "market_analysis": {},
        "strategy": {},
        "coaching_history": [],
        "current_step": "started",
        "needs_followup": False,
        "replan_trigger": None,
        "error": None
    }

    # 先存入内存，让 /status 可轮询到中间状态
    user_states[user_id] = initial_state

    # 后台执行完整流程
    # 用可变容器在闭包中捕获 agent_steps
    captured_steps: Dict[str, Any] = {}

    async def run_graph():
        try:
            result = await graph.ainvoke(initial_state)
            # 从 user_states 中读取执行期间 _update_progress 写入的 agent_steps
            # （graph.ainvoke 返回的 result 不含此字段）
            captured_steps.update(user_states.get(user_id, {}).get("agent_steps", {}))
            user_states[user_id] = result
            user_states[user_id]["agent_steps"] = captured_steps
            await save_strategy_to_db(user_id, result)
        except Exception as e:
            user_states[user_id]["error"] = str(e)
            print(f"Graph execution error for {user_id}: {e}")

    asyncio.create_task(run_graph())

    return OrchestratorResponse(
        user_id=user_id,
        current_step="started",
        user_profile={},
        market_analysis={},
        strategy={},
        coaching_history=[]
    )


@app.post("/replan", response_model=OrchestratorResponse)
async def replan(request: ReplanRequest):
    """触发重规划 - P0-6: 修复为完整重新执行"""
    user_id = str(request.user_id)

    # 从内存或数据库加载已有状态
    current_state = user_states.get(user_id)
    if not current_state:
        db_state = await load_strategy_from_db(user_id)
        if db_state:
            # 转换为 FinancialPlanningState
            risk_assessment = {"age": 30, "income": 20000, "expenses": 12000,
                            "risk_tolerance": "moderate", "investment_horizon": "5y"}
            current_state = {
                "user_id": user_id,
                "risk_assessment": risk_assessment,
                "user_profile": db_state.get("user_profile", {}),
                "market_analysis": db_state.get("market_analysis", {}),
                "strategy": db_state.get("strategy", {}),
                "coaching_history": db_state.get("coaching_history", []),
                "current_step": "started",
                "needs_followup": False,
                "replan_trigger": request.trigger,
                "error": None
            }
        else:
            raise HTTPException(status_code=404, detail="User planning session not found")

    current_state["replan_trigger"] = request.trigger

    # P0-6 fix: 完整重新执行，而非从指定节点开始
    # LangGraph的ainvoke总是从entry_point开始，所以这里是完整重执行
    # replan_from 用于告知用户重规划的原因范围
    try:
        result = await graph.ainvoke(current_state)
        user_states[user_id] = result

        # 持久化新的结果
        await save_strategy_to_db(user_id, result)

        return OrchestratorResponse(
            user_id=user_id,
            current_step=result.get("current_step", "unknown"),
            user_profile=result.get("user_profile"),
            market_analysis=result.get("market_analysis"),
            strategy=result.get("strategy"),
            coaching_history=result.get("coaching_history")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{user_id}", response_model=OrchestratorResponse)
async def get_status(user_id: str):
    """查询当前流程状态 - P0-5: 支持从DB加载"""
    state = user_states.get(user_id)

    # 如果内存状态缺失字段，从数据库补充
    if state:
        missing_fields = []
        if not state.get("strategy", {}).get("four_buckets"):
            missing_fields.append("strategy")
        if not state.get("market_analysis", {}).get("market_overview"):
            missing_fields.append("market_analysis")
        if not state.get("user_profile", {}).get("lifecycle_stage"):
            missing_fields.append("user_profile")

        if missing_fields:
            db_state = await load_strategy_from_db(user_id)
            if db_state:
                for field in missing_fields:
                    if db_state.get(field):
                        state[field] = db_state[field]

    if not state:
        state = await load_strategy_from_db(user_id)
        if not state:
            raise HTTPException(status_code=404, detail="User planning session not found")

    return OrchestratorResponse(
        user_id=user_id,
        current_step=state.get("current_step", "unknown"),
        user_profile=state.get("user_profile"),
        market_analysis=state.get("market_analysis"),
        strategy=state.get("strategy"),
        coaching_history=state.get("coaching_history")
    )


class ChatRequest(BaseModel):
    user_id: str
    user_message: str
    strategy: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


@app.post("/chat")
async def chat_with_advisor(request: ChatRequest):
    """AI 对话 - 代理到 Coaching Agent，支持对话历史"""
    try:
        context_parts = []

        # 市场数据上下文
        if request.market_analysis:
            ma = request.market_analysis
            if ma.get("market_overview"):
                overview = ma["market_overview"]
                lines = ["当前市场状况："]
                for asset, info in overview.items():
                    asset_name = {"equity": "权益", "bond": "债券", "commodity": "商品"}.get(asset, asset)
                    lines.append(f"- {asset_name}: 预期收益{info.get('expected_return', 0)*100:.1f}%, 波动率{info.get('volatility', 0)*100:.1f}%, {info.get('recommendation', '')}")
                context_parts.append("\n".join(lines))
            if ma.get("risk_factors"):
                context_parts.append(f"市场风险因素: {', '.join(ma['risk_factors'])}")
            if ma.get("overall_recommendation"):
                context_parts.append(f"整体建议: {ma['overall_recommendation']}")

        # 策略上下文
        if request.strategy:
            buckets = request.strategy.get("four_buckets", {})
            if buckets:
                lines = ["用户资产配置："]
                name_map = {"living_money": "活钱", "stable_money": "稳健", "growth_money": "长期", "protection_money": "保障"}
                for key, name in name_map.items():
                    b = buckets.get(key, {})
                    if b:
                        lines.append(f"- {name}: {b.get('allocation', 0)*100:.0f}%, 产品: {', '.join(b.get('products', [])[:3])}")
                context_parts.append("\n".join(lines))
            if request.strategy.get("stress_test"):
                context_parts.append(f"压力测试: {json.dumps(request.strategy['stress_test'], ensure_ascii=False)}")

        context = "\n\n".join(context_parts) if context_parts else "暂无市场数据和配置方案"

        async with httpx.AsyncClient() as client:
            payload = {
                "user_id": request.user_id,
                "context": context,
                "strategy": request.strategy,
                "user_message": request.user_message,
            }
            if request.conversation_history:
                payload["conversation_history"] = request.conversation_history

            response = await client.post(
                "http://agent-coaching:8004/interact",
                json=payload,
                timeout=60.0
            )
            result = response.json()
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchestrator"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=port)
