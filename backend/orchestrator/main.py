import os
import uuid as uuid_lib
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from orchestrator.graph import graph
from orchestrator.state import FinancialPlanningState
from shared.database import async_session
from shared.models.portfolio import Portfolio, Strategy, MarketAnalysis
from shared.models.profile import UserProfile

app = FastAPI(title="Orchestrator")

user_states: Dict[str, FinancialPlanningState] = {}


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
                    correlation_matrix={}
                )
                db.add(market_record)
                await db.flush()

            # 保存策略
            strategy_data = state.get("strategy", {})
            four_buckets = strategy_data.get("four_buckets", {})

            # 获取可投资资产
            result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == uuid_lib.UUID(user_id))
            )
            profile = result.scalar_one_or_none()
            total_assets = float(profile.investable_assets) if profile and profile.investable_assets else 0

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
                            state["market_analysis"] = {
                                "market_overview": ma_record.market_overview or {},
                                "risk_factors": ma_record.risk_factors or [],
                            }

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
    """启动理财规划流程"""
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

    try:
        result = await graph.ainvoke(initial_state)
        user_states[user_id] = result

        # P0-5: 持久化到数据库
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

    if not state:
        # 尝试从数据库加载
        db_state = await load_strategy_from_db(user_id)
        if db_state:
            return OrchestratorResponse(
                user_id=user_id,
                current_step=db_state.get("current_step", "unknown"),
                user_profile=db_state.get("user_profile"),
                market_analysis=db_state.get("market_analysis"),
                strategy=db_state.get("strategy"),
                coaching_history=db_state.get("coaching_history")
            )
        raise HTTPException(status_code=404, detail="User planning session not found")

    return OrchestratorResponse(
        user_id=user_id,
        current_step=state.get("current_step", "unknown"),
        user_profile=state.get("user_profile"),
        market_analysis=state.get("market_analysis"),
        strategy=state.get("strategy"),
        coaching_history=state.get("coaching_history")
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchestrator"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=port)
