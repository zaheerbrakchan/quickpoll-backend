# app/routes/polls.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models, schemas
from app.utils.dependencies import get_current_user  # updated import

router = APIRouter()


# ---------------------------
# Create Poll (Admin Only)
# ---------------------------
@router.post("/", response_model=schemas.Poll)
def create_poll(
    poll: schemas.PollCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    db_poll = models.Poll(title=poll.title, description=poll.description)
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)

    # Add options
    for opt in poll.options:
        db_option = models.Option(text=opt.text, poll_id=db_poll.id)
        db.add(db_option)
    db.commit()
    db.refresh(db_poll)
    return db_poll


# ---------------------------
# Get All Polls (with vote counts)
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
                "text": opt.text,
                "votes": vote_count
            })

        poll_data = {
            "id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "options": options_data,
            "created_at": poll.created_at,
            "created_by": getattr(poll, "created_by", None)
        }

        result.append(poll_data)

    return result


# ---------------------------
# Get Single Poll (with vote counts)
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
            "text": opt.text,
            "votes": vote_count
        })

    poll_data = {
        "id": poll.id,
        "title": poll.title,
        "description": poll.description,
        "options": options_data,
        "created_at": poll.created_at,
        "created_by": getattr(poll, "created_by", None)
    }

    return poll_data

