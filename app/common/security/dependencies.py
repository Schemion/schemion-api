from typing import Optional, List
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import ApplicationContainer
from app.core.entities.user import User as EntityUser
from app.core.services import UserService
from app.config import settings
from app.dependencies import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

@inject
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_db),
        user_service: UserService = Depends(Provide[ApplicationContainer.user_service]),
) -> EntityUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: Optional[UUID] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_service.get_user_by_id(session,user_id)
    if not user:
        raise credentials_exception

    return user

def require_roles(roles: List[str]):
    async def role_checker(user: EntityUser = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough rights"
            )
        return user
    return role_checker