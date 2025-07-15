"""Admin dashboard routes for bot management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import jwt
import bcrypt

from ...database import get_db
from ...models.group import MonitoredGroup
from ...models.token import Token
from ...models.token_metrics import TokenMetrics
from ...config.settings import get_settings

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()

class AdminUser(BaseModel):
    """Schema for admin user."""
    email: EmailStr
    password: str
    is_superuser: bool = False

class AdminUserUpdate(BaseModel):
    """Schema for updating admin user."""
    email: Optional[EmailStr]
    is_superuser: Optional[bool]

class GroupCreate(BaseModel):
    """Schema for creating a monitored group."""
    name: str
    chat_id: int
    is_active: bool = True
    weight: float = 1.0

class TokenFilter(BaseModel):
    """Schema for token filtering."""
    min_safety_score: Optional[float] = None
    min_hype_score: Optional[float] = None
    min_holders: Optional[int] = None
    min_volume: Optional[float] = None
    min_liquidity: Optional[float] = None

class BotSettings(BaseModel):
    """Schema for bot settings."""
    min_safety_score: float
    min_hype_score: float
    alert_cooldown: int
    max_alerts_per_hour: int
    blacklist_threshold: int

async def verify_admin(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify admin token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if not payload.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Admin user management
@router.post("/users/")
async def create_admin_user(user: AdminUser, db: Session = Depends(get_db)):
    """Create a new admin user."""
    # Hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(user.password.encode(), salt)
    
    # Create admin user
    admin = {
        "email": user.email,
        "password": hashed.decode(),
        "is_superuser": user.is_superuser
    }
    
    # Store in database (would use proper Admin model in production)
    db.execute(
        "INSERT INTO admin_users (email, password_hash, is_superuser) VALUES (:email, :password, :is_superuser)",
        admin
    )
    db.commit()
    
    return {"status": "success", "message": "Admin user created successfully"}

@router.get("/users/", response_model=List[dict])
async def get_admin_users(db: Session = Depends(get_db), admin: dict = Depends(verify_admin)):
    """Get all admin users."""
    if not admin.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Superuser required")
        
    # Get users from database
    result = db.execute("SELECT id, email, is_superuser FROM admin_users")
    users = result.fetchall()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "is_superuser": user.is_superuser
        }
        for user in users
    ]

@router.put("/users/{user_id}")
async def update_admin_user(
    user_id: int,
    user: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Update admin user."""
    if not admin.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Superuser required")
        
    # Update user
    updates = {}
    if user.email is not None:
        updates["email"] = user.email
    if user.is_superuser is not None:
        updates["is_superuser"] = user.is_superuser
        
    if updates:
        query = "UPDATE admin_users SET "
        query += ", ".join(f"{k} = :{k}" for k in updates.keys())
        query += " WHERE id = :user_id"
        updates["user_id"] = user_id
        
        result = db.execute(query, updates)
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
    return {"status": "success", "message": "User updated successfully"}

# Enhanced group management
@router.get("/groups/", response_model=List[dict])
async def get_monitored_groups(
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Get all monitored Telegram groups."""
    groups = db.query(MonitoredGroup).all()
    return [group.__dict__ for group in groups]

@router.post("/groups/")
async def add_monitored_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Add a new Telegram group to monitor."""
    db_group = MonitoredGroup(
        name=group.name,
        chat_id=group.chat_id,
        is_active=group.is_active,
        weight=group.weight
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return {"status": "success", "message": "Group added successfully"}

@router.put("/groups/{chat_id}")
async def update_group(
    chat_id: int,
    group: GroupCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Update a monitored group."""
    db_group = db.query(MonitoredGroup).filter(MonitoredGroup.chat_id == chat_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    for key, value in group.dict(exclude_unset=True).items():
        setattr(db_group, key, value)
    
    db.commit()
    db.refresh(db_group)
    return {"status": "success", "message": "Group updated successfully"}

# Bot settings management
@router.get("/settings/")
async def get_bot_settings(admin: dict = Depends(verify_admin)):
    """Get current bot settings."""
    return {
        "min_safety_score": settings.min_safety_score,
        "min_hype_score": settings.min_hype_score,
        "alert_cooldown": settings.alert_cooldown,
        "max_alerts_per_hour": settings.max_alerts_per_hour,
        "blacklist_threshold": settings.blacklist_threshold
    }

@router.put("/settings/")
async def update_bot_settings(
    bot_settings: BotSettings,
    admin: dict = Depends(verify_admin)
):
    """Update bot settings."""
    # Update settings in database
    settings_dict = bot_settings.dict()
    
    # Store in database (would use proper Settings model in production)
    query = """
    INSERT INTO bot_settings (
        min_safety_score,
        min_hype_score,
        alert_cooldown,
        max_alerts_per_hour,
        blacklist_threshold,
        updated_at
    ) VALUES (
        :min_safety_score,
        :min_hype_score,
        :alert_cooldown,
        :max_alerts_per_hour,
        :blacklist_threshold,
        CURRENT_TIMESTAMP
    )
    """
    
    try:
        db.execute(query, settings_dict)
        db.commit()
        
        # Update runtime settings
        settings.min_safety_score = bot_settings.min_safety_score
        settings.min_hype_score = bot_settings.min_hype_score
        settings.alert_cooldown = bot_settings.alert_cooldown
        settings.max_alerts_per_hour = bot_settings.max_alerts_per_hour
        settings.blacklist_threshold = bot_settings.blacklist_threshold
        
        return {
            "status": "success", 
            "message": "Settings updated successfully",
            "settings": settings_dict
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        )

# Token management
@router.get("/tokens/")
async def get_tokens(
    filter: TokenFilter = Depends(),
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Get filtered tokens."""
    query = db.query(Token)
    if filter.min_safety_score:
        query = query.join(TokenMetrics).filter(TokenMetrics.safety_score >= filter.min_safety_score)
    if filter.min_hype_score:
        query = query.join(TokenMetrics).filter(TokenMetrics.hype_score >= filter.min_hype_score)
    if filter.min_holders:
        query = query.join(TokenMetrics).filter(TokenMetrics.holder_count >= filter.min_holders)
    
    tokens = query.all()
    return [token.__dict__ for token in tokens]

@router.post("/tokens/blacklist/{address}")
async def blacklist_token(
    address: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """Blacklist a token."""
    token = db.query(Token).filter(Token.address == address).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token.is_blacklisted = True
    db.commit()
    return {"status": "success", "message": "Token blacklisted successfully"}