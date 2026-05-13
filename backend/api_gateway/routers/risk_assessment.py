from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from shared.database import get_db
from shared.models.profile import RiskAssessment, UserProfile
from shared.schemas.profile import RiskAssessmentInput, RiskAssessmentResponse
from api_gateway.middleware.auth import get_current_user

router = APIRouter()


def calculate_risk_level(assessment: RiskAssessmentInput) -> tuple[int, str]:
    """计算风险等级"""
    score = 0

    if assessment.age < 30:
        score += 30
    elif assessment.age < 40:
        score += 25
    elif assessment.age < 50:
        score += 20
    else:
        score += 10

    if assessment.income > 30000:
        score += 25
    elif assessment.income > 15000:
        score += 20
    elif assessment.income > 8000:
        score += 15
    else:
        score += 10

    risk_scores = {"conservative": 10, "moderate": 20, "aggressive": 30}
    score += risk_scores.get(assessment.risk_tolerance, 15)

    horizon_scores = {"1y": 5, "3y": 15, "5y": 25, "10y+": 30}
    score += horizon_scores.get(assessment.investment_horizon, 10)

    if score < 50:
        risk_level = "conservative"
    elif score < 75:
        risk_level = "moderate"
    else:
        risk_level = "aggressive"

    return score, risk_level


@router.post("/", response_model=RiskAssessmentResponse)
async def create_risk_assessment(
    assessment_data: RiskAssessmentInput,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = UUID(current_user["user_id"])

    score, risk_level = calculate_risk_level(assessment_data)

    assessment = RiskAssessment(
        user_id=user_id,
        answers=assessment_data.model_dump(),
        score=score,
        risk_level=risk_level
    )
    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(
            user_id=user_id,
            risk_capacity="medium" if risk_level == "moderate" else ("low" if risk_level == "conservative" else "high"),
            investable_assets=assessment_data.income * 12 * 0.3,
            monthly_surplus=assessment_data.income - assessment_data.expenses
        )
        db.add(profile)
    else:
        profile.risk_capacity = "medium" if risk_level == "moderate" else ("low" if risk_level == "conservative" else "high")
        profile.monthly_surplus = assessment_data.income - assessment_data.expenses

    return assessment
