from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models, schemas
from app.utils.dependencies import get_current_user

import asyncio
import json

from app.routes.polls_ws import get_redis

router = APIRouter()


# ---------------------------
# Create Poll
# ---------------------------
@router.post("/", response_model=schemas.Poll)
async def create_poll(
    poll: schemas.PollCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_poll = models.Poll(
        title=poll.title,
        description=poll.description,
        likes_count=0,  # ✅ default for new poll
        created_by=current_user.username,
    )
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)

    # Add options
    for opt in poll.options:
        db_option = models.Option(text=opt.text, poll_id=db_poll.id)
        db.add(db_option)
    db.commit()
    db.refresh(db_poll)

    # ✅ Return normalized poll data for frontend
    poll_data = {
        "type": "new_poll",
        "id": str(db_poll.id),
        "title": db_poll.title,
        "description": db_poll.description,
        "created_at": db_poll.created_at.isoformat() if isinstance(db_poll.created_at, datetime) else str(db_poll.created_at),
        "created_by": db_poll.created_by,
        "likes_count": db_poll.likes_count or 0,
        "options": [
            {"id": str(o.id), "poll_id": str(o.poll_id), "text": o.text, "votes": 0}
            for o in db_poll.options
        ],
    }

    # Broadcast to global WS channel
    redis_conn = await get_redis()
    if redis_conn:
        await redis_conn.publish("polls:global", json.dumps(poll_data,default=str))
        print("📡 Broadcasted new poll to Redis global channel")

    return poll_data


# ---------------------------
# Delete Poll
# ---------------------------
@router.delete("/{poll_id}")
async def delete_poll(
    poll_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 🔍 1️⃣ Find the poll
    db_poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not db_poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    # 🔐 2️⃣ Verify ownership
    if db_poll.created_by != current_user.username:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this poll")

    # 🧹 3️⃣ Delete related options first (due to FK constraints)
    db.query(models.Option).filter(models.Option.poll_id == poll_id).delete()

    # 4️⃣ Delete the poll itself
    db.delete(db_poll)
    db.commit()

    # 📡 5️⃣ Broadcast the deletion to all connected clients
    poll_data = {
        "type": "poll_deleted",
        "poll_id": str(poll_id),
    }

    redis_conn = await get_redis()
    if redis_conn:
        await redis_conn.publish("polls:global", json.dumps(poll_data, default=str))
        print(f"📡 Broadcasted poll_deleted for Poll ID {poll_id}")

    return {"message": "Poll deleted successfully", "poll_id": poll_id}



# ---------------------------
# Get All Polls (with votes)
# ---------------------------
@router.get("/", response_model=list[schemas.Poll])
def get_polls(db: Session = Depends(get_db)):
    polls = db.query(models.Poll).all()
    result = []

    for poll in polls:
        options_data = []
        for opt in poll.options:
            vote_count = db.query(models.Vote).filter(models.Vote.option_id == opt.id).count()
            options_data.append({
                "id": opt.id,
                "poll_id": opt.poll_id,
                "text": opt.text,
                "votes": vote_count,
            })

        # ✅ Recalculate likes live from Like table
        like_count = db.query(models.Like).filter(models.Like.poll_id == poll.id).count()

        poll_data = {
            "id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "created_at": poll.created_at,
            "created_by": poll.created_by,
            "likes_count": like_count,
            "options": options_data,
        }
        result.append(poll_data)

    return result


# ---------------------------
# Get Single Poll (with votes)
# ---------------------------
@router.get("/{poll_id}", response_model=schemas.Poll)
def get_poll(poll_id: str, db: Session = Depends(get_db)):
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    options_data = []
    for opt in poll.options:
        vote_count = db.query(models.Vote).filter(models.Vote.option_id == opt.id).count()
        options_data.append({
            "id": opt.id,
            "poll_id": opt.poll_id,
            "text": opt.text,
            "votes": vote_count,
        })

    like_count = db.query(models.Like).filter(models.Like.poll_id == poll.id).count()

    poll_data = {
        "id": poll.id,
        "title": poll.title,
        "description": poll.description,
        "created_at": poll.created_at,
        "created_by": poll.created_by,
        "likes_count": like_count,
        "options": options_data,
    }

    return poll_data
