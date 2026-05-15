from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from agents.market.agent import MarketAnalysisAgent
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


def fetch_real_market_data() -> Dict[str, Any]:
    """尝试从AKShare获取真实市场数据，失败则返回默认数据"""
    try:
        import akshare as ak
        data = {}

        # 沪深300指数
        try:
            df_300 = ak.stock_zh_index_daily(symbol="sh000300")
            if not df_300.empty:
                latest = df_300.iloc[-1]
                prev = df_300.iloc[-2] if len(df_300) > 1 else latest
                pe = float(latest.get('pe', 12.5)) if 'pe' in latest else 12.5
                daily_change = (float(latest['close']) - float(prev['close'])) / float(prev['close'])
                data["沪深300"] = {
                    "latest_price": float(latest['close']),
                    "pe_ratio": pe,
                    "pb_ratio": 1.3,
                    "daily_change": daily_change
                }
                logger.info(f"Fetched real 沪深300 data: {data['沪深300']['latest_price']}")
        except Exception as e:
            logger.warning(f"Failed to fetch 沪深300: {e}")

        # 创业板指
        try:
            df_cyb = ak.stock_zh_index_daily(symbol="sz399006")
            if not df_cyb.empty:
                latest = df_cyb.iloc[-1]
                prev = df_cyb.iloc[-2] if len(df_cyb) > 1 else latest
                pe = float(latest.get('pe', 35.0)) if 'pe' in latest else 35.0
                daily_change = (float(latest['close']) - float(prev['close'])) / float(prev['close'])
                data["创业板指"] = {
                    "latest_price": float(latest['close']),
                    "pe_ratio": pe,
                    "pb_ratio": 3.8,
                    "daily_change": daily_change
                }
                logger.info(f"Fetched real 创业板指 data: {data['创业板指']['latest_price']}")
        except Exception as e:
            logger.warning(f"Failed to fetch 创业板指: {e}")

        # 国债收益率
        try:
            df_bond = ak.bond_zh_us_rate()
            if not df_bond.empty:
                # 列名: '中国国债收益率10年', 取最新非NaN值
                col_10y = '中国国债收益率10年'
                if col_10y in df_bond.columns:
                    latest_bond = df_bond[col_10y].dropna()
                    if not latest_bond.empty:
                        yield_val = float(latest_bond.iloc[-1])
                        data["10年国债"] = {"yield": yield_val}
                        logger.info(f"Fetched real 10Y bond yield: {yield_val}%")
        except Exception as e:
            logger.warning(f"Failed to fetch bond yield: {e}")

        # CPI
        try:
            df_cpi = ak.macro_china_cpi_monthly()
            if not df_cpi.empty:
                # 列名: '今值'
                col_val = '今值'
                if col_val in df_cpi.columns:
                    latest_cpi = float(df_cpi[col_val].dropna().iloc[-1])
                    data["CPI"] = {"latest": latest_cpi}
                    logger.info(f"Fetched real CPI: {latest_cpi}%")
        except Exception as e:
            logger.warning(f"Failed to fetch CPI: {e}")

        if data:
            logger.info(f"Using real market data: {list(data.keys())}")
            return data
    except ImportError:
        logger.info("AKShare not installed, using default market data")
    except Exception as e:
        logger.warning(f"Failed to fetch real market data: {e}")

    return {}


def get_default_market_data() -> Dict[str, Any]:
    """获取默认市场数据（硬编码回退）"""
    return {
        "沪深300": {"latest_price": 3800, "pe_ratio": 12.5, "pb_ratio": 1.3},
        "创业板指": {"latest_price": 2200, "pe_ratio": 35.2, "pb_ratio": 3.8},
        "10年国债": {"yield": 2.65},
        "CPI": {"latest": 0.7}
    }


@app.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(request: MarketAnalysisRequest):
    try:
        # 优先使用真实数据
        market_data = fetch_real_market_data()
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
