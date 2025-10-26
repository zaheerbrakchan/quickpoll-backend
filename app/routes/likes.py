# app/routes/likes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models, schemas
from app.utils.dependencies import get_current_user  # updated import

router = APIRouter()


# ---------------------------
# Like Poll (Simple Counter Version)
# ---------------------------
@router.post("/", response_model=schemas.LikeUpdate)
def like_poll(
    like: schemas.LikeUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    poll = db.query(models.Poll).filter(models.Poll.id == like.poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    # Increment like count
    poll.likes += 1
    db.commit()
    db.refresh(poll)
    return like
