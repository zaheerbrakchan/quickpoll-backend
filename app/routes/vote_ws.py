# app/routes/vote_ws.py
import os
import json
import asyncio
import redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app import models

from dotenv import load_dotenv

router = APIRouter()

# ---------------------------
# Config
# ---------------------------
REDIS_URL = os.getenv("REDIS_URL")
redis_client = None
active_connections = {}  # in-memory fallback

# ---------------------------
# Redis Connection Helper
# ---------------------------
async def get_redis():
    global redis_client
    if not redis_client:
        try:
            redis_client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            print(f"✅ Connected to Redis: {REDIS_URL}")
        except Exception as e:
            print(f"⚠️ Redis connection failed ({e}), using in-memory fallback")
            redis_client = None
    return redis_client

# ---------------------------
# Broadcast Vote Update
# ---------------------------
async def broadcast_vote_update(poll_id: str, db: Session):
    options = (
        db.query(models.Option.id, models.Option.text)
        .filter(models.Option.poll_id == poll_id)
        .all()
    )

    payload = []
    for opt in options:
        count = db.query(models.Vote).filter(models.Vote.option_id == opt.id).count()
        payload.append({"id": str(opt.id), "text": opt.text, "votes": count})

    redis = await get_redis()

    if redis:
        # ✅ Publish to Redis channel
        await redis.publish(f"poll:{poll_id}", json.dumps(payload))
        print(f"📢 Published to Redis for poll {poll_id}")
    else:
        # 🔁 Local fallback
        if poll_id in active_connections:
            for ws in active_connections[poll_id]:
                try:
                    await ws.send_json({"poll_id": poll_id, "options": payload})
                    print(f"✅ Sent update directly to a client (no Redis)")
                except Exception as e:
                    print(f"⚠️ Failed to send update: {e}")

# ---------------------------
# WebSocket Handler
# ---------------------------
@router.websocket("/ws/polls/{poll_id}")
async def websocket_poll_updates(websocket: WebSocket, poll_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    print(f"🔗 WebSocket connected for poll {poll_id}")

    # Add to local active connections
    if poll_id not in active_connections:
        active_connections[poll_id] = []
    active_connections[poll_id].append(websocket)

    redis = await get_redis()

    if redis:
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"poll:{poll_id}")
        print(f"✅ Subscribed to Redis channel poll:{poll_id}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json({"poll_id": poll_id, "options": data})
        except WebSocketDisconnect:
            print(f"❌ WebSocket disconnected for poll {poll_id}")
        finally:
            await pubsub.unsubscribe(f"poll:{poll_id}")
    else:
        # Local-only loop (fallback)
        try:
            while True:
                await asyncio.sleep(15)
        except WebSocketDisconnect:
            print(f"❌ WebSocket disconnected for poll {poll_id}")

    # Cleanup
    active_connections[poll_id].remove(websocket)
    if not active_connections[poll_id]:
        del active_connections[poll_id]
