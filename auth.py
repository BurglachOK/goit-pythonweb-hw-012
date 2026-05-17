import os
import json
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db import get_db
import models
import redis
from datetime import timezone

load_dotenv() 
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    """
    Verifies if a plain text password matches its corresponding bcrypt hash.

    :param plain_password: The raw password provided by the user.
    :type plain_password: str
    :param hashed_password: The securely stored bcrypt hash from the database.
    :type hashed_password: str
    :return: True if the password matches the hash, False otherwise.
    :rtype: bool
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Generates a secure bcrypt hash from a plain text password string.

    :param password: The plain text password to encrypt.
    :type password: str
    :return: The generated cryptographic bcrypt hash.
    :rtype: str
    """
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """
    Generates a short-lived JWT access token valid for the configured minutes.

    :param data: Dictionary containing user-specific identifiers to encode.
    :type data: dict
    :return: Cryptographically signed JWT access token string.
    :rtype: str
    """
    to_encode = data.copy()
    expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decodes the provided JWT token, checks its validity, and retrieves the corresponding user from DB or Redis cache.

    :param token: The JWT access token extracted from the Authorization header.
    :type token: str
    :param db: The database session dependency instance.
    :type db: Session
    :raises HTTPException 401: If the token is invalid, expired, or payload parsing fails.
    :return: The authenticated user database object.
    :rtype: models.User
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    redis_key = f"user:{email}"
    try:
        cached_user = redis_client.get(redis_key)
        if cached_user:
            user_data = json.loads(cached_user)
            return models.User(**user_data)
    except Exception:
        pass

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception

    try:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "password": user.password,
            "avatar": user.avatar,
            "role": user.role,
            "confirmed": user.confirmed
        }
        redis_client.setex(redis_key, 300, json.dumps(user_dict))
    except Exception:
        pass

    return user

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: models.User = Depends(get_current_user)):
        if not hasattr(current_user, "role") or current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user
    

def create_reset_password_token(email: str) -> str:
    """
    Generates a temporary JWT token for password reset, valid for 15 minutes.
    """
    to_encode = {"sub": email, "action": "reset_password"}
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    expire_naive = expire.replace(tzinfo=None)
    
    to_encode.update({"exp": expire_naive})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """
    Generates a long-lived JWT refresh token valid for 7 days.

    :param data: Dictionary containing the data payload to encode.
    :type data: dict
    :return: Encoded cryptographic JWT refresh token string.
    :rtype: str
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    to_encode.update({"exp": expire, "scope": "refresh_token"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)