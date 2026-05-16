from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from shared.config import get_settings

settings = get_settings()


class UserProfileAgent:
    """用户画像Agent - 确定性计算画像指标，LLM仅生成文案"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-v4-pro",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.3
        )

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户数据，生成画像。
        画像指标由确定性公式计算，LLM只生成自然语言文案。"""

        has_assets = user_data.get('investable_assets') is not None

        # 1. 确定性计算所有画像指标
        metrics = self._compute_profile_metrics(user_data)

        # 2. LLM 只生成文案（基于已计算的指标）
        summary = await self._generate_narrative(user_data, metrics)

        result = {
            **metrics,
            **summary,
            "needs_followup": False,
            "followup_questions": [],
        }

        if has_assets:
            result["needs_followup"] = False
            result["followup_questions"] = []

        return result

    def _compute_profile_metrics(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """确定性计算所有画像指标"""

        age = user_data.get('age', 30)
        income = user_data.get('income', 0)
        expenses = user_data.get('expenses', 0)
        risk_tolerance = user_data.get('risk_tolerance', 'moderate')
        investable = user_data.get('investable_assets', 0) or 0
        monthly_surplus = income - expenses
        savings_rate = round(monthly_surplus / income * 100, 1) if income > 0 else 0
        emergency_months = round(investable / expenses, 1) if expenses > 0 else 0
        total_savings = user_data.get('total_savings') or investable
        monthly_debt = user_data.get('monthly_debt', 0) or 0
        has_insurance = user_data.get('has_insurance', False)
        investment_horizon = user_data.get('investment_horizon', '5y')

        # === 1. 生命周期阶段（确定性规则） ===
        if age < 35:
            lifecycle_stage = "accumulation"
            lifecycle_explanation = "您处于财富积累期，收入增长空间大，可以承担较高风险获取长期复利。"
        elif age < 50:
            lifecycle_stage = "consolidation"
            lifecycle_explanation = "您处于财富巩固期，需在资产增值和风险控制之间取得平衡，逐步增加稳健类配置。"
        else:
            lifecycle_stage = "distribution"
            lifecycle_explanation = "您处于财富分配期，资产保值与现金流管理是核心目标，应降低高风险资产比例。"

        # === 2. 风险承受能力（确定性映射） ===
        risk_capacity_map = {"conservative": "low", "moderate": "medium", "aggressive": "high"}
        risk_capacity = risk_capacity_map.get(risk_tolerance, "medium")
        risk_explanations = {
            "low": f"您选择了保守型偏好，风险承受能力较低（评分{user_data.get('risk_score', '-')}分），建议以稳健类产品为主。",
            "medium": f"您选择了稳健型偏好，具备中等风险承受能力（评分{user_data.get('risk_score', '-')}分），可适度配置权益类资产。",
            "high": f"您选择了进取型偏好，有较高风险承受意愿（评分{user_data.get('risk_score', '-')}分），可加大成长型资产配置。",
        }

        # === 3. 投资风格（风险+年龄组合） ===
        age_bracket = "young" if age < 35 else ("mature" if age < 50 else "senior")
        style_map = {
            ("low", "young"): "保守稳健型",
            ("low", "mature"): "稳健保值型",
            ("low", "senior"): "保守保值型",
            ("medium", "young"): "平衡成长型",
            ("medium", "mature"): "稳健收益型",
            ("medium", "senior"): "保守收益型",
            ("high", "young"): "积极进取型",
            ("high", "mature"): "成长导向型",
            ("high", "senior"): "均衡配置型",
        }
        investment_style = style_map.get((risk_capacity, age_bracket), "均衡型投资者")

        # === 4. 财务健康评分（0-100，4维度公式） ===
        savings_score = min(savings_rate * 0.8, 30)  # 储蓄力 0-30分
        if emergency_months >= 6:
            emergency_score = 30
        elif emergency_months >= 3:
            emergency_score = 20
        elif emergency_months >= 1:
            emergency_score = 10
        else:
            emergency_score = 0  # 应急力 0-30分

        invest_score = 20 if investment_horizon in ('5y', '10y+') else (15 if investment_horizon == '3y' else 10)
        protection_score = 20 if has_insurance else 10  # 保障力 0-20分

        financial_health_score = int(round(savings_score + emergency_score + invest_score + protection_score))

        # 财务健康评语
        if financial_health_score >= 85:
            health_comment = f"财务状况优秀（{financial_health_score}分），储蓄率{savings_rate}%，应急储备{emergency_months}个月。"
        elif financial_health_score >= 70:
            health_comment = f"财务状况良好（{financial_health_score}分），建议继续提高储蓄率和应急储备。"
        elif financial_health_score >= 55:
            health_comment = f"财务状况一般（{financial_health_score}分），需要加强储蓄和保障规划。"
        else:
            health_comment = f"财务基础薄弱（{financial_health_score}分），建议优先建立应急金和基础保障。"

        # === 5. 优劣势（数据触发规则） ===
        strengths = []
        weaknesses = []

        if savings_rate >= 30:
            strengths.append(f"储蓄率良好（{savings_rate}%），财务纪律性强")
        elif savings_rate < 15:
            weaknesses.append(f"储蓄率偏低（{savings_rate}%），建议控制支出提高结余")

        if emergency_months >= 6:
            strengths.append(f"应急储备充足（覆盖{emergency_months}个月支出）")
        elif emergency_months < 3:
            weaknesses.append(f"应急储备不足（仅覆盖{emergency_months}个月），建议优先建立3-6个月应急金")

        if age < 35:
            strengths.append("投资期限长，可承受短期波动获取长期复利收益")
        elif age >= 50:
            weaknesses.append("接近退休年龄，需逐步降低高风险资产配置比例")

        if monthly_surplus >= 5000:
            strengths.append(f"月结余充裕（¥{monthly_surplus:,.0f}），投资本金积累能力强")
        elif monthly_surplus <= 0:
            weaknesses.append("月收支为负，需要立刻优化支出结构")

        if monthly_debt > 0:
            debt_ratio = round(monthly_debt / income * 100, 1) if income > 0 else 0
            if debt_ratio > 40:
                weaknesses.append(f"负债率偏高（{debt_ratio}%），建议优先偿还高息债务")
            elif debt_ratio > 0:
                strengths.append(f"负债可控（{debt_ratio}%），还贷能力良好" if debt_ratio < 20 else f"负债率{debt_ratio}%，尚在合理范围")

        if has_insurance:
            strengths.append("已配置保险保障，风险兜底意识好")
        else:
            weaknesses.append("未配置保险保障，建议补充重疾险和医疗险以防范因病返贫")

        # === 6. 画像总结（模板生成） ===
        profile_summary = (
            f"{age}岁，{lifecycle_explanation} "
            f"月收入¥{income:,.0f}，月结余¥{monthly_surplus:,.0f}（储蓄率{savings_rate}%），"
            f"可投资资产约¥{investable:,.0f}。"
            f"风险偏好{risk_tolerance}，投资期限{investment_horizon}，"
            f"财务健康评分{financial_health_score}分。"
        )

        return {
            "lifecycle_stage": lifecycle_stage,
            "lifecycle_explanation": lifecycle_explanation,
            "risk_capacity": risk_capacity,
            "risk_explanation": risk_explanations.get(risk_capacity, ""),
            "investment_style": investment_style,
            "financial_health_score": financial_health_score,
            "financial_health_comment": health_comment,
            "health_score_breakdown": {
                "savings": {"score": round(savings_score), "label": "储蓄力", "detail": f"储蓄率{savings_rate}%"},
                "emergency": {"score": emergency_score, "label": "应急力", "detail": f"应急储备{emergency_months}个月"},
                "investment": {"score": invest_score, "label": "投资力", "detail": f"投资期限{investment_horizon}"},
                "protection": {"score": protection_score, "label": "保障力", "detail": "已配置保险" if has_insurance else "未配置保险"},
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "profile_summary": profile_summary,
            "investable_assets": investable,
            "monthly_surplus": monthly_surplus,
            "savings_rate": savings_rate,
            "emergency_months": emergency_months,
            "debt_to_income": round(monthly_debt / income * 100, 1) if income > 0 and monthly_debt > 0 else 0,
        }

    async def _generate_narrative(self, user_data: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, str]:
        """LLM 仅生成叙事性文案（基于已计算的真实指标）"""

        system_prompt = """你是一个专业的理财规划师。基于已经计算好的财务指标，用温暖专业的语言为用户生成画像总结。

注意：所有数字指标已经计算完毕，你只负责用自然语言写一段2-3句话的总结。
不要编造新的数字，不要给出具体的投资建议。只做客观描述。"""

        user_prompt = f"""用户基本信息：
- 年龄：{user_data.get('age')}岁
- 生命周期阶段：{metrics['lifecycle_stage']}（{metrics['lifecycle_explanation']}）
- 风险承受能力：{metrics['risk_capacity']}（{metrics['risk_explanation']}）
- 投资风格：{metrics['investment_style']}
- 财务健康评分：{metrics['financial_health_score']}分
- 月收入：¥{user_data.get('income', 0):,}，月支出：¥{user_data.get('expenses', 0):,}
- 月结余：¥{metrics['monthly_surplus']:,}（储蓄率{metrics['savings_rate']}%）
- 可投资资产：¥{metrics['investable_assets']:,}
- 优势：{', '.join(metrics['strengths']) if metrics['strengths'] else '无'}
- 需要注意：{', '.join(metrics['weaknesses']) if metrics['weaknesses'] else '无'}

请用2-3句温暖专业的话总结这个用户的财务状况。不要编造任何新数字。

只输出纯文本，不要JSON。"""

        try:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            response = await self.llm.ainvoke(messages)
            narrative = response.content.strip()
            # 清理可能的JSON标记
            narrative = narrative.replace("```json", "").replace("```", "").strip()
            return {"profile_summary": narrative if len(narrative) > 20 else metrics['profile_summary']}
        except Exception:
            return {"profile_summary": metrics['profile_summary']}
