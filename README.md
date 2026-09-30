# Legal Metrology Online Verification System (PS-26036 Prototype)

A secure, role-based web prototype for managing the digital lifecycle of weighing and measuring instruments: registration, verification/re-verification applications, document uploads, review, scheduling, inspection recording, authorized decision and certificate issuance, QR-based public status checking, expiry reminders, and role-based monitoring.

## 📋 Project Status

This is a **prototype** for SIH26036 / PS-26036 — Development of an Online Verification System for Weighing and Measuring Instruments.

**Document status:** Prototype specification; not an approved government deployment specification.

## ✨ Implemented Features

### Core Workflow (End-to-End)
- ✅ **Owner Registration & Authentication** - JWT-based auth with role-based access
- ✅ **Instrument Registration** - Owner creates instrument records with validation
- ✅ **Verification Application** - Initial & re-verification with file uploads (PDF, JPG, PNG)
- ✅ **LMO Review** - Request correction, reject, or approve for scheduling with mandatory reasons
- ✅ **Scheduling & Allocation** - Assign officer/centre, date/time/location with conflict detection
- ✅ **Inspection Recording** - Pass/Fail/Needs Follow-up with observations, checklist, photos
- ✅ **Certificate Issuance** - Authorized LMO only, requires passing inspection
- ✅ **Certificate Revocation/Supersession** - Authorized LMO with reasons, audit trail
- ✅ **QR-based Public Verification** - Scan QR or enter certificate ID, server-side status check

### Role-Based Dashboards
- ✅ **Owner Dashboard** - Instruments, applications, appointments, certificates, expiring soon
- ✅ **LMO Dashboard** - Pending reviews, scheduled inspections, decision pending, completed
- ✅ **GATC Dashboard** - Assigned applications, upcoming slots, pending test records
- ✅ **Regulator Dashboard** - Pendency by stage, workload by officer, expiry summaries
- ✅ **Admin Dashboard** - User management, role distribution, system configuration

### Security & Compliance
- ✅ Backend-enforced RBAC (not just UI hiding)
- ✅ Ownership & jurisdiction checks on all endpoints
- ✅ Password hashing (bcrypt), JWT tokens
- ✅ Input validation, file type/size limits
- ✅ Audit logging for all critical transitions
- ✅ Public verification exposes only approved fields

### Additional Features
- ✅ In-app notifications with expiry reminders
- ✅ Search & filtering across instruments, applications, certificates
- ✅ Responsive design (desktop + mobile)
- ✅ Synthetic demo data with 7 demo accounts

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL |
| Frontend | React 18, Vite, Tailwind CSS, React Router |
| Auth | JWT (HS256), bcrypt password hashing |
| Database | PostgreSQL 15 with Alembic migrations |
| QR Codes | qrcode.react |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (recommended)
- OR: Python 3.11+, Node.js 20+, PostgreSQL 15+

### Using Docker Compose (Recommended)

```bash
# Clone and navigate
cd legal-metrology-verification

# Copy environment file
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# Seed demo data
docker-compose exec backend python seed_demo.py

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and JWT_SECRET_KEY

# Run migrations
alembic upgrade head

# Seed demo data
python seed_demo.py

# Start server
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## 🔐 Demo Accounts

All demo accounts use password: **`demo1234`**

| Email | Role | Capabilities |
|-------|------|--------------|
| `owner1@demo.com` | Instrument Owner | Register instruments, submit applications, view own certificates |
| `owner2@demo.com` | Instrument Owner | Same as above (separate data isolation) |
| `lmo1@demo.com` | Legal Metrology Officer | Review apps, schedule, inspect, **issue/revoke certificates** (North Zone) |
| `lmo2@demo.com` | Legal Metrology Officer | Same (South Zone) |
| `gatc1@demo.com` | GATC Centre | View assigned, manage calendar, record test results |
| `regulator1@demo.com` | Regulator | View jurisdiction dashboards, reports, audit |
| `admin@demo.com` | Platform Admin | Manage users, roles, configuration |

## 🔗 Key API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Current user
- `POST /api/v1/auth/register` - Register (admin only for privileged roles)
- `POST /api/v1/auth/demo/seed` - Seed demo accounts

### Instruments
- `GET /api/v1/instruments` - List (filtered by role)
- `POST /api/v1/instruments` - Create (owner)
- `GET /api/v1/instruments/{id}` - Get details
- `PATCH /api/v1/instruments/{id}` - Update (owner)
- `DELETE /api/v1/instruments/{id}` - Delete (owner)

### Applications
- `GET /api/v1/applications` - List
- `POST /api/v1/applications` - Create (owner)
- `POST /api/v1/applications/{id}/submit` - Submit (owner)
- `GET /api/v1/applications/{id}` - Details with timeline
- `POST /api/v1/applications/{id}/review` - Review (LMO)
- `POST /api/v1/applications/{id}/resubmit` - Resubmit after correction (owner)
- `POST /api/v1/applications/{id}/schedule` - Schedule (LMO/GATC/Admin)
- `POST /api/v1/applications/{id}/attachments` - Upload files

### Inspections
- `POST /api/v1/inspections` - Record inspection (assigned inspector)
- `GET /api/v1/inspections` - List inspections
- `GET /api/v1/inspections/{id}` - Get details
- `PATCH /api/v1/inspections/{id}` - Update (before finalization)

### Certificates
- `POST /api/v1/certificates/{application_id}/issue` - Issue (authorized LMO)
- `POST /api/v1/certificates/{id}/revoke` - Revoke (authorized LMO)
- `POST /api/v1/certificates/{id}/supersede` - Supersede (authorized LMO)
- `GET /api/v1/certificates` - List certificates
- `GET /api/v1/certificates/{id}` - Certificate details
- `GET /api/v1/certificates/public/verify/{token}` - **Public verification (no auth)**
- `GET /api/v1/certificates/public/verify?certificate_id=...` - Public verify by ID

### Dashboards & Search
- `GET /api/v1/dashboards` - Role-based dashboard
- `GET /api/v1/search/instruments` - Search instruments
- `GET /api/v1/search/applications` - Search applications
- `GET /api/v1/search/certificates` - Search certificates

### Notifications & Audit
- `GET /api/v1/notifications` - List notifications
- `POST /api/v1/notifications/{id}/read` - Mark read
- `GET /api/v1/audit` - Audit events (admin/regulator)

## 🎯 Acceptance Criteria Status

| # | Criteria | Status |
|---|----------|--------|
| 1 | Owner can register instrument & submit application with attachment | ✅ |
| 2 | Owner A cannot access Owner B's data by changing IDs | ✅ (backend enforced) |
| 3 | LMO can review permitted cases with reasons | ✅ |
| 4 | Scheduling prevents conflicting slots | ✅ |
| 5 | Assigned inspector can record pass/fail/follow-up | ✅ |
| 6 | Failed inspection cannot generate valid certificate | ✅ |
| 7 | Unauthorized roles cannot issue/revoke certificates | ✅ (backend enforced) |
| 8 | Authorized issuance creates certificate + QR | ✅ |
| 9 | Expired/revoked/superseded/invalid IDs show distinct statuses | ✅ |
| 10 | Important state changes create audit events | ✅ |
| 11 | Dashboards reflect database records | ✅ |
| 12 | Responsive on desktop & mobile | ✅ |

## ⚠️ Simulated / Planned Features

| Feature | Status | Notes |
|---------|--------|-------|
| Payment gateway integration | ❌ Simulated | Fee fields exist but no payment processing |
| Email/SMS notifications | ❌ Simulated | In-app notifications only |
| Digital signatures | ❌ Planned | Signature metadata field exists |
| Offline mobile sync | ❌ Planned | Web-only prototype |
| Blockchain/advanced crypto | ❌ Out of scope | Not required for prototype |
| Integration with govt databases | ❌ Out of scope | Requires approvals |
| Production security hardening | ❌ Planned | Prototype security only |

## 📁 Project Structure

```
legal-metrology-verification/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── core/            # Config, security, permissions, errors
│   │   ├── db/              # Database session
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # Migrations
│   ├── seed_demo.py         # Demo data script
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/             # Layout, routing
│   │   ├── components/      # Shared UI components
│   │   ├── features/        # Feature modules
│   │   ├── lib/             # API client, auth, utils
│   │   └── styles/          # Tailwind styles
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest app/tests/ -v

# Frontend lint
cd frontend
npm run lint
```

## 📝 License

Prototype for SIH26036 / PS-26036. Not for production use without proper security review, legal compliance, and government approvals.

## 📚 References

- SIH Problem Statement: https://sih2026.vuce.in/ps/SIH26036
- Legal Metrology Act, 2009 (India)
- Relevant state legal metrology rules