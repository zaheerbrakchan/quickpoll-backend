# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import polls, votes, likes, auth

app = FastAPI(title="QuickPoll Backend")

# Register routers
app.include_router(polls.router, prefix="/api/polls", tags=["Polls"])
app.include_router(votes.router, prefix="/api/votes", tags=["Votes"])
app.include_router(likes.router, prefix="/api/likes", tags=["Likes"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Allow all origins (not recommended for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 👈 allow all domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "QuickPoll API is running 🚀"}
