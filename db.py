from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Configure DB URL (adjust to match your PostgreSQL setup)
DB_URL = "postgresql://postgres:password@localhost:5432/mcp_tasks"

import psycopg2
from sqlalchemy.exc import OperationalError

def ensure_db_exists(db_name="mcp_tasks", user="postgres", password="password", host="localhost", port=5432):
    try:
        # Connect to the default 'postgres' database
        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Check if the target database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()

        if not exists:
            print(f"[⚙️] Creating database '{db_name}'...")
            cur.execute(f"CREATE DATABASE {db_name}")
        else:
            print(f"[✅] Database '{db_name}' already exists.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"[❌] Could not ensure DB exists: {e}")

ensure_db_exists()

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
