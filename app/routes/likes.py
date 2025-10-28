from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from app.db import get_db
from app import models, schemas
from app.utils.dependencies import get_current_user
from app.routes.vote_ws import broadcast_like_update  # ✅ use your existing ws system

router = APIRouter()

@router.post("/{poll_id}")
async def toggle_like(
    poll_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    existing_like = (
        db.query(models.Like)
        .filter(models.Like.poll_id == poll_id, models.Like.user_id == current_user.id)
        .first()
    )

    if existing_like:
        # Unlike (remove)
        db.delete(existing_like)
        poll.likes = max(0, poll.likes - 1)
        db.commit()
        db.refresh(poll)
        like_status = False
    else:
        # Like (add)
        new_like = models.Like(id=str(uuid4()), poll_id=poll_id, user_id=current_user.id)
        db.add(new_like)
        poll.likes += 1
        db.commit()
        db.refresh(poll)
        like_status = True

    # 🔴 Broadcast like updates (via Redis or in-memory fallback)
    await broadcast_like_update(poll_id, db)

    return {"liked": like_status, "likes": poll.likes}


@router.get("/user/{poll_id}")
def get_user_like(
    poll_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing_like = (
        db.query(models.Like)
        .filter(models.Like.poll_id == poll_id, models.Like.user_id == current_user.id)
        .first()
    )
    return {"liked": bool(existing_like)}
