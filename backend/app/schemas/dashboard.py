from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, date


class TrendDataPoint(BaseModel):
    label: str
    value: int
    date: Optional[datetime] = None


class WorkloadDistribution(BaseModel):
    officer: str
    count: int


class OwnerDashboardStats(BaseModel):
    total_instruments: int
    instruments_by_status: Dict[str, int] = {}
    active_applications: int
    applications_by_status: Dict[str, int] = {}
    upcoming_appointments: int
    active_certificates: int
    expiring_soon: int
    expiring_7_days: int = 0
    expired_certificates: int = 0
    application_trend: List[TrendDataPoint] = []


class LMODashboardStats(BaseModel):
    pending_reviews: int
    scheduled_inspections: int
    in_progress_inspections: int = 0
    decision_pending: int
    recently_completed: int
    applications_by_status: Dict[str, int] = {}
    inspection_trend: List[TrendDataPoint] = []
    inspection_results: Dict[str, int] = {}


class GATCDashboardStats(BaseModel):
    assigned_applications: int
    upcoming_slots: int
    pending_test_records: int
    applications_by_status: Dict[str, int] = {}
    slots_by_status: Dict[str, int] = {}
    test_trend: List[TrendDataPoint] = []
    test_results: Dict[str, int] = {}


class WorkloadDistribution(BaseModel):
    officer: str
    count: int


class RegulatorDashboardStats(BaseModel):
    pending_by_stage: Dict[str, int]
    workload_by_office: Dict[str, int]
    workload_distribution: List[WorkloadDistribution] = []
    expiry_summaries: Dict[str, int]
    cert_status_distribution: Dict[str, int] = {}
    application_trend: List[TrendDataPoint] = []
    enforcement_summary: Dict[str, int] = {}
    standards_calibration: Dict[str, int] = {}


class AdminDashboardStats(BaseModel):
    active_users: int
    inactive_users: int = 0
    total_users: int
    role_distribution: Dict[str, int]
    centre_configuration: int
    total_instruments: int = 0
    total_applications: int = 0
    total_certificates: int = 0
    total_inspections: int = 0
    total_standards: int = 0
    total_enforcement_cases: int = 0
    total_repair_records: int = 0
    recent_audit_events: int = 0
    pending_reviews: int = 0
    pending_inspections: int = 0
    overdue_standards: int = 0


class DashboardResponse(BaseModel):
    owner: Optional["OwnerDashboardStats"] = None
    lmo: Optional["LMODashboardStats"] = None
    gatc: Optional["GATCDashboardStats"] = None
    regulator: Optional["RegulatorDashboardStats"] = None
    admin: Optional["AdminDashboardStats"] = None


OwnerDashboardStats.model_rebuild()
LMODashboardStats.model_rebuild()
GATCDashboardStats.model_rebuild()
RegulatorDashboardStats.model_rebuild()
AdminDashboardStats.model_rebuild()
DashboardResponse.model_rebuild()