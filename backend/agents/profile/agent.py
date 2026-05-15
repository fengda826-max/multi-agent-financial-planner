from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from shared.config import get_settings

settings = get_settings()


class UserProfileAgent:
    """用户画像Agent - 深度分析用户财务数据构建数字画像"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-v4-pro",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.3
        )

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户数据，生成画像"""

        has_assets = user_data.get('investable_assets') is not None
        income = user_data.get('income', 0)
        expenses = user_data.get('expenses', 0)
        monthly_surplus = income - expenses
        savings_rate = round(monthly_surplus / income * 100, 1) if income > 0 else 0

        system_prompt = """你是一个专业的理财规划师。根据用户的财务数据，构建全面的用户投资画像。

你需要输出以下内容（JSON格式）：
{
    "lifecycle_stage": "积累期/巩固期/分配期",
    "lifecycle_explanation": "为什么处于这个阶段（1-2句话）",
    "risk_capacity": "低/中/高",
    "risk_explanation": "风险承受能力的判断依据",
    "investment_style": "用户的投资风格描述（如：稳健偏成长型）",
    "financial_health_score": 85,
    "financial_health_comment": "财务状况简短评价",
    "strengths": ["财务优势1", "财务优势2"],
    "weaknesses": ["需要注意的方面1"],
    "profile_summary": "用户画像总结（2-3句话，温暖专业）",
    "needs_followup": false,
    "followup_questions": []
}

financial_health_score 评分参考：
- 90-100: 收入高、结余率高、有明确投资计划
- 75-89: 财务状况良好，有提升空间
- 60-74: 收支平衡，需加强储蓄和投资
- <60: 需要改善财务基础

重要：
- 如果用户已提供可投资资产信息，needs_followup 必须为 false
- 请用中文回答
- 只输出JSON，不要有其他内容"""

        user_prompt = f"""用户财务数据：
- 年龄：{user_data.get('age')}岁
- 月收入：{income}元
- 月支出：{expenses}元
- 月结余：{monthly_surplus}元（储蓄率 {savings_rate}%）
- 风险偏好：{user_data.get('risk_tolerance')}（conservative=保守/moderate=稳健/aggressive=进取）
- 投资期限：{user_data.get('investment_horizon')}（1y/3y/5y/10y+）
- 可投资资产：{user_data.get('investable_assets', '未提供')}元
- 风险测评得分：{user_data.get('risk_score', '未测评')}
- 风险测评等级：{user_data.get('risk_level', '未测评')}

请输出全面的用户投资画像JSON。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)

        import json
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            content = content.strip()
            result = json.loads(content)
            # 如果已提供资产信息，强制不需要追问
            if has_assets:
                result["needs_followup"] = False
                result["followup_questions"] = []
        except (json.JSONDecodeError, ValueError):
            result = self._default_analysis(user_data)

        return result

    def _default_analysis(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """默认分析逻辑（LLM解析失败时使用）"""
        age = user_data.get('age', 30)
        risk_tolerance = user_data.get('risk_tolerance', 'moderate')
        income = user_data.get('income', 0)
        expenses = user_data.get('expenses', 0)
        monthly_surplus = income - expenses
        savings_rate = round(monthly_surplus / income * 100, 1) if income > 0 else 0

        if age < 35:
            lifecycle_stage = "accumulation"
            lifecycle_explanation = "您处于财富积累期，收入增长空间大，可以承担较高风险获取长期复利。"
        elif age < 50:
            lifecycle_stage = "consolidation"
            lifecycle_explanation = "您处于财富巩固期，需要在资产增值和风险控制之间取得平衡。"
        else:
            lifecycle_stage = "distribution"
            lifecycle_explanation = "您处于财富分配期，资产保值与现金流管理是核心目标。"

        risk_capacity_map = {
            "conservative": "low",
            "moderate": "medium",
            "aggressive": "high"
        }
        risk_capacity = risk_capacity_map.get(risk_tolerance, "medium")
        risk_explanations = {
            "low": "基于您保守的风险偏好，建议以稳健型产品为主。",
            "medium": "您具备中等风险承受能力，可适度配置权益类资产。",
            "high": "您有较高的风险承受意愿，可加大成长型资产配置。"
        }

        if savings_rate >= 50:
            health_score = 90
        elif savings_rate >= 30:
            health_score = 80
        elif savings_rate >= 15:
            health_score = 70
        else:
            health_score = 60

        return {
            "lifecycle_stage": lifecycle_stage,
            "lifecycle_explanation": lifecycle_explanation,
            "risk_capacity": risk_capacity,
            "risk_explanation": risk_explanations.get(risk_capacity, ""),
            "investment_style": f"{"保守" if risk_capacity == 'low' else "稳健" if risk_capacity == 'medium' else "进取"}型投资者",
            "financial_health_score": health_score,
            "financial_health_comment": f"月结余{monthly_surplus}元，储蓄率{savings_rate}%。",
            "strengths": [f"月结余{monthly_surplus}元" if monthly_surplus > 0 else "收支平衡", f"储蓄率{savings_rate}%" if savings_rate > 20 else "建议提高储蓄率"],
            "weaknesses": [f"储蓄率仅{savings_rate}%，建议提升至30%以上" if savings_rate < 30 else "财务指标良好"],
            "profile_summary": f"{age}岁，处于{lifecycle_explanation}",
            "needs_followup": user_data.get('investable_assets') is None,
            "followup_questions": ["您目前有多少可投资资产？"] if user_data.get('investable_assets') is None else []
        }
