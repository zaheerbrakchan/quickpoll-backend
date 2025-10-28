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
    # ✅ Check if user has already voted in this poll
    existing_vote = (
        db.query(models.Vote)
        .join(models.Option)
        .filter(
            models.Option.poll_id == vote.poll_id,
            models.Vote.user_id == current_user.id
        )
        .first()
    )

    if existing_vote:
        raise HTTPException(
            status_code=400,
            detail="You have already voted in this poll."
        )

    # ✅ Create a new vote
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

@router.get("/user/{poll_id}")
def get_user_vote(
    poll_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    existing_vote = (
        db.query(models.Vote)
        .filter(models.Vote.poll_id == poll_id, models.Vote.user_id == current_user.id)
        .first()
    )
    if not existing_vote:
        return {"voted": False}

    return {
        "voted": True,
        "option_id": existing_vote.option_id
    }
