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

        import json
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            result = self._default_analysis(user_data)

        return result

    def _default_analysis(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """默认分析逻辑（当LLM返回异常时使用）"""
        age = user_data.get('age', 30)
        risk_tolerance = user_data.get('risk_tolerance', 'moderate')

        if age < 35:
            lifecycle_stage = "accumulation"
        elif age < 50:
            lifecycle_stage = "consolidation"
        else:
            lifecycle_stage = "distribution"

        risk_capacity_map = {
            "conservative": "low",
            "moderate": "medium",
            "aggressive": "high"
        }
        risk_capacity = risk_capacity_map.get(risk_tolerance, "medium")

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
