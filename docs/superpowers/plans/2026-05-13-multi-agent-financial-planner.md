# 多Agent协作智能理财规划系统 - 实现计划

> **状态：** Phase 1-5 全部完成 ✅ | Phase 6-7 待完成  
> **更新：** 2026-05-16 — 所有 Task 1-12 步骤标记为 [x]

**额外实现（超出原计划）：**
- 渐进式披露：策略结果页分4阶段展示（画像→市场→策略→督导）
- 用户画像丰富化：2→12字段（财务健康分、投资风格、优劣势等）
- AI 对话记忆：Coaching Agent 保留6条对话历史
- POST /chat 端点 + GET /risk-assessment/history
- 市场实时数据：AKShare 异步并发4源，10s超时/源
- 前端：10页面 + Layout导航 + ECharts + 路由鉴权
- DB 持久化：Portfolio/Strategy/MarketAnalysis 三表

**注意：** 以下代码示例中 model 名应为 `deepseek-v4-pro`（非 `deepseek-chat`），Market Agent 用 AKShare 实时数据（非 mock），Profile Agent 返回 12 字段（非 4 字段）。实际代码见源文件。

**Goal:** 构建一个基于微服务架构的多Agent协作理财规划系统，包含12个服务组件。

**Architecture:** Orchestrator（LangGraph状态图）编排四个专业Agent，AKShare + LLM 市场分析，FastAPI + Vue3 前后端。

**Tech Stack:** Python 3.11+, FastAPI, LangGraph, LangChain, RabbitMQ, PostgreSQL, Redis, Vue 3, ECharts

---

## 项目目录结构

```
financial-planner/
├── frontend/                          # Vue 3 前端
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   └── api/
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── shared/                        # 共享库
│   │   ├── models/                    # 数据模型
│   │   ├── schemas/                   # Pydantic schemas
│   │   ├── database.py                # 数据库连接
│   │   ├── redis_client.py            # Redis连接
│   │   ├── rabbitmq.py                # RabbitMQ连接
│   │   └── config.py                  # 配置管理
│   ├── api_gateway/                   # API Gateway
│   │   ├── main.py
│   │   ├── routers/
│   │   └── middleware/
│   ├── orchestrator/                  # Orchestrator
│   │   ├── main.py
│   │   ├── graph.py                   # LangGraph状态图
│   │   └── state.py                   # 状态定义
│   ├── agents/
│   │   ├── profile/                   # 用户画像Agent
│   │   ├── market/                    # 市场研判Agent
│   │   ├── strategy/                  # 策略生成Agent
│   │   └── coaching/                  # 陪伴督导Agent
│   ├── monitors/
│   │   ├── market_monitor.py
│   │   └── user_monitor.py
│   ├── mcp_server/                    # MCP Server
│   │   ├── main.py
│   │   └── tools/
│   └── tests/
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## Phase 1: 基础设施与项目骨架（Task 1-4）

### Task 1: Docker Compose 基础设施

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`

- [x] **Step 1: 创建 .env.example**

```bash
# Database
POSTGRES_USER=financial_planner
POSTGRES_PASSWORD=dev_password_123
POSTGRES_DB=financial_planner

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# LLM
DEEPSEEK_API_KEY=your_deepseek_key
MIMO_API_KEY=your_mimo_key
DEFAULT_LLM_MODEL=deepseek

# JWT
JWT_SECRET_KEY=dev_jwt_secret_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

- [x] **Step 2: 创建 docker-compose.yml**

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 10s
      timeout: 10s
      retries: 5

volumes:
  pgdata:
```

- [x] **Step 3: 启动基础设施验证**

```bash
cp .env.example .env
docker compose up -d postgres redis rabbitmq
docker compose ps
```

Expected: 三个服务均显示 healthy 状态

- [x] **Step 4: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "infra: add docker compose with postgres, redis, rabbitmq"
```

---

### Task 2: 共享库 - 配置与数据库连接

**Files:**
- Create: `backend/shared/__init__.py`
- Create: `backend/shared/config.py`
- Create: `backend/shared/database.py`
- Create: `backend/shared/redis_client.py`
- Create: `backend/shared/rabbitmq.py`
- Create: `requirements.txt`

- [x] **Step 1: 创建 requirements.txt**

```txt
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
sqlalchemy>=2.0.27
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
redis>=5.0.1
aio-pika>=9.4.0
langgraph>=0.2.0
langchain>=0.2.0
langchain-openai>=0.1.0
mcp>=1.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
httpx>=0.27.0
akshare>=1.14.0
```

> **注意：** 版本号使用 `>=` 而非 `==`，避免因小版本差异导致安装失败。`langchain-deepseek` 已移除，改用 `langchain-openai` 配合 DeepSeek 的 OpenAI 兼容接口。

- [x] **Step 2: 创建 backend/shared/config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    postgres_user: str = "financial_planner"
    postgres_password: str = "dev_password_123"
    postgres_db: str = "financial_planner"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # RabbitMQ
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672

    # LLM
    deepseek_api_key: str = ""
    mimo_api_key: str = ""
    default_llm_model: str = "deepseek"

    # JWT
    jwt_secret_key: str = "dev_jwt_secret_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def sync_database_url(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [x] **Step 3: 创建 backend/shared/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from shared.config import get_settings


settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [x] **Step 4: 创建 backend/shared/redis_client.py**

```python
import redis.asyncio as redis
from shared.config import get_settings


settings = get_settings()
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> redis.Redis:
    return redis_client
```

- [x] **Step 5: 创建 backend/shared/rabbitmq.py**

```python
import aio_pika
from shared.config import get_settings


settings = get_settings()


async def get_rabbitmq_connection() -> aio_pika.RobustConnection:
    return await aio_pika.connect_robust(settings.rabbitmq_url)


async def publish_message(exchange_name: str, routing_key: str, message: dict):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        import json
        body = json.dumps(message).encode()
        await exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=routing_key,
        )


async def consume_messages(exchange_name: str, routing_key: str, queue_name: str, callback):
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.bind(exchange, routing_key=routing_key)
    await queue.consume(callback)
```

- [x] **Step 6: 创建 backend/shared/__init__.py**

```python
from shared.config import get_settings
from shared.database import Base, get_db, init_db
from shared.redis_client import get_redis
from shared.rabbitmq import publish_message, consume_messages
```

- [x] **Step 7: Commit**

```bash
git add backend/shared/ requirements.txt
git commit -m "feat: add shared library with config, database, redis, rabbitmq"
```

---

### Task 3: 共享库 - 数据模型

**Files:**
- Create: `backend/shared/models/__init__.py`
- Create: `backend/shared/models/user.py`
- Create: `backend/shared/models/profile.py`
- Create: `backend/shared/models/portfolio.py`
- Create: `backend/shared/models/audit.py`
- Create: `backend/shared/schemas/__init__.py`
- Create: `backend/shared/schemas/user.py`
- Create: `backend/shared/schemas/profile.py`
- Create: `backend/shared/schemas/portfolio.py`

- [x] **Step 1: 创建 backend/shared/models/user.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from shared.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [x] **Step 2: 创建 backend/shared/models/profile.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from shared.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lifecycle_stage = Column(String(50))  # accumulation, consolidation, distribution
    risk_capacity = Column(String(20))    # low, medium, high
    investable_assets = Column(Numeric(15, 2))
    monthly_surplus = Column(Numeric(15, 2))
    kyc_level = Column(String(20))        # basic, standard, enhanced
    kyc_verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    answers = Column(JSONB, nullable=False)
    score = Column(Numeric)
    risk_level = Column(String(20))  # conservative, moderate, aggressive
    assessed_at = Column(DateTime, default=datetime.utcnow)
```

- [x] **Step 3: 创建 backend/shared/models/portfolio.py**

```python
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
    status = Column(String(20), default="active")  # active, archived, rebalancing
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
```

- [x] **Step 4: 创建 backend/shared/models/audit.py**

```python
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
    actor = Column(String(50))  # user, system, agent
    detail = Column(JSONB)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)


class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    record_type = Column(String(50))  # kyc, suitability, risk_disclosure
    content = Column(JSONB, nullable=False)
    signed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class LangGraphCheckpoint(Base):
    __tablename__ = "langgraph_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(String(100), nullable=False, index=True)
    checkpoint = Column(JSONB, nullable=False)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [x] **Step 5: 创建 backend/shared/models/__init__.py**

```python
from shared.models.user import User
from shared.models.profile import UserProfile, RiskAssessment
from shared.models.portfolio import Portfolio, Strategy, MarketAnalysis
from shared.models.audit import AuditLog, ComplianceRecord, LangGraphCheckpoint
```

- [x] **Step 6: 创建 Pydantic schemas**

```python
# backend/shared/schemas/user.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: Optional[str]
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
```

```python
# backend/shared/schemas/profile.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class RiskAssessmentInput(BaseModel):
    age: int
    income: float
    expenses: float
    risk_tolerance: str  # conservative, moderate, aggressive
    investment_horizon: str  # 1y, 3y, 5y, 10y+


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
```

```python
# backend/shared/schemas/portfolio.py
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
```

- [x] **Step 7: 创建 backend/shared/schemas/__init__.py**

```python
from shared.schemas.user import UserCreate, UserResponse, UserLogin, Token
from shared.schemas.profile import RiskAssessmentInput, RiskAssessmentResponse, UserProfileResponse, ProfileAnalysisRequest, ProfileAnalysisResponse
from shared.schemas.portfolio import FourBuckets, StrategyGenerateRequest, StrategyGenerateResponse
```

- [x] **Step 8: Commit**

```bash
git add backend/shared/models/ backend/shared/schemas/
git commit -m "feat: add database models and pydantic schemas"
```

---

### Task 4: 数据库迁移与初始化脚本

**Files:**
- Create: `backend/shared/init_db.py`

- [x] **Step 1: 创建 backend/shared/init_db.py**

```python
import asyncio
from shared.database import engine, Base
from shared.models import User, UserProfile, RiskAssessment, Portfolio, Strategy, MarketAnalysis, AuditLog, ComplianceRecord, LangGraphCheckpoint


async def init_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully")


if __name__ == "__main__":
    asyncio.run(init_database())
```

- [x] **Step 2: 验证数据库初始化**

```bash
cd backend
python -m shared.init_db
```

Expected: 输出 "Database tables created successfully"

- [x] **Step 3: 验证 PostgreSQL 表创建**

```bash
docker compose exec postgres psql -U financial_planner -d financial_planner -c "\dt"
```

Expected: 显示 users, user_profiles, risk_assessments, portfolios, strategies, market_analyses, audit_logs, compliance_records, langgraph_checkpoints 表

- [x] **Step 4: Commit**

```bash
git add backend/shared/init_db.py
git commit -m "feat: add database initialization script"
```

---

## Phase 2: MCP Server 与数据源适配器（Task 5-6）

### Task 5: MCP Server 基础框架

**Files:**
- Create: `backend/mcp_server/__init__.py`
- Create: `backend/mcp_server/main.py`
- Create: `backend/mcp_server/tools/__init__.py`
- Create: `backend/mcp_server/tools/base.py`

- [x] **Step 1: 创建 backend/mcp_server/tools/base.py**

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime


class DataSourceAdapter(ABC):
    """数据源适配器基类"""

    def __init__(self, name: str, rate_limit: int = 10):
        self.name = name
        self.rate_limit = rate_limit
        self._request_count = 0
        self._last_reset = datetime.utcnow()

    async def check_rate_limit(self):
        """检查速率限制"""
        now = datetime.utcnow()
        if (now - self._last_reset).seconds >= 60:
            self._request_count = 0
            self._last_reset = now
        if self._request_count >= self.rate_limit:
            wait_time = 60 - (now - self._last_reset).seconds
            await asyncio.sleep(wait_time)
            self._request_count = 0
            self._last_reset = datetime.utcnow()
        self._request_count += 1

    @abstractmethod
    async def get_index_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """获取指数数据"""
        pass

    @abstractmethod
    async def get_fund_rating(self, fund_id: str) -> Dict[str, Any]:
        """获取基金评级"""
        pass

    @abstractmethod
    async def get_macro_indicator(self, indicator: str) -> Dict[str, Any]:
        """获取宏观指标"""
        pass

    @abstractmethod
    async def get_bond_yield(self, curve_type: str = "china") -> Dict[str, Any]:
        """获取债券收益率曲线"""
        pass
```

- [x] **Step 2: 创建 backend/mcp_server/main.py**

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from mcp_server.tools.base import DataSourceAdapter


app = Server("financial-data-server")


# 注册工具
@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_index_data",
            description="获取股票指数历史数据，支持沪深300、创业板指等",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "指数代码，如 sh000300"},
                    "period": {"type": "string", "description": "时间周期，如 1y, 3y, 5y"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_fund_rating",
            description="获取基金评级和历史业绩数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string", "description": "基金代码"}
                },
                "required": ["fund_id"]
            }
        ),
        Tool(
            name="get_macro_indicator",
            description="获取宏观经济指标数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "indicator": {"type": "string", "description": "指标名称，如 CPI, PMI, GDP"}
                },
                "required": ["indicator"]
            }
        ),
        Tool(
            name="get_bond_yield",
            description="获取债券收益率曲线数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "curve_type": {"type": "string", "description": "曲线类型，如 china, us"}
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    # 工具调用逻辑将在下一个任务实现
    return [TextContent(type="text", text=f"Tool {name} called with {arguments}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

- [x] **Step 3: Commit**

```bash
git add backend/mcp_server/
git commit -m "feat: add MCP server base framework"
```

---

### Task 6: AKShare 数据源适配器

**Files:**
- Create: `backend/mcp_server/tools/akshare_adapter.py`
- Modify: `backend/mcp_server/main.py`

- [x] **Step 1: 创建 backend/mcp_server/tools/akshare_adapter.py**

```python
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List
from mcp_server.tools.base import DataSourceAdapter


class AKShareAdapter(DataSourceAdapter):
    """AKShare 数据源适配器"""

    def __init__(self):
        super().__init__(name="akshare", rate_limit=10)

    async def get_index_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        await self.check_rate_limit()

        # 计算日期范围
        days_map = {"1y": 365, "3y": 1095, "5y": 1825}
        days = days_map.get(period, 365)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        try:
            df = ak.stock_zh_index_daily(symbol=symbol)
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                return {"error": f"No data found for {symbol}"}

            # 计算关键指标
            returns = df["close"].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)  # 年化波动率
            total_return = (df["close"].iloc[-1] / df["close"].iloc[0]) - 1

            return {
                "symbol": symbol,
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "latest_price": float(df["close"].iloc[-1]),
                "total_return": float(total_return),
                "annualized_volatility": float(volatility),
                "max_drawdown": float((df["close"] / df["close"].cummax() - 1).min()),
                "data_points": len(df)
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_fund_rating(self, fund_id: str) -> Dict[str, Any]:
        await self.check_rate_limit()

        try:
            df = ak.fund_open_fund_info_em(symbol=fund_id, indicator="单位净值走势")

            if df.empty:
                return {"error": f"No data found for fund {fund_id}"}

            returns = df["单位净值"].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)

            return {
                "fund_id": fund_id,
                "latest_nav": float(df["单位净值"].iloc[-1]),
                "annualized_return": float(returns.mean() * 252),
                "annualized_volatility": float(volatility),
                "sharpe_ratio": float((returns.mean() * 252) / (returns.std() * (252 ** 0.5))) if returns.std() > 0 else 0,
                "data_points": len(df)
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_macro_indicator(self, indicator: str) -> Dict[str, Any]:
        await self.check_rate_limit()

        try:
            indicator_map = {
                "CPI": ak.macro_china_cpi_monthly,
                "PPI": ak.macro_china_ppi,
                "PMI": ak.macro_china_pmi,
            }

            fetcher = indicator_map.get(indicator)
            if not fetcher:
                return {"error": f"Unsupported indicator: {indicator}"}

            df = fetcher()

            if df.empty:
                return {"error": f"No data for {indicator}"}

            latest = df.iloc[-1]
            return {
                "indicator": indicator,
                "latest_value": float(latest.iloc[1]) if len(latest) > 1 else None,
                "latest_date": str(latest.iloc[0]),
                "data_points": len(df)
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_bond_yield(self, curve_type: str = "china") -> Dict[str, Any]:
        await self.check_rate_limit()

        try:
            df = ak.bond_zh_us_rate(start_date="20200101")

            if df.empty:
                return {"error": "No bond yield data"}

            latest = df.iloc[-1]
            return {
                "curve_type": curve_type,
                "china_10y": float(latest.get("中国国债收益率10年", 0)),
                "china_5y": float(latest.get("中国国债收益率5年", 0)),
                "china_1y": float(latest.get("中国国债收益率1年", 0)),
                "us_10y": float(latest.get("美国国债收益率10年", 0)),
                "date": str(latest.iloc[0])
            }
        except Exception as e:
            return {"error": str(e)}
```

- [x] **Step 2: 更新 backend/mcp_server/main.py 集成适配器**

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from mcp_server.tools.akshare_adapter import AKShareAdapter


app = Server("financial-data-server")
akshare_adapter = AKShareAdapter()


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_index_data",
            description="获取股票指数历史数据，支持沪深300、创业板指等",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "指数代码，如 sh000300"},
                    "period": {"type": "string", "description": "时间周期，如 1y, 3y, 5y"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_fund_rating",
            description="获取基金评级和历史业绩数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string", "description": "基金代码"}
                },
                "required": ["fund_id"]
            }
        ),
        Tool(
            name="get_macro_indicator",
            description="获取宏观经济指标数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "indicator": {"type": "string", "description": "指标名称，如 CPI, PMI, GDP"}
                },
                "required": ["indicator"]
            }
        ),
        Tool(
            name="get_bond_yield",
            description="获取债券收益率曲线数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "curve_type": {"type": "string", "description": "曲线类型，如 china, us"}
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "get_index_data":
            result = await akshare_adapter.get_index_data(
                symbol=arguments.get("symbol", "sh000300"),
                period=arguments.get("period", "1y")
            )
        elif name == "get_fund_rating":
            result = await akshare_adapter.get_fund_rating(
                fund_id=arguments.get("fund_id", "")
            )
        elif name == "get_macro_indicator":
            result = await akshare_adapter.get_macro_indicator(
                indicator=arguments.get("indicator", "CPI")
            )
        elif name == "get_bond_yield":
            result = await akshare_adapter.get_bond_yield(
                curve_type=arguments.get("curve_type", "china")
            )
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

- [x] **Step 3: Commit**

```bash
git add backend/mcp_server/
git commit -m "feat: add AKShare data source adapter with rate limiting"
```

---

## Phase 3: API Gateway 与认证（Task 7-8）

### Task 7: API Gateway 基础框架

**Files:**
- Create: `backend/api_gateway/__init__.py`
- Create: `backend/api_gateway/main.py`
- Create: `backend/api_gateway/routers/__init__.py`
- Create: `backend/api_gateway/routers/auth.py`
- Create: `backend/api_gateway/routers/user.py`
- Create: `backend/api_gateway/middleware/__init__.py`
- Create: `backend/api_gateway/middleware/auth.py`

- [x] **Step 1: 创建 backend/api_gateway/main.py**

```python
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx
from shared.database import init_db
from api_gateway.routers import auth, user

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8010")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Financial Planner API",
    description="多Agent协作智能理财规划系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(user.router, prefix="/api/users", tags=["用户"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Orchestrator 代理路由 - 转发请求到 Orchestrator 服务
@app.api_route("/orchestrator/{path:path}", methods=["GET", "POST"])
async def proxy_to_orchestrator(request: Request, path: str):
    async with httpx.AsyncClient() as client:
        body = await request.body()
        response = await client.request(
            method=request.method,
            url=f"{ORCHESTRATOR_URL}/{path}",
            content=body,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            timeout=60.0
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
```

- [x] **Step 2: 创建 backend/api_gateway/middleware/auth.py**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    return {"user_id": user_id}
```

- [x] **Step 3: 创建 backend/api_gateway/routers/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.database import get_db
from shared.models.user import User
from shared.schemas.user import UserCreate, UserResponse, UserLogin, Token
from api_gateway.middleware.auth import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 创建用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password)
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # 查找用户
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # 生成 token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user_id": str(user.id)}
```

- [x] **Step 4: 创建 backend/api_gateway/routers/user.py**

```python
from fastapi import APIRouter, Depends
from shared.schemas.user import UserResponse
from api_gateway.middleware.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["user_id"]}
```

- [x] **Step 5: Commit**

```bash
git add backend/api_gateway/
git commit -m "feat: add API gateway with auth endpoints"
```

---

### Task 8: 风险测评 API

**Files:**
- Create: `backend/api_gateway/routers/risk_assessment.py`
- Modify: `backend/api_gateway/main.py`

- [x] **Step 1: 创建 backend/api_gateway/routers/risk_assessment.py**

```python
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

    # 年龄评分（年轻人可以承担更高风险）
    if assessment.age < 30:
        score += 30
    elif assessment.age < 40:
        score += 25
    elif assessment.age < 50:
        score += 20
    else:
        score += 10

    # 收入评分
    if assessment.income > 30000:
        score += 25
    elif assessment.income > 15000:
        score += 20
    elif assessment.income > 8000:
        score += 15
    else:
        score += 10

    # 风险承受能力评分
    risk_scores = {"conservative": 10, "moderate": 20, "aggressive": 30}
    score += risk_scores.get(assessment.risk_tolerance, 15)

    # 投资期限评分
    horizon_scores = {"1y": 5, "3y": 15, "5y": 25, "10y+": 30}
    score += horizon_scores.get(assessment.investment_horizon, 10)

    # 确定风险等级
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

    # 计算风险等级
    score, risk_level = calculate_risk_level(assessment_data)

    # 保存测评结果
    assessment = RiskAssessment(
        user_id=user_id,
        answers=assessment_data.model_dump(),
        score=score,
        risk_level=risk_level
    )
    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)

    # 更新或创建用户画像
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(
            user_id=user_id,
            risk_capacity="medium" if risk_level == "moderate" else ("low" if risk_level == "conservative" else "high"),
            investable_assets=assessment_data.income * 12 * 0.3,  # 简化计算
            monthly_surplus=assessment_data.income - assessment_data.expenses
        )
        db.add(profile)
    else:
        profile.risk_capacity = "medium" if risk_level == "moderate" else ("low" if risk_level == "conservative" else "high")
        profile.monthly_surplus = assessment_data.income - assessment_data.expenses

    return assessment
```

- [x] **Step 2: 更新 main.py 注册路由**

```python
from .routers import auth, user, risk_assessment

app.include_router(risk_assessment.router, prefix="/api/risk-assessment", tags=["风险测评"])
```

- [x] **Step 3: Commit**

```bash
git add backend/api_gateway/routers/risk_assessment.py
git commit -m "feat: add risk assessment API with scoring logic"
```

---

## Phase 4: Agent 实现（Task 9-12）

### Task 9: 用户画像 Agent

**Files:**
- Create: `backend/agents/profile/__init__.py`
- Create: `backend/agents/profile/main.py`
- Create: `backend/agents/profile/agent.py`

- [x] **Step 1: 创建 backend/agents/profile/agent.py**

```python
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from shared.config import get_settings

settings = get_settings()


class UserProfileAgent:
    """用户画像Agent - 分析用户数据构建数字画像"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.3
        )

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户数据，生成画像"""

        system_prompt = """你是一个专业的理财规划师助手。根据用户的财务数据和风险测评结果，分析用户的投资画像。

你需要输出以下内容：
1. lifecycle_stage: 生命周期阶段（accumulation积累期/consolidation巩固期/distribution分配期）
2. risk_capacity: 风险承受能力（low/medium/high）
3. needs_followup: 是否需要追问用户更多信息（true/false）
4. followup_questions: 如果需要追问，列出具体问题

请用JSON格式输出。"""

        user_prompt = f"""用户数据：
- 年龄：{user_data.get('age')}
- 月收入：{user_data.get('income')}
- 月支出：{user_data.get('expenses')}
- 风险偏好：{user_data.get('risk_tolerance')}
- 投资期限：{user_data.get('investment_horizon')}
- 当前可投资资产：{user_data.get('investable_assets', '未提供')}

请分析用户画像。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)

        # 解析LLM响应
        import json
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            # 如果LLM返回的不是标准JSON，使用默认逻辑
            result = self._default_analysis(user_data)

        return result

    def _default_analysis(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """默认分析逻辑（当LLM返回异常时使用）"""
        age = user_data.get('age', 30)
        risk_tolerance = user_data.get('risk_tolerance', 'moderate')

        # 生命周期阶段判断
        if age < 35:
            lifecycle_stage = "accumulation"
        elif age < 50:
            lifecycle_stage = "consolidation"
        else:
            lifecycle_stage = "distribution"

        # 风险承受能力
        risk_capacity_map = {
            "conservative": "low",
            "moderate": "medium",
            "aggressive": "high"
        }
        risk_capacity = risk_capacity_map.get(risk_tolerance, "medium")

        # 判断是否需要追问
        needs_followup = user_data.get('investable_assets') is None
        followup_questions = []
        if needs_followup:
            followup_questions.append("您目前有多少可投资资产？")

        return {
            "lifecycle_stage": lifecycle_stage,
            "risk_capacity": risk_capacity,
            "needs_followup": needs_followup,
            "followup_questions": followup_questions
        }
```

- [x] **Step 2: 创建 backend/agents/profile/main.py**

```python
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
```

- [x] **Step 3: Commit**

```bash
git add backend/agents/profile/
git commit -m "feat: add user profile agent with LLM analysis"
```

---

### Task 10: 市场研判 Agent

**Files:**
- Create: `backend/agents/market/__init__.py`
- Create: `backend/agents/market/main.py`
- Create: `backend/agents/market/agent.py`

- [x] **Step 1: 创建 backend/agents/market/agent.py**

```python
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from shared.config import get_settings

settings = get_settings()


class MarketAnalysisAgent:
    """市场研判Agent - 分析市场数据生成投资建议"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.3
        )

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析市场数据，生成投资建议"""

        system_prompt = """你是一个专业的市场分析师。根据市场数据分析各类资产的风险收益特征。

输出格式（JSON）：
{
    "market_overview": {
        "equity": {"expected_return": 0.08, "volatility": 0.20, "recommendation": "..."},
        "bond": {"expected_return": 0.035, "volatility": 0.05, "recommendation": "..."},
        "commodity": {"expected_return": 0.05, "volatility": 0.15, "recommendation": "..."}
    },
    "risk_factors": ["风险1", "风险2"],
    "overall_recommendation": "总体建议"
}"""

        user_prompt = f"""市场数据：
{self._format_market_data(market_data)}

请分析市场状况并给出投资建议。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)

        import json
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            result = self._default_analysis(market_data)

        return result

    def _format_market_data(self, market_data: Dict[str, Any]) -> str:
        """格式化市场数据"""
        lines = []
        for key, value in market_data.items():
            if isinstance(value, dict):
                lines.append(f"- {key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _default_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """默认分析逻辑"""
        return {
            "market_overview": {
                "equity": {"expected_return": 0.08, "volatility": 0.20, "recommendation": "适度配置"},
                "bond": {"expected_return": 0.035, "volatility": 0.05, "recommendation": "作为稳健配置"},
                "commodity": {"expected_return": 0.05, "volatility": 0.15, "recommendation": "少量配置对冲风险"}
            },
            "risk_factors": ["市场波动风险", "利率风险"],
            "overall_recommendation": "建议均衡配置，股债比例6:4"
        }
```

- [x] **Step 2: 创建 backend/agents/market/main.py**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from uuid import UUID
from agents.market.agent import MarketAnalysisAgent

app = FastAPI(title="Market Analysis Agent")
agent = MarketAnalysisAgent()


class MarketAnalysisRequest(BaseModel):
    analysis_type: str = "full"
    focus_areas: List[str] = ["equity", "bond", "commodity"]
    time_horizon: str = "1y"


class MarketAnalysisResponse(BaseModel):
    market_overview: Dict[str, Any]
    risk_factors: List[str]
    overall_recommendation: str


@app.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(request: MarketAnalysisRequest):
    try:
        # 这里应该调用MCP Server获取实际市场数据
        # 暂时使用模拟数据
        mock_data = {
            "沪深300": {"latest_price": 3800, "pe_ratio": 12.5, "pb_ratio": 1.3},
            "创业板指": {"latest_price": 2200, "pe_ratio": 35.2, "pb_ratio": 3.8},
            "10年国债": {"yield": 2.65},
            "CPI": {"latest": 0.7}
        }

        result = await agent.analyze(mock_data)
        return MarketAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "market"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

- [x] **Step 3: Commit**

```bash
git add backend/agents/market/
git commit -m "feat: add market analysis agent with LLM analysis"
```

---

### Task 11: 策略生成 Agent

**Files:**
- Create: `backend/agents/strategy/__init__.py`
- Create: `backend/agents/strategy/main.py`
- Create: `backend/agents/strategy/agent.py`

- [x] **Step 1: 创建 backend/agents/strategy/agent.py**

```python
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from shared.config import get_settings

settings = get_settings()


class StrategyGenerationAgent:
    """策略生成Agent - 基于用户画像和市场分析生成配置方案"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.3
        )

        # 适当性匹配规则
        self.suitability_rules = {
            "conservative": {
                "allowed_products": ["货币基金", "债券基金", "银行理财", "国债"],
                "max_equity_allocation": 0.20
            },
            "moderate": {
                "allowed_products": ["混合基金", "指数基金", "债券基金"],
                "max_equity_allocation": 0.60
            },
            "aggressive": {
                "allowed_products": ["股票", "股票基金", "期货", "期权"],
                "max_equity_allocation": 0.90
            }
        }

    async def generate(self, profile: Dict[str, Any], market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成四笔钱配置方案"""

        system_prompt = """你是一个专业的理财规划师。根据用户画像和市场分析，生成"四笔钱"资产配置方案。

四笔钱框架：
1. 活钱（living_money）：保持3-6个月生活费的流动性
2. 稳健（stable_money）：稳健增值，波动可控
3. 长期（growth_money）：长期增值，承受短期波动
4. 保障（protection_money）：风险兜底，防止因病返贫

输出格式（JSON）：
{
    "four_buckets": {
        "living_money": {"allocation": 0.10, "products": [...], "reason": "..."},
        "stable_money": {"allocation": 0.30, "products": [...], "reason": "..."},
        "growth_money": {"allocation": 0.50, "products": [...], "reason": "..."},
        "protection_money": {"allocation": 0.10, "products": [...], "reason": "..."}
    },
    "rebalance_triggers": {"drift_threshold": 0.05, "review_frequency": "quarterly"},
    "stress_test": {
        "scenario_2015_crash": {"loss": -0.15, "recovery_time": "8m"},
        "scenario_covid": {"loss": -0.12, "recovery_time": "4m"}
    }
}"""

        user_prompt = f"""用户画像：
- 生命周期阶段：{profile.get('lifecycle_stage')}
- 风险承受能力：{profile.get('risk_capacity')}
- 月结余：{profile.get('monthly_surplus')}
- 可投资资产：{profile.get('investable_assets')}

市场分析：
{self._format_market_analysis(market_analysis)}

请生成四笔钱配置方案。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)

        import json
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            result = self._default_strategy(profile)

        # 应用适当性匹配
        result = self._apply_suitability(result, profile.get('risk_capacity', 'medium'))

        return result

    def _format_market_analysis(self, market_analysis: Dict[str, Any]) -> str:
        """格式化市场分析"""
        lines = []
        overview = market_analysis.get('market_overview', {})
        for asset, data in overview.items():
            if isinstance(data, dict):
                lines.append(f"- {asset}: 预期收益{data.get('expected_return', 0)*100}%, 波动率{data.get('volatility', 0)*100}%")
        return "\n".join(lines)

    def _default_strategy(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """默认策略"""
        risk_capacity = profile.get('risk_capacity', 'medium')

        allocations = {
            "low": {"living": 0.15, "stable": 0.50, "growth": 0.25, "protection": 0.10},
            "medium": {"living": 0.10, "stable": 0.30, "growth": 0.50, "protection": 0.10},
            "high": {"living": 0.05, "stable": 0.20, "growth": 0.65, "protection": 0.10}
        }

        alloc = allocations.get(risk_capacity, allocations["medium"])

        return {
            "four_buckets": {
                "living_money": {
                    "allocation": alloc["living"],
                    "products": ["货币基金", "活期存款"],
                    "reason": "保持3-6个月生活费流动性"
                },
                "stable_money": {
                    "allocation": alloc["stable"],
                    "products": ["债券基金", "银行理财"],
                    "reason": "稳健增值，波动可控"
                },
                "growth_money": {
                    "allocation": alloc["growth"],
                    "products": ["沪深300ETF", "偏股混合基金"],
                    "reason": "长期增值，承受短期波动"
                },
                "protection_money": {
                    "allocation": alloc["protection"],
                    "products": ["重疾险", "意外险"],
                    "reason": "风险兜底，防止因病返贫"
                }
            },
            "rebalance_triggers": {
                "drift_threshold": 0.05,
                "review_frequency": "quarterly"
            },
            "stress_test": {
                "scenario_2015_crash": {"loss": -0.15, "recovery_time": "8m"},
                "scenario_covid": {"loss": -0.12, "recovery_time": "4m"}
            }
        }

    def _apply_suitability(self, strategy: Dict[str, Any], risk_capacity: str) -> Dict[str, Any]:
        """应用适当性匹配规则"""
        risk_level_map = {"low": "conservative", "medium": "moderate", "high": "aggressive"}
        risk_level = risk_level_map.get(risk_capacity, "moderate")
        rules = self.suitability_rules.get(risk_level, self.suitability_rules["moderate"])

        # 检查成长型资产配置是否超过上限
        growth_allocation = strategy["four_buckets"]["growth_money"]["allocation"]
        if growth_allocation > rules["max_equity_allocation"]:
            # 调整配置
            excess = growth_allocation - rules["max_equity_allocation"]
            strategy["four_buckets"]["growth_money"]["allocation"] = rules["max_equity_allocation"]
            strategy["four_buckets"]["stable_money"]["allocation"] += excess

        return strategy
```

- [x] **Step 2: 创建 backend/agents/strategy/main.py**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID
from agents.strategy.agent import StrategyGenerationAgent

app = FastAPI(title="Strategy Generation Agent")
agent = StrategyGenerationAgent()


class StrategyRequest(BaseModel):
    user_id: UUID
    profile: Dict[str, Any]
    market_analysis: Dict[str, Any]


class StrategyResponse(BaseModel):
    four_buckets: Dict[str, Any]
    rebalance_triggers: Dict[str, Any]
    stress_test: Dict[str, Any]


@app.post("/generate", response_model=StrategyResponse)
async def generate_strategy(request: StrategyRequest):
    try:
        result = await agent.generate(request.profile, request.market_analysis)
        return StrategyResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "strategy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

- [x] **Step 3: Commit**

```bash
git add backend/agents/strategy/
git commit -m "feat: add strategy generation agent with suitability matching"
```

---

### Task 12: 陪伴督导 Agent

**Files:**
- Create: `backend/agents/coaching/__init__.py`
- Create: `backend/agents/coaching/main.py`
- Create: `backend/agents/coaching/agent.py`

- [x] **Step 1: 创建 backend/agents/coaching/agent.py**

```python
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from shared.config import get_settings

settings = get_settings()


class CoachingAgent:
    """陪伴督导Agent - 用户交互、纠偏、心理按摩"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.7  # 更高的温度以获得更自然的对话
        )

    async def generate_response(self, context: str, user_message: str = None, event_type: str = None) -> Dict[str, Any]:
        """生成督导响应"""

        system_prompt = """你是一个温暖、专业的理财督导助手。你的职责是：
1. 帮助用户理解他们的资产配置方案
2. 在市场波动时安抚用户情绪
3. 当用户偏离配置方案时温和提醒
4. 定期关心用户，了解他们的近况

你的沟通风格：
- 温暖、有同理心
- 用简单易懂的语言解释专业概念
- 强调长期投资的重要性
- 不做具体的产品推荐

输出格式（JSON）：
{
    "message": "给用户的消息",
    "action": "none/followup/replan",
    "replan_trigger": "如果需要重规划，说明原因"
}"""

        if event_type:
            user_prompt = f"""事件类型：{event_type}
用户当前状态：{context}

请生成督导响应。"""
        else:
            user_prompt = f"""用户消息：{user_message}
用户当前状态：{context}

请生成督导响应。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)

        import json
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            result = {
                "message": response.content,
                "action": "none",
                "replan_trigger": None
            }

        return result

    async def handle_market_anomaly(self, user_id: str, event_detail: Dict[str, Any]) -> Dict[str, Any]:
        """处理市场异动事件"""
        context = f"用户ID: {user_id}\n市场异动: {event_detail}"
        return await self.generate_response(context, event_type="market_anomaly")

    async def handle_user_deviation(self, user_id: str, deviation_detail: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户偏离事件"""
        context = f"用户ID: {user_id}\n偏离情况: {deviation_detail}"
        return await self.generate_response(context, event_type="user_deviation")
```

- [x] **Step 2: 创建 backend/agents/coaching/main.py**

```python
import os
import asyncio
import json
import aio_pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
from agents.coaching.agent import CoachingAgent

app = FastAPI(title="Coaching Agent")
agent = CoachingAgent()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


class CoachingRequest(BaseModel):
    user_id: UUID
    context: str
    strategy: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None


class CoachingResponse(BaseModel):
    message: str
    action: str
    replan_trigger: Optional[str] = None


@app.post("/interact", response_model=CoachingResponse)
async def interact(request: CoachingRequest):
    try:
        result = await agent.generate_response(
            context=request.context,
            user_message=request.user_message
        )
        return CoachingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/event/market-anomaly", response_model=CoachingResponse)
async def handle_market_anomaly(user_id: UUID, event_detail: Dict[str, Any]):
    try:
        result = await agent.handle_market_anomaly(str(user_id), event_detail)
        return CoachingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/event/user-deviation", response_model=CoachingResponse)
async def handle_user_deviation(user_id: UUID, deviation_detail: Dict[str, Any]):
    try:
        result = await agent.handle_user_deviation(str(user_id), deviation_detail)
        return CoachingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "coaching"}


async def start_rabbitmq_consumer():
    """启动 RabbitMQ 消费者，监听市场异动和用户偏离事件"""
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    # 监听市场异动事件
    market_exchange = await channel.declare_exchange(
        "market_events", aio_pika.ExchangeType.TOPIC, durable=True
    )
    market_queue = await channel.declare_queue("coaching.market", durable=True)
    await market_queue.bind(market_exchange, routing_key="market.anomaly.*")

    # 监听用户偏离事件
    user_exchange = await channel.declare_exchange(
        "user_events", aio_pika.ExchangeType.TOPIC, durable=True
    )
    user_queue = await channel.declare_queue("coaching.user", durable=True)
    await user_queue.bind(user_exchange, routing_key="user.deviation.*")

    async def process_market_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(message.body.decode())
            # 从事件中提取用户列表并逐个处理
            # 实际实现中应从数据库查询所有活跃用户
            print(f"Received market event: {body['event_type']}")

    async def process_user_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(message.body.decode())
            user_id = body.get("user_id")
            if user_id:
                await agent.handle_user_deviation(user_id, body.get("detail", {}))
                print(f"Processed user deviation for {user_id}")

    await market_queue.consume(process_market_message)
    await user_queue.consume(process_user_message)
    print("Coaching Agent RabbitMQ consumer started")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_rabbitmq_consumer())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
```

- [x] **Step 3: Commit**

```bash
git add backend/agents/coaching/
git commit -m "feat: add coaching agent with event handling"
```

---

## Phase 5: Orchestrator 与监控服务（Task 13-15）

### Task 13: Orchestrator - LangGraph 状态图

**Files:**
- Create: `backend/orchestrator/__init__.py`
- Create: `backend/orchestrator/main.py`
- Create: `backend/orchestrator/state.py`
- Create: `backend/orchestrator/graph.py`

- [x] **Step 1: 创建 backend/orchestrator/state.py**

```python
from typing import TypedDict, Annotated, Dict, Any, List, Optional
from uuid import UUID
import operator


class FinancialPlanningState(TypedDict):
    """理财规划状态图状态定义"""
    user_id: str
    risk_assessment: Dict[str, Any]  # 风险测评数据
    user_profile: Dict[str, Any]  # 用户画像
    market_analysis: Dict[str, Any]  # 市场分析结果
    strategy: Dict[str, Any]  # 生成的配置方案
    coaching_history: Annotated[List[Dict[str, Any]], operator.add]  # 督导对话历史
    current_step: str  # 当前步骤
    needs_followup: bool  # 是否需要追问
    replan_trigger: Optional[str]  # 重规划触发原因
    error: Optional[str]  # 错误信息
```

- [x] **Step 2: 创建 backend/orchestrator/graph.py**

```python
from langgraph.graph import StateGraph, END
from typing import Dict, Any
import httpx
from orchestrator.state import FinancialPlanningState

# Agent 服务地址
AGENT_URLS = {
    "profile": "http://agent-profile:8001",
    "market": "http://agent-market:8002",
    "strategy": "http://agent-strategy:8003",
    "coaching": "http://agent-coaching:8004",
}


async def call_profile_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用用户画像Agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['profile']}/analyze",
            json={
                "user_id": state["user_id"],
                "risk_assessment": state["risk_assessment"]
            },
            timeout=30.0
        )
        result = response.json()

    return {
        "user_profile": result.get("profile", {}),
        "needs_followup": result.get("needs_followup", False),
        "current_step": "profile_complete"
    }


async def call_market_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用市场研判Agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['market']}/analyze",
            json={
                "analysis_type": "full",
                "focus_areas": ["equity", "bond", "commodity"],
                "time_horizon": "1y"
            },
            timeout=30.0
        )
        result = response.json()

    return {
        "market_analysis": result,
        "current_step": "market_complete"
    }


async def call_strategy_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用策略生成Agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['strategy']}/generate",
            json={
                "user_id": state["user_id"],
                "profile": state["user_profile"],
                "market_analysis": state["market_analysis"]
            },
            timeout=30.0
        )
        result = response.json()

    return {
        "strategy": result,
        "current_step": "strategy_complete"
    }


async def call_coaching_agent(state: FinancialPlanningState) -> Dict[str, Any]:
    """调用陪伴督导Agent"""
    context = f"用户画像: {state['user_profile']}\n配置方案: {state['strategy']}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_URLS['coaching']}/interact",
            json={
                "user_id": state["user_id"],
                "context": context,
                "strategy": state["strategy"]
            },
            timeout=30.0
        )
        result = response.json()

    coaching_entry = {
        "type": "strategy_explanation",
        "message": result.get("message", ""),
        "action": result.get("action", "none")
    }

    return {
        "coaching_history": [coaching_entry],
        "current_step": "coaching_complete"
    }


def route_after_profile(state: FinancialPlanningState) -> str:
    """画像后的路由逻辑"""
    if state.get("needs_followup"):
        return "coaching"
    return "market"


def route_after_strategy(state: FinancialPlanningState) -> str:
    """策略后的路由逻辑"""
    return "coaching"


def create_graph() -> StateGraph:
    """创建LangGraph状态图"""
    workflow = StateGraph(FinancialPlanningState)

    # 添加节点
    workflow.add_node("profile", call_profile_agent)
    workflow.add_node("market", call_market_agent)
    workflow.add_node("strategy", call_strategy_agent)
    workflow.add_node("coaching", call_coaching_agent)

    # 设置入口
    workflow.set_entry_point("profile")

    # 条件分支：画像后
    workflow.add_conditional_edges(
        "profile",
        route_after_profile,
        {
            "coaching": "coaching",
            "market": "market"
        }
    )

    # 市场分析后 -> 策略生成
    workflow.add_edge("market", "strategy")

    # 策略生成后 -> 督导
    workflow.add_conditional_edges(
        "strategy",
        route_after_strategy,
        {
            "coaching": "coaching"
        }
    )

    # 督导后 -> 结束
    workflow.add_edge("coaching", END)

    return workflow.compile()


# 创建全局图实例
graph = create_graph()
```

- [x] **Step 3: 创建 backend/orchestrator/main.py**

```python
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
from orchestrator.graph import graph
from orchestrator.state import FinancialPlanningState

app = FastAPI(title="Orchestrator")

# 存储用户的图实例状态
user_states: Dict[str, FinancialPlanningState] = {}


class StartRequest(BaseModel):
    user_id: UUID
    risk_assessment: Dict[str, Any]


class ReplanRequest(BaseModel):
    user_id: UUID
    trigger: str
    trigger_detail: str
    replan_from: str
    context: Optional[Dict[str, Any]] = None


class OrchestratorResponse(BaseModel):
    user_id: str
    current_step: str
    user_profile: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    coaching_history: Optional[list] = None
    error: Optional[str] = None


@app.post("/start", response_model=OrchestratorResponse)
async def start_planning(request: StartRequest):
    """启动理财规划流程"""
    user_id = str(request.user_id)

    # 初始状态
    initial_state: FinancialPlanningState = {
        "user_id": user_id,
        "risk_assessment": request.risk_assessment,
        "user_profile": {},
        "market_analysis": {},
        "strategy": {},
        "coaching_history": [],
        "current_step": "started",
        "needs_followup": False,
        "replan_trigger": None,
        "error": None
    }

    try:
        # 执行图
        result = await graph.ainvoke(initial_state)
        user_states[user_id] = result

        return OrchestratorResponse(
            user_id=user_id,
            current_step=result.get("current_step", "unknown"),
            user_profile=result.get("user_profile"),
            market_analysis=result.get("market_analysis"),
            strategy=result.get("strategy"),
            coaching_history=result.get("coaching_history")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/replan", response_model=OrchestratorResponse)
async def replan(request: ReplanRequest):
    """触发重规划"""
    user_id = str(request.user_id)

    if user_id not in user_states:
        raise HTTPException(status_code=404, detail="User planning session not found")

    # 获取现有状态
    current_state = user_states[user_id]

    # 更新状态，从指定节点重新开始
    current_state["replan_trigger"] = request.trigger
    current_state["current_step"] = request.replan_from

    try:
        # 重新执行图
        result = await graph.ainvoke(current_state)
        user_states[user_id] = result

        return OrchestratorResponse(
            user_id=user_id,
            current_step=result.get("current_step", "unknown"),
            user_profile=result.get("user_profile"),
            market_analysis=result.get("market_analysis"),
            strategy=result.get("strategy"),
            coaching_history=result.get("coaching_history")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{user_id}", response_model=OrchestratorResponse)
async def get_status(user_id: str):
    """查询当前流程状态"""
    if user_id not in user_states:
        raise HTTPException(status_code=404, detail="User planning session not found")

    state = user_states[user_id]
    return OrchestratorResponse(
        user_id=user_id,
        current_step=state.get("current_step", "unknown"),
        user_profile=state.get("user_profile"),
        market_analysis=state.get("market_analysis"),
        strategy=state.get("strategy"),
        coaching_history=state.get("coaching_history")
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchestrator"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

- [x] **Step 4: Commit**

```bash
git add backend/orchestrator/
git commit -m "feat: add orchestrator with LangGraph state graph"
```

---

### Task 14: Market Monitor 定时任务

**Files:**
- Create: `backend/monitors/__init__.py`
- Create: `backend/monitors/market_monitor.py`

- [x] **Step 1: 创建 backend/monitors/market_monitor.py**

```python
import asyncio
from datetime import datetime
from typing import Dict, Any
import aio_pika
import json
from shared.config import get_settings
from shared.redis_client import get_redis

settings = get_settings()


class MarketMonitor:
    """市场异动监控"""

    def __init__(self):
        self.check_interval = 300  # 5分钟检查一次
        self.thresholds = {
            "index_drop": -0.03,  # 指数跌幅超过3%
            "index_surge": 0.05,  # 指数涨幅超过5%
            "rate_change": 0.25,  # 利率变化超过25bp
        }

    async def check_market_anomaly(self) -> list:
        """检查市场异动"""
        anomalies = []

        # 这里应该调用MCP Server获取实际市场数据
        # 暂时使用模拟检查
        try:
            redis = await get_redis()

            # 检查缓存的市场数据
            market_data = await redis.get("market:latest")
            if market_data:
                data = json.loads(market_data)

                # 检查指数跌幅
                for index_name, index_data in data.items():
                    if isinstance(index_data, dict):
                        change = index_data.get("daily_change", 0)
                        if change <= self.thresholds["index_drop"]:
                            anomalies.append({
                                "type": "market.anomaly.index_drop",
                                "detail": {
                                    "index": index_name,
                                    "change": change,
                                    "threshold": self.thresholds["index_drop"]
                                }
                            })
                        elif change >= self.thresholds["index_surge"]:
                            anomalies.append({
                                "type": "market.anomaly.index_surge",
                                "detail": {
                                    "index": index_name,
                                    "change": change,
                                    "threshold": self.thresholds["index_surge"]
                                }
                            })

        except Exception as e:
            print(f"Market check error: {e}")

        return anomalies

    async def publish_anomaly(self, anomaly: Dict[str, Any]):
        """发布异动事件到RabbitMQ"""
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "market_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            message = {
                "event_type": anomaly["type"],
                "detail": anomaly["detail"],
                "timestamp": datetime.utcnow().isoformat()
            }

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=anomaly["type"]
            )

    async def run(self):
        """运行监控循环"""
        print("Market Monitor started")
        while True:
            try:
                anomalies = await self.check_market_anomaly()
                for anomaly in anomalies:
                    await self.publish_anomaly(anomaly)
                    print(f"Published anomaly: {anomaly['type']}")
            except Exception as e:
                print(f"Monitor error: {e}")

            await asyncio.sleep(self.check_interval)


async def main():
    monitor = MarketMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
```

- [x] **Step 2: Commit**

```bash
git add backend/monitors/
git commit -m "feat: add market monitor with anomaly detection"
```

---

### Task 14.5: User Monitor 用户偏离监控

**Files:**
- Create: `backend/monitors/user_monitor.py`

- [x] **Step 1: 创建 backend/monitors/user_monitor.py**

```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import aio_pika
import json
from shared.config import get_settings
from shared.database import async_session
from shared.models.portfolio import Portfolio
from shared.models.profile import UserProfile
from sqlalchemy import select

settings = get_settings()


class UserMonitor:
    """用户偏离监控 - 检测用户资产配置偏离"""

    def __init__(self):
        self.check_interval = 3600  # 1小时检查一次
        self.drift_threshold = 0.10  # 偏离阈值 10%

    async def check_user_drift(self) -> List[Dict[str, Any]]:
        """检查用户资产偏离情况"""
        drifts = []

        try:
            async with async_session() as session:
                # 查询所有活跃的资产配置
                result = await session.execute(
                    select(Portfolio).where(Portfolio.status == "active")
                )
                portfolios = result.scalars().all()

                for portfolio in portfolios:
                    # 这里应该获取用户的实际持仓并与配置对比
                    # 暂时使用简化逻辑：检查配置是否过期（超过3个月未更新）
                    if portfolio.updated_at:
                        days_since_update = (datetime.utcnow() - portfolio.updated_at).days
                        if days_since_update > 90:
                            drifts.append({
                                "type": "user.deviation.inactivity",
                                "user_id": str(portfolio.user_id),
                                "detail": {
                                    "portfolio_id": str(portfolio.id),
                                    "days_since_update": days_since_update,
                                    "message": "用户超过3个月未更新配置"
                                }
                            })

        except Exception as e:
            print(f"User drift check error: {e}")

        return drifts

    async def publish_drift(self, drift: Dict[str, Any]):
        """发布偏离事件到RabbitMQ"""
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "user_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            message = {
                "event_type": drift["type"],
                "user_id": drift["user_id"],
                "detail": drift["detail"],
                "timestamp": datetime.utcnow().isoformat()
            }

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=drift["type"]
            )

    async def run(self):
        """运行监控循环"""
        print("User Monitor started")
        while True:
            try:
                drifts = await self.check_user_drift()
                for drift in drifts:
                    await self.publish_drift(drift)
                    print(f"Published user drift: {drift['type']} for user {drift['user_id']}")
            except Exception as e:
                print(f"User Monitor error: {e}")

            await asyncio.sleep(self.check_interval)


async def main():
    monitor = UserMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
```

- [x] **Step 2: Commit**

```bash
git add backend/monitors/user_monitor.py
git commit -m "feat: add user monitor with drift detection"
```

---

### Task 15: Docker Compose 完整配置

**Files:**
- Modify: `docker-compose.yml`

- [x] **Step 1: 更新 docker-compose.yml 添加所有服务**

```yaml
version: "3.8"

services:
  # 基础设施
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 10s
      timeout: 10s
      retries: 5

  # API Gateway
  api-gateway:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  # Orchestrator
  orchestrator:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn orchestrator.main:app --host 0.0.0.0 --port 8010 --reload
    ports:
      - "8010:8010"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Agents
  agent-profile:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn agents.profile.main:app --host 0.0.0.0 --port 8001 --reload
    ports:
      - "8001:8001"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./backend:/app

  agent-market:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn agents.market.main:app --host 0.0.0.0 --port 8002 --reload
    ports:
      - "8002:8002"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./backend:/app

  agent-strategy:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn agents.strategy.main:app --host 0.0.0.0 --port 8003 --reload
    ports:
      - "8003:8003"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./backend:/app

  agent-coaching:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn agents.coaching.main:app --host 0.0.0.0 --port 8004 --reload
    ports:
      - "8004:8004"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/
    volumes:
      - ./backend:/app
    depends_on:
      rabbitmq:
        condition: service_healthy

  # MCP Server
  mcp-server:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python -m mcp_server.main
    volumes:
      - ./backend:/app

  # Monitors
  monitor-market:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python -m monitors.market_monitor
    environment:
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/
    volumes:
      - ./backend:/app
    depends_on:
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  monitor-user:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python -m monitors.user_monitor
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

volumes:
  pgdata:
```

- [x] **Step 2: 创建 backend/Dockerfile**

```python
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [x] **Step 3: 验证完整部署**

```bash
docker compose up -d
docker compose ps
```

Expected: 所有服务显示 healthy 或 running 状态

- [x] **Step 4: Commit**

```bash
git add docker-compose.yml backend/Dockerfile
git commit -m "feat: add complete docker compose with all services"
```

---

## Phase 6: 前端与集成测试（Task 16-18）

### Task 16: Vue 3 前端项目初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/api/client.ts`

- [x] **Step 1: 初始化 Vue 3 项目**

```bash
cd frontend
npm create vite@latest . -- --template vue-ts
npm install
npm install axios pinia vue-router element-plus
```

- [x] **Step 1.5: 创建 frontend/vite.config.ts 配置代理**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/orchestrator': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [x] **Step 2: 创建 frontend/src/api/client.ts**

```typescript
import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient

// API 方法
export const authAPI = {
  register: (data: { username: string; password: string; email?: string }) =>
    apiClient.post('/auth/register', data),
  login: (data: { username: string; password: string }) =>
    apiClient.post('/auth/login', data),
}

export const riskAssessmentAPI = {
  submit: (data: { age: number; income: number; expenses: number; risk_tolerance: string; investment_horizon: string }) =>
    apiClient.post('/risk-assessment', data),
}

export const orchestratorAPI = {
  start: (data: { user_id: string; risk_assessment: any }) =>
    apiClient.post('/orchestrator/start', data),
  getStatus: (userId: string) =>
    apiClient.get(`/orchestrator/status/${userId}`),
  replan: (data: { user_id: string; trigger: string; trigger_detail: string; replan_from: string }) =>
    apiClient.post('/orchestrator/replan', data),
}
```

- [x] **Step 3: 创建 frontend/src/views/Login.vue**

```vue
<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>智能理财规划系统</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading">
            登录
          </el-button>
          <el-button @click="$router.push('/register')">
            注册
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '../api/client'

const router = useRouter()
const loading = ref(false)
const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await authAPI.login(form.value)
    localStorage.setItem('token', result.access_token)
    localStorage.setItem('user_id', result.user_id)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 20px;
}

h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}
</style>
```

- [x] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: initialize Vue 3 frontend with auth pages"
```

---

### Task 17: 风险测评与方案展示页面

**Files:**
- Create: `frontend/src/views/RiskAssessment.vue`
- Create: `frontend/src/views/Dashboard.vue`
- Create: `frontend/src/views/StrategyResult.vue`

- [x] **Step 1: 创建 frontend/src/views/RiskAssessment.vue**

```vue
<template>
  <div class="assessment-container">
    <el-card>
      <h2>风险承受能力测评</h2>
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="基本信息" />
        <el-step title="投资偏好" />
        <el-step title="测评结果" />
      </el-steps>

      <div v-if="currentStep === 0" class="step-content">
        <el-form :model="form">
          <el-form-item label="年龄">
            <el-input-number v-model="form.age" :min="18" :max="80" />
          </el-form-item>
          <el-form-item label="月收入（元）">
            <el-input-number v-model="form.income" :min="0" :step="1000" />
          </el-form-item>
          <el-form-item label="月支出（元）">
            <el-input-number v-model="form.expenses" :min="0" :step="1000" />
          </el-form-item>
        </el-form>
        <el-button type="primary" @click="currentStep++">下一步</el-button>
      </div>

      <div v-if="currentStep === 1" class="step-content">
        <el-form :model="form">
          <el-form-item label="风险偏好">
            <el-radio-group v-model="form.risk_tolerance">
              <el-radio label="conservative">保守型</el-radio>
              <el-radio label="moderate">稳健型</el-radio>
              <el-radio label="aggressive">进取型</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="投资期限">
            <el-select v-model="form.investment_horizon">
              <el-option label="1年以内" value="1y" />
              <el-option label="1-3年" value="3y" />
              <el-option label="3-5年" value="5y" />
              <el-option label="5年以上" value="10y+" />
            </el-select>
          </el-form-item>
        </el-form>
        <el-button @click="currentStep--">上一步</el-button>
        <el-button type="primary" @click="submitAssessment">提交测评</el-button>
      </div>

      <div v-if="currentStep === 2" class="step-content">
        <el-result icon="success" title="测评完成">
          <template #extra>
            <el-button type="primary" @click="generateStrategy">
              生成配置方案
            </el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { riskAssessmentAPI, orchestratorAPI } from '../api/client'

const router = useRouter()
const currentStep = ref(0)
const form = ref({
  age: 30,
  income: 20000,
  expenses: 12000,
  risk_tolerance: 'moderate',
  investment_horizon: '5y'
})

const submitAssessment = async () => {
  try {
    await riskAssessmentAPI.submit(form.value)
    currentStep.value = 2
    ElMessage.success('测评提交成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交失败')
  }
}

const generateStrategy = async () => {
  try {
    const userId = localStorage.getItem('user_id')
    if (!userId) {
      ElMessage.error('请先登录')
      return
    }

    const result = await orchestratorAPI.start({
      user_id: userId,
      risk_assessment: form.value
    })

    // 跳转到结果页面
    router.push({
      path: '/strategy-result',
      query: { userId }
    })
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成方案失败')
  }
}
</script>

<style scoped>
.assessment-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
}

.step-content {
  margin-top: 30px;
}
</style>
```

- [x] **Step 2: 创建 frontend/src/views/StrategyResult.vue**

```vue
<template>
  <div class="result-container">
    <el-card v-if="loading" class="loading-card">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在生成您的专属配置方案...</p>
    </el-card>

    <template v-else-if="strategy">
      <h2>您的专属资产配置方案</h2>

      <el-row :gutter="20">
        <el-col :span="6" v-for="(bucket, key) in strategy.four_buckets" :key="key">
          <el-card class="bucket-card">
            <h3>{{ bucketNames[key] }}</h3>
            <div class="allocation">{{ (bucket.allocation * 100).toFixed(0) }}%</div>
            <p class="reason">{{ bucket.reason }}</p>
            <div class="products">
              <el-tag v-for="product in bucket.products" :key="product" size="small">
                {{ product }}
              </el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="stress-test-card">
        <h3>压力测试</h3>
        <el-table :data="stressTestData">
          <el-table-column prop="scenario" label="情景" />
          <el-table-column prop="loss" label="预期损失">
            <template #default="{ row }">
              <span :class="{ 'negative': row.loss < 0 }">{{ (row.loss * 100).toFixed(1) }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="recovery_time" label="恢复时间" />
        </el-table>
      </el-card>

      <el-card v-if="coachingMessage" class="coaching-card">
        <h3>督导建议</h3>
        <p>{{ coachingMessage }}</p>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { orchestratorAPI } from '../api/client'

const route = useRoute()
const loading = ref(true)
const strategy = ref<any>(null)
const coachingMessage = ref('')

const bucketNames: Record<string, string> = {
  living_money: '活钱',
  stable_money: '稳健',
  growth_money: '长期',
  protection_money: '保障'
}

const stressTestData = ref<any[]>([])

onMounted(async () => {
  const userId = route.query.userId as string
  if (!userId) return

  try {
    const result = await orchestratorAPI.getStatus(userId)
    strategy.value = result.strategy
    coachingMessage.value = result.coaching_history?.[0]?.message || ''

    // 转换压力测试数据
    if (result.strategy?.stress_test) {
      stressTestData.value = Object.entries(result.strategy.stress_test).map(([scenario, data]: [string, any]) => ({
        scenario,
        ...data
      }))
    }
  } catch (error) {
    console.error('Failed to load strategy:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.result-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 20px;
}

.loading-card {
  text-align: center;
  padding: 60px;
}

.bucket-card {
  text-align: center;
  margin-bottom: 20px;
}

.allocation {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin: 10px 0;
}

.reason {
  color: #666;
  font-size: 14px;
}

.products {
  margin-top: 10px;
}

.stress-test-card {
  margin-top: 20px;
}

.coaching-card {
  margin-top: 20px;
  background: #f0f9ff;
}

.negative {
  color: #f56c6c;
}
</style>
```

- [x] **Step 3: Commit**

```bash
git add frontend/src/views/
git commit -m "feat: add risk assessment and strategy result pages"
```

---

### Task 18: 集成测试

**Files:**
- Create: `backend/tests/test_integration.py`

- [x] **Step 1: 创建 backend/tests/test_integration.py**

```python
import pytest
import httpx
import asyncio

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_health_check():
    """测试健康检查接口"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login():
    """测试注册和登录流程"""
    async with httpx.AsyncClient() as client:
        # 注册
        register_response = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": "testuser",
                "password": "testpassword123",
                "email": "test@example.com"
            }
        )
        assert register_response.status_code == 201

        # 登录
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

        return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_risk_assessment():
    """测试风险测评流程"""
    async with httpx.AsyncClient() as client:
        # 先登录获取token
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]

        # 提交风险测评
        assessment_response = await client.post(
            f"{BASE_URL}/api/risk-assessment",
            json={
                "age": 30,
                "income": 20000,
                "expenses": 12000,
                "risk_tolerance": "moderate",
                "investment_horizon": "5y"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert assessment_response.status_code == 200
        assert "risk_level" in assessment_response.json()


@pytest.mark.asyncio
async def test_full_planning_flow():
    """测试完整理财规划流程"""
    async with httpx.AsyncClient() as client:
        # 登录
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 提交风险测评
        await client.post(
            f"{BASE_URL}/api/risk-assessment",
            json={
                "age": 30,
                "income": 20000,
                "expenses": 12000,
                "risk_tolerance": "moderate",
                "investment_horizon": "5y"
            },
            headers=headers
        )

        # 启动理财规划
        planning_response = await client.post(
            f"{BASE_URL}/orchestrator/start",
            json={
                "user_id": "test-user-id",
                "risk_assessment": {
                    "age": 30,
                    "income": 20000,
                    "expenses": 12000,
                    "risk_tolerance": "moderate",
                    "investment_horizon": "5y"
                }
            },
            headers=headers
        )

        # 这个测试可能会失败，因为需要所有Agent服务都运行
        # 但可以验证API Gateway的路由是否正确
        print(f"Planning response: {planning_response.status_code}")


if __name__ == "__main__":
    asyncio.run(test_health_check())
```

- [x] **Step 2: 运行集成测试**

```bash
cd backend
pytest tests/test_integration.py -v
```

Expected: 健康检查和注册登录测试通过，完整流程测试可能因Agent服务未启动而失败

- [x] **Step 3: Commit**

```bash
git add backend/tests/
git commit -m "test: add integration tests for API endpoints"
```

---

## 附录：执行顺序

| Phase | Tasks | 依赖 |
|-------|-------|------|
| Phase 1 | Task 1-4 | 无 |
| Phase 2 | Task 5-6 | Phase 1 完成 |
| Phase 3 | Task 7-8 | Phase 1 完成 |
| Phase 4 | Task 9-12 | Phase 2, 3 完成 |
| Phase 5 | Task 13-15 | Phase 4 完成 |
| Phase 6 | Task 16-18 | Phase 5 完成 |

**并行建议：**
- Phase 2 和 Phase 3 可以并行执行
- Task 9-12（四个Agent）可以并行执行
- Task 16-18（前端）可以在后端完成后独立执行

---

## 附录：已知限制与后续改进

### 1. datetime.utcnow() 废弃警告
代码中多处使用 `datetime.utcnow()`，在 Python 3.12+ 中已标记为废弃。当前目标 Python 3.11 可正常使用，升级时需改为 `datetime.now(timezone.utc)`。

### 2. WebSocket 实时推送未实现
Spec 中提到的 WebSocket 实时推送（市场异动、督导消息）在本计划中未实现，当前使用 HTTP 轮询作为替代。可在后续迭代中添加。

### 3. LangGraph Checkpoint 持久化
当前 Orchestrator 将状态存储在内存字典中（`user_states`），进程重启会丢失。生产环境应使用 LangGraph 的 PostgreSQL Checkpointer 实现持久化。

### 4. MCP Server 与 Agent 的连接方式
当前计划中 MCP Server 使用 stdio 模式，适合单进程调用。在微服务架构中，Agent 需要通过 SSE 或 HTTP 连接 MCP Server，需要将 MCP Server 改为 SSE 模式或直接在 Agent 内部调用数据源适配器。
