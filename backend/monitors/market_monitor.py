import asyncio
from datetime import datetime
from typing import Dict, Any
import aio_pika
import json
from shared.config import get_settings
from shared.redis_client import get_redis

settings = get_settings()


class MarketMonitor:
    """市场异动监控"""

    def __init__(self):
        self.check_interval = 300  # 5分钟检查一次
        self.thresholds = {
            "index_drop": -0.03,  # 指数跌幅超过3%
            "index_surge": 0.05,  # 指数涨幅超过5%
            "rate_change": 0.25,  # 利率变化超过25bp
        }

    async def check_market_anomaly(self) -> list:
        """检查市场异动"""
        anomalies = []

        try:
            redis = await get_redis()

            market_data = await redis.get("market:latest")
            if market_data:
                data = json.loads(market_data)

                for index_name, index_data in data.items():
                    if isinstance(index_data, dict):
                        change = index_data.get("daily_change", 0)
                        if change <= self.thresholds["index_drop"]:
                            anomalies.append({
                                "type": "market.anomaly.index_drop",
                                "detail": {
                                    "index": index_name,
                                    "change": change,
                                    "threshold": self.thresholds["index_drop"]
                                }
                            })
                        elif change >= self.thresholds["index_surge"]:
                            anomalies.append({
                                "type": "market.anomaly.index_surge",
                                "detail": {
                                    "index": index_name,
                                    "change": change,
                                    "threshold": self.thresholds["index_surge"]
                                }
                            })

        except Exception as e:
            print(f"Market check error: {e}")

        return anomalies

    async def publish_anomaly(self, anomaly: Dict[str, Any]):
        """发布异动事件到RabbitMQ"""
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "market_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            message = {
                "event_type": anomaly["type"],
                "detail": anomaly["detail"],
                "timestamp": datetime.utcnow().isoformat()
            }

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=anomaly["type"]
            )

    async def run(self):
        """运行监控循环"""
        print("Market Monitor started")
        while True:
            try:
                anomalies = await self.check_market_anomaly()
                for anomaly in anomalies:
                    await self.publish_anomaly(anomaly)
                    print(f"Published anomaly: {anomaly['type']}")
            except Exception as e:
                print(f"Monitor error: {e}")

            await asyncio.sleep(self.check_interval)


async def main():
    monitor = MarketMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
