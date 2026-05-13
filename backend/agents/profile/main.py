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
        return ProfileAnalysisResponse(
            profile={
                "lifecycle_stage": result.get("lifecycle_stage"),
                "risk_capacity": result.get("risk_capacity"),
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
