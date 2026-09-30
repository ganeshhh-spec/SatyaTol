import os
import sys
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

import app.models  # Register all models with Base.metadata
from app.db.session import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.models.instrument import Instrument, InstrumentCategory, InstrumentStatus
from app.models.application import Application, VerificationType, ApplicationStatus
from app.models.attachment import Attachment
from app.models.inspection import Inspection, InspectionResult
from app.models.certificate import Certificate, CertificateStatus
from app.main import app


@pytest.fixture(scope="session")
def engine():
    """Isolated in-memory SQLite engine for fast, safe test execution."""
    test_db_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    if test_db_url.startswith("sqlite"):
        engine = create_engine(
            test_db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(test_db_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(engine):
    """Provides a transactional database session rolled back after every test."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, expire_on_commit=False)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    """FastAPI TestClient with get_db overridden to use test session."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def owner1_user(db) -> User:
    user = User(
        email="owner1_test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Owner One",
        role=UserRole.OWNER,
        organization="Alpha Scales Pvt Ltd",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def owner2_user(db) -> User:
    user = User(
        email="owner2_test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Owner Two",
        role=UserRole.OWNER,
        organization="Beta Industries Ltd",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def lmo_user(db) -> User:
    user = User(
        email="lmo_test@example.gov",
        hashed_password=get_password_hash("password123"),
        full_name="Inspector Vikram Roy",
        role=UserRole.LMO,
        organization="Dept of Legal Metrology",
        jurisdiction="South Zone",
        can_issue_certificate=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def gatc_user(db) -> User:
    user = User(
        email="gatc_test@example.gov",
        hashed_password=get_password_hash("password123"),
        full_name="GATC Regional Testing Centre",
        role=UserRole.GATC,
        organization="National Test House",
        jurisdiction="South Zone",
        can_issue_certificate=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regulator_user(db) -> User:
    user = User(
        email="regulator_test@example.gov",
        hashed_password=get_password_hash("password123"),
        full_name="Controller of Metrology",
        role=UserRole.REGULATOR,
        organization="Legal Metrology HQ",
        can_issue_certificate=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db) -> User:
    user = User(
        email="admin_test@example.gov",
        hashed_password=get_password_hash("password123"),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        organization="Gov Admin",
        can_issue_certificate=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner1_headers(owner1_user) -> dict:
    return auth_header_for_user(owner1_user)


@pytest.fixture
def owner2_headers(owner2_user) -> dict:
    return auth_header_for_user(owner2_user)


@pytest.fixture
def lmo_headers(lmo_user) -> dict:
    return auth_header_for_user(lmo_user)


@pytest.fixture
def gatc_headers(gatc_user) -> dict:
    return auth_header_for_user(gatc_user)


@pytest.fixture
def regulator_headers(regulator_user) -> dict:
    return auth_header_for_user(regulator_user)


@pytest.fixture
def admin_headers(admin_user) -> dict:
    return auth_header_for_user(admin_user)


@pytest.fixture
def test_instrument(db, owner1_user) -> Instrument:
    inst = Instrument(
        serial_number=f"SN-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        category=InstrumentCategory.WEIGHING_NON_AUTOMATIC,
        instrument_type="Platform Scale",
        model="Bench Scale Pro 5000",
        manufacturer="Acme Metrology",
        capacity="50.0",
        unit="kg",
        status=InstrumentStatus.REGISTERED,
        owner_id=owner1_user.id,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


@pytest.fixture
def test_application(db, owner1_user, test_instrument, lmo_user) -> Application:
    app = Application(
        instrument_id=test_instrument.id,
        applicant_id=owner1_user.id,
        verification_type=VerificationType.INITIAL,
        status=ApplicationStatus.SUBMITTED,
        assigned_officer_id=lmo_user.id,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app
