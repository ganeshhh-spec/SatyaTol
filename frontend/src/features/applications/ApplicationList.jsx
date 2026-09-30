import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Filter, X, FileText, ChevronRight } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function ApplicationList() {
  const { user, isOwner, isLMO, isGATC, isRegulator, isAdmin } = useAuth()
  const [applications, setApplications] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [status, setStatus] = useState('')
  const [verificationType, setVerificationType] = useState('')

  const statuses = [
    'draft', 'submitted', 'under_review', 'correction_requested', 'resubmitted',
    'approved_for_scheduling', 'scheduled', 'inspection_in_progress', 'inspection_recorded',
    'decision_pending', 'completed', 'rejected', 'withdrawn', 'cancelled'
  ]

  const types = ['initial', 'reverification']

  useEffect(() => {
    fetchApplications()
  }, [page, status, verificationType])

  const fetchApplications = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }
      if (status) params.status = status
      if (verificationType) params.verification_type = verificationType
      const response = await api.get('/applications', { params })
      setApplications(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to fetch applications', error)
    } finally {
      setLoading(false)
    }
  }

  const clearFilters = () => {
    setStatus('')
    setVerificationType('')
    setPage(1)
  }

  const hasFilters = status || verificationType

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
          <p className="text-gray-600">Manage verification and re-verification applications</p>
        </div>
        {(isOwner || isAdmin) && (
          <Link to="/applications/new" className="btn-primary">
            <Plus className="h-4 w-4 mr-2" />
            New Application
          </Link>
        )}
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row gap-4">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input w-full sm:w-48"
            >
              <option value="">All Statuses</option>
              {statuses.map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
            <select
              value={verificationType}
              onChange={(e) => setVerificationType(e.target.value)}
              className="input w-full sm:w-40"
            >
              <option value="">All Types</option>
              {types.map((t) => (
                <option key={t} value={t}>{t === 'initial' ? 'Initial' : 'Re-verification'}</option>
              ))}
            </select>
            {hasFilters && (
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
        ) : applications.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No applications found</h3>
            {isOwner && (
              <p className="text-gray-500 mb-4">Submit your first verification application</p>
            )}
            {isOwner && (
              <Link to="/applications/new" className="btn-primary inline-flex">
                <Plus className="h-4 w-4 mr-2" />
                New Application
              </Link>
            )}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reference</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instrument</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Submitted</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {applications.map((app) => (
                    <tr key={app.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <Link to={`/applications/${app.id}`} className="font-medium text-gray-900 hover:text-primary-600">
                          #{app.id}
                        </Link>
                      </td>
                      <td className="px-4 py-4">
                        <Link to={`/instruments/${app.instrument?.id}`} className="text-gray-900 hover:text-primary-600">
                          {app.instrument?.manufacturer} {app.instrument?.model}
                        </Link>
                        <p className="text-sm text-gray-500 font-mono">{app.instrument?.serial_number}</p>
                      </td>
                      <td className="px-4 py-4">
                        <span className="badge badge-blue">{app.verification_type === 'initial' ? 'Initial' : 'Re-verification'}</span>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`badge ${getStatusBadge(app.status)}`}>{getStatusLabel(app.status)}</span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">{formatDate(app.submitted_at || app.created_at)}</td>
                      <td className="px-4 py-4 text-right">
                        <Link to={`/applications/${app.id}`} className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center justify-end">
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