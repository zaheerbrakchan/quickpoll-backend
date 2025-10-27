# app/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


# User
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

# Token
class Token(BaseModel):
    access_token: str
    username:str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

# Option
class OptionBase(BaseModel):
    text: str

class OptionCreate(OptionBase):
    pass

class Option(OptionBase):
    id: UUID
    poll_id: UUID
    votes: int = 0
    class Config:
        orm_mode = True


# Poll
class PollBase(BaseModel):
    title: str
    description: Optional[str] = None

class PollCreate(PollBase):
    options: List[OptionCreate]

class Poll(PollBase):
    id: UUID
    created_at: datetime
    likes: int
    options: List[Option] = []

    class Config:
        orm_mode = True


# Vote
class VoteCreate(BaseModel):
    poll_id: UUID
    option_id: UUID


# Like
class LikeUpdate(BaseModel):
    poll_id: UUID
