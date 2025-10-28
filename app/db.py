from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# Database URL builder
# ---------------------------
def get_database_url():
    USER = os.getenv("USER") or os.getenv("user")
    PASSWORD = os.getenv("PASSWORD") or os.getenv("password")
    HOST = os.getenv("HOST") or os.getenv("host")
    PORT = os.getenv("PORT") or os.getenv("port")
    DBNAME = os.getenv("DBNAME") or os.getenv("dbname")

    return f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"


# ---------------------------
# SQLAlchemy setup
# ---------------------------
DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # ✅ ensures dead connections are detected
    pool_recycle=1800,    # ✅ refresh connections every 30 mins
    pool_size=5,          # ✅ maintain 5 persistent connections
    max_overflow=10,      # ✅ allow up to 10 extra when busy
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------
# FastAPI DB dependency
# ---------------------------
def get_db():
    """
    Yield a database session for FastAPI routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# Keep DB connection alive (optional but recommended for Railway/Supabase)
# ---------------------------
def keep_db_alive():
    """
    Sends a lightweight query every 5 minutes to prevent Railway/Supabase from
    closing idle SSL connections.
    """
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            time.sleep(300)  # every 5 minutes
        except Exception as e:
            print(f"⚠️ DB keep-alive failed: {e}")
            time.sleep(60)


# Start keep-alive thread in background
threading.Thread(target=keep_db_alive, daemon=True).start()
