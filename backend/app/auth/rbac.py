from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.auth.keycloak import validate_token, get_token_roles, get_token_sub

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency that extracts the Bearer token and validates it against Keycloak JWKS keys.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token missing in Authorization header"
        )
    return await validate_token(token)

def get_current_user(payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)) -> User:
    """
    Dependency that retrieves the user object from Postgres.
    Auto-provisions the user if they do not exist in the database yet.
    """
    sub = get_token_sub(payload)
    user = db.query(User).filter(User.keycloak_sub == sub).first()
    
    if not user:
        import uuid
        # Fetch user metadata from token claims
        username = payload.get("preferred_username") or payload.get("username") or f"user_{sub[:8]}"
        email = payload.get("email") or f"{username}@zt-dashboard.local"
        department = payload.get("department")
        
        # Determine organizational role mapping from Keycloak realm roles
        roles = get_token_roles(payload)
        user_role = "employee"
        if "admin" in roles:
            user_role = "admin"
        elif "analyst" in roles:
            user_role = "analyst"
        elif "employee" in roles:
            user_role = "employee"

        # Create user record in DB aligning the primary key with Keycloak's UUID
        user = User(
            id=uuid.UUID(sub),
            keycloak_sub=sub,
            username=username,
            email=email,
            role=user_role,
            department=department
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            # Double check for concurrent writes
            user = db.query(User).filter(User.keycloak_sub == sub).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database failed to auto-provision user account"
                )
    return user

def require_roles(*allowed_roles: str):
    """
    Role check decorator returning a dependency.
    Validates if the user has any of the required roles in the OIDC claims.
    """
    def dependency(payload: dict = Depends(get_current_user_payload)):
        user_roles = get_token_roles(payload)
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: User does not possess the required permissions"
            )
        return True
    return dependency
