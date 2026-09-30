from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.errors import UnauthorizedError, ValidationError
from app.core.config import settings


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")
    return user


def create_user_token(user: User) -> str:
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires,
    )


def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.OWNER,
    jurisdiction: Optional[str] = None,
    organization: Optional[str] = None,
    phone: Optional[str] = None,
    can_issue_certificate: bool = False,
) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValidationError("Email already registered")

    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        jurisdiction=jurisdiction,
        organization=organization,
        phone=phone,
        can_issue_certificate=can_issue_certificate,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user