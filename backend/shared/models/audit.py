import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from shared.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(50))
    detail = Column(JSONB)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    record_type = Column(String(50))
    content = Column(JSONB, nullable=False)
    signed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class LangGraphCheckpoint(Base):
    __tablename__ = "langgraph_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(String(100), nullable=False, index=True)
    checkpoint = Column(JSONB, nullable=False)
    checkpoint_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
