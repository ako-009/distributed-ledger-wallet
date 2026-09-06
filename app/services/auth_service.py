from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import verify_password, get_password_hash
from app.schemas.auth import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Find a user by email address."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user.
    - Hash the password before storing
    - Never store plain text passwords
    """
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise ValueError("Email already registered")

    # Hash the password
    hashed_password = get_password_hash(user_data.password)

    # Create the user object
    user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> User | None:
    """
    Verify email and password.
    Returns the user if valid, None if invalid.
    """
    user = await get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user