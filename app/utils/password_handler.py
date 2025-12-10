
# app/utils/password_handler.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    if password is None:
        return None
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)
