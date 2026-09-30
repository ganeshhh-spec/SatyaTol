from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token
from app.schemas.user import UserResponse, Token, LoginRequest, UserCreate
from app.services.auth import authenticate_user, create_user_token, register_user
from app.models.user import User, UserRole
from app.core.permissions import has_permission, Permission
from app.core.errors import UnauthorizedError, ValidationError

router = APIRouter(tags=["auth"])


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        raise UnauthorizedError()

    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    if not token:
        raise UnauthorizedError()

    payload = decode_token(token)
    if not payload:
        raise UnauthorizedError("Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


def get_current_user_optional(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User | None:
    if not authorization:
        return None

    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    if not token:
        return None

    payload = decode_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        return None

    return user


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise UnauthorizedError("Invalid credentials")

    access_token = create_user_token(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(
        db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role,
        jurisdiction=user_data.jurisdiction,
        organization=user_data.organization,
        phone=user_data.phone,
        can_issue_certificate=user_data.can_issue_certificate,
    )
    return user


@router.post("/demo/seed", response_model=dict)
def seed_demo_accounts(db: Session = Depends(get_db)):
    from app.services.auth import register_user
    from app.models.user import UserRole

    demo_accounts = [
        {
            "email": "owner1@demo.com",
            "password": "demo1234",
            "full_name": "Demo Owner 1",
            "role": UserRole.OWNER,
            "organization": "Demo Trading Co.",
        },
        {
            "email": "owner2@demo.com",
            "password": "demo1234",
            "full_name": "Demo Owner 2",
            "role": UserRole.OWNER,
            "organization": "Sample Industries",
        },
        {
            "email": "lmo1@demo.com",
            "password": "demo1234",
            "full_name": "LMO Officer 1",
            "role": UserRole.LMO,
            "jurisdiction": "North Zone",
            "organization": "Legal Metrology Dept - North",
            "can_issue_certificate": True,
        },
        {
            "email": "lmo2@demo.com",
            "password": "demo1234",
            "full_name": "LMO Officer 2",
            "role": UserRole.LMO,
            "jurisdiction": "South Zone",
            "organization": "Legal Metrology Dept - South",
            "can_issue_certificate": True,
        },
        {
            "email": "gatc1@demo.com",
            "password": "demo1234",
            "full_name": "GATC Centre 1",
            "role": UserRole.GATC,
            "organization": "GATC - Central Lab",
        },
        {
            "email": "regulator1@demo.com",
            "password": "demo1234",
            "full_name": "Regulator 1",
            "role": UserRole.REGULATOR,
            "organization": "Regulatory Authority",
        },
        {
            "email": "admin@demo.com",
            "password": "demo1234",
            "full_name": "Platform Admin",
            "role": UserRole.ADMIN,
            "organization": "Platform Administration",
        },
    ]

    created = []
    for acc in demo_accounts:
        existing = db.query(User).filter(User.email == acc["email"]).first()
        if not existing:
            user = register_user(db, **acc)
            created.append(user.email)

    return {"created": created, "message": "Demo accounts seeded. Password for all: demo1234"}