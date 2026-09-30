import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Calendar,
  Clock,
  MapPin,
  User,
  Building2,
  FileText,
  ArrowLeft,
  ChevronRight,
  AlertTriangle,
  Scale,
  XCircle,
  Eye,
} from 'lucide-react'
import api from '../../lib/api'
import { formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function AppointmentDetail() {
  const { id } = useParams()
  const { user, isOwner, isLMO, isGATC, isRegulator, isAdmin } = useAuth()
  const [appointment, setAppointment] = useState(null)
  const [application, setApplication] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [cancelling, setCancelling] = useState(false)

  useEffect(() => {
    fetchAppointment()
  }, [id])

  const fetchAppointment = async () => {
    setLoading(true)
    setError(null)
    try {
      const apptRes = await api.get(`/appointments/${id}`)
      setAppointment(apptRes.data)

      if (apptRes.data?.application_id) {
        try {
          const appRes = await api.get(`/applications/${apptRes.data.application_id}`)
          setApplication(appRes.data)
        } catch (appErr) {
          console.warn('Could not load linked application details', appErr)
        }
      }
    } catch (err) {
      console.error('Failed to fetch appointment', err)
      if (err.response?.status === 404) {
        setError('Appointment not found')
      } else if (err.response?.status === 403) {
        setError('You are not authorized to view this appointment')
      } else {
        setError(err.response?.data?.detail || 'Failed to load appointment details')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) {
      return
    }

    setCancelling(true)
    try {
      const response = await api.post(`/appointments/${id}/cancel`)
      setAppointment(response.data)
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel appointment')
    } finally {
      setCancelling(false)
    }
  }

  const canCancel = (isLMO || isAdmin) && appointment?.status === 'scheduled'
  const canInspect = (isLMO || isGATC) && ['scheduled', 'in_progress'].includes(appointment?.status)

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

  if (error || !appointment) {
    return (
      <div className="text-center py-12">
        <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">{error || 'Appointment not found'}</h3>
        <p className="text-gray-500 mt-1">
          {error === 'You are not authorized to view this appointment'
            ? 'Your account does not have permission to view this appointment.'
            : 'The appointment you are looking for does not exist.'}
        </p>
        <Link to="/appointments" className="btn-primary mt-4 inline-flex items-center">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Appointments
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link to="/appointments" className="btn-ghost p-2 mr-4">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Appointment #{appointment.id}</h1>
            <p className="text-gray-600">
              {formatDateTime(appointment.scheduled_start)} — {formatDateTime(appointment.scheduled_end)}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`badge ${getStatusBadge(appointment.status)}`}>
            {getStatusLabel(appointment.status)}
          </span>
          {canCancel && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="btn-danger text-sm flex items-center"
            >
              <XCircle className="h-4 w-4 mr-1.5" />
              {cancelling ? 'Cancelling...' : 'Cancel Appointment'}
            </button>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Appointment Details Card */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-gray-500" />
              Appointment Information
            </h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">Appointment ID</dt>
                <dd className="font-mono text-gray-900 mt-1">#{appointment.id}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Status</dt>
                <dd className="mt-1">
                  <span className={`badge ${getStatusBadge(appointment.status)}`}>
                    {getStatusLabel(appointment.status)}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Scheduled Start</dt>
                <dd className="mt-1 text-gray-900 flex items-center">
                  <Clock className="h-4 w-4 mr-1.5 text-gray-400" />
                  {formatDateTime(appointment.scheduled_start)}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Scheduled End</dt>
                <dd className="mt-1 text-gray-900 flex items-center">
                  <Clock className="h-4 w-4 mr-1.5 text-gray-400" />
                  {formatDateTime(appointment.scheduled_end)}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Mode</dt>
                <dd className="mt-1 text-gray-900 capitalize">
                  {appointment.mode ? appointment.mode.replace(/_/g, ' ') : 'Standard'}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Location / Centre</dt>
                <dd className="mt-1 text-gray-900 flex items-center">
                  <MapPin className="h-4 w-4 mr-1.5 text-gray-400" />
                  {appointment.location || 'TBD'}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Assigned Officer</dt>
                <dd className="mt-1 flex items-center text-gray-900">
                  <User className="h-4 w-4 mr-1.5 text-gray-400" />
                  {appointment.assigned_officer ? (
                    <span>
                      {appointment.assigned_officer.full_name}{' '}
                      <span className="text-xs text-gray-500">({appointment.assigned_officer.email})</span>
                    </span>
                  ) : (
                    <span className="text-gray-400">Unassigned</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Assigned Test Centre</dt>
                <dd className="mt-1 flex items-center text-gray-900">
                  <Building2 className="h-4 w-4 mr-1.5 text-gray-400" />
                  {appointment.assigned_centre ? (
                    <span>
                      {appointment.assigned_centre.full_name}{' '}
                      <span className="text-xs text-gray-500">({appointment.assigned_centre.email})</span>
                    </span>
                  ) : (
                    <span className="text-gray-400">Unassigned</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Created At</dt>
                <dd className="mt-1 text-gray-900">{formatDateTime(appointment.created_at)}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Last Updated</dt>
                <dd className="mt-1 text-gray-900">{formatDateTime(appointment.updated_at)}</dd>
              </div>
              {appointment.notes && (
                <div className="sm:col-span-2">
                  <dt className="text-sm text-gray-500">Notes</dt>
                  <dd className="mt-1 text-gray-900 bg-gray-50 p-3 rounded border border-gray-100">
                    {appointment.notes}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Linked Application & Instrument Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <FileText className="h-5 w-5 mr-2 text-gray-500" />
                Linked Application
              </h2>
              <Link
                to={`/applications/${appointment.application_id}`}
                className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center"
              >
                View Full Application <ChevronRight className="h-4 w-4 ml-1" />
              </Link>
            </div>

            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">Application Reference</dt>
                <dd className="font-mono text-gray-900 mt-1">
                  <Link
                    to={`/applications/${appointment.application_id}`}
                    className="text-primary-600 hover:underline"
                  >
                    #{appointment.application_id}
                  </Link>
                </dd>
              </div>

              {application && (
                <>
                  <div>
                    <dt className="text-sm text-gray-500">Verification Type</dt>
                    <dd className="mt-1">
                      <span className="badge badge-blue capitalize">
                        {application.verification_type === 'initial' ? 'Initial' : 'Re-verification'}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Application Status</dt>
                    <dd className="mt-1">
                      <span className={`badge ${getStatusBadge(application.status)}`}>
                        {getStatusLabel(application.status)}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Applicant</dt>
                    <dd className="mt-1 flex items-center text-gray-900">
                      <User className="h-4 w-4 mr-1.5 text-gray-400" />
                      {application.applicant?.full_name || 'N/A'}{' '}
                      {application.applicant?.email && (
                        <span className="text-xs text-gray-500 ml-1">
                          ({application.applicant.email})
                        </span>
                      )}
                    </dd>
                  </div>
                  {application.instrument && (
                    <div className="sm:col-span-2 pt-2 border-t border-gray-100">
                      <dt className="text-sm text-gray-500 flex items-center">
                        <Scale className="h-4 w-4 mr-1.5 text-gray-400" />
                        Instrument
                      </dt>
                      <dd className="mt-1 flex items-center justify-between">
                        <div>
                          <Link
                            to={`/instruments/${application.instrument.id}`}
                            className="text-gray-900 font-medium hover:text-primary-600"
                          >
                            {application.instrument.manufacturer} {application.instrument.model}
                          </Link>
                          <p className="text-xs text-gray-500">
                            Serial: {application.instrument.serial_number} • Category:{' '}
                            {application.instrument.category?.replace(/_/g, ' ')}
                          </p>
                        </div>
                        <Link
                          to={`/instruments/${application.instrument.id}`}
                          className="btn-secondary text-xs"
                        >
                          View Instrument
                        </Link>
                      </dd>
                    </div>
                  )}
                </>
              )}
            </dl>
          </div>
        </div>

        {/* Sidebar / Quick Actions */}
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link to="/appointments" className="btn-secondary w-full justify-start">
                <Calendar className="h-4 w-4 mr-2" />
                All Appointments
              </Link>
              <Link
                to={`/applications/${appointment.application_id}`}
                className="btn-secondary w-full justify-start"
              >
                <FileText className="h-4 w-4 mr-2" />
                View Application #{appointment.application_id}
              </Link>
              {application?.instrument?.id && (
                <Link
                  to={`/instruments/${application.instrument.id}`}
                  className="btn-secondary w-full justify-start"
                >
                  <Scale className="h-4 w-4 mr-2" />
                  View Instrument Details
                </Link>
              )}
              {canInspect && (
                <Link
                  to={`/inspections/new/${appointment.application_id}`}
                  className="btn-primary w-full justify-start"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  Record Inspection
                </Link>
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
}
