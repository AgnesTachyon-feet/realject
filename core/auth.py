from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], default="pbkdf2_sha256")

def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)