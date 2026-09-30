import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { FileText, ChevronRight, Clock, User, Building2, Paperclip, AlertTriangle, Edit, ArrowLeft, CheckCircle, XCircle, Eye, Calendar, Award } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

const statusFlow = [
  'draft',
  'submitted',
  'under_review',
  'correction_requested',
  'resubmitted',
  'approved_for_scheduling',
  'scheduled',
  'inspection_in_progress',
  'inspection_recorded',
  'decision_pending',
  'completed',
]

export default function ApplicationDetail() {
  const { id } = useParams()
  const { user, isOwner, isLMO, isGATC, isRegulator, isAdmin, canIssueCertificate } = useAuth()
  const [application, setApplication] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchApplication()
  }, [id])

  const fetchApplication = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/applications/${id}`)
      setApplication(response.data)
    } catch (error) {
      console.error('Failed to fetch application', error)
    } finally {
      setLoading(false)
    }
  }

  const canReview = isLMO && application?.assigned_officer_id === user?.id
  const canSchedule = (isLMO || isGATC || isAdmin) && application?.status === 'approved_for_scheduling'
  const canInspect = (isLMO || isGATC) && ['scheduled', 'inspection_in_progress'].includes(application?.status)
  
  const hasDraftInspection = application?.inspections?.some(i => !i.is_finalized)
  const hasFinalizedInspection = application?.inspections?.some(i => i.is_finalized)
  const finalizedInspection = application?.inspections?.find(i => i.is_finalized)
  const canFinalizeInspection = (isLMO || isGATC) && hasDraftInspection && ['scheduled', 'inspection_in_progress', 'inspection_recorded'].includes(application?.status)
  
  const isIneligibleForCertificate = application?.status !== 'decision_pending' ||
    !finalizedInspection ||
    finalizedInspection.result !== 'pass'
  const canDecide = canIssueCertificate && application?.status === 'decision_pending' && 
    finalizedInspection?.result === 'pass'

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <svg className="animate-spin h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    )
  }

  if (!application) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">Application not found</h3>
        <Link to="/applications" className="btn-primary mt-4 inline-flex">Back to Applications</Link>
      </div>
    )
  }

  const currentStatusIndex = statusFlow.indexOf(application.status)
  const isTerminal = ['completed', 'rejected', 'withdrawn', 'cancelled'].includes(application.status)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button onClick={() => window.history.back()} className="btn-ghost p-2 mr-4">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Application #{application.id}</h1>
            <p className="text-gray-600">
              {application.verification_type === 'initial' ? 'Initial' : 'Re-verification'} •
              {application.instrument?.manufacturer} {application.instrument?.model}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`badge ${getStatusBadge(application.status)}`}>{getStatusLabel(application.status)}</span>
          {(isOwner && application.applicant_id === user?.id) || isAdmin ? (
            <Link to={`/applications/${id}/edit`} className="btn-secondary text-sm">
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Link>
          ) : null}
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Status Timeline</h2>
          </div>
        </div>
        <div className="px-4 py-4">
          <div className="relative">
            <div className="absolute left-7 top-0 bottom-0 w-0.5 bg-gray-200" />
            {statusFlow.map((status, index) => {
              const isCompleted = index < currentStatusIndex
              const isCurrent = index === currentStatusIndex
              const isFuture = index > currentStatusIndex
              const isCorrection = status === 'correction_requested'
              const isRejected = ['rejected', 'withdrawn', 'cancelled'].includes(application.status) && index >= currentStatusIndex

              return (
                <div key={status} className="relative flex items-start mb-6 last:mb-0">
                  <div className={`relative flex items-center justify-center h-10 w-10 rounded-full ${
                    isCompleted ? 'bg-green-500' : isCurrent ? 'bg-primary-600' : 'bg-gray-200'
                  }`}>
                    {isCompleted && <CheckCircle className="h-6 w-6 text-white" />}
                    {isCurrent && !isTerminal && <div className="h-3 w-3 rounded-full bg-white animate-pulse" />}
                    {isCurrent && isTerminal && <CheckCircle className="h-6 w-6 text-white" />}
                    {isFuture && !isRejected && <div className="h-3 w-3 rounded-full bg-gray-300" />}
                    {isRejected && <XCircle className="h-6 w-6 text-red-500" />}
                  </div>
                  <div className="ml-4 flex-1">
                    <p className={`text-sm font-medium ${isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-500'}`}>
                      {status.replace(/_/g, ' ')}
                    </p>
                    {isCurrent && !isTerminal && (
                      <p className="text-xs text-primary-600 mt-1">Current stage</p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Application Details</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">Reference Number</dt>
                <dd className="font-mono text-gray-900 mt-1">#{application.id}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Verification Type</dt>
                <dd className="mt-1"><span className="badge badge-blue">{application.verification_type === 'initial' ? 'Initial' : 'Re-verification'}</span></dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Instrument</dt>
                <dd className="mt-1">
                  <Link to={`/instruments/${application.instrument?.id}`} className="text-gray-900 hover:text-primary-600">
                    {application.instrument?.manufacturer} {application.instrument?.model}
                  </Link>
                  <p className="text-sm text-gray-500 font-mono">{application.instrument?.serial_number}</p>
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Applicant</dt>
                <dd className="mt-1 flex items-center">
                  <User className="h-4 w-4 mr-1 text-gray-400" />
                  {application.applicant?.full_name} ({application.applicant?.email})
                </dd>
              </div>
              {application.jurisdiction && (
                <div>
                  <dt className="text-sm text-gray-500">Jurisdiction</dt>
                  <dd className="mt-1 text-gray-900">{application.jurisdiction}</dd>
                </div>
              )}
              {application.assigned_officer && (
                <div>
                  <dt className="text-sm text-gray-500">Assigned Officer</dt>
                  <dd className="mt-1 flex items-center">
                    <User className="h-4 w-4 mr-1 text-gray-400" />
                    {application.assigned_officer.full_name}
                  </dd>
                </div>
              )}
              {application.assigned_centre && (
                <div>
                  <dt className="text-sm text-gray-500">Assigned Centre</dt>
                  <dd className="mt-1 flex items-center">
                    <Building2 className="h-4 w-4 mr-1 text-gray-400" />
                    {application.assigned_centre.full_name}
                  </dd>
                </div>
              )}
              {application.submitted_at && (
                <div>
                  <dt className="text-sm text-gray-500">Submitted On</dt>
                  <dd className="mt-1 text-gray-900">{formatDateTime(application.submitted_at)}</dd>
                </div>
              )}
              {application.requested_appointment && (
                <div>
                  <dt className="text-sm text-gray-500">Requested Appointment</dt>
                  <dd className="mt-1 text-gray-900">{formatDateTime(application.requested_appointment)}</dd>
                </div>
              )}
              {application.fee_amount && (
                <div>
                  <dt className="text-sm text-gray-500">Fee</dt>
                  <dd className="mt-1 text-gray-900 flex items-center">
                    ₹{application.fee_amount} {application.fee_paid ? '(Paid - Simulated)' : '(Pending - Simulated)'}
                    <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">Demo Payment</span>
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {application.attachments && application.attachments.length > 0 && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Paperclip className="h-5 w-5 mr-2 text-gray-500" />
                Attachments
              </h2>
              <div className="space-y-2">
                {application.attachments.map((att) => (
                  <div key={att.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <Paperclip className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{att.filename}</p>
                        <p className="text-xs text-gray-500">{att.media_type} • {formatDateTime(att.uploaded_at)}</p>
                      </div>
                    </div>
                    <a href={`/uploads/${att.storage_key}`} target="_blank" rel="noopener noreferrer" className="btn-secondary text-sm">
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}

          {application.appointments && application.appointments.length > 0 && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Calendar className="h-5 w-5 mr-2 text-gray-500" />
                Appointments
              </h2>
              <div className="space-y-3">
                {application.appointments.map((appt) => (
                  <Link key={appt.id} to={`/appointments/${appt.id}`} className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">Appointment #{appt.id}</p>
                        <p className="text-sm text-gray-500">
                          {formatDateTime(appt.scheduled_start)} — {formatDateTime(appt.scheduled_end)}
                        </p>
                        {appt.location && <p className="text-sm text-gray-500">{appt.location}</p>}
                      </div>
                      <span className={`badge ${getStatusBadge(appt.status)}`}>{getStatusLabel(appt.status)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {application.inspections && application.inspections.length > 0 && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Inspections</h2>
              <div className="space-y-3">
                {application.inspections.map((insp) => (
                  <div key={insp.id} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900 flex items-center">
                          Inspection #{insp.id}
                          {!insp.is_finalized && (
                            <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">Draft</span>
                          )}
                          {insp.is_finalized && (
                            <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded">Finalized</span>
                          )}
                        </p>
                        <p className="text-sm text-gray-500">
                          By {insp.inspector?.full_name} on {formatDateTime(insp.inspection_date)}
                        </p>
                        {insp.observations && <p className="text-sm text-gray-600 mt-1">{insp.observations}</p>}
                      </div>
                      <span className={`badge ${getStatusBadge(insp.result)}`}>{getStatusLabel(insp.result)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {application.certificates && application.certificates.length > 0 && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Award className="h-5 w-5 mr-2 text-gray-500" />
                Certificates
              </h2>
              <div className="space-y-3">
                {application.certificates.map((cert) => (
                  <Link key={cert.id} to={`/certificates/${cert.id}`} className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{cert.certificate_number}</p>
                        <p className="text-sm text-gray-500">
                          Issued {formatDate(cert.issue_date)} • Valid until {formatDate(cert.valid_until)}
                        </p>
                      </div>
                      <span className={`badge ${getStatusBadge(cert.status)}`}>{getStatusLabel(cert.status)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {application.remarks && (
            <div className="card p-6 bg-blue-50 border-blue-200">
              <h3 className="font-medium text-gray-900 mb-1">Remarks</h3>
              <p className="text-gray-700">{application.remarks}</p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions</h2>
            <div className="space-y-3">
              {application.status === 'draft' && application.applicant_id === user?.id && (
                <button className="btn-primary w-full justify-start" onClick={() => api.post(`/applications/${id}/submit`)}>
                  <Paperclip className="h-4 w-4 mr-2" />
                  Submit Application
                </button>
              )}

              {application.status === 'correction_requested' && application.applicant_id === user?.id && (
                <button className="btn-primary w-full justify-start" onClick={() => api.post(`/applications/${id}/resubmit`)}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Resubmit After Correction
                </button>
              )}

              {canReview && ['submitted', 'resubmitted'].includes(application.status) && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-gray-700">Review Actions</p>
                  <button className="btn-primary w-full justify-start" onClick={() => handleReview('approve')}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve for Scheduling
                  </button>
                  <button className="btn-secondary w-full justify-start" onClick={() => handleReview('request_correction')}>
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    Request Correction
                  </button>
                  <button className="btn-danger w-full justify-start" onClick={() => handleReview('reject')}>
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </button>
                </div>
              )}

              {canSchedule && (
                <Link to="/appointments" className="btn-primary w-full justify-start" state={{ applicationId: id }}>
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Appointment
                </Link>
              )}

              {canInspect && !hasFinalizedInspection && !hasDraftInspection && (
                <Link to={`/inspections/new/${id}`} className="btn-primary w-full justify-start">
                  <Eye className="h-4 w-4 mr-2" />
                  Record Inspection
                </Link>
              )}

              {canFinalizeInspection && (
                <Link to={`/inspections/${application.inspections.find(i => !i.is_finalized).id}/${id}`} className="btn-primary w-full justify-start">
                  <Flag className="h-4 w-4 mr-2" />
                  Finalize Inspection
                </Link>
              )}

              {canDecide && !isIneligible && (
                <Link to={`/certificates/issue/${id}`} className="btn-primary w-full justify-start">
                  <Award className="h-4 w-4 mr-2" />
                  Issue Certificate
                </Link>
              )}

              {canDecide && isIneligible && (
                <button className="btn-primary w-full justify-start opacity-50 cursor-not-allowed" disabled>
                  <Award className="h-4 w-4 mr-2" />
                  Issue Certificate (Prerequisites not met)
                </button>
              )}

              {canDecide && (
                <Link to={`/certificates/issue/${id}`} className="btn-primary w-full justify-start">
                  <Award className="h-4 w-4 mr-2" />
                  Issue Certificate
                </Link>
              )}

              {isTerminal && (
                <p className="text-sm text-gray-500 text-center">This application has reached a terminal state.</p>
              )}
            </div>
          </div>

          <div className="card p-6 bg-gray-50 border-yellow-200">
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-gray-900">Prototype System</h3>
                <p className="text-sm text-gray-600 mt-1">
                  This is a prototype for PS-26036. Data is synthetic and not legally binding.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  function handleReview(action) {
    const reason = action === 'approve' ? 'Approved for scheduling' : prompt(`${action === 'reject' ? 'Rejection' : 'Correction'} reason:`)
    if (reason !== null) {
      api.post(`/applications/${id}/review`, { action, reason }).then(() => fetchApplication())
    }
  }
}