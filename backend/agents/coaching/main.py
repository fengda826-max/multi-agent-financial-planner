import os
import asyncio
import json
import aio_pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from uuid import UUID
from agents.coaching.agent import CoachingAgent

app = FastAPI(title="Coaching Agent")
agent = CoachingAgent()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


class CoachingRequest(BaseModel):
    user_id: str
    context: str
    strategy: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class CoachingResponse(BaseModel):
    message: str
    action: str
    replan_trigger: Optional[str] = None


@app.post("/interact", response_model=CoachingResponse)
async def interact(request: CoachingRequest):
    try:
        result = await agent.generate_response(
            context=request.context,
            user_message=request.user_message,
            conversation_history=request.conversation_history
        )
        return CoachingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/event/market-anomaly", response_model=CoachingResponse)
async def handle_market_anomaly(user_id: UUID, event_detail: Dict[str, Any]):
    try:
        result = await agent.handle_market_anomaly(str(user_id), event_detail)
        return CoachingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/event/user-deviation", response_model=CoachingResponse)
async def handle_user_deviation(user_id: UUID, deviation_detail: Dict[str, Any]):
    try:
        result = await agent.handle_user_deviation(str(user_id), deviation_detail)
        return CoachingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "coaching"}


async def start_rabbitmq_consumer():
    """启动 RabbitMQ 消费者，监听市场异动和用户偏离事件"""
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    market_exchange = await channel.declare_exchange(
        "market_events", aio_pika.ExchangeType.TOPIC, durable=True
    )
    market_queue = await channel.declare_queue("coaching.market", durable=True)
    await market_queue.bind(market_exchange, routing_key="market.anomaly.*")

    user_exchange = await channel.declare_exchange(
        "user_events", aio_pika.ExchangeType.TOPIC, durable=True
    )
    user_queue = await channel.declare_queue("coaching.user", durable=True)
    await user_queue.bind(user_exchange, routing_key="user.deviation.*")

    async def process_market_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(message.body.decode())
            print(f"Received market event: {body['event_type']}")

    async def process_user_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(message.body.decode())
            user_id = body.get("user_id")
            if user_id:
                await agent.handle_user_deviation(user_id, body.get("detail", {}))
                print(f"Processed user deviation for {user_id}")

    await market_queue.consume(process_market_message)
    await user_queue.consume(process_user_message)
    print("Coaching Agent RabbitMQ consumer started")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_rabbitmq_consumer())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
