from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from app.utils.database import AsyncSessionDep
from app.models.user import User, UserCreate, UserPublic
from app.models.token import Token
from app.exceptions.user import UnauthorizedException
from app.utils.security import (
    get_current_user,
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.utils.logging_config import logger


router = APIRouter(prefix="/api")

@router.post("/register", response_model=Token)
async def register(
    session: AsyncSessionDep,
    user: UserCreate
):
    try:
        logger.info(f"New user registration attempt: {user.username}")

        db_user = await User.get_by_username(session, user.username)
        if db_user:
            logger.warning(f"Registration failed - username already exists: {user.username}")
            raise UnauthorizedException(
                detail="Username already registered"
            )
        
        if len(user.password) < 8:
            raise UnauthorizedException(
                detail="Password must be at least 8 characters long"
            )
        
        hashed_password = get_password_hash(user.password)
        user_obj = User(
            username=user.username,
            password=hashed_password,
        )
        user_obj = await User.add(session, user_obj)

        access_token = create_access_token(data={"sub": user_obj.username})
        return Token(access_token=access_token)
    except IntegrityError:
        await session.rollback()
        raise UnauthorizedException(
            detail="Username already exists"
        )

@router.post("/token", response_model=Token)
async def login(
    session: AsyncSessionDep,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    if not form_data.username or not form_data.password:
        raise UnauthorizedException(
            detail="Incorrect username or password"
        )
        
    user = await User.get_by_username(session, form_data.username)
    if not user:
        raise UnauthorizedException(
            detail="Incorrect username or password"
        )
    
    if not verify_password(form_data.password, user.password):
        raise UnauthorizedException(
            detail="Incorrect username or password"
        )
        
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token)

@router.get("/profile")
async def profile(session: AsyncSessionDep, current_user: User = Depends(get_current_user)):
    return UserPublic(
        id=current_user.id,
        username=current_user.username,
        balance=f"{await current_user.total_balance(session):.2f}"
    )
