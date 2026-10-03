import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(override=True)

raw_url = os.getenv("DATABASE_URL", "sqlite:///./shopforge.db")
if raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://")

connect_args = {"check_same_thread": False} if raw_url.startswith("sqlite") else {}

engine = create_engine(
    raw_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()