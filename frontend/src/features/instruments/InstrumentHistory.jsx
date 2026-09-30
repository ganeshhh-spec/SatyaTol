import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, FileText, Calendar, Search, Award, ClipboardCheck, AlertTriangle, CheckCircle, XCircle, Package, User, Building2, History, ChevronDown, ChevronUp, Filter } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { cn } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function InstrumentHistory() {
  const { id } = useParams()
  const { user, isOwner, isLMO, isGATC, isRegulator, isAdmin } = useAuth()
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState('all')

  useEffect(() => {
    fetchHistory()
  }, [id])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/instruments/${id}/history`)
      setHistory(response.data)
    } catch (error) {
      console.error('Failed to fetch instrument history', error)
    } finally {
      setLoading(false)
    }
  }

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

  if (!history) {
    return (
      <div className="text-center py-12">
        <Package className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">Instrument not found</h3>
        <Link to="/instruments" className="btn-primary mt-4 inline-flex">Back to Instruments</Link>
      </div>
    )
  }

  const { instrument, timeline } = history

  const filteredTimeline = timeline.filter(event => {
    if (activeFilter === 'all') return true
    return event.type.startsWith(activeFilter)
  })

  const filterOptions = [
    { value: 'all', label: 'All Events', icon: History },
    { value: 'instrument', label: 'Instrument', icon: Package },
    { value: 'application', label: 'Applications', icon: FileText },
    { value: 'appointment', label: 'Appointments', icon: Calendar },
    { value: 'inspection', label: 'Inspections', icon: ClipboardCheck },
    { value: 'certificate', label: 'Certificates', icon: Award },
    { value: 'audit', label: 'Audit', icon: Search },
  ]

  const getEventIcon = (type) => {
    if (type.startsWith('instrument')) return Package
    if (type.startsWith('application')) return FileText
    if (type.startsWith('appointment')) return Calendar
    if (type.startsWith('inspection')) return ClipboardCheck
    if (type.startsWith('certificate')) {
      if (type.includes('revoked')) return XCircle
      if (type.includes('superseded')) return AlertTriangle
      return Award
    }
    return History
  }

  const getEventColor = (type) => {
    if (type.startsWith('instrument')) return 'text-blue-600 bg-blue-50'
    if (type.startsWith('application')) return 'text-purple-600 bg-purple-50'
    if (type.startsWith('appointment')) return 'text-green-600 bg-green-50'
    if (type.startsWith('inspection')) return 'text-orange-600 bg-orange-50'
    if (type.startsWith('certificate')) {
      if (type.includes('revoked')) return 'text-red-600 bg-red-50'
      if (type.includes('superseded')) return 'text-yellow-600 bg-yellow-50'
      return 'text-indigo-600 bg-indigo-50'
    }
    return 'text-gray-600 bg-gray-50'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button onClick={() => window.history.back()} className="btn-ghost p-2 mr-4">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Instrument History</h1>
            <p className="text-gray-600">Digital Passport - {instrument.manufacturer} {instrument.model}</p>
          </div>
        </div>
        <Link to={`/instruments/${id}`} className="btn-secondary">
          <Package className="h-4 w-4 mr-2" />
          View Instrument
        </Link>
      </div>

      <div className="card p-6 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <dt className="text-sm text-gray-500">Serial Number</dt>
            <dd className="font-mono text-lg text-gray-900 mt-1">{instrument.serial_number}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Category</dt>
            <dd className="mt-1"><span className="badge badge-blue">{instrument.category.replace(/_/g, ' ')}</span></dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Status</dt>
            <dd className="mt-1"><span className={`badge ${getStatusBadge(instrument.status)}`}>{getStatusLabel(instrument.status)}</span></dd>
          </div>
          <div className="md:col-span-3">
            <dt className="text-sm text-gray-500">Location</dt>
            <dd className="mt-1 text-gray-900">{instrument.location || 'Not specified'}</dd>
          </div>
          <div className="md:col-span-3">
            <dt className="text-sm text-gray-500">Use Context</dt>
            <dd className="mt-1 text-gray-900">{instrument.use_context || 'Not specified'}</dd>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-wrap gap-2">
            {filterOptions.map((filter) => (
              <button
                key={filter.value}
                onClick={() => setActiveFilter(filter.value)}
                className={cn(
                  'btn-sm px-3 py-1.5 rounded-lg transition-colors flex items-center',
                  activeFilter === filter.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                <filter.icon className="h-4 w-4 mr-1" />
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        <div className="divide-y divide-gray-100">
          {filteredTimeline.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Filter className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No events match the selected filter</p>
            </div>
          ) : (
            filteredTimeline.map((event, index) => {
              const Icon = getEventIcon(event.type)
              const colorClass = getEventColor(event.type)
              
              return (
                <div key={`${event.entity_type}-${event.entity_id}-${index}`} className="p-4 hover:bg-gray-50">
                  <div className="flex items-start">
                    <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${colorClass}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="ml-4 flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-gray-900">{event.title}</h3>
                        <span className="text-xs text-gray-500 whitespace-nowrap">{event.date ? formatDateTime(event.date) : 'N/A'}</span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{event.details}</p>
                      <div className="flex items-center mt-2 space-x-4 text-xs text-gray-500">
                        <span className="px-2 py-0.5 bg-gray-100 rounded">{event.entity_type}</span>
                        <span>ID: {event.entity_id}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })
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
  )
}