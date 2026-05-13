import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from shared.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lifecycle_stage = Column(String(50))
    risk_capacity = Column(String(20))
    investable_assets = Column(Numeric(15, 2))
    monthly_surplus = Column(Numeric(15, 2))
    kyc_level = Column(String(20))
    kyc_verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    answers = Column(JSONB, nullable=False)
    score = Column(Integer)
    risk_level = Column(String(20))
    assessed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
