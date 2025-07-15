"""Authentication and authorization utilities."""
from typing import Callable, Optional
from fastapi import HTTPException, Depends, Header
from src.config.settings import get_settings
import jwt

settings = get_settings()

def get_admin_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract admin token from authorization header."""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("is_admin"):
            return token
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        return None

def admin_only(authorization: Optional[str] = Header(None)) -> bool:
    """Dependency to check if user is an admin."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header provided")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if not payload.get("is_admin"):
            raise HTTPException(status_code=403, detail="Not authorized")
        return True
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to get current user from token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header provided")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
