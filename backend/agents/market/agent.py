from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from shared.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class MarketAnalysisAgent:
    """市场研判Agent - 统计计算量化指标，LLM仅生成风险因素和整体建议"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-v4-pro",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.3
        )

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析市场数据。量化指标由统计计算，LLM仅生成定性分析。"""

        # 1. 从原始数据计算量化指标
        computed = self._compute_market_metrics(market_data)

        # 2. LLM 生成风险因素和定性建议（基于计算好的数据）
        qualitative = await self._generate_qualitative(market_data, computed)

        return {
            "market_overview": {
                "equity": {
                    "expected_return": round(computed["equity_return"], 4),
                    "volatility": round(computed["equity_vol"], 4),
                    "max_drawdown": round(computed["equity_max_dd"], 4),
                    "pe_ttm": computed.get("cs300_pe"),
                    "pe_percentile": computed.get("cs300_pe_percentile", "数据不足"),
                    "equity_risk_premium": round(computed["erp"], 4),
                    "recommendation": qualitative.get("equity_rec", "适度配置"),
                },
                "bond": {
                    "expected_return": round(computed["bond_yield"] / 100, 4),
                    "volatility": 0.03,
                    "recommendation": qualitative.get("bond_rec", "作为稳健配置"),
                },
                "commodity": {
                    "expected_return": 0.05,
                    "volatility": 0.15,
                    "recommendation": qualitative.get("commodity_rec", "少量配置对冲风险"),
                }
            },
            "risk_factors": qualitative.get("risk_factors", ["市场波动风险", "利率风险"]),
            "overall_recommendation": qualitative.get("overall_recommendation", "建议均衡配置"),
            "data_timestamp": computed.get("data_timestamp", ""),
            "computed_metrics": computed,  # 供前端详情展示
        }

    def _compute_market_metrics(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """从原始数据统计计算所有量化指标"""

        result = {}
        now_str = ""

        try:
            import akshare as ak
            import numpy as np
            from datetime import datetime

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

            # === CSI 300 历史统计 ===
            try:
                df = ak.stock_zh_index_daily(symbol="sh000300")
                close = df['close'].astype(float)

                # 近5年数据
                five_years_ago = datetime.now().replace(year=datetime.now().year - 5)
                recent = df[df['date'] >= five_years_ago.date()]
                recent_close = recent['close'].astype(float)
                ret = recent_close.pct_change().dropna()

                result["equity_return"] = float(ret.mean() * 252)
                result["equity_vol"] = float(ret.std() * np.sqrt(252))
                result["equity_max_dd"] = float((recent_close / recent_close.cummax() - 1).min())
                logger.info(f"Computed CSI300 stats: return={result['equity_return']:.4f}, vol={result['equity_vol']:.4f}, maxdd={result['equity_max_dd']:.4f}")
            except Exception as e:
                logger.warning(f"Failed to compute CSI300 stats: {e}")
                result["equity_return"] = 0.08
                result["equity_vol"] = 0.20
                result["equity_max_dd"] = -0.30

            # === CSI 300 PE ===
            try:
                df_pe = ak.stock_index_pe_lg(symbol="沪深300")
                latest_pe = float(df_pe.iloc[-1]['滚动市盈率'])
                result["cs300_pe"] = round(latest_pe, 2)

                # PE 历史分位（近5年）
                pe_5y = df_pe[df_pe['日期'] >= five_years_ago.date()]
                if len(pe_5y) > 50:
                    pe_values = pe_5y['滚动市盈率'].astype(float).dropna()
                    percentile = (pe_values < latest_pe).sum() / len(pe_values)
                    if percentile > 0.7:
                        result["cs300_pe_percentile"] = f"偏高（历史{percentile:.0%}分位）"
                    elif percentile > 0.3:
                        result["cs300_pe_percentile"] = f"适中（历史{percentile:.0%}分位）"
                    else:
                        result["cs300_pe_percentile"] = f"偏低（历史{percentile:.0%}分位）"
                logger.info(f"CSI300 PE: {latest_pe}, percentile: {result.get('cs300_pe_percentile', 'N/A')}")
            except Exception as e:
                logger.warning(f"Failed to fetch CSI300 PE: {e}")
                result["cs300_pe"] = None

            # === 股权风险溢价 (ERP) ===
            bond_data = market_data.get("10年国债", {})
            bond_yield = bond_data.get("yield", 2.65)
            result["bond_yield"] = float(bond_yield)
            if result.get("cs300_pe") and result["cs300_pe"] > 0:
                earnings_yield = 1.0 / result["cs300_pe"]
                result["erp"] = earnings_yield - result["bond_yield"] / 100
            else:
                result["erp"] = 0.04  # default

        except Exception as e:
            logger.warning(f"Market computation failed: {e}")
            result.update({
                "equity_return": 0.08, "equity_vol": 0.20, "equity_max_dd": -0.30,
                "bond_yield": 2.65, "erp": 0.04,
            })

        result["data_timestamp"] = now_str
        return result

    async def _generate_qualitative(self, market_data: Dict[str, Any], computed: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 基于计算好的指标生成定性分析"""

        system_prompt = """你是一个专业的市场分析师。基于已经计算好的量化指标，生成定性分析。

注意：所有量化指标（预期收益、波动率、PE、ERP）已经由后端统计计算完毕，你做以下事情：
1. 为每个资产类别写一句配置建议（不超过30字）
2. 列出3-5个当前需关注的风险因素
3. 写一段2-3句话的整体建议

输出JSON格式，只输出JSON：
{
    "equity_rec": "权益配置建议",
    "bond_rec": "债券配置建议",
    "commodity_rec": "商品配置建议",
    "risk_factors": ["风险1", "风险2", "风险3"],
    "overall_recommendation": "2-3句话整体建议"
}"""

        pe_str = f"TTM PE={computed['cs300_pe']}" if computed.get('cs300_pe') else "PE数据暂缺"
        pe_pct_str = computed.get('cs300_pe_percentile', '历史分位数据暂缺')

        user_prompt = f"""已计算的量化指标：
- 权益（沪深300）：年化收益 {computed['equity_return']*100:.1f}%，年化波动率 {computed['equity_vol']*100:.1f}%，最大回撤 {computed['equity_max_dd']*100:.1f}%
- 权益估值：{pe_str}（{pe_pct_str}）
- 股权风险溢价(ERP)：{computed['erp']*100:.1f}%（{('有吸引力' if computed['erp'] > 0.06 else '正常' if computed['erp'] > 0.03 else '偏低')}）
- 债券：10年国债收益率 {computed['bond_yield']:.2f}%
- 商品：暂无实时量化数据

请基于以上真实数据生成定性分析JSON。"""

        try:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            response = await self.llm.ainvoke(messages)
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            content = content.strip()
            import json
            result = json.loads(content)
            return result
        except Exception as e:
            logger.warning(f"LLM qualitative analysis failed: {e}")
            return {
                "equity_rec": "适度配置，关注估值水平",
                "bond_rec": "作为稳健配置底仓",
                "commodity_rec": "少量配置对冲风险",
                "risk_factors": ["市场波动风险", "利率风险", "地缘政治风险"],
                "overall_recommendation": "当前市场估值处于合理区间，建议均衡配置，股债比例根据个人风险偏好确定。"
            }
