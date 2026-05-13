from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class RiskAssessmentInput(BaseModel):
    age: int = Field(..., ge=0, le=150)
    income: float = Field(..., ge=0)
    expenses: float = Field(..., ge=0)
    risk_tolerance: str
    investment_horizon: str


class RiskAssessmentResponse(BaseModel):
    id: UUID
    score: int
    risk_level: str
    assessed_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: UUID
    lifecycle_stage: Optional[str] = None
    risk_capacity: Optional[str] = None
    investable_assets: Optional[float] = None
    monthly_surplus: Optional[float] = None
    kyc_level: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileAnalysisRequest(BaseModel):
    user_id: UUID
    risk_assessment: RiskAssessmentInput


class ProfileAnalysisResponse(BaseModel):
    profile: UserProfileResponse
    needs_followup: bool
    followup_questions: List[str]
