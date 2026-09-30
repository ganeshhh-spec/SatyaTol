import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, Text
from app.db.session import Base


class UserRole(str, enum.Enum):
    OWNER = "owner"
    LMO = "lmo"
    GATC = "gatc"
    REGULATOR = "regulator"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.OWNER)
    is_active = Column(Boolean, default=True)
    jurisdiction = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    can_issue_certificate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)