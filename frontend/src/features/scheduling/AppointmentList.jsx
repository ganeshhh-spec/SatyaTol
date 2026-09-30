import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, ChevronRight, Filter, X } from 'lucide-react'
import api from '../../lib/api'
import { formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function AppointmentList() {
  const { user, isOwner, isLMO, isGATC, isRegulator, isAdmin } = useAuth()
  const [appointments, setAppointments] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [status, setStatus] = useState('')

  const statuses = ['scheduled', 'in_progress', 'completed', 'cancelled', 'no_show']

  useEffect(() => {
    fetchAppointments()
  }, [page, status])

  const fetchAppointments = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }
      if (status) params.status = status
      const response = await api.get('/appointments', { params })
      setAppointments(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to fetch appointments', error)
    } finally {
      setLoading(false)
    }
  }

  const clearFilters = () => {
    setStatus('')
    setPage(1)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
          <p className="text-gray-600">View and manage scheduled inspections</p>
        </div>
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row gap-4">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input w-full sm:w-40"
            >
              <option value="">All Statuses</option>
              {statuses.map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
            {status && (
              <button type="button" onClick={clearFilters} className="btn-secondary">
                <X className="h-4 w-4 mr-1" />
                Clear
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <svg className="animate-spin h-8 w-8 text-primary-600 mx-auto" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : appointments.length === 0 ? (
          <div className="p-8 text-center">
            <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No appointments found</h3>
            <p className="text-gray-500">No appointments match your current filters</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Appointment</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date & Time</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assigned To</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {appointments.map((appt) => (
                    <tr key={appt.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 font-medium text-gray-900">#{appt.id}</td>
                      <td className="px-4 py-4">
                        <Link to={`/applications/${appt.application_id}`} className="text-gray-900 hover:text-primary-600">
                          Application #{appt.application_id}
                        </Link>
                        <p className="text-sm text-gray-500">
                          {appt.application?.instrument?.manufacturer} {appt.application?.instrument?.model}
                        </p>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">
                        {formatDateTime(appt.scheduled_start)} — {formatDateTime(appt.scheduled_end)}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">{appt.location || 'TBD'}</td>
                      <td className="px-4 py-4 text-sm text-gray-500">
                        {appt.assigned_officer?.full_name || appt.assigned_centre?.full_name || 'Unassigned'}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`badge ${getStatusBadge(appt.status)}`}>{getStatusLabel(appt.status)}</span>
                      </td>
                      <td className="px-4 py-4 text-right">
                        <Link to={`/appointments/${appt.id}`} className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center justify-end">
                          View <ChevronRight className="h-4 w-4 ml-1" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {total > pageSize && (
              <div className="p-4 border-t border-gray-200 flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} results
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="btn-secondary px-3 py-1"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page * pageSize >= total}
                    className="btn-secondary px-3 py-1"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}