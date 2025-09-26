from typing import Optional, TypeVar, Generic
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from fastapi import Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

T = TypeVar("T")

# -------------------- Repos --------------------

class BaseRepo(Generic[T]):
    @staticmethod
    def insert(db: Session, model: T) -> T:
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

class UsersRepo(BaseRepo):
    @staticmethod
    def find_by_username(db: Session, model, username: str):
        return db.query(model).filter(model.username == username).first()

# -------------------- JWT --------------------

class JWTRepo:
    @staticmethod
    def generate_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        )
        # jose จะเข้าใจ "exp" เป็น datetime-aware ได้
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        try:
            # ถ้า token หมดอายุ jose จะโยนข้อยกเว้นให้เลย ไม่ต้องเช็กเอง
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

# -------------------- Bearer dependency (ถ้าจะใช้) --------------------

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=403, detail="Invalid auth scheme")

        payload = JWTRepo.decode_token(credentials.credentials)
        if payload is None:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
        return payload
