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
@router.post("/", response_model=schemas.VoteCreate)
def cast_vote(
    vote: schemas.VoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check poll exists
    poll = db.query(models.Poll).filter(models.Poll.id == vote.poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    # Check option belongs to poll
    option = db.query(models.Option).filter(models.Option.id == vote.option_id).first()
    if not option or option.poll_id != vote.poll_id:
        raise HTTPException(status_code=400, detail="Invalid option")

    # Ensure the user has not voted in this poll
    existing_vote = (
        db.query(models.Vote)
        .filter(models.Vote.poll_id == vote.poll_id, models.Vote.user_id == current_user.id)
        .first()
    )
    if existing_vote:
        raise HTTPException(status_code=400, detail="You have already voted in this poll")

    # Create vote
    db_vote = models.Vote(
        poll_id=vote.poll_id,
        option_id=vote.option_id,
        user_id=current_user.id
    )
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)
    return vote
