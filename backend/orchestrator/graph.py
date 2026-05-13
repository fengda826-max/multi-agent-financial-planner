from langgraph.graph import StateGraph, END
from typing import Dict, Any
import httpx
from orchestrator.state import FinancialPlanningState

AGENT_URLS = {
    "profile": "http://agent-profile:8001",
    "market": "http://agent-market:8002",
    "strategy": "http://agent-strategy:8003",
    "coaching": "http://agent-coaching:8004",
}


async def call_profile_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用用户画像Agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['profile']}/analyze",
            json={
                "user_id": state["user_id"],
                "risk_assessment": state["risk_assessment"]
            },
            timeout=30.0
        )
        result = response.json()

    return {
        "user_profile": result.get("profile", {}),
        "needs_followup": result.get("needs_followup", False),
        "current_step": "profile_complete"
    }


async def call_market_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用市场研判Agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['market']}/analyze",
            json={
                "analysis_type": "full",
                "focus_areas": ["equity", "bond", "commodity"],
                "time_horizon": "1y"
            },
            timeout=30.0
        )
        result = response.json()

    return {
        "market_analysis": result,
        "current_step": "market_complete"
    }


async def call_strategy_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用策略生成Agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['strategy']}/generate",
            json={
                "user_id": state["user_id"],
                "profile": state["user_profile"],
                "market_analysis": state["market_analysis"]
            },
            timeout=30.0
        )
        result = response.json()

    return {
        "strategy": result,
        "current_step": "strategy_complete"
    }


async def call_coaching_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用陪伴督导Agent"""
    context = f"用户画像: {state['user_profile']}\n配置方案: {state['strategy']}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['coaching']}/interact",
            json={
                "user_id": state["user_id"],
                "context": context,
                "strategy": state["strategy"]
            },
            timeout=30.0
        )
        result = response.json()

    coaching_entry = {
        "type": "strategy_explanation",
        "message": result.get("message", ""),
        "action": result.get("action", "none")
    }

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
