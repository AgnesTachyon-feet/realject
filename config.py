from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from datetime import datetime 
import os, pytz

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

TH_TZ = pytz.timezone("Asia/Bangkok")
def now_th():
    return datetime.now(TH_TZ)

templates = Jinja2Templates(directory="templates")

def th_datetime(dt):
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            if dt.endswith("Z"):
                dt.replace("Z", "+00:00")
            dt = datetime.fromisoformat()
        except Exception:
            return dt
    try:
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(TH_TZ).strftime("%d %b %Y %H:%M")
    except Exception:
        return str(dt)
templates.env.filters["th_datetime"] = th_datetime



@event.listens_for(engine, "connect")
def set_bangkok_timezone(dbapi_conn, conn_record):
    try:
        cur = dbapi_conn.cursor()
        cur.execute("SET TIME ZONE 'Asia/Bangkok';")
        cur.close()
    except Exception:
        pass