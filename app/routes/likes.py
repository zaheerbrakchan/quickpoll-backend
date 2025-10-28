# app/routes/likes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from app.db import get_db
from app import models
from app.utils.dependencies import get_current_user
from app.routes.polls_ws import broadcast_like_update

router = APIRouter(tags=["Likes"])


@router.post("/{poll_id}", response_model=dict)
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
        db.delete(existing_like)
        poll.likes_count = max(0, (poll.likes_count or 0) - 1)
        like_status = False
    else:
        new_like = models.Like(id=str(uuid4()), poll_id=poll_id, user_id=current_user.id)
        db.add(new_like)
        poll.likes_count = (poll.likes_count or 0) + 1
        like_status = True

    db.commit()
    db.refresh(poll)

    try:
        await broadcast_like_update(poll_id, db)
    except Exception as e:
        print(f"WS broadcast error: {e}")

    return {"liked": like_status, "likes": poll.likes_count}


@router.get("/user/{poll_id}", response_model=dict)
def get_user_like(
    poll_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    liked = (
        db.query(models.Like)
        .filter(models.Like.poll_id == poll_id, models.Like.user_id == current_user.id)
        .first()
        is not None
    )

    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    likes_count = poll.likes_count if poll else 0

    return {"liked": liked, "likes": likes_count}
