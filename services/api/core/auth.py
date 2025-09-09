"""
JWT Authentication utilities for OriginFD API
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
# from passlib.context import CryptContext  # Temporarily disabled due to bcrypt issues
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Password hashing - temporarily disabled due to bcrypt compatibility issues
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple hash function for now - replace with proper bcrypt once fixed
def simple_hash(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def simple_verify(password: str, hashed: str) -> bool:
    return simple_hash(password) == hashed

# JWT settings
SECRET_KEY = "your-secret-key-here-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# HTTP Bearer security scheme
security = HTTPBearer()


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: list[str] = []


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return simple_verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return simple_hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing expiration"
            )
        
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def create_token_pair(user_data: dict) -> tuple[str, str]:
    """Create both access and refresh tokens"""
    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(data=user_data)
    return access_token, refresh_token


# Mock user database for testing
MOCK_USERS_DB = {
    "admin@originfd.com": {
        "id": "user-123",
        "email": "admin@originfd.com",
        "full_name": "Admin User",
        "hashed_password": get_password_hash("admin"),
        "is_active": True,
        "roles": ["admin", "engineer"]
    },
    "user@originfd.com": {
        "id": "user-456", 
        "email": "user@originfd.com",
        "full_name": "Regular User",
        "hashed_password": get_password_hash("password"),
        "is_active": True,
        "roles": ["user"]
    }
}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate user with email and password"""
    user = MOCK_USERS_DB.get(email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID"""
    for user in MOCK_USERS_DB.values():
        if user["id"] == user_id:
            return user
    return None


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email"""
    return MOCK_USERS_DB.get(email)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token, "access")
    return payload