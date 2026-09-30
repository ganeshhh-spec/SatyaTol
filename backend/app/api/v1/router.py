from fastapi import APIRouter

from app.api.v1 import auth, instruments, applications, appointments, inspections, certificates, dashboards, notifications, audit, search, users, standards, exports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(instruments.router, prefix="/instruments", tags=["instruments"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["inspections"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(standards.router, prefix="/standards", tags=["standards"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])