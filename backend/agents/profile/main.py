from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from uuid import UUID
from agents.profile.agent import UserProfileAgent

app = FastAPI(title="User Profile Agent")
agent = UserProfileAgent()


class ProfileAnalysisRequest(BaseModel):
    user_id: UUID
    risk_assessment: Dict[str, Any]


class ProfileAnalysisResponse(BaseModel):
    profile: Dict[str, Any]
    needs_followup: bool
    followup_questions: List[str]


@app.post("/analyze", response_model=ProfileAnalysisResponse)
async def analyze_profile(request: ProfileAnalysisRequest):
    try:
        result = await agent.analyze(request.risk_assessment)
        # 透传 LLM 返回的所有画像字段
        return ProfileAnalysisResponse(
            profile={
                "lifecycle_stage": result.get("lifecycle_stage"),
                "lifecycle_explanation": result.get("lifecycle_explanation", ""),
                "risk_capacity": result.get("risk_capacity"),
                "risk_explanation": result.get("risk_explanation", ""),
                "investment_style": result.get("investment_style", ""),
                "financial_health_score": result.get("financial_health_score", 75),
                "financial_health_comment": result.get("financial_health_comment", ""),
                "health_score_breakdown": result.get("health_score_breakdown", {}),
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", []),
                "profile_summary": result.get("profile_summary", ""),
                "investable_assets": request.risk_assessment.get("investable_assets"),
                "monthly_surplus": request.risk_assessment.get("income", 0) - request.risk_assessment.get("expenses", 0),
                "savings_rate": result.get("savings_rate", 0),
                "emergency_months": result.get("emergency_months", 0),
                "debt_to_income": result.get("debt_to_income", 0),
                "computation_steps": result.get("computation_steps", []),
            },
            needs_followup=result.get("needs_followup", False),
            followup_questions=result.get("followup_questions", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "profile"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
