from typing import Optional, List
from uuid import UUID
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.entities.user import UserLight as EntityUser
from app.config import settings

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
        role: Optional[str] = payload.get("role")
        email: Optional[str] = payload.get("email")
        if user_id is None or role is None:
            raise credentials_exception

        user = EntityUser(
            id=UUID(user_id),
            role=role,
            email=email
        )

        return user
    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception

def require_roles(roles: List[str]):
    async def role_checker(user: EntityUser = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough rights"
            )
        return user
    return role_checker