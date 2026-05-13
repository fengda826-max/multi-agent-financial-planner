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

        growth_allocation = strategy["four_buckets"]["growth_money"]["allocation"]
        if growth_allocation > rules["max_equity_allocation"]:
            excess = growth_allocation - rules["max_equity_allocation"]
            strategy["four_buckets"]["growth_money"]["allocation"] = rules["max_equity_allocation"]
            strategy["four_buckets"]["stable_money"]["allocation"] += excess

        return strategy
