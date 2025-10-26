# app/utils/auth.py
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta
from jose import jwt

# Secret key for JWT
SECRET_KEY = "your_super_secret_key_here"  # change this in production
ALGORITHM = "HS256"


# ---------------------------
# Password hashing
# ---------------------------
def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pbkdf2_sha256.verify(password, hashed)


# ---------------------------
# JWT Token
# ---------------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
