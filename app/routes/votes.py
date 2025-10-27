# app/routes/votes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models, schemas
from app.utils.dependencies import get_current_user  # updated import

router = APIRouter()


# ---------------------------
# Cast Vote
# ---------------------------
from app.routes.vote_ws import broadcast_vote_update

@router.post("/", response_model=schemas.VoteCreate)
async def cast_vote(
    vote: schemas.VoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # (your existing validation code...)

    db_vote = models.Vote(
        poll_id=vote.poll_id,
        option_id=vote.option_id,
        user_id=current_user.id
    )
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)

    # ✅ Broadcast update
    await broadcast_vote_update(vote.poll_id, db)

    return vote
