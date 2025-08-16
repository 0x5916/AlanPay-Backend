from typing import Optional
import bcrypt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
import jwt
from cryptography.fernet import Fernet
import json

from app.utils.config import settings
from app.utils.database import AsyncSessionDep
from app.exceptions.user import UnauthorizedException
from app.models.user import User


fernet = Fernet(settings.FERNET_KEY.encode())

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token", auto_error=False)

async def get_current_user(
    # request: Request,
    session: AsyncSessionDep,
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    try:
        if token is None:
            raise UnauthorizedException(
                detail="Token is not found",
            )
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise UnauthorizedException(
                detail="Could not validate credentials",
            )
    except Exception:
        raise
    user = await User.get_by_username(session, username)
    if user is None:
        raise UnauthorizedException(
            detail="User not found",
        )
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def encrypt_payload(payload: dict) -> str:
    # Convert payload to JSON string and encrypt
    payload_bytes = json.dumps(payload).encode()
    return fernet.encrypt(payload_bytes).decode()

def decrypt_payload(encrypted_payload: str) -> dict:
    decrypted_bytes = fernet.decrypt(encrypted_payload.encode())
    return json.loads(decrypted_bytes.decode())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # standard JWT claims
    payload.update({
        "exp": expire.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp()
    })
    
    encrypted_payload = encrypt_payload(payload)
    
    token_payload = {"encrypted_data": encrypted_payload}
    return jwt.encode(token_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        token_data = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        decrypted_data = decrypt_payload(token_data["encrypted_data"])
        
        # Verify expiration
        exp = datetime.fromtimestamp(decrypted_data["exp"], tz=timezone.utc)
        if datetime.now(timezone.utc) >= exp:
            raise jwt.ExpiredSignatureError("Token has expired")
        return decrypted_data
    except Exception as e:
        raise ValueError(f"Error decoding token: {str(e)}")
