from langgraph.graph import StateGraph, END
from typing import Dict, Any
import httpx
from orchestrator.state import FinancialPlanningState, user_states

AGENT_URLS = {
    "profile": "http://agent-profile:8001",
    "market": "http://agent-market:8002",
    "strategy": "http://agent-strategy:8003",
    "coaching": "http://agent-coaching:8004",
}


def _update_progress(user_id: str, step: str, **kwargs):
    """更新内存中的进度状态（供 /status 轮询获取中间结果）"""
    if user_id in user_states:
        user_states[user_id]["current_step"] = step
        for key, value in kwargs.items():
            if value:
                if key == "computation_steps":
                    agent_name = step.replace("_complete", "").replace("analyzing_", "").replace("generating_", "")
                    if "agent_steps" not in user_states[user_id]:
                        user_states[user_id]["agent_steps"] = {}
                    user_states[user_id]["agent_steps"][agent_name] = value
                else:
                    user_states[user_id][key] = value


async def call_profile_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用用户画像Agent"""
    user_id = state["user_id"]
    _update_progress(user_id, "analyzing_profile")
    try:
        risk_assessment = dict(state["risk_assessment"])
        # 从收入/支出推算可投资资产，确保完整流程可执行
        if "investable_assets" not in risk_assessment:
            income = risk_assessment.get("income", 0)
            expenses = risk_assessment.get("expenses", 0)
            monthly_surplus = income - expenses
            risk_assessment["investable_assets"] = max(monthly_surplus * 12 * 0.3, 0)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_URLS['profile']}/analyze",
                json={
                    "user_id": state["user_id"],
                    "risk_assessment": risk_assessment
                },
                timeout=120.0
            )
            result = response.json()

        profile_data = result.get("profile", {})
        steps = profile_data.get("computation_steps", [])
        return_data = {
            "user_profile": profile_data,
            "needs_followup": result.get("needs_followup", False),
            "current_step": "profile_complete"
        }
        _update_progress(user_id, "profile_complete",
            user_profile=profile_data,
            computation_steps=steps)
        return return_data
    except Exception as e:
        print(f"Profile agent error: {e}")
        _update_progress(user_id, "profile_complete",
            user_profile={"error": str(e)},
            computation_steps=[{"step":"error","label":"画像分析超时","detail":f"Profile Agent调用失败: {e}","source":"error"}])
        return {
            "user_profile": {"error": str(e)},
            "needs_followup": False,
            "current_step": "profile_complete"
        }


async def call_market_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用市场研判Agent"""
    _update_progress(state["user_id"], "analyzing_market")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_URLS['market']}/analyze",
                json={
                    "analysis_type": "full",
                    "focus_areas": ["equity", "bond", "commodity"],
                    "time_horizon": "1y"
                },
                timeout=120.0
            )

            if response.status_code != 200:
                print(f"Market agent returned status {response.status_code}")
                return {
                    "market_analysis": {"error": f"Status {response.status_code}"},
                    "current_step": "market_complete"
                }

            result = response.json()

        steps = result.get("computation_steps", [])
        _update_progress(state["user_id"], "market_complete",
            market_analysis=result,
            computation_steps=steps)
        return {
            "market_analysis": result,
            "current_step": "market_complete"
        }
    except Exception as e:
        print(f"Market agent error: {type(e).__name__}: {e}")
        _update_progress(state["user_id"], "market_complete",
            market_analysis={"error": str(e)},
            computation_steps=[{"step":"error","label":"市场分析超时","detail":f"Market Agent调用失败: {e}","source":"error"}])
        return {
            "market_analysis": {"error": str(e)},
            "current_step": "market_complete"
        }


async def call_strategy_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用策略生成Agent"""
    _update_progress(state["user_id"], "generating_strategy")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_URLS['strategy']}/generate",
                json={
                    "user_id": state["user_id"],
                    "profile": state["user_profile"],
                    "market_analysis": state["market_analysis"]
                },
                timeout=120.0
            )

            if response.status_code != 200:
                print(f"Strategy agent returned status {response.status_code}")
                return {
                    "strategy": {"error": f"Status {response.status_code}"},
                    "current_step": "strategy_complete"
                }

            result = response.json()

        _update_progress(state["user_id"], "strategy_complete", strategy=result)
        return {
            "strategy": result,
            "current_step": "strategy_complete"
        }
    except Exception as e:
        print(f"Strategy agent error: {type(e).__name__}: {e}")
        return {
            "strategy": {"error": str(e)},
            "current_step": "strategy_complete"
        }


async def call_coaching_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用陪伴督导Agent"""
    _update_progress(state["user_id"], "generating_coaching")
    context = f"用户画像: {state['user_profile']}\n配置方案: {state['strategy']}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['coaching']}/interact",
            json={
                "user_id": state["user_id"],
                "context": context,
                "strategy": state["strategy"]
            },
            timeout=60.0
        )
        result = response.json()

    coaching_entry = {
        "type": "strategy_explanation",
        "message": result.get("message", ""),
        "action": result.get("action", "none")
    }

    _update_progress(state["user_id"], "coaching_complete", coaching_history=[coaching_entry])
    return {
        "coaching_history": [coaching_entry],
        "current_step": "coaching_complete"
    }


def route_after_profile(state: FinancialPlanningState) -> str:
    """画像后的路由逻辑"""
    if state.get("needs_followup"):
        return "coaching"
    return "market"


def route_after_strategy(state: FinancialPlanningState) -> str:
    """策略后的路由逻辑"""
    return "coaching"


def create_graph() -> StateGraph:
    """创建LangGraph状态图"""
    workflow = StateGraph(FinancialPlanningState)

    workflow.add_node("profile", call_profile_agent)
    workflow.add_node("market", call_market_agent)
    workflow.add_node("strategy", call_strategy_agent)
    workflow.add_node("coaching", call_coaching_agent)

    workflow.set_entry_point("profile")

    workflow.add_conditional_edges(
        "profile",
        route_after_profile,
        {
            "coaching": "coaching",
            "market": "market"
        }
    )

    workflow.add_edge("market", "strategy")

    workflow.add_conditional_edges(
        "strategy",
        route_after_strategy,
        {
            "coaching": "coaching"
        }
    )

    workflow.add_edge("coaching", END)

    return workflow.compile()


graph = create_graph()
