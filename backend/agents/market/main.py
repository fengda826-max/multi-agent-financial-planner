from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from uuid import UUID
from agents.market.agent import MarketAnalysisAgent

app = FastAPI(title="Market Analysis Agent")
agent = MarketAnalysisAgent()


class MarketAnalysisRequest(BaseModel):
    analysis_type: str = "full"
    focus_areas: List[str] = ["equity", "bond", "commodity"]
    time_horizon: str = "1y"


class MarketAnalysisResponse(BaseModel):
    market_overview: Dict[str, Any]
    risk_factors: List[str]
    overall_recommendation: str


@app.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(request: MarketAnalysisRequest):
    try:
        mock_data = {
            "沪深300": {"latest_price": 3800, "pe_ratio": 12.5, "pb_ratio": 1.3},
            "创业板指": {"latest_price": 2200, "pe_ratio": 35.2, "pb_ratio": 3.8},
            "10年国债": {"yield": 2.65},
            "CPI": {"latest": 0.7}
        }

        result = await agent.analyze(mock_data)
        return MarketAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "market"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
