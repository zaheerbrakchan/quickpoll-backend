import os
import asyncio
import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app import models

router = APIRouter()

# ---------------------------
# Redis setup
# ---------------------------
REDIS_URL = os.getenv("REDIS_URL")
redis_client = None
active_connections = {}  # in-memory fallback


async def get_redis():
    """Return a global async Redis connection, or None if unavailable."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await redis_client.ping()
            print(f"✅ Connected to Redis: {REDIS_URL}")
        except Exception as e:
            print(f"⚠️ Redis connection failed ({e}), using in-memory fallback")
            redis_client = None
    return redis_client


# ---------------------------
# Broadcast vote updates
# ---------------------------
async def broadcast_vote_update(poll_id: str, db: Session):
    """Send updated vote counts to all WebSocket clients."""
    options = (
        db.query(models.Option.id, models.Option.text)
        .filter(models.Option.poll_id == poll_id)
        .all()
    )

    payload = []
    for opt in options:
        count = db.query(models.Vote).filter(models.Vote.option_id == opt.id).count()
        payload.append({"id": opt.id, "text": opt.text, "votes": count})

    redis_conn = await get_redis()
    if redis_conn:
        # Publish to Redis channel
        await redis_conn.publish(f"poll:{poll_id}", str(payload))
        print(f"📡 Published update to Redis for poll {poll_id}")
    else:
        # Fallback: send directly to local WebSocket clients
        if poll_id in active_connections:
            for ws in active_connections[poll_id]:
                try:
                    await ws.send_json({"poll_id": poll_id, "options": payload})
                except Exception as e:
                    print(f"⚠️ Failed to send WS update: {e}")


# ---------------------------
# WebSocket endpoint
# ---------------------------
@router.websocket("/ws/polls/{poll_id}")
async def websocket_poll_updates(websocket: WebSocket, poll_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    print(f"🔗 WebSocket connected for poll {poll_id}")

    # Always add to local list (for fallback use)
    if poll_id not in active_connections:
        active_connections[poll_id] = []
    active_connections[poll_id].append(websocket)

    redis_conn = await get_redis()

    # If Redis available, subscribe to channel
    pubsub = None
    if redis_conn:
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe(f"poll:{poll_id}")
        print(f"✅ Subscribed to Redis channel poll:{poll_id}")

    try:
        if pubsub:
            # Listen for Redis messages
            async for message in pubsub.listen():
                if message is None or message["type"] != "message":
                    continue
                data = eval(message["data"])  # Because we sent str(payload)
                await websocket.send_json({"poll_id": poll_id, "options": data})
        else:
            # Fallback: keep connection alive (manual broadcast handled locally)
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
