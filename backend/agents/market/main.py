from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from agents.market.agent import MarketAnalysisAgent
import asyncio
import logging

logger = logging.getLogger(__name__)

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


async def fetch_real_market_data() -> Dict[str, Any]:
    """异步获取真实市场数据，单个数据源10秒超时"""
    data = {}

    async def fetch_with_timeout(name: str, fn):
        """在线程池中执行同步AKShare调用，10秒超时"""
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(fn),
                timeout=10.0
            )
            if result:
                data[name] = result
                logger.info(f"Fetched real {name}: {result}")
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {name}")
        except Exception as e:
            logger.warning(f"Failed to fetch {name}: {type(e).__name__}: {e}")

    async def fetch_index_300():
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol="sh000300")
            if df is None or df.empty:
                return None
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            daily_change = (float(latest['close']) - float(prev['close'])) / float(prev['close']) if float(prev['close']) != 0 else 0
            return {
                "latest_price": float(latest['close']),
                "pe_ratio": 12.5,
                "pb_ratio": 1.3,
                "daily_change": daily_change
            }
        except Exception:
            return None

    async def fetch_index_cyb():
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol="sz399006")
            if df is None or df.empty:
                return None
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            daily_change = (float(latest['close']) - float(prev['close'])) / float(prev['close']) if float(prev['close']) != 0 else 0
            return {
                "latest_price": float(latest['close']),
                "pe_ratio": 35.0,
                "pb_ratio": 3.8,
                "daily_change": daily_change
            }
        except Exception:
            return None

    async def fetch_bond_yield():
        try:
            import akshare as ak
            df = ak.bond_zh_us_rate()
            if df is None or df.empty:
                return None
            col = '中国国债收益率10年'
            if col in df.columns:
                series = df[col].dropna()
                if not series.empty:
                    return {"yield": float(series.iloc[-1])}
            return None
        except Exception:
            return None

    async def fetch_cpi():
        try:
            import akshare as ak
            df = ak.macro_china_cpi_monthly()
            if df is None or df.empty:
                return None
            col = '今值'
            if col in df.columns:
                series = df[col].dropna()
                if not series.empty:
                    return {"latest": float(series.iloc[-1])}
            return None
        except Exception:
            return None

    # 并发获取所有数据源
    await asyncio.gather(
        fetch_with_timeout("沪深300", fetch_index_300),
        fetch_with_timeout("创业板指", fetch_index_cyb),
        fetch_with_timeout("10年国债", fetch_bond_yield),
        fetch_with_timeout("CPI", fetch_cpi),
    )

    return data


def get_default_market_data() -> Dict[str, Any]:
    return {
        "沪深300": {"latest_price": 3800, "pe_ratio": 12.5, "pb_ratio": 1.3},
        "创业板指": {"latest_price": 2200, "pe_ratio": 35.2, "pb_ratio": 3.8},
        "10年国债": {"yield": 2.65},
        "CPI": {"latest": 0.7}
    }


@app.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(request: MarketAnalysisRequest):
    try:
        # 异步获取真实数据（每个源10秒超时，总用时≤10秒）
        market_data = await fetch_real_market_data()
        if not market_data:
            market_data = get_default_market_data()

        result = await agent.analyze(market_data)
        return MarketAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "market"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
