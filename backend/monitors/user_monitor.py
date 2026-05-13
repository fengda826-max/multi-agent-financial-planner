import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import aio_pika
import json
from shared.config import get_settings
from shared.database import async_session
from shared.models.portfolio import Portfolio
from shared.models.profile import UserProfile
from sqlalchemy import select

settings = get_settings()


class UserMonitor:
    """用户偏离监控 - 检测用户资产配置偏离"""

    def __init__(self):
        self.check_interval = 3600  # 1小时检查一次
        self.drift_threshold = 0.10  # 偏离阈值 10%

    async def check_user_drift(self) -> List[Dict[str, Any]]:
        """检查用户资产偏离情况"""
        drifts = []

        try:
            async with async_session() as session:
                result = await session.execute(
                    select(Portfolio).where(Portfolio.status == "active")
                )
                portfolios = result.scalars().all()

                for portfolio in portfolios:
                    if portfolio.updated_at:
                        days_since_update = (datetime.utcnow() - portfolio.updated_at).days
                        if days_since_update > 90:
                            drifts.append({
                                "type": "user.deviation.inactivity",
                                "user_id": str(portfolio.user_id),
                                "detail": {
                                    "portfolio_id": str(portfolio.id),
                                    "days_since_update": days_since_update,
                                    "message": "用户超过3个月未更新配置"
                                }
                            })

        except Exception as e:
            print(f"User drift check error: {e}")

        return drifts

    async def publish_drift(self, drift: Dict[str, Any]):
        """发布偏离事件到RabbitMQ"""
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "user_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            message = {
                "event_type": drift["type"],
                "user_id": drift["user_id"],
                "detail": drift["detail"],
                "timestamp": datetime.utcnow().isoformat()
            }

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=drift["type"]
            )

    async def run(self):
        """运行监控循环"""
        print("User Monitor started")
        while True:
            try:
                drifts = await self.check_user_drift()
                for drift in drifts:
                    await self.publish_drift(drift)
                    print(f"Published user drift: {drift['type']} for user {drift['user_id']}")
            except Exception as e:
                print(f"User Monitor error: {e}")

            await asyncio.sleep(self.check_interval)


async def main():
    monitor = UserMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
