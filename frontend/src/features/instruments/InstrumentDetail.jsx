import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Scale, Package, FileText, Calendar, Award, AlertTriangle, Edit, Clock, MapPin, Hash, ArrowLeft, ChevronRight, History } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function InstrumentDetail() {
  const { id } = useParams()
  const { user, isOwner, isLMO, isAdmin, isRegulator, isGATC } = useAuth()
  const [instrument, setInstrument] = useState(null)
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchInstrument()
  }, [id])

  const fetchInstrument = async () => {
    setLoading(true)
    try {
      const [instRes, appsRes] = await Promise.all([
        api.get(`/instruments/${id}`),
        api.get('/applications', { params: { instrument_id: id, page_size: 20 } }),
      ])
      setInstrument(instRes.data)
      setApplications(appsRes.data.items)
    } catch (error) {
      console.error('Failed to fetch instrument', error)
    } finally {
      setLoading(false)
    }
  }

  const canEdit = isOwner && instrument?.owner_id === user?.id

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

  if (!instrument) {
    return (
      <div className="text-center py-12">
        <Scale className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">Instrument not found</h3>
        <Link to="/instruments" className="btn-primary mt-4 inline-flex">Back to Instruments</Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button onClick={() => window.history.back()} className="btn-ghost p-2 mr-4">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{instrument.manufacturer} {instrument.model}</h1>
            <p className="text-gray-600">{instrument.instrument_type} • {instrument.category.replace(/_/g, ' ')}</p>
          </div>
        </div>
        {canEdit && (
          <Link to={`/instruments/${id}/edit`} className="btn-secondary">
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Instrument Details</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">Serial Number</dt>
                <dd className="font-mono text-gray-900 mt-1">{instrument.serial_number}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Category</dt>
                <dd className="mt-1"><span className="badge badge-gray">{instrument.category.replace(/_/g, ' ')}</span></dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Instrument Type</dt>
                <dd className="mt-1 text-gray-900">{instrument.instrument_type}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Manufacturer</dt>
                <dd className="mt-1 text-gray-900">{instrument.manufacturer}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Model</dt>
                <dd className="mt-1 text-gray-900">{instrument.model}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Capacity / Range</dt>
                <dd className="mt-1 text-gray-900">{instrument.capacity || '-'} {instrument.unit || ''}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Status</dt>
                <dd className="mt-1"><span className={`badge ${getStatusBadge(instrument.status)}`}>{getStatusLabel(instrument.status)}</span></dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Registered On</dt>
                <dd className="mt-1 text-gray-900">{formatDate(instrument.registration_date)}</dd>
              </div>
              {instrument.location && (
                <div className="sm:col-span-2">
                  <dt className="text-sm text-gray-500">Location</dt>
                  <dd className="mt-1 text-gray-900 flex items-center">
                    <MapPin className="h-4 w-4 mr-1 text-gray-400" />
                    {instrument.location}
                  </dd>
                </div>
              )}
              {instrument.use_context && (
                <div className="sm:col-span-2">
                  <dt className="text-sm text-gray-500">Use Context</dt>
                  <dd className="mt-1 text-gray-900">{instrument.use_context}</dd>
                </div>
              )}
            </dl>
          </div>

          <div className="card">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Applications</h2>
              <Link to="/applications/new" className="btn-secondary text-sm">New Application</Link>
            </div>
            <div className="divide-y divide-gray-100">
              {applications.length === 0 ? (
                <div className="p-6 text-center text-gray-500">No applications for this instrument</div>
              ) : (
                applications.map((app) => (
                  <Link key={app.id} to={`/applications/${app.id}`} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">Application #{app.id}</p>
                      <p className="text-sm text-gray-500">
                        {app.verification_type === 'initial' ? 'Initial' : 'Re-verification'} • {formatDate(app.submitted_at || app.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`badge ${getStatusBadge(app.status)}`}>{getStatusLabel(app.status)}</span>
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    </div>
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link to="/applications/new" className="btn-secondary w-full justify-start">
                <FileText className="h-4 w-4 mr-2" />
                New Application
              </Link>
              <Link to="/appointments" className="btn-secondary w-full justify-start">
                <Calendar className="h-4 w-4 mr-2" />
                View Appointments
              </Link>
              <Link to="/certificates" className="btn-secondary w-full justify-start">
                <Award className="h-4 w-4 mr-2" />
                View Certificates
              </Link>
              <Link to={`/instruments/${id}/history`} className="btn-secondary w-full justify-start">
                <History className="h-4 w-4 mr-2" />
                View History (Digital Passport)
              </Link>
            </div>
          </div>

          <div className="card p-6 bg-gray-50 border-yellow-200">
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-gray-900">Prototype System</h3>
                <p className="text-sm text-gray-600 mt-1">
                  This is a prototype for PS-26036. Data is synthetic and not legally binding.
                  Certificates issued here are not official legal metrology certificates.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}