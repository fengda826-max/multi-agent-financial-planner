import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from shared.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), nullable=True)
    four_buckets = Column(JSONB, nullable=False)
    total_assets = Column(Numeric(15, 2))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    market_analysis_id = Column(UUID(as_uuid=True), nullable=True)
    rebalance_triggers = Column(JSONB)
    stress_test_results = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketAnalysis(Base):
    __tablename__ = "market_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_type = Column(String(50))
    market_overview = Column(JSONB)
    correlation_matrix = Column(JSONB)
    risk_factors = Column(JSONB)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
