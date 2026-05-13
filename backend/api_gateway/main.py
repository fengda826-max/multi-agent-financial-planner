import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx
from shared.database import init_db
from api_gateway.routers import auth, user, risk_assessment

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
app.include_router(risk_assessment.router, prefix="/api/risk-assessment", tags=["风险测评"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Orchestrator 代理路由
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
