# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    USER = os.getenv("USER") or os.getenv("user")
    PASSWORD = os.getenv("PASSWORD") or os.getenv("password")
    HOST = os.getenv("HOST") or os.getenv("host")
    PORT = os.getenv("PORT") or os.getenv("port") or 5432
    DBNAME = os.getenv("DBNAME") or os.getenv("dbname")

    return f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

DATABASE_URL = get_database_url()

from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,          # number of persistent connections
    max_overflow=10,      # extra connections for bursts
    pool_timeout=30,
    pool_recycle=1800,    # reconnect every 30 mins
    connect_args={"sslmode": "require"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
