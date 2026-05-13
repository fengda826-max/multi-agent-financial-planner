import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
from orchestrator.graph import graph
from orchestrator.state import FinancialPlanningState

app = FastAPI(title="Orchestrator")

user_states: Dict[str, FinancialPlanningState] = {}


class StartRequest(BaseModel):
    user_id: UUID
    risk_assessment: Dict[str, Any]


class ReplanRequest(BaseModel):
    user_id: UUID
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
    """触发重规划"""
    user_id = str(request.user_id)

    if user_id not in user_states:
        raise HTTPException(status_code=404, detail="User planning session not found")

    current_state = user_states[user_id]
    current_state["replan_trigger"] = request.trigger
    current_state["current_step"] = request.replan_from

    try:
        result = await graph.ainvoke(current_state)
        user_states[user_id] = result

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
    """查询当前流程状态"""
    if user_id not in user_states:
        raise HTTPException(status_code=404, detail="User planning session not found")

    state = user_states[user_id]
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
