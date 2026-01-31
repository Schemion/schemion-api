from typing import List, Optional, Set
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings
from app.core.entities.user import UserLight as EntityUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
) -> EntityUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

        user_id: Optional[str] = payload.get("sub")
        roles: Set[str] = payload.get("roles", [])
        email: Optional[str] = payload.get("email")
        if not user_id or not roles:
            raise credentials_exception

        return EntityUser(
            id=UUID(user_id),
            roles=roles,
            email=email,
        )
    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception

def require_roles(allowed_roles: List[str]):
    async def checker(user: EntityUser = Depends(get_current_user),) -> EntityUser:
        if not any(role in allowed_roles for role in user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough rights",
            )
        return user
    return checker
