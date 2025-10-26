# QuickPoll Backend

A **FastAPI** backend for a real-time polling platform where users can create polls, vote, like polls, and see live updates.

---

## **Features**

- Users can register and login with JWT authentication.
- Create polls with multiple options.
- Vote on polls (one vote per user per poll).
- Like polls.
- Live updates for votes and likes.
- Admins can manage polls (optional if you restrict features).

---

## **Tech Stack**

- **Backend:** FastAPI, SQLAlchemy
- **Database:** PostgreSQL (or any SQL database)
- **Authentication:** JWT, Passlib (pbkdf2_sha256)
- **Real-time updates:** WebSockets (optional)
- **Deployment:** Railway / any cloud platform

---

## **Installation**

1. Clone the repository:

```bash
git clone <repo-url>
cd quickpoll-backend
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set environment variables (example `.env` file):

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your_super_secret_key
```

5. Run the app:

```bash
uvicorn app.main:app --reload
```

---

## **API Endpoints**

### **Authentication**
- `POST /api/auth/register` → Register a new user
- `POST /api/auth/login` → Login and get JWT token

### **Polls**
- `POST /api/polls/` → Create a new poll
- `GET /api/polls/` → List all polls
- `GET /api/polls/{poll_id}` → Get poll details

### **Votes**
- `POST /api/votes/` → Cast a vote

### **Likes**
- `POST /api/likes/` → Like a poll

> All protected routes require **Bearer token** in Authorization header.

---

