import asyncio
from shared.database import engine, Base
from shared.models import User, UserProfile, RiskAssessment, Portfolio, Strategy, MarketAnalysis, AuditLog, ComplianceRecord, LangGraphCheckpoint


async def init_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully")


if __name__ == "__main__":
    asyncio.run(init_database())
