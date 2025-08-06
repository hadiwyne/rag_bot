import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithms=["HS256"])
        return encoded_jwt
    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Basic input sanitization"""
        return text.strip()[:1000]  # Limit input length to prevent abuse
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """Generate a secure filename using a hash"""
        extension = original_filename.split('.')[-1] if '.' in original_filename else ''
        secure_name = hashlib.sha256(
            f"{original_filename}{secrets.token_hex(8)}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        return f"{secure_name}.{extension}" if extension else secure_name