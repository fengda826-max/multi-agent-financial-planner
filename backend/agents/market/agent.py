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
