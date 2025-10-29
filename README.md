# ⚙️ QuickPoll – Backend (FastAPI + WebSockets)

The backend for **QuickPoll**, a real-time opinion polling platform that supports creating, voting, liking, and deleting polls with **instant updates** across all connected users.

Built using **FastAPI (Python)**, **PostgreSQL**, and **Redis (for WebSocket broadcasting)**.

👉 **Live API:** https://quickpoll-backend-production.up.railway.app  
👉 **Frontend Repo:** https://github.com/zaheerbrakchan/quickpoll-frontend

---

## 🚀 Features

- 🗳️ **Create, Retrieve, and Delete Polls**
- 💬 **Vote in real time (one vote per user per poll)**
- ❤️ **Like/Unlike polls instantly**
- ⚡ **Live updates via WebSockets (Redis or in-memory fallback)**
- 🔐 **JWT Authentication**
- 🧱 **PostgreSQL Database with SQLAlchemy ORM**
- 🌍 **CORS Enabled for Frontend Integration**
- 🧭 **Clean REST + WebSocket architecture**

---

## 🧠 System Architecture

```text
┌──────────────────────────────────────────┐
│              Frontend (Next.js)          │
│  - Interacts via REST & WebSocket APIs   │
│  - Displays polls, votes, and likes live │
└──────────────────────────┬───────────────┘
                           │
             REST & WS     │
                           ▼
┌──────────────────────────────────────────┐
│             Backend (FastAPI)            │
│  - REST API endpoints (CRUD, Auth)       │
│  - WebSocket endpoints for live updates  │
│  - Redis Pub/Sub for real-time events    │
└──────────────────────────┬───────────────┘
                           │
                           ▼
┌──────────────────────────────────────────┐
│     PostgreSQL + Redis (via Railway)     │
│  - Poll, Vote, Like, User persistence    │
│  - Pub/Sub message broadcasting          │
└──────────────────────────────────────────┘
```

**Data Flow:**
1. Frontend sends REST request (create/vote/like).
2. FastAPI processes it, updates DB.
3. FastAPI broadcasts updates through Redis/WebSocket.
4. All connected clients instantly receive the update.

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| Framework | FastAPI |
| Language | Python |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Real-time | WebSocket + Redis Pub/Sub |
| Auth | JWT (via `python-jose` & `passlib`) |
| Deployment | Railway |
| Env Config | python-dotenv |

---

## 📁 Project Structure

```
app/
│
├── main.py                # FastAPI app entry point
├── db.py                  # Database setup (SQLAlchemy + Railway)
├── models.py              # ORM models
├── schemas.py             # Pydantic schemas
│
├── routes/
│   ├── polls.py           # CRUD for polls
│   ├── votes.py           # Voting logic
│   ├── likes.py           # Like/unlike logic
│   ├── auth.py            # Register/Login + JWT
│   └── polls_ws.py        # WebSocket endpoints + Redis
│
├── utils/
│   ├── auth.py            # Token + password hashing helpers
│   └── dependencies.py    # Dependency functions (get_current_user)
│
├── .env                   # Environment config
└── requirements.txt        # Dependencies
```

---

## 🛠️ Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/zaheerbrakchan/quickpoll-backend
cd quickpoll-backend
```

### 2️⃣ Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Setup `.env` File
Create a `.env` file in the root directory:

```bash
user=postgres
password=yourpassword
host=yourhost
port=35740
dbname=railway
sslmode=require
SECRET_KEY=astrdttev67tv
ALGORITHM=HS256
REDIS_URL=rediss://your_redis_url_here
```

> ⚠️ *The `REDIS_URL` is optional — if not provided, WebSockets will still work using in-memory broadcasting.*

---

### 5️⃣ Run Migrations (if using Alembic)
(Optional, if DB schema management is enabled)
```bash
alembic upgrade head
```

### 6️⃣ Run the Application
```bash
uvicorn app.main:app --reload
```

Backend runs at:  
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

API docs:  
👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔌 API Endpoints Overview

| Method | Endpoint | Description |
|--------|-----------|-------------|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login and get JWT token |
| `GET`  | `/api/polls/` | Get all polls with live counts |
| `POST` | `/api/polls/` | Create a new poll |
| `DELETE` | `/api/polls/{poll_id}` | Delete a poll |
| `POST` | `/api/votes/` | Cast a vote |
| `GET`  | `/api/votes/user/{poll_id}` | Get if user already voted |
| `POST` | `/api/likes/{poll_id}` | Like/unlike a poll |
| `GET`  | `/api/likes/user/{poll_id}` | Get user's like status |
| `WS` | `/ws/polls` | Global channel for new polls/deletions |
| `WS` | `/ws/polls/{poll_id}` | Real-time updates for a specific poll |

---

## 🧪 Example API Flow

### Create Poll
```bash
POST /api/polls/
Authorization: Bearer <token>
{
  "title": "Your favorite framework?",
  "description": "Vote for your favorite web framework",
  "options": [
    {"text": "React"},
    {"text": "Vue"},
    {"text": "Angular"}
  ]
}
```

### Vote
```bash
POST /api/votes/
{
  "poll_id": "abc123",
  "option_id": "xyz789"
}
```

### Like Poll
```bash
POST /api/likes/{poll_id}
```

---

## 🌐 Deployment

This backend is deployed on **Railway**.  
Make sure to:
- Add environment variables in Railway Dashboard.  
- Allow CORS for your frontend domain.  
- Connect Redis add-on for WebSocket broadcasting (optional).  

---

## 🧠 Research & References

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [Redis Pub/Sub Docs](https://redis.io/docs/latest/develop/pubsub/)
- [Railway.app](https://railway.app)

---

## 👨‍💻 Author

**Zaheer Brakchan**  
Full Stack Developer | FastAPI + TypeScript + WebSocket  
🔗 [GitHub](https://github.com/zaheerbrakchan)
