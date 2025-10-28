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
# SQLAlchemy Engine Setup
# ---------------------------
DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # ✅ auto-reconnects dropped DB connections
    pool_recycle=1800,        # ✅ refresh every 30 mins to avoid idle drops
    pool_size=10,             # ✅ base connections
    max_overflow=20,          # ✅ burst capacity
    pool_timeout=60,          # ✅ wait 60s before timeout
    connect_args={"connect_timeout": 10},  # ✅ fail fast on bad DB
    echo=False,               # change to True for debug logs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------
# FastAPI DB dependency
# ---------------------------
def get_db():
    """
    Dependency to provide a scoped DB session.
    Closes automatically after the request ends.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        print(f"⚠️ DB rollback due to exception: {e}")
        raise
    finally:
        db.close()  # ✅ always return connection to pool


# ---------------------------
# Keep DB alive (for Railway/Supabase)
# ---------------------------
def keep_db_alive():
    """
    Pings the database every 5 minutes to keep Railway connections active.
    If DB goes down temporarily, retries every 60s.
    """
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            time.sleep(300)
        except Exception as e:
            print(f"⚠️ DB keep-alive failed: {e}")
            time.sleep(60)


# ---------------------------
# Background thread for keep-alive
# ---------------------------
thread = threading.Thread(target=keep_db_alive, daemon=True)
thread.start()
