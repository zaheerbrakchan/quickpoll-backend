import os
import asyncio
import json
import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.db import SessionLocal, get_db
from app import models

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL")
redis_client = None
active_connections = {}  # in-memory fallback


# ---------------------------
# Redis setup
# ---------------------------
async def get_redis():
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await redis_client.ping()
            print(f"✅ Connected to Redis: {REDIS_URL}")
        except Exception as e:
            print(f"⚠️ Redis connection failed ({e}), using in-memory fallback")
            redis_client = None
    return redis_client


# ---------------------------
# Broadcast vote updates
# ---------------------------
async def broadcast_vote_update(poll_id: str):
    """Send updated vote counts to all WebSocket clients."""
    db = SessionLocal()
    try:
        options = (
            db.query(models.Option.id, models.Option.text)
            .filter(models.Option.poll_id == poll_id)
            .all()
        )

        payload = []
        for opt in options:
            count = db.query(models.Vote).filter(models.Vote.option_id == opt.id).count()
            payload.append({"id": str(opt.id), "text": opt.text, "votes": count})

        message = {"poll_id": str(poll_id), "options": payload}

        redis_conn = await get_redis()
        if redis_conn:
            await redis_conn.publish(f"poll:{poll_id}", json.dumps(message))
            print(f"📡 Published update to Redis for poll {poll_id}")
        else:
            if poll_id in active_connections:
                for ws in active_connections[poll_id]:
                    try:
                        await ws.send_json(message)
                    except Exception as e:
                        print(f"⚠️ Failed to send WS update: {e}")
    finally:
        db.close()  # ✅ ensure session released


# ---------------------------
# Broadcast like updates
# ---------------------------
async def broadcast_like_update(poll_id: str):
    """Send updated like count to all WebSocket clients for this poll."""
    db = SessionLocal()
    try:
        poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
        if not poll:
            return

        message = {
            "type": "like_update",
            "poll_id": str(poll_id),
            "likes": poll.likes_count or 0,
        }

        redis_conn = await get_redis()
        if redis_conn:
            await redis_conn.publish(f"poll:{poll_id}", json.dumps(message))
            print(f"❤️ Published like update to Redis for poll {poll_id}")
        else:
            if poll_id in active_connections:
                for ws in active_connections[poll_id]:
                    try:
                        await ws.send_json(message)
                    except Exception as e:
                        print(f"⚠️ Failed to send WS like update: {e}")
    finally:
        db.close()  # ✅ ensure session released


# ---------------------------
# Global WebSocket endpoint (new poll broadcast)
# ---------------------------
@router.websocket("/ws/polls")
async def websocket_all_polls(websocket: WebSocket):
    await websocket.accept()
    print("🌍 Global Poll WebSocket connected")

    redis_conn = await get_redis()
    pubsub = None

    if redis_conn:
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe("polls:global")
        print("✅ Subscribed to Redis channel polls:global")

    try:
        if pubsub:
            async for message in pubsub.listen():
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
        else:
            while True:
                await asyncio.sleep(15)
    except WebSocketDisconnect:
        print("❌ Global Poll WebSocket disconnected")
        if pubsub:
            await pubsub.unsubscribe("polls:global")
            await pubsub.close()


# ---------------------------
# Per-poll WebSocket endpoint
# ---------------------------
@router.websocket("/ws/polls/{poll_id}")
async def websocket_poll_updates(websocket: WebSocket, poll_id: str):
    await websocket.accept()
    print(f"🔗 WebSocket connected for poll {poll_id}")

    # Immediately send latest state
    await broadcast_vote_update(poll_id)
    await broadcast_like_update(poll_id)

    if poll_id not in active_connections:
        active_connections[poll_id] = []
    active_connections[poll_id].append(websocket)

    redis_conn = await get_redis()
    pubsub = None

    if redis_conn:
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe(f"poll:{poll_id}")
        print(f"✅ Subscribed to Redis channel poll:{poll_id}")

    try:
        if pubsub:
            async for message in pubsub.listen():
                if message and message["type"] == "message":
                    await websocket.send_json(json.loads(message["data"]))
        else:
            while True:
                await asyncio.sleep(15)
    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnected for poll {poll_id}")
        active_connections[poll_id].remove(websocket)
        if not active_connections[poll_id]:
            del active_connections[poll_id]
        if pubsub:
            await pubsub.unsubscribe(f"poll:{poll_id}")
            await pubsub.close()
