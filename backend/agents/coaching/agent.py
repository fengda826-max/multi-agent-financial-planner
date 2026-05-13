from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from shared.config import get_settings

settings = get_settings()


class CoachingAgent:
    """陪伴督导Agent - 用户交互、纠偏、心理按摩"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-v4-pro",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.7
        )

    async def generate_response(self, context: str, user_message: str = None, event_type: str = None) -> Dict[str, Any]:
        """生成督导响应"""

        system_prompt = """你是一个温暖、专业的理财督导助手。你的职责是：
1. 帮助用户理解他们的资产配置方案
2. 在市场波动时安抚用户情绪
3. 当用户偏离配置方案时温和提醒
4. 定期关心用户，了解他们的近况

你的沟通风格：
- 温暖、有同理心
- 用简单易懂的语言解释专业概念
- 强调长期投资的重要性
- 不做具体的产品推荐

输出格式（JSON）：
{
    "message": "给用户的消息",
    "action": "none/followup/replan",
    "replan_trigger": "如果需要重规划，说明原因"
}"""

        if event_type:
            user_prompt = f"""事件类型：{event_type}
用户当前状态：{context}

请生成督导响应。"""
        else:
            user_prompt = f"""用户消息：{user_message}
用户当前状态：{context}

请生成督导响应。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)

        import json
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            result = {
                "message": response.content,
                "action": "none",
                "replan_trigger": None
            }

        return result

    async def handle_market_anomaly(self, user_id: str, event_detail: Dict[str, Any]) -> Dict[str, Any]:
        """处理市场异动事件"""
        context = f"用户ID: {user_id}\n市场异动: {event_detail}"
        return await self.generate_response(context, event_type="market_anomaly")

    async def handle_user_deviation(self, user_id: str, deviation_detail: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户偏离事件"""
        context = f"用户ID: {user_id}\n偏离情况: {deviation_detail}"
        return await self.generate_response(context, event_type="user_deviation")
