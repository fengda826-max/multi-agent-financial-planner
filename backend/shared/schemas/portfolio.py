from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Dict, List, Optional


class BucketConfig(BaseModel):
    allocation: float
    products: List[str]
    reason: str


class FourBuckets(BaseModel):
    living_money: BucketConfig
    stable_money: BucketConfig
    growth_money: BucketConfig
    protection_money: BucketConfig


class RebalanceTriggers(BaseModel):
    drift_threshold: float
    review_frequency: str


class StressTestResult(BaseModel):
    scenario: str
    loss: float
    recovery_time: str


class StrategyGenerateRequest(BaseModel):
    user_id: UUID
    profile: dict
    market_analysis: dict


class StrategyGenerateResponse(BaseModel):
    four_buckets: FourBuckets
    rebalance_triggers: RebalanceTriggers
    stress_test: Dict[str, StressTestResult]
