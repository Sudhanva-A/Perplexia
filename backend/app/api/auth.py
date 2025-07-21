import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.models import db_models
from app.core.config import settings
import requests
from jose import jwt, jwk
from jose.exceptions import JWTError

logger = logging.getLogger(__name__)

router = APIRouter()

# Set up Clerk URLs based on your settings
CLERK_ISSUER = settings.CLERK_ISSUER
CLERK_JWKS_URL = settings.CLERK_JWKS_ENDPOINT

def get_jwks():
    """Fetch the JSON Web Key Set from Clerk"""
    try:
        response = requests.get(CLERK_JWKS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch authentication keys")

def get_public_key(kid):
    """Get the public key for the given key ID"""
    jwks = get_jwks()
    for key in jwks.get('keys', []):
        if key.get('kid') == kid:
            return jwk.construct(key)
    raise HTTPException(status_code=401, detail="Invalid token key ID")

async def verify_jwt(token):
    """Verify the JWT token using Clerk's public keys"""
    try:
        headers = jwt.get_unverified_headers(token)
        kid = headers.get('kid')
        
        if not kid:
            raise HTTPException(status_code=401, detail="Missing key ID in token header")
        
        public_key = get_public_key(kid)
        
        # Decode and verify the token
        payload = jwt.decode(
            token, 
            public_key.to_pem().decode('utf-8'),
            algorithms=['RS256'],
            audience=settings.CLERK_JWT_AUDIENCE,
            issuer=CLERK_ISSUER
        )
        
        logger.info(f"Token verification successful for user: {payload.get('sub')}")
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")

async def get_current_user(authorization: str = Header(None), db = Depends(get_db)) -> db_models.User:
    """Authenticates user using Clerk JWT from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        token = authorization.split(" ")[1]  # Assuming "Bearer <token>" format
        
        # Log the token verification attempt
        logger.info("Attempting to verify Clerk token")
        
        # Get the JWT payload
        payload = await verify_jwt(token)
        
        # Extract user ID from verified JWT
        clerk_user_id = payload.get('sub')
        if not clerk_user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Find user in database using async query style
        stmt = select(db_models.User).where(db_models.User.clerk_user_id == clerk_user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Create a new user
            email = payload.get('email')
            user = db_models.User(
                clerk_user_id=clerk_user_id,
                username=clerk_user_id.split('_')[-1],  # Basic username from user ID
                email=email
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication system error")

@router.get("/me")
async def get_me(current_user: db_models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username
    }

async def get_optional_current_user(authorization: str = Header(None), db = Depends(get_db)) -> Optional[db_models.User]:
    """Like get_current_user but returns None for unauthenticated requests instead of 401."""
    if not authorization:
        return None
    
    try:
        token = authorization.split(" ")[1]  # Assuming "Bearer <token>" format
        
        # Get the JWT payload
        payload = await verify_jwt(token)
        
        # Extract user ID from verified JWT
        clerk_user_id = payload.get('sub')
        if not clerk_user_id:
            return None
        
        # Find user in database using async query style
        stmt = select(db_models.User).where(db_models.User.clerk_user_id == clerk_user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Create a new user
            email = payload.get('email')
            user = db_models.User(
                clerk_user_id=clerk_user_id,
                username=clerk_user_id.split('_')[-1],
                email=email
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
            
    except (HTTPException, Exception) as e:
        # Log the error but return None instead of raising an exception
        logger.info(f"Optional auth failed: {e}")
        return None
    
   