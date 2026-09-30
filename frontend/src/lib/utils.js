import { clsx } from 'clsx'

export function cn(...inputs) {
  return clsx(inputs)
}

export function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getStatusBadge(status) {
  const statusMap = {
    // Application statuses
    draft: 'badge-gray',
    submitted: 'badge-blue',
    under_review: 'badge-yellow',
    correction_requested: 'badge-yellow',
    resubmitted: 'badge-blue',
    approved_for_scheduling: 'badge-green',
    scheduled: 'badge-blue',
    inspection_in_progress: 'badge-purple',
    inspection_recorded: 'badge-blue',
    decision_pending: 'badge-yellow',
    completed: 'badge-green',
    rejected: 'badge-red',
    withdrawn: 'badge-gray',
    cancelled: 'badge-gray',
    // Inspection results
    pass: 'badge-green',
    fail: 'badge-red',
    needs_follow_up: 'badge-yellow',
    // Certificate statuses
    valid: 'badge-green',
    expired: 'badge-red',
    revoked: 'badge-red',
    superseded: 'badge-purple',
    // Appointment statuses
    scheduled: 'badge-blue',
    in_progress: 'badge-purple',
    completed: 'badge-green',
    cancelled: 'badge-gray',
    no_show: 'badge-red',
  }
  return statusMap[status] || 'badge-gray'
}

export function getStatusLabel(status) {
  const labels = {
    draft: 'Draft',
    submitted: 'Submitted',
    under_review: 'Under Review',
    correction_requested: 'Correction Required',
    resubmitted: 'Resubmitted',
    approved_for_scheduling: 'Approved for Scheduling',
    scheduled: 'Scheduled',
    inspection_in_progress: 'Inspection in Progress',
    inspection_recorded: 'Inspection Recorded',
    decision_pending: 'Decision Pending',
    completed: 'Completed',
    rejected: 'Rejected',
    withdrawn: 'Withdrawn',
    cancelled: 'Cancelled',
    pass: 'Pass',
    fail: 'Fail',
    needs_follow_up: 'Needs Follow-up',
    valid: 'Valid',
    expired: 'Expired',
    revoked: 'Revoked',
    superseded: 'Superseded',
    in_progress: 'In Progress',
    no_show: 'No Show',
  }
  return labels[status] || status
}

export function getRoleLabel(role) {
  const labels = {
    owner: 'Instrument Owner',
    lmo: 'Legal Metrology Officer',
    gatc: 'Government Approved Test Centre',
    regulator: 'Regulator / Supervisor',
    admin: 'Platform Administrator',
  }
  return labels[role] || role
}