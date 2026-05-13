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
