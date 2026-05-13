import json

import aio_pika
from shared.config import get_settings


settings = get_settings()


async def get_rabbitmq_connection() -> aio_pika.RobustConnection:
    return await aio_pika.connect_robust(settings.rabbitmq_url)


async def publish_message(exchange_name: str, routing_key: str, message: dict):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        body = json.dumps(message).encode()
        await exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=routing_key,
        )


async def consume_messages(exchange_name: str, routing_key: str, queue_name: str, callback):
    # This connection is intentionally kept open for the lifetime of the consumer.
    # To stop consuming, cancel the consuming task and call `await connection.close()`.
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.bind(exchange, routing_key=routing_key)
    await queue.consume(callback)
    return connection
