from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class RiskAssessmentInput(BaseModel):
    age: int
    income: float
    expenses: float
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
    lifecycle_stage: str
    risk_capacity: str
    investable_assets: float
    monthly_surplus: float
    kyc_level: str

    class Config:
        from_attributes = True


class ProfileAnalysisRequest(BaseModel):
    user_id: UUID
    risk_assessment: RiskAssessmentInput


class ProfileAnalysisResponse(BaseModel):
    profile: UserProfileResponse
    needs_followup: bool
    followup_questions: List[str]
