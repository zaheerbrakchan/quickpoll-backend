from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
import asyncio

router = APIRouter()

active_connections = {}

async def broadcast_vote_update(poll_id: str, db: Session):
    options = (
        db.query(models.Option.id, models.Option.text)
        .filter(models.Option.poll_id == poll_id)
        .all()
    )

    payload = []
    for opt in options:
        count = db.query(models.Vote).filter(models.Vote.option_id == opt.id).count()
        payload.append({"id": opt.id, "text": opt.text, "votes": count})

    if poll_id in active_connections:
        for ws in active_connections[poll_id]:
            try:
                await ws.send_json({"poll_id": poll_id, "options": payload})
            except:
                pass  # ignore broken sockets


@router.websocket("/ws/polls/{poll_id}")
async def websocket_poll_updates(websocket: WebSocket, poll_id: str, db: Session = Depends(get_db)):
    await websocket.accept()

    if poll_id not in active_connections:
        active_connections[poll_id] = []
    active_connections[poll_id].append(websocket)

    try:
        while True:
            # 🔄 keep connection alive, no need to receive anything
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        active_connections[poll_id].remove(websocket)
        if not active_connections[poll_id]:
            del active_connections[poll_id]
