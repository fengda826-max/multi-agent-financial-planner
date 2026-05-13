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

        days_map = {"1y": 365, "3y": 1095, "5y": 1825}
        days = days_map.get(period, 365)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        try:
            df = ak.stock_zh_index_daily(symbol=symbol)
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                return {"error": f"No data found for {symbol}"}

            returns = df["close"].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)
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
