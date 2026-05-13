from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID
from agents.strategy.agent import StrategyGenerationAgent

app = FastAPI(title="Strategy Generation Agent")
agent = StrategyGenerationAgent()


class StrategyRequest(BaseModel):
    user_id: UUID
    profile: Dict[str, Any]
    market_analysis: Dict[str, Any]


class StrategyResponse(BaseModel):
    four_buckets: Dict[str, Any]
    rebalance_triggers: Dict[str, Any]
    stress_test: Dict[str, Any]


@app.post("/generate", response_model=StrategyResponse)
async def generate_strategy(request: StrategyRequest):
    try:
        result = await agent.generate(request.profile, request.market_analysis)
        return StrategyResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "strategy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
