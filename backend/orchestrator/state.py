from typing import TypedDict, Annotated, Dict, Any, List, Optional
from uuid import UUID
import operator


class FinancialPlanningState(TypedDict):
    """理财规划状态图状态定义"""
    user_id: str
    risk_assessment: Dict[str, Any]
    user_profile: Dict[str, Any]
    market_analysis: Dict[str, Any]
    strategy: Dict[str, Any]
    coaching_history: Annotated[List[Dict[str, Any]], operator.add]
    current_step: str
    needs_followup: bool
    replan_trigger: Optional[str]
    error: Optional[str]


# 全局内存状态存储，供 graph 节点和 main 端点共享
user_states: Dict[str, FinancialPlanningState] = {}

# 独立的 agent_steps 存储，避免被 LangGraph 状态覆盖
agent_steps_store: Dict[str, Dict[str, list]] = {}
