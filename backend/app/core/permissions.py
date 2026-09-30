from enum import Enum
from typing import Optional
from app.models.user import User, UserRole


class Permission(str, Enum):
    INSTRUMENT_CREATE = "instrument:create"
    INSTRUMENT_READ_OWN = "instrument:read_own"
    INSTRUMENT_READ_ALL = "instrument:read_all"
    INSTRUMENT_UPDATE_OWN = "instrument:update_own"
    INSTRUMENT_DELETE_OWN = "instrument:delete_own"

    APPLICATION_CREATE = "application:create"
    APPLICATION_READ_OWN = "application:read_own"
    APPLICATION_READ_ASSIGNED = "application:read_assigned"
    APPLICATION_READ_ALL = "application:read_all"
    APPLICATION_SUBMIT = "application:submit"
    APPLICATION_REVIEW = "application:review"
    APPLICATION_SCHEDULE = "application:schedule"

    INSPECTION_CREATE = "inspection:create"
    INSPECTION_READ_ASSIGNED = "inspection:read_assigned"
    INSPECTION_READ_ALL = "inspection:read_all"
    INSPECTION_UPDATE_OWN = "inspection:update_own"

    CERTIFICATE_ISSUE = "certificate:issue"
    CERTIFICATE_REVOKE = "certificate:revoke"
    CERTIFICATE_SUPERSEDE = "certificate:supersede"
    CERTIFICATE_READ_OWN = "certificate:read_own"
    CERTIFICATE_READ_ALL = "certificate:read_all"

    USER_MANAGE = "user:manage"
    CONFIG_MANAGE = "config:manage"
    AUDIT_READ = "audit:read"

    PUBLIC_VERIFY = "public:verify"


ROLE_PERMISSIONS = {
    UserRole.OWNER: {
        Permission.INSTRUMENT_CREATE,
        Permission.INSTRUMENT_READ_OWN,
        Permission.INSTRUMENT_UPDATE_OWN,
        Permission.INSTRUMENT_DELETE_OWN,
        Permission.APPLICATION_CREATE,
        Permission.APPLICATION_READ_OWN,
        Permission.APPLICATION_SUBMIT,
        Permission.CERTIFICATE_READ_OWN,
        Permission.PUBLIC_VERIFY,
    },
    UserRole.LMO: {
        Permission.INSTRUMENT_READ_ALL,
        Permission.APPLICATION_READ_ASSIGNED,
        Permission.APPLICATION_REVIEW,
        Permission.APPLICATION_SCHEDULE,
        Permission.INSPECTION_CREATE,
        Permission.INSPECTION_READ_ASSIGNED,
        Permission.INSPECTION_READ_ALL,
        Permission.INSPECTION_UPDATE_OWN,
        Permission.CERTIFICATE_READ_ALL,
        Permission.AUDIT_READ,
        Permission.PUBLIC_VERIFY,
    },
    UserRole.GATC: {
        Permission.INSTRUMENT_READ_ALL,
        Permission.APPLICATION_READ_ASSIGNED,
        Permission.INSPECTION_READ_ASSIGNED,
        Permission.INSPECTION_CREATE,
        Permission.INSPECTION_UPDATE_OWN,
        Permission.CERTIFICATE_READ_ALL,
        Permission.PUBLIC_VERIFY,
    },
    UserRole.REGULATOR: {
        Permission.INSTRUMENT_READ_ALL,
        Permission.APPLICATION_READ_ALL,
        Permission.INSPECTION_READ_ALL,
        Permission.CERTIFICATE_READ_ALL,
        Permission.AUDIT_READ,
        Permission.PUBLIC_VERIFY,
    },
    UserRole.ADMIN: {
        Permission.INSTRUMENT_READ_ALL,
        Permission.APPLICATION_READ_ALL,
        Permission.INSPECTION_READ_ALL,
        Permission.CERTIFICATE_READ_ALL,
        Permission.USER_MANAGE,
        Permission.CONFIG_MANAGE,
        Permission.AUDIT_READ,
        Permission.PUBLIC_VERIFY,
    },
}


AUTHORIZED_ISSUER_ROLES = {UserRole.LMO}


def has_permission(user: User, permission: Permission) -> bool:
    if not user.is_active:
        return False
    role_perms = ROLE_PERMISSIONS.get(user.role, set())
    return permission in role_perms


def is_authorized_issuer(user: User) -> bool:
    return user.role in AUTHORIZED_ISSUER_ROLES and user.is_active and getattr(user, 'can_issue_certificate', False)


def can_access_instrument(user: User, instrument_owner_id: int) -> bool:
    if not user.is_active:
        return False
    if user.role == UserRole.OWNER:
        return user.id == instrument_owner_id
    return user.role in {UserRole.LMO, UserRole.GATC, UserRole.REGULATOR, UserRole.ADMIN}


def can_access_application(user: User, application_applicant_id: int, application_assigned_to_id: Optional[int], application_jurisdiction: Optional[str] = None) -> bool:
    if not user.is_active:
        return False
    if user.role == UserRole.OWNER:
        return user.id == application_applicant_id
    if user.role == UserRole.LMO:
        if user.id != application_assigned_to_id:
            return False
        if application_jurisdiction and user.jurisdiction and user.jurisdiction != application_jurisdiction:
            return False
        return True
    if user.role == UserRole.GATC:
        if user.id != application_assigned_to_id:
            return False
        return True
    return user.role in {UserRole.REGULATOR, UserRole.ADMIN}


def can_access_inspection(user: User, inspection_inspector_id: int, inspection_jurisdiction: Optional[str] = None) -> bool:
    if not user.is_active:
        return False
    if user.role in {UserRole.LMO, UserRole.GATC}:
        if user.id != inspection_inspector_id:
            return False
        if inspection_jurisdiction and user.jurisdiction and user.jurisdiction != inspection_jurisdiction:
            return False
        return True
    return user.role in {UserRole.REGULATOR, UserRole.ADMIN}