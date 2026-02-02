from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.infrastructure.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        roles: List[str] = payload.get("roles", [])
        permissions: List[str] = payload.get("permissions", [])
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return {"id": user_id, "roles": roles, "permissions": permissions}


def require_roles(allowed_roles: List[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if not any(role in allowed_roles for role in current_user["roles"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough rights"
            )
        return current_user

    return role_checker


def require_permission(permission: str):
    async def checker(current_user: dict = Depends(get_current_user), ):
        token_permissions = current_user.get("permissions", [])
        if not permission in token_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied"
            )
        return current_user

    return checker
