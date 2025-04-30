import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import OAuth2PasswordBearer
from src.models.user import User
from src.models.token import BlacklistedToken
import os
from dotenv import load_dotenv
from typing import Optional, Union, Dict, Any, Tuple

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def verify_password(plain_password, hashed_password):
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": TOKEN_TYPE_ACCESS})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": TOKEN_TYPE_REFRESH})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def decode_token(token: str) -> Tuple[Dict[str, Any], datetime]:
    """
    Decode and validate a JWT token
    Returns the payload and expiration time if valid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        exp = payload.get("exp")
        
        if user_id is None or token_type is None or exp is None:
            raise jwt.InvalidTokenError("Invalid token payload")
            
        # Convert exp to datetime
        expiration = datetime.fromtimestamp(exp, tz=timezone.utc)
        
        # Check if token is blacklisted
        blacklisted = await BlacklistedToken.find_one({"token": token})
        if blacklisted:
            raise jwt.InvalidTokenError("Token has been revoked")
            
        return payload, expiration
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def blacklist_token(token: str, user_id: str, token_type: str, expires_at: datetime):
    """Add a token to the blacklist"""
    blacklisted_token = BlacklistedToken(
        token=token,
        token_type=token_type,
        user_id=user_id,
        expires_at=expires_at
    )
    await blacklisted_token.insert()
    return blacklisted_token


async def get_token_from_header(authorization: str = Depends(oauth2_scheme)) -> Optional[str]:
    """Extract token from Authorization header"""
    if not authorization:
        return None
    return authorization


async def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract token from cookie"""
    return request.cookies.get("refresh_token")


async def get_current_user_from_token(token: str) -> User:
    """Get current user from JWT token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload, _ = await decode_token(token)
    user_id = payload.get("sub")
    
    user = await User.find_one({"_id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user


async def get_current_user(token: str = Depends(get_token_from_header)) -> User:
    
    """Get current user from access token (for API endpoints)"""
    return await get_current_user_from_token(token)


async def get_current_user_from_refresh_token(request: Request) -> User:
    """Get current user from refresh token (for token refresh)"""
    token = request.cookies.get("refresh_token")
    return await get_current_user_from_token(token)
